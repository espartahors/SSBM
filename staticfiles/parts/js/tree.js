// parts/static/parts/js/tree.js

// Enable debugging
const DEBUG = true;

// Global variables
let partsTree = [];
let selectedPart = null;

/**
 * Debug logging function
 */
function debugLog(message, data = null) {
    if (!DEBUG) return;
    
    if (data) {
        console.log(`[TreeDebug] ${message}:`, data);
    } else {
        console.log(`[TreeDebug] ${message}`);
    }
}

/**
 * Initialize the parts tree
 * @param {string} treeDataUrl - URL to fetch tree data
 * @param {boolean} initiallyExpanded - Whether to show tree expanded by default
 */
function initPartsTree(treeDataUrl, initiallyExpanded = false) {
    debugLog('Initializing tree with URL', treeDataUrl);
    
    const statusBar = document.getElementById('statusBar');
    if (statusBar) {
        statusBar.textContent = 'Loading tree data...';
    }
    
    // Test if the URL is defined
    if (!treeDataUrl) {
        console.error('Tree data URL is missing!');
        updateStatus('Error: Tree data URL is missing');
        return;
    }
    
    // Fetch tree data from server
    debugLog('Fetching data from URL...');
    
    fetch(treeDataUrl)
        .then(response => {
            debugLog('Received response', response);
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            debugLog('Received data', data);
            
            if (!data || data.length === 0) {
                debugLog('Warning: Empty data returned');
                updateStatus('No parts found in the database');
            }
            
            partsTree = data;
            renderTree(partsTree, initiallyExpanded);
            updateStatus('Tree data loaded successfully');
        })
        .catch(error => {
            console.error('Error fetching tree data:', error);
            debugLog('Fetch error', error);
            updateStatus('Error loading parts tree. See console for details.');
            
            // Display error in tree container
            const treeContainer = document.getElementById('partsTree');
            if (treeContainer) {
                treeContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error loading tree data:</strong> ${error.message}
                        <p>Check browser console for more details.</p>
                        <p>URL: ${treeDataUrl}</p>
                    </div>
                `;
            }
        });
}

/**
 * Render the tree in the tree container
 * @param {Array} treeData - Array of tree nodes
 * @param {boolean} initiallyExpanded - Whether to show tree expanded by default
 */
function renderTree(treeData, initiallyExpanded = false) {
    debugLog('Rendering tree', { nodesCount: treeData.length, initiallyExpanded });
    
    const treeContainer = document.getElementById('partsTree');
    if (!treeContainer) {
        console.error('Tree container element not found! Expected element with id "partsTree"');
        return;
    }
    
    treeContainer.innerHTML = '';
    
    if (!treeData || treeData.length === 0) {
        treeContainer.innerHTML = '<p class="text-muted p-3">No parts found in the database.</p>';
        return;
    }
    
    // Create tree root elements
    const ul = document.createElement('ul');
    ul.className = 'tree-root';
    
    // Add each root node
    treeData.forEach(node => {
        try {
            const li = createTreeNode(node, initiallyExpanded);
            ul.appendChild(li);
        } catch (error) {
            console.error('Error creating tree node:', error, node);
            const errorLi = document.createElement('li');
            errorLi.innerHTML = `<div class="text-danger">Error rendering node: ${node.text || 'Unknown'}</div>`;
            ul.appendChild(errorLi);
        }
    });
    
    treeContainer.appendChild(ul);
    debugLog('Tree rendering complete');
}

/**
 * Create a tree node element
 * @param {Object} node - Tree node data
 * @param {boolean} initiallyExpanded - Whether to show node expanded by default
 * @returns {HTMLElement} - The li element for this node
 */
function createTreeNode(node, initiallyExpanded = false) {
    // Validate required node properties
    if (!node || !node.id) {
        throw new Error('Invalid node data: missing required properties');
    }
    
    const li = document.createElement('li');
    
    // Create the node element
    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'tree-node';
    nodeDiv.setAttribute('data-id', node.id);
    nodeDiv.setAttribute('data-part-id', node.part_id || '');
    
    // If marked, add marked class
    if (node.marked) {
        nodeDiv.classList.add('marked');
    }
    
    // Add expand/collapse icon if has children
    const expandIcon = document.createElement('span');
    expandIcon.className = 'expand-icon';
    
    if (node.children && node.children.length > 0) {
        expandIcon.textContent = initiallyExpanded ? '-' : '+';
        expandIcon.onclick = function(e) {
            e.stopPropagation();
            toggleChildNodes(nodeDiv);
        };
    } else {
        expandIcon.textContent = '•';
    }
    nodeDiv.appendChild(expandIcon);
    
    // Add document icon if has documents
    if (node.has_documents) {
        const docIcon = document.createElement('span');
        docIcon.className = 'doc-icon';
        docIcon.textContent = '📄';
        docIcon.title = 'Has documents';
        nodeDiv.appendChild(docIcon);
    }
    
    // Add part text
    const nodeText = document.createElement('span');
    nodeText.className = 'node-text';
    nodeText.textContent = node.text || `ID: ${node.id}`;
    nodeDiv.appendChild(nodeText);
    
    // Add click event to show details
    nodeDiv.onclick = function() {
        debugLog('Node clicked', node);
        selectPart(node);
    };
    
    li.appendChild(nodeDiv);
    
    // Create child container if has children
    if (node.children && node.children.length > 0) {
        const childUl = document.createElement('ul');
        childUl.className = 'child-nodes';
        childUl.style.display = initiallyExpanded ? 'block' : 'none';
        
        // Add each child node
        node.children.forEach(childNode => {
            try {
                const childLi = createTreeNode(childNode, initiallyExpanded);
                childUl.appendChild(childLi);
            } catch (error) {
                console.error('Error creating child tree node:', error, childNode);
                const errorLi = document.createElement('li');
                errorLi.innerHTML = `<div class="text-danger">Error rendering child node</div>`;
                childUl.appendChild(errorLi);
            }
        });
        
        li.appendChild(childUl);
    }
    
    return li;
}

/**
 * Toggle child nodes visibility
 * @param {HTMLElement} nodeDiv - The node element to toggle
 */
function toggleChildNodes(nodeDiv) {
    debugLog('Toggling child nodes');
    
    const li = nodeDiv.parentElement;
    const childUl = li.querySelector('ul.child-nodes');
    const expandIcon = nodeDiv.querySelector('.expand-icon');
    
    if (childUl) {
        if (childUl.style.display === 'none') {
            childUl.style.display = 'block';
            expandIcon.textContent = '-';
        } else {
            childUl.style.display = 'none';
            expandIcon.textContent = '+';
        }
    }
}

/**
 * Select a part and show its details
 * @param {Object} part - Part data object
 */
function selectPart(part) {
    debugLog('Selecting part', part);
    
    // Update selected part
    selectedPart = part;
    
    // Remove selected class from all tree nodes
    document.querySelectorAll('.tree-node').forEach(node => {
        node.classList.remove('selected');
    });
    
    // Add selected class to current node
    const node = document.querySelector(`.tree-node[data-id="${part.id}"]`);
    if (node) {
        node.classList.add('selected');
    }
    
    // Fetch and show part details
    loadPartDetails(part.id);
    
    // Update mark forms
    updateMarkForms(part);
    
    // Update status
    updateStatus(`Selected part: ${part.text}`);
}

/**
 * Load part details from server
 * @param {number} partId - Part ID
 */
function loadPartDetails(partId) {
    debugLog('Loading part details', partId);
    
    const detailsUrl = `/parts/${partId}/`;
    debugLog('Fetching from URL', detailsUrl);
    
    fetch(detailsUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load part details: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // Extract just the part details section
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Get the part details div
            const detailsContent = tempDiv.querySelector('.component-info');
            if (detailsContent) {
                const partDetailsEl = document.getElementById('partDetails');
                if (partDetailsEl) {
                    partDetailsEl.innerHTML = '';
                    partDetailsEl.appendChild(detailsContent);
                } else {
                    console.error('Part details container not found');
                }
            } else {
                console.error('Could not extract part details from response');
                debugLog('Response HTML', html.substring(0, 500) + '...');
            }
            
            // Get the document viewer content
            const docViewerContent = tempDiv.querySelector('.document-viewer');
            if (docViewerContent) {
                const docViewerEl = document.getElementById('documentViewer');
                if (docViewerEl) {
                    docViewerEl.innerHTML = '';
                    docViewerEl.appendChild(docViewerContent);
                }
            }
        })
        .catch(error => {
            console.error('Error loading part details:', error);
            updateStatus('Error loading part details: ' + error.message);
            
            // Show error in details section
            const partDetailsEl = document.getElementById('partDetails');
            if (partDetailsEl) {
                partDetailsEl.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error loading part details:</strong> ${error.message}
                    </div>
                `;
            }
        });
}

