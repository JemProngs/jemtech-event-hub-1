// Collage editor functionality using Fabric.js
document.addEventListener('DOMContentLoaded', function() {
    let canvas = null;
    let selectedTemplate = null;
    let currentImages = [];

    // Initialize collage editor
    function initCollageEditor() {
        const canvasElement = document.getElementById('collage-canvas');
        if (!canvasElement) return;

        // Initialize Fabric.js canvas
        canvas = new fabric.Canvas('collage-canvas', {
            width: 800,
            height: 600,
            backgroundColor: '#ffffff'
        });

        // Set up event listeners
        setupEventListeners();

        // Load default template
        loadTemplate('basic_2x2');
    }

    // Set up event listeners
    function setupEventListeners() {
        // Template selection
        document.querySelectorAll('.template-item').forEach(item => {
            item.addEventListener('click', function() {
                const templateId = this.dataset.template;
                loadTemplate(templateId);
            });
        });

        // Tool buttons
        document.querySelectorAll('.collage-tool').forEach(tool => {
            tool.addEventListener('click', function() {
                const toolType = this.dataset.tool;
                activateTool(toolType);
            });
        });

        // Image upload
        const imageUpload = document.getElementById('image-upload');
        if (imageUpload) {
            imageUpload.addEventListener('change', function(e) {
                if (this.files && this.files[0]) {
                    loadImageToEditor(this.files[0]);
                }
            });
        }

        // Filter application
        document.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', function() {
                const filterName = this.dataset.filter;
                applyFilter(filterName);
            });
        });

        // Sticker application
        document.querySelectorAll('.sticker-item').forEach(item => {
            item.addEventListener('click', function() {
                const stickerPath = this.dataset.sticker;
                addSticker(stickerPath);
            });
        });

        // Save collage
        const saveBtn = document.getElementById('save-collage');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveCollage);
        }

        // Download options
        document.querySelectorAll('.download-option').forEach(option => {
            option.addEventListener('click', function() {
                const format = this.dataset.format;
                downloadCollage(format);
            });
        });
    }

    // Load template
    function loadTemplate(templateId) {
        if (!canvas) return;

        // Clear current canvas
        canvas.clear();
        canvas.backgroundColor = '#ffffff';
        currentImages = [];

        // Get template configuration
        const template = window.COLLAGE_TEMPLATES[templateId];
        if (!template) return;

        selectedTemplate = templateId;

        // Update UI
        document.querySelectorAll('.template-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.template-item[data-template="${templateId}"]`).classList.add('active');

        // Draw template guides (optional)
        if (template.layout) {
            template.layout.forEach((slot, index) => {
                const rect = new fabric.Rect({
                    left: slot.x * canvas.width,
                    top: slot.y * canvas.height,
                    width: slot.width * canvas.width,
                    height: slot.height * canvas.height,
                    fill: 'transparent',
                    stroke: '#cccccc',
                    strokeDashArray: [5, 5],
                    selectable: false,
                    evented: false
                });
                canvas.add(rect);
            });
        }
    }

    // Activate tool
    function activateTool(toolType) {
        if (!canvas) return;

        // Update UI
        document.querySelectorAll('.collage-tool').forEach(tool => {
            tool.classList.remove('active');
        });
        document.querySelector(`.collage-tool[data-tool="${toolType}"]`).classList.add('active');

        // Set cursor based on tool
        switch (toolType) {
            case 'select':
                canvas.defaultCursor = 'default';
                canvas.selection = true;
                break;
            case 'move':
                canvas.defaultCursor = 'move';
                canvas.selection = true;
                break;
            case 'crop':
                canvas.defaultCursor = 'crosshair';
                canvas.selection = false;
                // Implement crop functionality
                break;
            case 'text':
                addTextToCollage();
                break;
        }
    }

    // Load image to editor
    function loadImageToEditor(file) {
        if (!canvas || !file) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            fabric.Image.fromURL(e.target.result, function(img) {
                // Scale image to fit canvas
                const maxWidth = canvas.width * 0.8;
                const maxHeight = canvas.height * 0.8;

                if (img.width > maxWidth || img.height > maxHeight) {
                    const scale = Math.min(maxWidth / img.width, maxHeight / img.height);
                    img.scale(scale);
                }

                // Center image
                img.set({
                    left: (canvas.width - img.width * img.scaleX) / 2,
                    top: (canvas.height - img.height * img.scaleY) / 2,
                    cornerStyle: 'circle',
                    cornerColor: '#005EB8',
                    cornerSize: 10,
                    transparentCorners: false
                });

                canvas.add(img);
                canvas.setActiveObject(img);
                currentImages.push(img);

                canvas.renderAll();
            });
        };
        reader.readAsDataURL(file);
    }

    // Apply filter to selected image
    function applyFilter(filterName) {
        const activeObject = canvas.getActiveObject();
        if (!activeObject || !activeObject.type === 'image') return;

        // Store original image data for filter reversion
        if (!activeObject.originalFilters) {
            activeObject.originalFilters = activeObject.filters ? [...activeObject.filters] : [];
        }

        // Clear existing filters
        activeObject.filters = [];

        // Apply new filter
        switch (filterName) {
            case 'grayscale':
                activeObject.filters.push(new fabric.Image.filters.Grayscale());
                break;
            case 'sepia':
                activeObject.filters.push(new fabric.Image.filters.Sepia());
                break;
            case 'vintage':
                activeObject.filters.push(new fabric.Image.filters.Sepia());
                activeObject.filters.push(new fabric.Image.filters.Brightness({ brightness: 0.1 }));
                break;
            case 'blur':
                activeObject.filters.push(new fabric.Image.filters.Blur({ blur: 0.2 }));
                break;
            case 'sharpen':
                activeObject.filters.push(new fabric.Image.filters.Convolute({
                    matrix: [ 0, -1,  0,
                             -1,  5, -1,
                              0, -1,  0 ]
                }));
                break;
            case 'normal':
                // Revert to original
                activeObject.filters = activeObject.originalFilters;
                break;
        }

        activeObject.applyFilters();
        canvas.renderAll();
    }

    // Add sticker to collage
    function addSticker(stickerPath) {
        if (!canvas) return;

        const fullPath = `/static/images/stickers/${stickerPath}`;

        fabric.Image.fromURL(fullPath, function(img) {
            // Scale sticker appropriately
            img.scale(0.3);

            // Position sticker
            img.set({
                left: canvas.width / 2 - (img.width * img.scaleX) / 2,
                top: canvas.height / 2 - (img.height * img.scaleY) / 2,
                cornerStyle: 'circle',
                cornerColor: '#005EB8',
                cornerSize: 8,
                transparentCorners: false
            });

            canvas.add(img);
            canvas.setActiveObject(img);
            canvas.renderAll();
        });
    }

    // Add text to collage
    function addTextToCollage() {
        if (!canvas) return;

        const text = new fabric.IText('Double click to edit', {
            left: canvas.width / 2,
            top: canvas.height / 2,
            fontFamily: 'Arial',
            fontSize: 24,
            fill: '#000000',
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            cornerStyle: 'circle',
            cornerColor: '#005EB8',
            cornerSize: 8,
            transparentCorners: false
        });

        canvas.add(text);
        canvas.setActiveObject(text);
        canvas.renderAll();
    }

    // Save collage
    function saveCollage() {
        if (!canvas) return;

        const eventId = document.getElementById('collage-event-id').value;
        const title = document.getElementById('collage-title').value || 'My Collage';

        // Get collage data
        const dataURL = canvas.toDataURL({
            format: 'jpeg',
            quality: 0.9
        });

        // Send to server
        fetch('/collage/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_id: eventId,
                title: title,
                template: selectedTemplate,
                image_data: dataURL
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Collage saved successfully!', 'success');
            } else {
                showAlert('Failed to save collage: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Failed to save collage. Please try again.', 'danger');
        });
    }

    // Download collage
    function downloadCollage(format) {
        if (!canvas) return;

        let dataURL;
        let filename = `jemtech-collage-${new Date().getTime()}`;

        switch (format) {
            case 'jpg':
                dataURL = canvas.toDataURL({
                    format: 'jpeg',
                    quality: 0.9
                });
                filename += '.jpg';
                break;
            case 'png':
                dataURL = canvas.toDataURL({
                    format: 'png'
                });
                filename += '.png';
                break;
            case 'pdf':
                // PDF generation would require additional libraries
                showAlert('PDF export requires additional setup.', 'info');
                return;
        }

        // Create download link
        const link = document.createElement('a');
        link.href = dataURL;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Show alert message
    function showAlert(message, type) {
        // Create or use existing alert container
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'position-fixed top-0 end-0 p-3';
            alertContainer.style.zIndex = '1050';
            document.body.appendChild(alertContainer);
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    }

    // Initialize when page loads
    initCollageEditor();
});