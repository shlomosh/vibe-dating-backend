/**
 * Frontend Integration Example for Vibe Profile Image Service
 * 
 * This example shows how to integrate the profile image upload and management
 * functionality into a Telegram Mini-App frontend.
 */

// Configuration
const API_BASE_URL = 'https://your-api-gateway-url.execute-api.il-central-1.amazonaws.com/dev';

/**
 * Profile Image Service Class
 * Handles all profile image upload, processing, and management operations
 */
class VibeProfileImageService {
    constructor(authService) {
        this.auth = authService;
        this.uploadQueue = new Map(); // Track upload progress
        this.processingStatus = new Map(); // Track processing status
    }

    /**
     * Request upload URL for a new profile image
     */
    async requestUploadUrl(profileId, imageFile, order = 1) {
        try {
            // Extract image metadata
            const metadata = await this.extractImageMetadata(imageFile);
            
            const requestData = {
                type: 'image',
                aspectRatio: '3:4',
                metadata: metadata,
                order: order
            };

            const response = await this.auth.apiRequest(`/profiles/${profileId}/media/request-upload`, {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'Failed to request upload URL');
            }

            const uploadData = await response.json();
            
            // Store upload info for tracking
            this.uploadQueue.set(uploadData.mediaId, {
                profileId,
                file: imageFile,
                uploadData,
                status: 'pending'
            });

            return uploadData;

        } catch (error) {
            console.error('Failed to request upload URL:', error);
            throw error;
        }
    }