/**
 * Load documents for a part
 * @param {number} partId - Part ID
 */
function loadDocuments(partId) {
    fetch(`/parts/${partId}/documents/`)
        .then(response => response.text())
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            const docViewerContent = tempDiv.querySelector('.document-viewer');
            if (docViewerContent) {
                document.getElementById('documentViewer').innerHTML = '';
                document.getElementById('documentViewer').appendChild(docViewerContent);
                updateStatus('Documents loaded');
            } else {
                document.getElementById('documentViewer').innerHTML = '<p>No documents available for this part.</p>';
                updateStatus('No documents available');
            }
        })
        .catch(error => {
            console.error('Error loading documents:', error);
            updateStatus('Error loading documents');
        });
}

/**
 * Update the marker forms for current part
 * @param {Object} part - Selected part data
 */
function updateMarkForms(part) {
    const addForm = document.getElementById('addMarkerForm');
    const removeForm = document.getElementById('removeMarkerForm');
    
    // Update form actions and visibility based on whether part is marked
    if (part.marked) {
        addForm.style.display = 'none';
        removeForm.style.display = 'block';
        removeForm.action = `/parts/${part.id}/unmark/`;
    } else {
        addForm.style.display = 'block';
        removeForm.style.display = 'none';
        addForm.action = `/parts/${part.id}/mark/`;
        document.getElementById('markPartId').value = part.id;
    }
}

