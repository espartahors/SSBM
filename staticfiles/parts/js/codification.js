// parts/static/parts/js/codification.js

document.addEventListener('DOMContentLoaded', function() {
    // Toggle between views
    document.getElementById('treeViewBtn').addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('codificationViewBtn').classList.remove('active');
        document.getElementById('partsTree').style.display = 'block';
        document.getElementById('codificationTree').style.display = 'none';
        document.getElementById('treeStructureHeader').style.display = 'inline';
        document.getElementById('codificationHeader').style.display = 'none';
    });
    
    document.getElementById('codificationViewBtn').addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('treeViewBtn').classList.remove('active');
        document.getElementById('partsTree').style.display = 'none';
        document.getElementById('codificationTree').style.display = 'block';
        document.getElementById('treeStructureHeader').style.display = 'none';
        document.getElementById('codificationHeader').style.display = 'inline';
        
        // Load codification data if not already loaded
        if (!codificationLoaded) {
            loadCodificationTree();
        }
    });
    
    let codificationLoaded = false;
    
    function loadCodificationTree() {
        fetch('{% url "codification-tree-json" %}')
            .then(response => response.json())
            .then(data => {
                renderCodificationTree(data);
                codificationLoaded = true;
            })
            .catch(error => {
                console.error('Error loading codification tree:', error);
                document.getElementById('codificationTree').innerHTML = 
                    '<div class="alert alert-danger">Error loading codification data</div>';
            });
    }
    
    function renderCodificationTree(data) {
        // Similar to your existing codification rendering code
        // but integrated with the dashboard
        const container = document.getElementById('codificationTree');
        container.innerHTML = '';
        
        data.forEach(system => {
            const systemNode = createCodificationNode(system, 1);
            container.appendChild(systemNode);
        });
    }
    
    function createCodificationNode(node, level) {
        // Create a tree node with proper coloring based on level
        // Use your existing codification viewer code as a reference
    }
});