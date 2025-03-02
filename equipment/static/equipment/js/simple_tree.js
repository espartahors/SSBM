// Simple tree implementation for testing
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tree script loaded');
    
    // Check if jQuery is loaded
    if (typeof jQuery === 'undefined') {
        console.error('jQuery is not loaded');
        return;
    }
    
    // Check if jstree is loaded
    if (typeof $.jstree === 'undefined') {
        console.error('jstree plugin is not loaded');
        return;
    }
    
    // Check if tree container exists
    const treeContainer = document.getElementById('equipment-tree');
    if (!treeContainer) {
        console.error('Tree container #equipment-tree not found');
        return;
    }
    
    console.log('Initializing tree');
    
    // Simple hard-coded data for testing
    const testData = [
        { "id": "node_1", "text": "Root node", "children": [
            { "id": "node_2", "text": "Child 1" },
            { "id": "node_3", "text": "Child 2" }
        ]}
    ];
    
    // Initialize with simple configuration
    $(treeContainer).jstree({
        'core': {
            'data': testData,
            'themes': {
                'name': 'default',
                'responsive': true
            }
        }
    });
    
    // Log when tree is ready
    $(treeContainer).on('ready.jstree', function() {
        console.log('Tree is ready');
    });
});
