// parts/static/parts/js/marker.js

/**
 * Marker functionality for parts
 * 
 * Handles the marking and unmarking of parts in the tree view and list
 */

// Global variables
const markedParts = new Set();

/**
 * Initialize the marker functionality
 * @param {Array} initialMarkedPartIds - Array of initially marked part IDs
 */
function initMarker(initialMarkedPartIds = []) {
    // Initialize marked parts
    if (initialMarkedPartIds && initialMarkedPartIds.length > 0) {
        initialMarkedPartIds.forEach(id => markedParts.add(parseInt(id)));
    }
    
    // Update UI to reflect marked parts
    updateMarkedPartsUI();
    
    // Set up event listeners
    setupMarkerEventListeners();
}

/**
 * Update UI to reflect marked parts
 */
function updateMarkedPartsUI() {
    // Update tree nodes
    document.querySelectorAll('.tree-node').forEach(node => {
        const partId = parseInt(node.getAttribute('data-id'));
        if (markedParts.has(partId)) {
            node.classList.add('marked');
        } else {
            node.classList.remove('marked');
        }
    });
    
    // Update list view if present
    document.querySelectorAll('tr[data-part-id]').forEach(row => {
        const partId = parseInt(row.getAttribute('data-part-id'));
        if (markedParts.has(partId)) {
            row.classList.add('bg-light-warning');
        } else {
            row.classList.remove('bg-light-warning');
        }
    });
}

/**
 * Set up event listeners for marker functionality
 */
function setupMarkerEventListeners() {
    // Add marker button
    const addMarkerBtn = document.getElementById('addMarkerBtn');
    if (addMarkerBtn) {
        addMarkerBtn.addEventListener('click', function() {
            const selectedPart = getSelectedPart();
            if (selectedPart) {
                markPart(selectedPart.id);
            } else {
                updateStatus('Please select a part to mark');
            }
        });
    }
    
    // Remove marker button
    const removeMarkerBtn = document.getElementById('removeMarkerBtn');
    if (removeMarkerBtn) {
        removeMarkerBtn.addEventListener('click', function() {
            const selectedPart = getSelectedPart();
            if (selectedPart) {
                unmarkPart(selectedPart.id);
            } else {
                updateStatus('Please select a part to unmark');
            }
        });
    }
    
    // Clean all markers button
    const cleanAllMarkersBtn = document.getElementById('cleanAllMarkersBtn');
    if (cleanAllMarkersBtn) {
        cleanAllMarkersBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to remove all markers?')) {
                clearAllMarkers();
            }
        });
    }
    
    // Mark buttons in list view
    document.querySelectorAll('.mark-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const partId = parseInt(this.getAttribute('data-part-id'));
            markPart(partId);
        });
    });
    
    // Unmark buttons in list view
    document.querySelectorAll('.unmark-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const partId = parseInt(this.getAttribute('data-part-id'));
            unmarkPart(partId);
        });
    });
}

/**
 * Mark a part
 * @param {number} partId - Part ID to mark
 */
function markPart(partId) {
    // Add to the set of marked parts
    markedParts.add(partId);
    
    // Update UI
    updateMarkedPartsUI();
    
    // Save to server
    fetch(`/parts/${partId}/mark/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ part: partId })
    })
    .then(response => {
        if (response.ok) {
            updateStatus(`Part ${partId} has been marked`);
        } else {
            throw new Error('Failed to mark part');
        }
    })
    .catch(error => {
        console.error('Error marking part:', error);
        updateStatus('Error marking part');
        // Remove from set if server request failed
        markedParts.delete(partId);
        updateMarkedPartsUI();
    });
}

/**
 * Unmark a part
 * @param {number} partId - Part ID to unmark
 */
function unmarkPart(partId) {
    // Remove from the set of marked parts
    markedParts.delete(partId);
    
    // Update UI
    updateMarkedPartsUI();
    
    // Remove from server
    fetch(`/parts/${partId}/unmark/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (response.ok) {
            updateStatus(`Part ${partId} has been unmarked`);
        } else {
            throw new Error('Failed to unmark part');
        }
    })
    .catch(error => {
        console.error('Error unmarking part:', error);
        updateStatus('Error unmarking part');
        // Add back to set if server request failed
        markedParts.add(partId);
        updateMarkedPartsUI();
    });
}

/**
 * Clear all markers
 */
function clearAllMarkers() {
    // Clear the set of marked parts
    markedParts.clear();
    
    // Update UI
    updateMarkedPartsUI();
    
    // Clear on server
    fetch('/parts/clear-all-marks/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (response.ok) {
            updateStatus('All markers have been cleared');
        } else {
            throw new Error('Failed to clear markers');
        }
    })
    .catch(error => {
        console.error('Error clearing markers:', error);
        updateStatus('Error clearing markers');
    });
}

/**
 * Check if a part is marked
 * @param {number} partId - Part ID to check
 * @returns {boolean} - Whether the part is marked
 */
function isPartMarked(partId) {
    return markedParts.has(partId);
}

/**
 * Get CSRF token from cookie
 * @returns {string} - CSRF token
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initMarker,
        markPart,
        unmarkPart,
        clearAllMarkers,
        isPartMarked
    };
}