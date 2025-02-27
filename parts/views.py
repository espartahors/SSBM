# parts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .models import Part, Document, MarkedPart, ImportLog
from .forms import PartForm, DocumentForm, DocumentUpdateForm, MarkedPartForm, ImportCSVForm, PartSearchForm
from .services.csv_handler import CSVHandler, CSVImportException
from .services.document_handler import DocumentHandler
from users.models import UserActivity

# Tree View Components
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Part, MarkedPart
from django.views.decorators.csrf import ensure_csrf_cookie

class DashboardView(LoginRequiredMixin, ListView):
    """Main dashboard with the parts tree and search"""
    model = Part
    template_name = 'parts/dashboard.html'
    context_object_name = 'root_parts'
    
    def get_queryset(self):
        # Get only root parts (level 0)
        return Part.objects.filter(level=0).order_by('part_id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add search form
        context['search_form'] = PartSearchForm(self.request.GET)
        
        # Add marked parts for this user
        marked_parts = MarkedPart.objects.filter(user=self.request.user)
        context['marked_parts'] = marked_parts
        
        # Check if the user has expanded tree preference
        context['show_tree_expanded'] = self.request.user.profile.show_parts_tree_expanded
        
        # Check user permissions
        context['can_add_parts'] = self.request.user.profile.can_add_parts
        context['can_edit_parts'] = self.request.user.profile.can_edit_parts
        context['can_delete_parts'] = self.request.user.profile.can_delete_parts
        context['can_upload_csv'] = self.request.user.profile.can_upload_csv
        
        return context

@login_required
def part_tree_json(request):
    """API endpoint to get the parts tree as JSON for the tree view"""
    def build_tree_data(parts, marked_part_ids=None):
        if marked_part_ids is None:
            marked_part_ids = []
            
        tree_data = []
        for part in parts:
            # Check if part has documents
            has_documents = part.documents.exists()
            
            # Build node data
            node = {
                'id': part.id,
                'part_id': part.part_id,
                'text': f"{part.part_id} - {part.name}",
                'level': part.level,
                'has_documents': has_documents,
                'marked': part.id in marked_part_ids
            }
            
            # Recursively add children
            children = part.children.all().order_by('part_id')
            if children:
                node['children'] = build_tree_data(children, marked_part_ids)
            
            tree_data.append(node)
        return tree_data
    
    # Get user's marked parts for highlighting in the tree
    marked_part_ids = list(MarkedPart.objects.filter(
        user=request.user
    ).values_list('part_id', flat=True))
    
    # Get root parts (level 0)
    root_parts = Part.objects.filter(level=0).order_by('part_id')
    
    # Build tree data
    tree_data = build_tree_data(root_parts, marked_part_ids)
    
    return JsonResponse(tree_data, safe=False)

@login_required
def codification_tree_json(request):
    """API endpoint to get the parts tree as JSON for the codification view"""
    def build_codification_tree(parts):
        tree_data = []
        
        # Group parts by system code (level 1)
        systems = {}
        for part in parts:
            if part.system_code:
                if part.system_code not in systems:
                    systems[part.system_code] = {
                        'code': part.system_code,
                        'description': part.name,
                        'level': 1,
                        'id': part.id,
                        'children': []
                    }
                
                # Add subsystems if present
                if part.subsystem_code:
                    # Find or create subsystem
                    subsystem = next(
                        (s for s in systems[part.system_code]['children'] 
                        if s['code'] == part.subsystem_code), 
                        None
                    )
                    
                    if not subsystem:
                        subsystem = {
                            'code': part.subsystem_code,
                            'description': part.name,
                            'level': 2,
                            'id': part.id,
                            'children': []
                        }
                        systems[part.system_code]['children'].append(subsystem)
                    
                    # Continue for component and subcomponent...
        
        # Convert systems dict to list
        for system_code, system in systems.items():
            tree_data.append(system)
        
        return tree_data
    
    # Get parts with codification data
    parts = Part.objects.exclude(equipment_code='').order_by('system_code', 'subsystem_code')
    
    # Build tree data
    tree_data = build_codification_tree(parts)
    
    return JsonResponse(tree_data, safe=False)

@login_required
def parts_tree_view(request):
    """View for rendering the parts tree page"""
    # Get root parts for initial display
    root_parts = Part.objects.filter(level=0).order_by('part_id')
    
    # Get user preferences for tree display
    show_expanded = request.user.profile.show_parts_tree_expanded
    
    # Get marked parts for this user
    marked_parts = MarkedPart.objects.filter(user=request.user).select_related('part')
    
    context = {
        'root_parts': root_parts,
        'show_tree_expanded': show_expanded,
        'marked_parts': marked_parts,
        'can_add_parts': request.user.profile.can_add_parts,
        'can_edit_parts': request.user.profile.can_edit_parts,
        'can_delete_parts': request.user.profile.can_delete_parts,
    }
    
    return render(request, 'parts/parts_tree.html', context)

class PartListView(LoginRequiredMixin, ListView):
    """List view of all parts (flat view)"""
    model = Part
    template_name = 'parts/part_list.html'
    context_object_name = 'parts'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Part.objects.all().order_by('level', 'part_id')
        
        # Apply search if form is valid
        form = PartSearchForm(self.request.GET)
        if form.is_valid():
            search_term = form.cleaned_data.get('search_term')
            level = form.cleaned_data.get('level')
            has_documents = form.cleaned_data.get('has_documents')
            is_marked = form.cleaned_data.get('is_marked')
            
            if search_term:
                queryset = queryset.filter(
                    Q(part_id__icontains=search_term) | 
                    Q(name__icontains=search_term) | 
                    Q(info__icontains=search_term)
                )
            
            if level is not None:
                queryset = queryset.filter(level=level)
            
            if has_documents:
                queryset = queryset.filter(documents__isnull=False).distinct()
            
            if is_marked:
                marked_part_ids = MarkedPart.objects.filter(user=self.request.user).values_list('part_id', flat=True)
                queryset = queryset.filter(id__in=marked_part_ids)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PartSearchForm(self.request.GET)
        
        # Add permissions
        context['can_add_parts'] = self.request.user.profile.can_add_parts
        context['can_edit_parts'] = self.request.user.profile.can_edit_parts
        context['can_delete_parts'] = self.request.user.profile.can_delete_parts
        
        # Add marked parts info
        marked_part_ids = MarkedPart.objects.filter(user=self.request.user).values_list('part_id', flat=True)
        context['marked_part_ids'] = list(marked_part_ids)
        
        return context

class PartDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a part"""
    model = Part
    template_name = 'parts/part_detail.html'
    context_object_name = 'part'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if the part is marked by the current user
        part = self.get_object()
        context['is_marked'] = MarkedPart.objects.filter(user=self.request.user, part=part).exists()
        
        # Add mark/unmark form
        if context['is_marked']:
            # Get the existing mark to show the note
            marked_part = MarkedPart.objects.get(user=self.request.user, part=part)
            context['marked_part'] = marked_part
        else:
            context['mark_form'] = MarkedPartForm(initial={'part': part.id})
        
        # Add parent info if exists
        if part.parent:
            context['parent'] = part.parent
        
        # Add child parts if any
        context['children'] = part.children.all().order_by('part_id')
        
        # Add documents
        context['documents'] = part.documents.all().order_by('-uploaded_at')
        
        # Check permissions
        context['can_edit_part'] = self.request.user.profile.can_edit_parts
        context['can_delete_part'] = self.request.user.profile.can_delete_parts
        context['can_add_document'] = self.request.user.profile.can_add_documents
        
        return context

class PartCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new part"""
    model = Part
    form_class = PartForm
    template_name = 'parts/part_form.html'
    
    def test_func(self):
        """Check if user has permission to add parts"""
        return self.request.user.profile.can_add_parts
    
    def form_valid(self, form):
        # Set created_by and modified_by
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='part_create',
            description=f"Created part: {form.instance.part_id} - {form.instance.name}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(self.request, f'Part {form.instance.part_id} created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Part'
        return context

class PartUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing part"""
    model = Part
    form_class = PartForm
    template_name = 'parts/part_form.html'
    
    def test_func(self):
        """Check if user has permission to edit parts"""
        return self.request.user.profile.can_edit_parts
    
    def form_valid(self, form):
        # Record who modified it
        form.instance.modified_by = self.request.user
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='part_update',
            description=f"Updated part: {form.instance.part_id} - {form.instance.name}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(self.request, f'Part {form.instance.part_id} updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Part: {self.object.part_id}'
        return context

class PartDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a part"""
    model = Part
    template_name = 'parts/part_confirm_delete.html'
    success_url = reverse_lazy('part-list')
    
    def test_func(self):
        """Check if user has permission to delete parts"""
        return self.request.user.profile.can_delete_parts
    
    def delete(self, request, *args, **kwargs):
        part = self.get_object()
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='part_delete',
            description=f"Deleted part: {part.part_id} - {part.name}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Part {part.part_id} deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def mark_part(request, pk):
    """Mark a part for the current user"""
    part = get_object_or_404(Part, pk=pk)
    
    if request.method == 'POST':
        form = MarkedPartForm(request.POST)
        if form.is_valid():
            # Check if already marked
            if not MarkedPart.objects.filter(user=request.user, part=part).exists():
                # Create new marked part
                marked_part = form.save(commit=False)
                marked_part.user = request.user
                marked_part.part = part
                marked_part.save()
                
                # Log the activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='part_mark',
                    description=f"Marked part: {part.part_id} - {part.name}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Part {part.part_id} has been marked')
            else:
                messages.info(request, f'Part {part.part_id} was already marked')
    
    return redirect('part-detail', pk=pk)

@login_required
def unmark_part(request, pk):
    """Unmark a part for the current user"""
    part = get_object_or_404(Part, pk=pk)
    
    # Try to find and delete the mark
    marked_part = MarkedPart.objects.filter(user=request.user, part=part).first()
    if marked_part:
        marked_part.delete()
        
        # Log the activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='part_unmark',
            description=f"Unmarked part: {part.part_id} - {part.name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Part {part.part_id} has been unmarked')
    else:
        messages.info(request, f'Part {part.part_id} was not marked')
    
    return redirect('part-detail', pk=pk)

@login_required
def clear_all_marks(request):
    """Clear all marks for the current user"""
    if request.method == 'POST':
        # Count how many marks were deleted
        count = MarkedPart.objects.filter(user=request.user).count()
        MarkedPart.objects.filter(user=request.user).delete()
        
        # Log the activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='clear_all_marks',
            description=f"Cleared {count} marked parts",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'All {count} marks have been cleared')
    
    return redirect('dashboard')

