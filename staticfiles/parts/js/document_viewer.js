// parts/static/parts/js/document_viewer.js

/**
 * Document viewer functionality
 * 
 * Handles displaying documents in the document viewer panel
 */

// Cache for document types based on file extensions
const fileTypeCache = {
    // Images
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.svg': 'image',
    // PDFs
    '.pdf': 'pdf',
    // Text files
    '.txt': 'text',
    '.csv': 'text',
    '.md': 'text',
    // Documents
    '.docx': 'office',
    '.xlsx': 'office',
    // CAD files
    '.dwg': 'cad',
    '.dxf': 'cad',
    // Other
    '.other': 'other'
};

/**
 * Show document preview in the viewer
 * @param {string} url - URL of the document to preview
 */
function showDocumentPreview(url) {
    const viewerContainer = document.getElementById('documentViewer');
    if (!viewerContainer) {
        console.error('Document viewer container not found');
        return;
    }
    
    // Extract file extension from URL
    const fileExtension = getFileExtension(url);
    const fileType = getFileType(fileExtension);
    
    // Show appropriate preview based on file type
    switch (fileType) {
        case 'image':
            showImagePreview(url, viewerContainer);
            break;
        case 'pdf':
            showPDFPreview(url, viewerContainer);
            break;
        case 'text':
            showTextPreview(url, viewerContainer);
            break;
        default:
            showGenericPreview(url, fileExtension, viewerContainer);
    }
    
    updateStatus(`Viewing document: ${getFileNameFromUrl(url)}`);
}

/**
 * Show image preview
 * @param {string} url - Image URL
 * @param {HTMLElement} container - Container element
 */
function showImagePreview(url, container) {
    container.innerHTML = `
        <div class="text-center">
            <img src="${url}" alt="Document preview" class="img-fluid">
        </div>
    `;
}

/**
 * Show PDF preview
 * @param {string} url - PDF URL
 * @param {HTMLElement} container - Container element
 */
function showPDFPreview(url, container) {
    container.innerHTML = `
        <div class="ratio ratio-16x9" style="height: 500px;">
            <iframe src="${url}" frameborder="0" allowfullscreen></iframe>
        </div>
    `;
}

/**
 * Show text file preview
 * @param {string} url - Text file URL
 * @param {HTMLElement} container - Container element
 */
function showTextPreview(url, container) {
    // Show loading message
    container.innerHTML = '<p class="text-center"><i>Loading text content...</i></p>';
    
    // Fetch the text content
    fetch(url)
        .then(response => response.text())
        .then(text => {
            // Escape HTML to prevent XSS
            const escapedText = escape(text);
            
            container.innerHTML = `
                <div class="text-content pre-scrollable">
                    <pre>${escapedText}</pre>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching text file:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <p>Error loading text file. Please try downloading the file instead.</p>
                    <a href="${url}" class="btn btn-primary btn-sm" target="_blank">Download File</a>
                </div>
            `;
        });
}

/**
 * Show generic preview for unsupported file types
 * @param {string} url - File URL
 * @param {string} fileExtension - File extension
 * @param {HTMLElement} container - Container element
 */
function showGenericPreview(url, fileExtension, container) {
    const fileName = getFileNameFromUrl(url);
    
    container.innerHTML = `
        <div class="text-center p-4">
            <div class="document-icon mb-3">
                <i class="bi bi-file-earmark" style="font-size: 4rem;"></i>
                <div class="file-extension">${fileExtension.toUpperCase()}</div>
            </div>
            <h5>${fileName}</h5>
            <p class="text-muted">This file type cannot be previewed directly.</p>
            <a href="${url}" class="btn btn-primary" target="_blank">Download File</a>
        </div>
    `;
}

/**
 * Extract file extension from URL
 * @param {string} url - URL to extract extension from
 * @returns {string} - File extension (with dot)
 */
function getFileExtension(url) {
    // Parse the URL to get just the filename
    const fileName = getFileNameFromUrl(url);
    
    // Extract extension from filename
    const extensionMatch = fileName.match(/\.[0-9a-z]+$/i);
    return extensionMatch ? extensionMatch[0].toLowerCase() : '';
}

/**
 * Get file name from URL
 * @param {string} url - URL to extract file name from
 * @returns {string} - File name
 */
function getFileNameFromUrl(url) {
    const urlParts = url.split('/');
    return urlParts[urlParts.length - 1];
}

/**
 * Get file type based on extension
 * @param {string} extension - File extension (with dot)
 * @returns {string} - File type (image, pdf, text, office, cad, other)
 */
function getFileType(extension) {
    return fileTypeCache[extension] || 'other';
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escape(text) {
    const element = document.createElement('div');
    element.textContent = text;
    return element.innerHTML;
}

/**
 * Update status message
 * @param {string} message - Status message
 */
function updateStatus(message) {
    const statusBar = document.getElementById('statusBar');
    if (statusBar) {
        statusBar.textContent = message;
    }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showDocumentPreview,
        getFileExtension,
        getFileType
    };
}