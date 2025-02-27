# parts/services/csv_handler.py

import csv
import io
import pandas as pd
from django.db import transaction
from django.utils import timezone
from ..models import Part, ImportLog

class CSVImportException(Exception):
    """Custom exception for CSV import errors"""
    pass

class CSVHandler:
    """Handler for CSV import and export operations"""
    
    REQUIRED_HEADERS = ['ID', 'Name', 'Level', 'Info', 'Parent']
    
    @staticmethod
    def validate_csv_structure(csv_file):
        """
        Validate that the CSV file has the required structure
        Returns True if valid, raises CSVImportException if invalid
        """
        # Reset file pointer to the beginning
        csv_file.seek(0)
        
        # Read the first few lines to check headers
        try:
            # Use pandas to read and detect headers
            df = pd.read_csv(csv_file, nrows=1)
            headers = df.columns.tolist()
            
            # Check for required headers (case insensitive)
            lower_headers = [h.lower() for h in headers]
            missing_headers = []
            
            for required in CSVHandler.REQUIRED_HEADERS:
                if required.lower() not in lower_headers:
                    missing_headers.append(required)
            
            if missing_headers:
                raise CSVImportException(f"Missing required headers: {', '.join(missing_headers)}")
            
            # Reset file pointer to the beginning
            csv_file.seek(0)
            return True
            
        except Exception as e:
            raise CSVImportException(f"Error validating CSV: {str(e)}")
    
    @staticmethod
    def import_csv(csv_file, user, update_mode='update_existing', skip_errors=True):
        """
        Import parts from CSV file
        
        Args:
            csv_file: The uploaded CSV file
            user: The user performing the import
            update_mode: One of 'add_only', 'update_existing', 'replace_all'
            skip_errors: Whether to skip errors and continue importing
            
        Returns:
            ImportLog instance with import results
        """
        # Create import log
        import_log = ImportLog.objects.create(
            imported_by=user,
            filename=csv_file.name,
            update_mode=update_mode,
            skip_errors=skip_errors
        )
        
        # Reset file pointer
        csv_file.seek(0)
        
        # Read CSV file
        try:
            df = pd.read_csv(csv_file)
            
            # Clean and standardize column names
            df.columns = [col.strip() for col in df.columns]
            renamed_columns = {}
            for col in df.columns:
                for required in CSVHandler.REQUIRED_HEADERS:
                    if col.lower() == required.lower():
                        renamed_columns[col] = required
            
            df = df.rename(columns=renamed_columns)
            
            # Start a database transaction
            with transaction.atomic():
                # If replace_all mode, delete all existing parts
                if update_mode == 'replace_all':
                    Part.objects.all().delete()
                    import_log.parts_deleted = Part.objects.count()
                
                # Process parts hierarchically by level
                if 'Level' in df.columns:
                    # Sort by Level to import parents before children
                    df = df.sort_values(by='Level')
                
                # Track parent mapping for hierarchical structure
                parent_map = {}
                
                # Process each row
                for _, row in df.iterrows():
                    try:
                        part_id = row['ID'].strip() if isinstance(row['ID'], str) else str(row['ID'])
                        name = row['Name'].strip() if isinstance(row['Name'], str) else str(row['Name'])
                        level = int(row['Level']) if 'Level' in row else 0
                        info = row['Info'] if 'Info' in row else ''
                        parent_id = row['Parent'] if 'Parent' in row and not pd.isna(row['Parent']) else None
                        
                        # Convert parent_id to string if it exists
                        if parent_id is not None and not isinstance(parent_id, str):
                            parent_id = str(parent_id)
                        
                        # Find parent part if a parent_id is provided
                        parent = None
                        if parent_id:
                            # Look in parent map first (for newly created parts)
                            if parent_id in parent_map:
                                parent = parent_map[parent_id]
                            else:
                                # Try to find in database
                                try:
                                    parent = Part.objects.get(part_id=parent_id)
                                except Part.DoesNotExist:
                                    if not skip_errors:
                                        raise CSVImportException(f"Parent part '{parent_id}' not found for part '{part_id}'")
                                    import_log.parts_skipped += 1
                                    continue
                        
                        # Check if part already exists
                        try:
                            existing_part = Part.objects.get(part_id=part_id)
                            
                            # Update existing part if mode allows
                            if update_mode in ['update_existing', 'replace_all']:
                                existing_part.name = name
                                existing_part.level = level
                                existing_part.info = info
                                existing_part.parent = parent
                                existing_part.modified_by = user
                                existing_part.save()
                                parent_map[part_id] = existing_part
                                import_log.parts_updated += 1
                            else:
                                # Skip if add_only mode
                                import_log.parts_skipped += 1
                                
                        except Part.DoesNotExist:
                            # Create new part
                            new_part = Part.objects.create(
                                part_id=part_id,
                                name=name,
                                level=level,
                                info=info,
                                parent=parent,
                                created_by=user,
                                modified_by=user
                            )
                            parent_map[part_id] = new_part
                            import_log.parts_added += 1
                    
                    except Exception as e:
                        if not skip_errors:
                            raise CSVImportException(f"Error processing row: {str(e)}")
                        import_log.error_log += f"Error on part {part_id}: {str(e)}\n"
                        import_log.parts_skipped += 1
            
            # Update import log with completion timestamp
            import_log.completed_at = timezone.now()
            import_log.save()
            
            return import_log
                        
        except Exception as e:
            # Log failure and re-raise
            import_log.error_log = f"Import failed: {str(e)}"
            import_log.completed_at = timezone.now()
            import_log.save()
            raise CSVImportException(f"Error importing CSV: {str(e)}")
    
    @staticmethod
    def export_csv(parts):
        """
        Export parts to CSV
        
        Args:
            parts: QuerySet of parts to export
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['ID', 'Name', 'Level', 'Info', 'Parent', 'Created By', 'Created At', 'Modified By', 'Modified At'])
        
        # Write part data
        for part in parts:
            writer.writerow([
                part.part_id,
                part.name,
                part.level,
                part.info,
                part.parent.part_id if part.parent else '',
                part.created_by.username if part.created_by else '',
                part.created_at.strftime('%Y-%m-%d %H:%M:%S') if part.created_at else '',
                part.modified_by.username if part.modified_by else '',
                part.modified_at.strftime('%Y-%m-%d %H:%M:%S') if part.modified_at else ''
            ])
        
        return output.getvalue()