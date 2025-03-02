/**
 * Advanced equipment tree management with drag and drop functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Tree configuration
    const treeContainer = document.getElementById('equipment-tree');
    if (!treeContainer) return;
    
    // Initialize the tree with jstree plugin
    $(treeContainer).jstree({
        'core': {
            'check_callback': function(operation, node, node_parent, node_position, more) {
                // This function controls which operations are permitted
                if (operation === 'move_node') {
                    // Don't allow equipment to become its own parent
                    if (more && more.dnd && (more.pos === 'i' || more.pos === 'a')) {
                        const nodeId = node.id.replace('equipment_', '');
                        const parentId = node_parent.id.replace('equipment_', '');
                        
                        // Check if we're trying to move a node inside itself or any of its children
                        let currentNode = node_parent;
                        while (currentNode && currentNode.id !== '#') {
                            if (currentNode.id === node.id) {
                                return false;
                            }
                            currentNode = treeContainer.jstree(true).get_node(currentNode.parent);
                        }
                        
                        return true;
                    }
                }
                return true;
            },
            'themes': {
                'name': 'default',
                'responsive': true,
                'dots': true,
                'icons': true
            },
            'data': {
                'url': function(node) {
                    return node.id === '#' ? 
                        equipmentDataUrl : 
                        `${equipmentChildrenUrl}?node=${node.id.replace('equipment_', '')}`;
                },
                'data': function(node) {
                    return { 'id': node.id === '#' ? null : node.id.replace('equipment_', '') };
                }
            }
        },
        'plugins': [
            'dnd',        // Drag and drop
            'wholerow',   // Clickable row 
            'search',     // Search functionality
            'state',      // Remember open/closed state
            'types',      // Custom node types
            'contextmenu' // Right-click menu
        ],
        'dnd': {
            'is_draggable': function(nodes) {
                // Allow dragging only for regular equipment nodes
                return nodes[0].type !== 'root';
            },
            'inside_pos': 'last'
        },
        'types': {
            'default': {
                'icon': 'fas fa-cube'
            },
            'root': {
                'icon': 'fas fa-industry'
            },
            'category': {
                'icon': 'fas fa-folder'
            },
            'active': {
                'icon': 'fas fa-check-circle text-success'
            },
            'inactive': {
                'icon': 'fas fa-times-circle text-secondary'
            },
            'maintenance': {
                'icon': 'fas fa-wrench text-warning'
            },
            'decommissioned': {
                'icon': 'fas fa-trash-alt text-danger'
            }
        },
        'contextmenu': {
            'items': function(node) {
                const tree = $('#equipment-tree').jstree(true);
                
                // Create the default context menu items
                return {
                    'view': {
                        'label': 'View Details',
                        'action': function() {
                            const equipmentId = node.id.replace('equipment_', '');
                            window.location.href = detailUrl.replace('0', equipmentId);
                        },
                        'icon': 'fas fa-eye'
                    },
                    'create': {
                        'label': 'Add Sub-Equipment',
                        'action': function() {
                            const equipmentId = node.id.replace('equipment_', '');
                            window.location.href = `${createUrl}?parent=${equipmentId}`;
                        },
                        'icon': 'fas fa-plus'
                    },
                    'edit': {
                        'label': 'Edit',
                        'action': function() {
                            const equipmentId = node.id.replace('equipment_', '');
                            window.location.href = editUrl.replace('0', equipmentId);
                        },
                        'icon': 'fas fa-edit'
                    },
                    'delete': {
                        'label': 'Delete',
                        'action': function() {
                            const equipmentId = node.id.replace('equipment_', '');
                            if (confirm('Are you sure you want to delete this equipment?')) {
                                window.location.href = deleteUrl.replace('0', equipmentId);
                            }
                        },
                        'icon': 'fas fa-trash'
                    },
                    'expand_all': {
                        'label': 'Expand All Children',
                        'action': function() {
                            tree.open_all(node);
                        },
                        'icon': 'fas fa-arrows-alt-v'
                    },
                    'collapse_all': {
                        'label': 'Collapse All Children',
                        'action': function() {
                            tree.close_all(node);
                        },
                        'icon': 'fas fa-compress-arrows-alt'
                    }
                };
            }
        }
    }).on('move_node.jstree', function(e, data) {
        // When a node is moved, send the update to the server
        const equipmentId = data.node.id.replace('equipment_', '');
        const newParentId = data.parent === '#' ? '' : data.parent.replace('equipment_', '');
        const position = data.position;
        
        // Call API to update the equipment's parent and position
        fetch(updatePositionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                id: equipmentId,
                parent_id: newParentId,
                position: position
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification('Equipment position updated successfully', 'success');
            } else {
                showNotification('Error: ' + data.message, 'error');
                // Reload the tree to reset to the previous state
                $('#equipment-tree').jstree(true).refresh();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Server error occurred', 'error');
            // Reload the tree to reset to the previous state
            $('#equipment-tree').jstree(true).refresh();
        });
    });
    
    // Search functionality
    const searchInput = document.getElementById('search-equipment');
    if (searchInput) {
        let searchTimeout = null;
        
        searchInput.addEventListener('keyup', function() {
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            searchTimeout = setTimeout(function() {
                const searchString = searchInput.value;
                $('#equipment-tree').jstree(true).search(searchString);
            }, 250);
        });
    }
    
    // Apply filters button
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            const statusFilter = document.getElementById('status-filter').value;
            const categoryFilter = document.getElementById('category-filter').value;
            
            // Custom filtering logic
            const tree = $('#equipment-tree').jstree(true);
            const allNodes = tree.get_json('#', {flat: true});
            
            allNodes.forEach(node => {
                const nodeElement = document.getElementById(node.id);
                if (!nodeElement) return;
                
                const nodeData = node.data || {};
                const nodeStatus = nodeData.status || '';
                const nodeCategory = nodeData.category || '';
                
                const matchesStatus = !statusFilter || nodeStatus === statusFilter;
                const matchesCategory = !categoryFilter || nodeCategory === categoryFilter;
                
                if (matchesStatus && matchesCategory) {
                    // Show this node
                    tree.show_node(node.id);
                    
                    // Make sure all parent nodes are visible too
                    let parent = tree.get_node(tree.get_parent(node.id));
                    while (parent && parent.id !== '#') {
                        tree.show_node(parent.id);
                        parent = tree.get_node(tree.get_parent(parent.id));
                    }
                } else {
                    // Hide this node
                    tree.hide_node(node.id);
                }
            });
        });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            // Reset form inputs
            document.getElementById('search-equipment').value = '';
            document.getElementById('status-filter').value = '';
            document.getElementById('category-filter').value = '';
            
            // Show all nodes
            const tree = $('#equipment-tree').jstree(true);
            tree.show_all();
            
            // Clear search
            tree.search('');
        });
    }
    
    // Helper function to show notifications
    function showNotification(message, type) {
        const notificationsContainer = document.getElementById('notifications');
        if (!notificationsContainer) return;
        
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show`;
        notification.setAttribute('role', 'alert');
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        notificationsContainer.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 150);
        }, 5000);
    }
});