/**
 * Search for parts in the tree
 * @param {string} term - Search term
 */
function searchParts(term) {
    if (!term.trim()) return;
    
    term = term.toLowerCase();
    let found = false;
    
    // Helper function to search in a node and its children
    function searchNode(node) {
        // Check if this node matches
        if (node.text.toLowerCase().includes(term) || 
            node.part_id.toLowerCase().includes(term)) {
            // Found a match
            selectPart(node);
            
            // Expand parents to make this node visible
            expandToNode(node.id);
            
            found = true;
            return true;
        }
        
        // Check children
        if (node.children && node.children.length > 0) {
            for (const child of node.children) {
                if (searchNode(child)) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    // Search in all root nodes
    for (const rootNode of partsTree) {
        if (searchNode(rootNode)) {
            break;
        }
    }
    
    if (!found) {
        updateStatus(`No parts found matching "${term}"`);
    }
}

/**
 * Expand tree to show a specific node
 * @param {number} nodeId - Node ID to expand to
 */
function expandToNode(nodeId) {
    const node = document.querySelector(`.tree-node[data-id="${nodeId}"]`);
    if (!node) return;
    
    // Get all parent ULs
    let parent = node.parentElement;
    while (parent) {
        if (parent.classList.contains('child-nodes')) {
            parent.style.display = 'block';
            
            // Update the expand icon
            const parentNode = parent.previousElementSibling;
            if (parentNode && parentNode.querySelector('.expand-icon')) {
                parentNode.querySelector('.expand-icon').textContent = '-';
            }
        }
        parent = parent.parentElement;
    }
    
    // Scroll to the node
    node.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Get the currently selected part
 * @returns {Object|null} The selected part or null if none selected
 */
function getSelectedPart() {
    return selectedPart;
}

/**
 * Update the status bar message
 * @param {string} message - Status message
 */
function updateStatus(message) {
    const statusBar = document.getElementById('statusBar');
    if (statusBar) {
        statusBar.textContent = message;
    }
    debugLog('Status updated', message);
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initPartsTree,
        renderTree,
        selectPart,
        debugLog
    };
}

// Auto-initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    debugLog('DOM ready, checking for tree initialization elements');
    
    // Check if we have the tree container
    const treeContainer = document.getElementById('partsTree');
    if (!treeContainer) {
        console.error('Tree container element not found! Expected element with id "partsTree"');
        return;
    }
    
    // Check for the URL in a data attribute
    const treeDataUrl = treeContainer.getAttribute('data-url') || '/parts/tree-json/';
    const initiallyExpanded = treeContainer.getAttribute('data-expanded') === 'true';
    
    debugLog('Auto-initializing tree', { treeDataUrl, initiallyExpanded });
    
    // Initialize the tree
    initPartsTree(treeDataUrl, initiallyExpanded);
});