@login_required
def marked_parts_list(request):
    """Show all parts marked by the current user"""
    marked_parts = MarkedPart.objects.filter(user=request.user).select_related('part').order_by('-marked_at')
    
    return render(request, 'parts/marked_parts_list.html', {
        'marked_parts': marked_parts
    })

class DocumentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Upload a new document"""
    model = Document
    form_class = DocumentForm
    template_name = 'parts/document_form.html'
    
    def test_func(self):
        """Check if user has permission to add documents"""
        return self.request.user.profile.can_add_documents
    
    def get_initial(self):
        initial = super().get_initial()
        
        # If a part ID is provided in the URL, pre-select that part
        part_id = self.kwargs.get('part_id')
        if part_id:
            initial['part'] = part_id
        
        return initial
    
    def form_valid(self, form):
        # Set uploaded_by
        form.instance.uploaded_by = self.request.user
        
        # Validate the file
        uploaded_file = self.request.FILES['file']
        try:
            DocumentHandler.validate_file(uploaded_file)
        except Exception as e:
            form.add_error('file', str(e))
            return self.form_invalid(form)
        
        # Save the form to create the document
        response = super().form_valid(form)
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='document_upload',
            description=f"Uploaded document: {form.instance.title} for part {form.instance.part.part_id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(self.request, f'Document "{form.instance.title}" uploaded successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload New Document'
        
        # If we have a part_id, get the part details
        part_id = self.kwargs.get('part_id')
        if part_id:
            part = get_object_or_404(Part, pk=part_id)
            context['part'] = part
        
        return context

class DocumentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update document metadata (not the file itself)"""
    model = Document
    form_class = DocumentUpdateForm
    template_name = 'parts/document_form.html'
    
    def test_func(self):
        """Check if user has permission to edit documents"""
        return self.request.user.profile.can_add_documents
    
    def form_valid(self, form):
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='document_update',
            description=f"Updated document metadata: {form.instance.title}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(self.request, f'Document "{form.instance.title}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Document: {self.object.title}'
        return context

class DocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a document"""
    model = Document
    template_name = 'parts/document_confirm_delete.html'
    
    def test_func(self):
        """Check if user has permission to delete documents"""
        return self.request.user.profile.can_add_documents
    
    def get_success_url(self):
        # Redirect back to the part detail page
        return reverse_lazy('part-detail', kwargs={'pk': self.object.part.pk})
    
    def delete(self, request, *args, **kwargs):
        document = self.get_object()
        
        # Delete the actual file
        DocumentHandler.delete_document_file(document)
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='document_delete',
            description=f"Deleted document: {document.title} for part {document.part.part_id}",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Document "{document.title}" deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def import_csv_view(request):
    """View for importing parts from CSV"""
    # Check permission
    if not request.user.profile.can_upload_csv:
        return HttpResponseForbidden("You don't have permission to import CSV files")
    
    if request.method == 'POST':
        form = ImportCSVForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get form data
                csv_file = request.FILES['csv_file']
                update_mode = form.cleaned_data['update_mode']
                skip_errors = form.cleaned_data['skip_errors']
                
                # Validate CSV structure
                CSVHandler.validate_csv_structure(csv_file)
                
                # Import the CSV
                import_log = CSVHandler.import_csv(
                    csv_file, 
                    request.user,
                    update_mode=update_mode,
                    skip_errors=skip_errors
                )
                
                # Log the activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='csv_import',
                    description=f"Imported CSV: {csv_file.name} - Added: {import_log.parts_added}, Updated: {import_log.parts_updated}, Skipped: {import_log.parts_skipped}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(
                    request, 
                    f'CSV imported successfully! Parts added: {import_log.parts_added}, '
                    f'updated: {import_log.parts_updated}, skipped: {import_log.parts_skipped}'
                )
                return redirect('dashboard')
                
            except CSVImportException as e:
                messages.error(request, f'Error importing CSV: {str(e)}')
            except Exception as e:
                messages.error(request, f'Unexpected error: {str(e)}')
    else:
        form = ImportCSVForm()
    
    return render(request, 'parts/import_csv.html', {'form': form})

@login_required
def export_csv_view(request):
    """Export parts to CSV"""
    # Get parts to export (could filter based on request parameters)
    parts = Part.objects.all().order_by('level', 'part_id')
    
    # Generate CSV content
    csv_content = CSVHandler.export_csv(parts)
    
    # Create HTTP response with CSV file
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parts_export.csv"'
    
    # Log the activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='csv_export',
        description=f"Exported {parts.count()} parts to CSV",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return response

@login_required
def import_logs_view(request):
    """View import logs (admin and managers only)"""
    # Check if user has permission
    if not (request.user.profile.role in ['admin', 'manager']):
        return HttpResponseForbidden("You don't have permission to view import logs")
    
    logs = ImportLog.objects.all().order_by('-imported_at')
    return render(request, 'parts/import_logs.html', {'logs': logs})

@login_required
def import_log_detail(request, pk):
    """View details of a specific import log"""
    # Check if user has permission
    if not (request.user.profile.role in ['admin', 'manager']):
        return HttpResponseForbidden("You don't have permission to view import logs")
    
    log = get_object_or_404(ImportLog, pk=pk)
    return render(request, 'parts/import_log_detail.html', {'log': log})

@login_required
@ensure_csrf_cookie
def codification_viewer(request):
    """View for the equipment codification tree viewer"""
    context = {
        'title': 'Equipment Codification Viewer'
    }
    return render(request, 'parts/codification_viewer.html', context)