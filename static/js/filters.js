// Image filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const filterItems = document.querySelectorAll('.filter-item');
    const imagePreview = document.getElementById('image-preview');
    const applyFilterBtn = document.getElementById('apply-filter');
    const saveFilteredBtn = document.getElementById('save-filtered');
    const filterIntensity = document.getElementById('filter-intensity');
    const intensityValue = document.getElementById('intensity-value');

    let originalImageData = null;
    let currentFilter = null;
    let currentImage = null;

    // Initialize filter functionality
    function initFilters() {
        if (!imagePreview) return;

        // Store original image data
        originalImageData = imagePreview.src;
        currentImage = imagePreview;

        // Set up event listeners
        setupFilterListeners();
    }

    // Set up event listeners
    function setupFilterListeners() {
        // Filter selection
        filterItems.forEach(item => {
            item.addEventListener('click', function() {
                const filterName = this.dataset.filter;
                selectFilter(filterName);
            });
        });

        // Filter intensity
        if (filterIntensity && intensityValue) {
            filterIntensity.addEventListener('input', function() {
                intensityValue.textContent = this.value + '%';
                if (currentFilter) {
                    applyFilter(currentFilter, this.value / 100);
                }
            });
        }

        // Apply filter button
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', function() {
                if (currentFilter) {
                    applyFilter(currentFilter, filterIntensity.value / 100);
                }
            });
        }

        // Save filtered image
        if (saveFilteredBtn) {
            saveFilteredBtn.addEventListener('click', saveFilteredImage);
        }

        // Reset filters
        const resetBtn = document.getElementById('reset-filters');
        if (resetBtn) {
            resetBtn.addEventListener('click', resetFilters);
        }
    }

    // Select filter
    function selectFilter(filterName) {
        // Update UI
        filterItems.forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.filter-item[data-filter="${filterName}"]`).classList.add('active');

        currentFilter = filterName;

        // Apply filter with default intensity
        applyFilter(filterName, 1.0);
    }

    // Apply filter to image
    function applyFilter(filterName, intensity = 1.0) {
        if (!currentImage) return;

        // Create off-screen image for processing
        const tempImage = new Image();
        tempImage.onload = function() {
            // Create canvas for processing
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = tempImage.width;
            canvas.height = tempImage.height;

            // Draw original image
            ctx.drawImage(tempImage, 0, 0);

            // Get image data
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            // Apply selected filter
            switch (filterName) {
                case 'grayscale':
                    applyGrayscaleFilter(data, intensity);
                    break;
                case 'sepia':
                    applySepiaFilter(data, intensity);
                    break;
                case 'vintage':
                    applyVintageFilter(data, intensity);
                    break;
                case 'warm':
                    applyWarmFilter(data, intensity);
                    break;
                case 'cool':
                    applyCoolFilter(data, intensity);
                    break;
                case 'clarity':
                    applyClarityFilter(ctx, imageData, intensity);
                    break;
                case 'brightness':
                    applyBrightnessFilter(data, intensity);
                    break;
                case 'contrast':
                    applyContrastFilter(data, intensity);
                    break;
                case 'blur':
                    applyBlurFilter(ctx, imageData, intensity);
                    break;
                case 'sharpen':
                    applySharpenFilter(ctx, imageData, intensity);
                    break;
                case 'edges':
                    applyEdgeDetectionFilter(ctx, imageData, intensity);
                    break;
            }

            // Put processed data back to canvas
            ctx.putImageData(imageData, 0, 0);

            // Update preview image
            currentImage.src = canvas.toDataURL('image/jpeg', 0.9);
        };

        tempImage.src = originalImageData;
    }

    // Filter implementations
    function applyGrayscaleFilter(data, intensity) {
        for (let i = 0; i < data.length; i += 4) {
            const avg = data[i] * 0.3 + data[i + 1] * 0.59 + data[i + 2] * 0.11;
            data[i] = data[i] * (1 - intensity) + avg * intensity;     // R
            data[i + 1] = data[i + 1] * (1 - intensity) + avg * intensity; // G
            data[i + 2] = data[i + 2] * (1 - intensity) + avg * intensity; // B
        }
    }

    function applySepiaFilter(data, intensity) {
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            data[i] = Math.min(255, r * (1 - 0.607 * intensity) + g * (0.769 * intensity) + b * (0.189 * intensity));     // R
            data[i + 1] = Math.min(255, r * (0.349 * intensity) + g * (1 - 0.314 * intensity) + b * (0.168 * intensity)); // G
            data[i + 2] = Math.min(255, r * (0.272 * intensity) + g * (0.534 * intensity) + b * (1 - 0.869 * intensity)); // B
        }
    }

    function applyVintageFilter(data, intensity) {
        // First apply sepia
        applySepiaFilter(data, intensity * 0.7);

        // Then reduce contrast
        applyContrastFilter(data, 1 - (intensity * 0.3));

        // Add some noise
        for (let i = 0; i < data.length; i += 4) {
            if (Math.random() < intensity * 0.1) {
                const noise = Math.random() * 50 - 25;
                data[i] = Math.min(255, Math.max(0, data[i] + noise));     // R
                data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise)); // G
                data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise)); // B
            }
        }
    }

    function applyWarmFilter(data, intensity) {
        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, data[i] + (30 * intensity));     // R (increase)
            data[i + 1] = Math.min(255, data[i + 1] + (15 * intensity)); // G (slight increase)
            data[i + 2] = Math.max(0, data[i + 2] - (10 * intensity));   // B (decrease)
        }
    }

    function applyCoolFilter(data, intensity) {
        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.max(0, data[i] - (10 * intensity));       // R (decrease)
            data[i + 1] = Math.max(0, data[i + 1] - (5 * intensity));   // G (slight decrease)
            data[i + 2] = Math.min(255, data[i + 2] + (30 * intensity)); // B (increase)
        }
    }

    function applyClarityFilter(ctx, imageData, intensity) {
        // This is a simplified clarity effect
        // A real implementation would use more advanced techniques

        // First sharpen slightly
        applySharpenFilter(ctx, imageData, intensity * 0.5);

        // Then adjust contrast
        applyContrastFilter(imageData.data, 1 + (intensity * 0.2));
    }

    function applyBrightnessFilter(data, intensity) {
        const adjustment = (intensity - 0.5) * 100; // -50 to +50 range

        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, Math.max(0, data[i] + adjustment));     // R
            data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + adjustment)); // G
            data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + adjustment)); // B
        }
    }

    function applyContrastFilter(data, intensity) {
        const factor = (259 * (intensity + 255)) / (255 * (259 - intensity));

        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, Math.max(0, factor * (data[i] - 128) + 128));     // R
            data[i + 1] = Math.min(255, Math.max(0, factor * (data[i + 1] - 128) + 128)); // G
            data[i + 2] = Math.min(255, Math.max(0, factor * (data[i + 2] - 128) + 128)); // B
        }
    }

    function applyBlurFilter(ctx, imageData, intensity) {
        // Simple box blur implementation
        const radius = Math.floor(intensity * 5);

        if (radius < 1) return;

        for (let i = 0; i < radius; i++) {
            const tempData = ctx.getImageData(0, 0, imageData.width, imageData.height);
            boxBlur(tempData.data, imageData.data, imageData.width, imageData.height, 1);
        }
    }

    function boxBlur(source, target, width, height, radius) {
        // Helper function for box blur
        for (let i = 0; i < source.length; i++) {
            target[i] = source[i];
        }

        // Horizontal pass
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                let r = 0, g = 0, b = 0, a = 0;
                let count = 0;

                for (let kx = -radius; kx <= radius; kx++) {
                    const px = Math.min(width - 1, Math.max(0, x + kx));
                    const idx = (y * width + px) * 4;

                    r += source[idx];
                    g += source[idx + 1];
                    b += source[idx + 2];
                    a += source[idx + 3];
                    count++;
                }

                const idx = (y * width + x) * 4;
                target[idx] = r / count;
                target[idx + 1] = g / count;
                target[idx + 2] = b / count;
                target[idx + 3] = a / count;
            }
        }

        // Vertical pass
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                let r = 0, g = 0, b = 0, a = 0;
                let count = 0;

                for (let ky = -radius; ky <= radius; ky++) {
                    const py = Math.min(height - 1, Math.max(0, y + ky));
                    const idx = (py * width + x) * 4;

                    r += target[idx];
                    g += target[idx + 1];
                    b += target[idx + 2];
                    a += target[idx + 3];
                    count++;
                }

                const idx = (y * width + x) * 4;
                target[idx] = r / count;
                target[idx + 1] = g / count;
                target[idx + 2] = b / count;
                target[idx + 3] = a / count;
            }
        }
    }

    function applySharpenFilter(ctx, imageData, intensity) {
        // Simple sharpen convolution
        const weight = 5 * intensity;
        const kernel = [
            0, -1, 0,
            -1, weight, -1,
            0, -1, 0
        ];

        convolutionFilter(ctx, imageData, kernel, 1 / (weight - 4));
    }

    function applyEdgeDetectionFilter(ctx, imageData, intensity) {
        // Sobel edge detection
        const kernelX = [
            -1, 0, 1,
            -2, 0, 2,
            -1, 0, 1
        ];

        const kernelY = [
            -1, -2, -1,
            0, 0, 0,
            1, 2, 1
        ];

        const tempData = new Uint8ClampedArray(imageData.data.length);

        // Apply Sobel operator
        for (let y = 1; y < imageData.height - 1; y++) {
            for (let x = 1; x < imageData.width - 1; x++) {
                let gx = 0, gy = 0;

                for (let ky = -1; ky <= 1; ky++) {
                    for (let kx = -1; kx <= 1; kx++) {
                        const idx = ((y + ky) * imageData.width + (x + kx)) * 4;
                        const gray = imageData.data[idx] * 0.3 + imageData.data[idx + 1] * 0.59 + imageData.data[idx + 2] * 0.11;

                        const kernelIndex = (ky + 1) * 3 + (kx + 1);
                        gx += gray * kernelX[kernelIndex];
                        gy += gray * kernelY[kernelIndex];
                    }
                }

                const magnitude = Math.min(255, Math.sqrt(gx * gx + gy * gy) * intensity);
                const idx = (y * imageData.width + x) * 4;

                tempData[idx] = magnitude;
                tempData[idx + 1] = magnitude;
                tempData[idx + 2] = magnitude;
                tempData[idx + 3] = 255;
            }
        }

        // Copy result back to imageData
        for (let i = 0; i < imageData.data.length; i++) {
            imageData.data[i] = tempData[i];
        }
    }

    function convolutionFilter(ctx, imageData, kernel, scale) {
        const tempData = new Uint8ClampedArray(imageData.data.length);
        const width = imageData.width;
        const height = imageData.height;
        const kernelSize = Math.sqrt(kernel.length);
        const radius = Math.floor(kernelSize / 2);

        for (let y = radius; y < height - radius; y++) {
            for (let x = radius; x < width - radius; x++) {
                let r = 0, g = 0, b = 0;

                for (let ky = -radius; ky <= radius; ky++) {
                    for (let kx = -radius; kx <= radius; kx++) {
                        const idx = ((y + ky) * width + (x + kx)) * 4;
                        const kernelIndex = (ky + radius) * kernelSize + (kx + radius);

                        r += imageData.data[idx] * kernel[kernelIndex];
                        g += imageData.data[idx + 1] * kernel[kernelIndex];
                        b += imageData.data[idx + 2] * kernel[kernelIndex];
                    }
                }

                const idx = (y * width + x) * 4;
                tempData[idx] = Math.min(255, Math.max(0, r * scale));
                tempData[idx + 1] = Math.min(255, Math.max(0, g * scale));
                tempData[idx + 2] = Math.min(255, Math.max(0, b * scale));
                tempData[idx + 3] = imageData.data[idx + 3];
            }
        }

        // Copy result back to imageData
        for (let i = 0; i < imageData.data.length; i++) {
            imageData.data[i] = tempData[i];
        }
    }

    // Save filtered image
    function saveFilteredImage() {
        if (!currentImage) return;

        // Create download link
        const link = document.createElement('a');
        link.href = currentImage.src;
        link.download = `filtered-image-${new Date().getTime()}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Reset filters
    function resetFilters() {
        if (!currentImage || !originalImageData) return;

        currentImage.src = originalImageData;
        currentFilter = null;

        // Update UI
        filterItems.forEach(item => {
            item.classList.remove('active');
        });

        if (filterIntensity && intensityValue) {
            filterIntensity.value = 100;
            intensityValue.textContent = '100%';
        }
    }

    // Initialize when page loads
    initFilters();
});