// equipment/static/equipment/js/tree.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the tree with sortable functionality
    $('#equipment-tree').jstree({
        'core': {
            'data': loadTreeData(),
            'themes': {
                'name': 'proton',
                'responsive': true
            },
            'check_callback': function(operation, node, node_parent, node_position, more) {
                // Allow all operations
                return true;
            }
        },
        'plugins': ['dnd', 'search', 'state', 'types', 'wholerow', 'contextmenu'],
        'dnd': {
            'is_draggable': function(nodes) {
                // Only allow dragging of equipment nodes
                return true;
            }
        },
        'types': {
            'default': {
                'icon': 'fas fa-cube'
            },
            'category': {
                'icon': 'fas fa-folder'
            },
            'equipment': {
                'icon': 'fas fa-tools'
            }
        },
        'contextmenu': {
            'items': customMenu
        }
    }).on('move_node.jstree', function(e, data) {
        // When a node is moved, update the server
        const itemId = data.node.id.replace('equipment_', '');
        const parentId = data.parent !== '#' ? data.parent.replace('equipment_', '') : null;
        
        $.ajax({
            url: updatePositionUrl,
            type: 'POST',
            data: {
                'id': itemId,
                'parent_id': parentId,
                'position': data.position,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                if (response.status === 'success') {
                    showNotification('Item moved successfully', 'success');
                } else {
                    showNotification('Error: ' + response.message, 'error');
                    // Reload the tree to revert to previous state
                    $('#equipment-tree').jstree(true).refresh();
                }
            },
            error: function() {
                showNotification('Server error occurred', 'error');
                $('#equipment-tree').jstree(true).refresh();
            }
        });
    });
    
    // Add search functionality
    $('#search-equipment').on('keyup', function() {
        $('#equipment-tree').jstree(true).search($(this).val());
    });
    
    // Context menu for tree nodes
    function customMenu(node) {
        const items = {
            'add': {
                'label': 'Add New Equipment',
                'action': function() {
                    window.location.href = createEquipmentUrl + '?parent=' + node.id.replace('equipment_', '');
                },
                'icon': 'fas fa-plus'
            },
            'edit': {
                'label': 'Edit',
                'action': function() {
                    window.location.href = editEquipmentUrl.replace('0', node.id.replace('equipment_', ''));
                },
                'icon': 'fas fa-edit'
            },
            'delete': {
                'label': 'Delete',
                'action': function() {
                    if (confirm('Are you sure you want to delete this item?')) {
                        window.location.href = deleteEquipmentUrl.replace('0', node.id.replace('equipment_', ''));
                    }
                },
                'icon': 'fas fa-trash'
            }
        };
        
        // Only show delete if the node has no children
        if ($('#' + node.id).find('li').length > 0) {
            delete items.delete;
        }
        
        return items;
    }
    
    // Function to load tree data
    function loadTreeData() {
        // This should be replaced with your data structure
        // For example, you might load this via AJAX
        return equipmentTreeData;
    }
    
    // Helper function to show notifications
    function showNotification(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const notification = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
            message +
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
            '<span aria-hidden="true">&times;</span>' +
            '</button>' +
            '</div>');
            
        $('#notifications').append(notification);
        
        // Auto-dismiss after 3 seconds
        setTimeout(function() {
            notification.alert('close');
        }, 3000);
    }
});


console.log('Tree script loaded');
console.log('jQuery available:', typeof $ !== 'undefined');
console.log('jstree plugin available:', typeof $.jstree !== 'undefined');
console.log('Tree container exists:', document.getElementById('equipment-tree') !== null);