    /**
     * Upload image to S3 using presigned URL
     */
    async uploadImageToS3(uploadData, imageFile) {
        try {
            const { uploadUrl, uploadMethod, uploadHeaders } = uploadData;

            // Create upload request
            const uploadRequest = new Request(uploadUrl, {
                method: uploadMethod,
                headers: uploadHeaders,
                body: imageFile
            });

            const response = await fetch(uploadRequest);

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
            }

            // Get ETag from response headers
            const etag = response.headers.get('ETag');
            
            return {
                success: true,
                etag: etag,
                size: imageFile.size
            };

        } catch (error) {
            console.error('S3 upload failed:', error);
            throw error;
        }
    }

    /**
     * Complete upload and trigger processing
     */
    async completeUpload(profileId, mediaId, uploadResult) {
        try {
            const completeData = {
                uploadSuccess: uploadResult.success,
                s3ETag: uploadResult.etag,
                actualSize: uploadResult.size
            };

            const response = await this.auth.apiRequest(`/profiles/${profileId}/media/${mediaId}/complete`, {
                method: 'POST',
                body: JSON.stringify(completeData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'Failed to complete upload');
            }

            const result = await response.json();
            
            // Update tracking
            const uploadInfo = this.uploadQueue.get(mediaId);
            if (uploadInfo) {
                uploadInfo.status = 'processing';
                this.processingStatus.set(mediaId, {
                    status: 'processing',
                    estimatedTime: result.estimatedProcessingTime
                });
            }

            return result;

        } catch (error) {
            console.error('Failed to complete upload:', error);
            throw error;
        }
    }

    /**
     * Check processing status of uploaded image
     */
    async getProcessingStatus(profileId, mediaId) {
        try {
            const response = await this.auth.apiRequest(`/profiles/${profileId}/media/${mediaId}/status`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'Failed to get processing status');
            }

            const statusData = await response.json();
            
            // Update tracking
            this.processingStatus.set(mediaId, statusData);
            
            // Clean up upload queue if completed
            if (statusData.status === 'completed' || statusData.status === 'failed') {
                this.uploadQueue.delete(mediaId);
            }

            return statusData;

        } catch (error) {
            console.error('Failed to get processing status:', error);
            throw error;
        }
    }

    /**
     * Delete a profile image
     */
    async deleteImage(profileId, mediaId) {
        try {
            const response = await this.auth.apiRequest(`/profiles/${profileId}/media/${mediaId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'Failed to delete image');
            }

            const result = await response.json();
            
            // Clean up tracking
            this.uploadQueue.delete(mediaId);
            this.processingStatus.delete(mediaId);

            return result;

        } catch (error) {
            console.error('Failed to delete image:', error);
            throw error;
        }
    }

    /**
     * Extract metadata from image file
     */
    async extractImageMetadata(imageFile) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            img.onload = () => {
                const width = img.width;
                const height = img.height;
                const aspect = this.calculateAspectRatio(width, height);

                // Get file format
                const format = imageFile.name.split('.').pop().toLowerCase();
                
                // Get camera/software info from EXIF if available
                const metadata = {
                    width: width,
                    height: height,
                    size: imageFile.size,
                    format: format,
                    aspect: aspect,
                    camera: null, // Will be extracted from EXIF if available
                    software: null, // Will be extracted from EXIF if available
                    timestamp: null, // Will be extracted from EXIF if available (captured-time)
                    location: null, // Will be extracted from EXIF if available (captured-location)
                    flags: ''
                };

                // Try to extract EXIF data
                this.extractExifData(imageFile).then(exifData => {
                    if (exifData) {
                        metadata.camera = exifData.Make && exifData.Model 
                            ? `${exifData.Make} ${exifData.Model}`.substring(0, 32)
                            : null;
                        metadata.software = exifData.Software ? exifData.Software.substring(0, 32) : null;
                        if (exifData.DateTimeOriginal) {
                            metadata.timestamp = new Date(exifData.DateTimeOriginal).toISOString();
                        }
                    }
                    resolve(metadata);
                }).catch(() => {
                    resolve(metadata);
                });
            };

            img.onerror = () => {
                reject(new Error('Failed to load image for metadata extraction'));
            };

            img.src = URL.createObjectURL(imageFile);
        });
    }

    /**
     * Calculate aspect ratio as string
     */
    calculateAspectRatio(width, height) {
        const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
        const divisor = gcd(width, height);
        const w = width / divisor;
        const h = height / divisor;
        return `${w}:${h}`;
    }

    /**
     * Extract EXIF data from image file
     */
    async extractExifData(imageFile) {
        // This is a simplified version - in production you'd use a proper EXIF library
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    // Basic EXIF extraction - in production use a library like exif-js
                    const arrayBuffer = e.target.result;
                    const view = new DataView(arrayBuffer);
                    
                    // Check for JPEG EXIF marker
                    if (view.getUint16(0, false) === 0xFFD8) {
                        const exifData = this.parseExifData(view);
                        resolve(exifData);
                    } else {
                        resolve(null);
                    }
                } catch (error) {
                    console.warn('EXIF extraction failed:', error);
                    resolve(null);
                }
            };
            reader.readAsArrayBuffer(imageFile);
        });
    }

    /**
     * Parse EXIF data from DataView
     * Note: This is a simplified implementation
     */
    parseExifData(view) {
        // Simplified EXIF parsing - in production use a proper library
        const exifData = {};
        
        try {
            // Look for EXIF marker
            for (let i = 0; i < view.byteLength - 1; i++) {
                if (view.getUint16(i, false) === 0xFFE1) {
                    // Found EXIF marker, parse data
                    // This is a very simplified version
                    break;
                }
            }
        } catch (error) {
            console.warn('EXIF parsing failed:', error);
        }
        
        return exifData;
    }

    /**
     * Get upload progress for a specific media ID
     */
    getUploadProgress(mediaId) {
        return this.uploadQueue.get(mediaId);
    }

    /**
     * Get processing status for a specific media ID
     */
    getProcessingProgress(mediaId) {
        return this.processingStatus.get(mediaId);
    }

    /**
     * Get all active uploads
     */
    getActiveUploads() {
        return Array.from(this.uploadQueue.entries());
    }

    /**
     * Get all processing images
     */
    getProcessingImages() {
        return Array.from(this.processingStatus.entries());
    }
}

/**
 * Profile Image UI Component Class
 * Handles the user interface for image upload and management
 */
class VibeProfileImageUI {
    constructor(profileImageService) {
        this.service = profileImageService;
        this.currentProfileId = null;
        this.imageOrder = 1;
        this.setupEventListeners();
    }

    /**
     * Initialize the UI for a specific profile
     */
    initialize(profileId) {
        this.currentProfileId = profileId;
        this.imageOrder = 1;
        this.renderImageGrid();
        this.updateUploadButton();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // File input change handler
        const fileInput = document.getElementById('profile-image-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
        }

        // Upload button click handler
        const uploadButton = document.getElementById('upload-image-btn');
        if (uploadButton) {
            uploadButton.addEventListener('click', () => {
                this.triggerFileSelection();
            });
        }

        // Delete button handlers (delegated)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-image-btn')) {
                const mediaId = e.target.dataset.mediaId;
                this.deleteImage(mediaId);
            }
        });
    }

    /**
     * Trigger file selection dialog
     */
    triggerFileSelection() {
        const fileInput = document.getElementById('profile-image-input');
        if (fileInput) {
            fileInput.click();
        }
    }

    /**
     * Handle file selection
     */
    async handleFileSelection(files) {
        if (!files || files.length === 0) return;

        const file = files[0];
        
        // Validate file
        if (!this.validateImageFile(file)) {
            return;
        }

        try {
            // Show upload progress
            this.showUploadProgress(file.name);

            // Request upload URL
            const uploadData = await this.service.requestUploadUrl(
                this.currentProfileId, 
                file, 
                this.imageOrder
            );

            // Upload to S3
            const uploadResult = await this.service.uploadImageToS3(uploadData, file);

            // Complete upload
            await this.service.completeUpload(
                this.currentProfileId, 
                uploadData.mediaId, 
                uploadResult
            );

            // Start monitoring processing
            this.monitorProcessing(uploadData.mediaId);

            // Update UI
            this.imageOrder++;
            this.updateUploadButton();
            this.hideUploadProgress();

        } catch (error) {
            console.error('Upload failed:', error);
            this.showError('Upload failed: ' + error.message);
            this.hideUploadProgress();
        }
    }

    /**
     * Validate image file
     */
    validateImageFile(file) {
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Invalid file type. Please select a JPEG, PNG, or WebP image.');
            return false;
        }

        // Check file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showError('File size too large. Please select an image smaller than 10MB.');
            return false;
        }

        return true;
    }

    /**
     * Monitor image processing status
     */
    async monitorProcessing(mediaId) {
        const maxAttempts = 60; // 5 minutes with 5-second intervals
        let attempts = 0;

        const checkStatus = async () => {
            try {
                const status = await this.service.getProcessingStatus(this.currentProfileId, mediaId);
                
                if (status.status === 'completed') {
                    this.onImageProcessed(mediaId, status);
                    return;
                } else if (status.status === 'failed') {
                    this.onImageProcessingFailed(mediaId, status);
                    return;
                }

                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000); // Check every 5 seconds
                } else {
                    this.onImageProcessingTimeout(mediaId);
                }

            } catch (error) {
                console.error('Status check failed:', error);
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 5000);
                }
            }
        };

        // Start monitoring
        setTimeout(checkStatus, 5000);
    }

    /**
     * Handle successful image processing
     */
    onImageProcessed(mediaId, status) {
        console.log('Image processed successfully:', mediaId, status);
        this.renderImageGrid(); // Refresh the grid
        this.showSuccess('Image uploaded successfully!');
    }

    /**
     * Handle failed image processing
     */
    onImageProcessingFailed(mediaId, status) {
        console.error('Image processing failed:', mediaId, status);
        this.showError('Image processing failed. Please try again.');
    }

    /**
     * Handle processing timeout
     */
    onImageProcessingTimeout(mediaId) {
        console.warn('Image processing timeout:', mediaId);
        this.showWarning('Image is still processing. Please check back later.');
    }

    /**
     * Delete an image
     */
    async deleteImage(mediaId) {
        if (!confirm('Are you sure you want to delete this image?')) {
            return;
        }

        try {
            await this.service.deleteImage(this.currentProfileId, mediaId);
            this.renderImageGrid(); // Refresh the grid
            this.imageOrder = Math.max(1, this.imageOrder - 1);
            this.updateUploadButton();
            this.showSuccess('Image deleted successfully!');
        } catch (error) {
            console.error('Delete failed:', error);
            this.showError('Failed to delete image: ' + error.message);
        }
    }

    /**
     * Render the image grid
     */
    renderImageGrid() {
        const gridContainer = document.getElementById('profile-images-grid');
        if (!gridContainer) return;

        // This would typically fetch current images from the API
        // For now, we'll show a placeholder
        gridContainer.innerHTML = `
            <div class="image-slot empty" data-order="1">
                <div class="upload-placeholder">
                    <i class="icon-plus"></i>
                    <span>Add Photo</span>
                </div>
            </div>
            <div class="image-slot empty" data-order="2">
                <div class="upload-placeholder">
                    <i class="icon-plus"></i>
                    <span>Add Photo</span>
                </div>
            </div>
            <div class="image-slot empty" data-order="3">
                <div class="upload-placeholder">
                    <i class="icon-plus"></i>
                    <span>Add Photo</span>
                </div>
            </div>
            <div class="image-slot empty" data-order="4">
                <div class="upload-placeholder">
                    <i class="icon-plus"></i>
                    <span>Add Photo</span>
                </div>
            </div>
            <div class="image-slot empty" data-order="5">
                <div class="upload-placeholder">
                    <i class="icon-plus"></i>
                    <span>Add Photo</span>
                </div>
            </div>
        `;
    }

    /**
     * Update upload button state
     */
    updateUploadButton() {
        const uploadButton = document.getElementById('upload-image-btn');
        if (!uploadButton) return;

        const activeUploads = this.service.getActiveUploads();
        const processingImages = this.service.getProcessingImages();

        if (activeUploads.length > 0 || processingImages.length > 0) {
            uploadButton.disabled = true;
            uploadButton.textContent = 'Uploading...';
        } else if (this.imageOrder > 5) {
            uploadButton.disabled = true;
            uploadButton.textContent = 'Max Images Reached';
        } else {
            uploadButton.disabled = false;
            uploadButton.textContent = 'Add Photo';
        }
    }

    /**
     * Show upload progress
     */
    showUploadProgress(filename) {
        const progressContainer = document.getElementById('upload-progress');
        if (progressContainer) {
            progressContainer.innerHTML = `
                <div class="upload-progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="upload-status">Uploading ${filename}...</div>
            `;
            progressContainer.style.display = 'block';
        }
    }

    /**
     * Hide upload progress
     */
    hideUploadProgress() {
        const progressContainer = document.getElementById('upload-progress');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show warning message
     */
    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    /**
     * Show notification
     */
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

/**
 * Usage Example
 */
async function initializeProfileImages(authService) {
    try {
        // Create profile image service
        const profileImageService = new VibeProfileImageService(authService);
        
        // Create UI component
        const profileImageUI = new VibeProfileImageUI(profileImageService);
        
        // Initialize with current profile
        const currentProfileId = 'profile123'; // Get from your app state
        profileImageUI.initialize(currentProfileId);
        
        console.log('Profile image service initialized successfully');
        
        return {
            service: profileImageService,
            ui: profileImageUI
        };

    } catch (error) {
        console.error('Failed to initialize profile image service:', error);
        throw error;
    }
}

/**
 * React Hook Example (if using React)
 */
function useProfileImages(authService) {
    const [profileImageService, setProfileImageService] = useState(null);
    const [profileImageUI, setProfileImageUI] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function setupProfileImages() {
            try {
                setIsLoading(true);
                setError(null);
                
                const { service, ui } = await initializeProfileImages(authService);
                
                setProfileImageService(service);
                setProfileImageUI(ui);
                
            } catch (error) {
                setError(error.message);
            } finally {
                setIsLoading(false);
            }
        }

        if (authService && authService.isAuthenticated) {
            setupProfileImages();
        }
    }, [authService]);

    return {
        profileImageService,
        profileImageUI,
        isLoading,
        error
    };
}

/**
 * Example HTML Structure
 * 
 * <div id="profile-images-container">
 *     <div id="profile-images-grid">
 *         <!-- Image slots will be rendered here -->
 *     </div>
 *     
 *     <div id="upload-controls">
 *         <input type="file" id="profile-image-input" accept="image/*" style="display: none;">
 *         <button id="upload-image-btn" class="btn btn-primary">Add Photo</button>
 *     </div>
 *     
 *     <div id="upload-progress" style="display: none;">
 *         <!-- Upload progress will be shown here -->
 *     </div>
 * </div>
 * 
 * <style>
 * .image-slot {
 *     width: 120px;
 *     height: 160px;
 *     border: 2px dashed #ccc;
 *     border-radius: 8px;
 *     display: flex;
 *     align-items: center;
 *     justify-content: center;
 *     margin: 8px;
 *     position: relative;
 * }
 * 
 * .image-slot.filled {
 *     border: none;
 *     background-size: cover;
 *     background-position: center;
 * }
 * 
 * .upload-placeholder {
 *     text-align: center;
 *     color: #666;
 * }
 * 
 * .upload-progress-bar {
 *     width: 100%;
 *     height: 4px;
 *     background: #eee;
 *     border-radius: 2px;
 *     overflow: hidden;
 * }
 * 
 * .progress-fill {
 *     height: 100%;
 *     background: #007bff;
 *     width: 0%;
 *     transition: width 0.3s ease;
 *     animation: progress-animation 2s infinite;
 * }
 * 
 * @keyframes progress-animation {
 *     0% { width: 0%; }
 *     50% { width: 70%; }
 *     100% { width: 100%; }
 * }
 * 
 * .notification {
 *     position: fixed;
 *     top: 20px;
 *     right: 20px;
 *     padding: 12px 16px;
 *     border-radius: 4px;
 *     color: white;
 *     z-index: 1000;
 *     animation: slide-in 0.3s ease;
 * }
 * 
 * .notification-success { background: #28a745; }
 * .notification-error { background: #dc3545; }
 * .notification-warning { background: #ffc107; color: #212529; }
 * 
 * @keyframes slide-in {
 *     from { transform: translateX(100%); opacity: 0; }
 *     to { transform: translateX(0); opacity: 1; }
 * }
 * </style>
 */

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        VibeProfileImageService,
        VibeProfileImageUI,
        initializeProfileImages,
        useProfileImages
    };
} 