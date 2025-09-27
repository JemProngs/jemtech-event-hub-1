// QR code scanner functionality
document.addEventListener('DOMContentLoaded', function() {
    const scannerContainer = document.getElementById('scanner-container');
    const scanResult = document.getElementById('scan-result');
    const startScannerBtn = document.getElementById('start-scanner');
    const stopScannerBtn = document.getElementById('stop-scanner');
    const manualEntryBtn = document.getElementById('manual-entry');
    const manualEntryModal = new bootstrap.Modal(document.getElementById('manualEntryModal'));
    const manualEntryForm = document.getElementById('manualEntryForm');

    let html5QrcodeScanner = null;
    let isScanning = false;

    // Initialize scanner
    function initScanner() {
        if (!scannerContainer) return;

        html5QrcodeScanner = new Html5QrcodeScanner(
            "scanner-container",
            {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                supportedScanTypes: [
                    Html5QrcodeScanType.SCAN_TYPE_CAMERA
                ]
            },
            false
        );
    }

    // Start scanning
    function startScanner() {
        if (isScanning) return;

        Html5Qrcode.getCameras().then(cameras => {
            if (cameras && cameras.length) {
                const cameraId = cameras[0].id; // Use first camera by default

                html5QrcodeScanner.render(
                    (decodedText, decodedResult) => {
                        handleScanResult(decodedText);
                    },
                    (errorMessage) => {
                        // Parse failure, ignore unless needed
                    }
                );

                isScanning = true;
                updateScannerUI();
            } else {
                showError('No cameras found. Please check your device permissions.');
            }
        }).catch(err => {
            showError('Unable to access camera. Please check permissions and try again.');
            console.error('Camera error:', err);
        });
    }

    // Stop scanning
    function stopScanner() {
        if (!isScanning || !html5QrcodeScanner) return;

        html5QrcodeScanner.clear().then(() => {
            isScanning = false;
            updateScannerUI();
        }).catch(err => {
            console.error('Failed to clear scanner:', err);
        });
    }

    // Handle scan result
    function handleScanResult(decodedText) {
        // Show scanning status
        if (scanResult) {
            scanResult.innerHTML = `
                <div class="alert alert-info">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        Processing QR code...
                    </div>
                </div>
            `;
        }

        // Send to server for validation
        fetch('/api/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: decodedText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`Check-in successful for: ${data.event.title}`);

                // Optionally stop scanner after successful scan
                setTimeout(() => {
                    stopScanner();
                    // Restart scanner after a delay
                    setTimeout(() => startScanner(), 2000);
                }, 2000);
            } else {
                showError(data.error || 'Invalid QR code. Please try again.');

                // Keep scanner running for next attempt
                setTimeout(() => {
                    if (scanResult) scanResult.innerHTML = '';
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Check-in failed. Please try again.');

            // Keep scanner running for next attempt
            setTimeout(() => {
                if (scanResult) scanResult.innerHTML = '';
            }, 3000);
        });
    }

    // Update UI based on scanner state
    function updateScannerUI() {
        if (startScannerBtn) {
            startScannerBtn.disabled = isScanning;
        }
        if (stopScannerBtn) {
            stopScannerBtn.disabled = !isScanning;
        }
        if (scannerContainer) {
            scannerContainer.style.display = isScanning ? 'block' : 'none';
        }
    }

    // Show success message
    function showSuccess(message) {
        if (scanResult) {
            scanResult.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    // Show error message
    function showError(message) {
        if (scanResult) {
            scanResult.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    // Event listeners
    if (startScannerBtn) {
        startScannerBtn.addEventListener('click', startScanner);
    }

    if (stopScannerBtn) {
        stopScannerBtn.addEventListener('click', stopScanner);
    }

    if (manualEntryBtn) {
        manualEntryBtn.addEventListener('click', function() {
            manualEntryModal.show();
        });
    }

    if (manualEntryForm) {
        manualEntryForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const tokenInput = this.querySelector('input[name="manual_token"]');
            if (tokenInput && tokenInput.value) {
                handleScanResult(tokenInput.value);
                manualEntryModal.hide();
                tokenInput.value = '';
            }
        });
    }

    // Camera selection
    const cameraSelect = document.getElementById('camera-select');
    if (cameraSelect) {
        // Populate camera options
        Html5Qrcode.getCameras().then(cameras => {
            if (cameras && cameras.length) {
                cameraSelect.innerHTML = '';
                cameras.forEach(camera => {
                    const option = document.createElement('option');
                    option.value = camera.id;
                    option.textContent = camera.label || `Camera ${cameraSelect.length + 1}`;
                    cameraSelect.appendChild(option);
                });

                cameraSelect.addEventListener('change', function() {
                    if (isScanning) {
                        stopScanner();
                        setTimeout(() => startScanner(), 500);
                    }
                });
            }
        });
    }

    // Initialize scanner when page loads
    initScanner();

    // Auto-start scanner if enabled
    const autoStart = scannerContainer && scannerContainer.dataset.autoStart === 'true';
    if (autoStart) {
        startScanner();
    }

    // Clean up when leaving page
    window.addEventListener('beforeunload', function() {
        if (isScanning) {
            stopScanner();
        }
    });
});