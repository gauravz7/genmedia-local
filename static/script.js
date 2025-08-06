document.addEventListener('DOMContentLoaded', function () {
    const loadingOverlay = document.getElementById('loading-overlay');

    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    const generatePromptBtn = document.getElementById('generate-prompt-btn');
    const userPromptTextarea = document.getElementById('user-prompt');
    const systemInstructionsTextarea = document.getElementById('system-instructions');
    const finalPromptTextarea = document.getElementById('final-prompt');
    const addToQueueBtn = document.getElementById('add-to-video-generation-btn');
    const promptQueueContainer = document.getElementById('prompt-queue');
    const runParallelBtn = document.getElementById('run-parallel-generation-btn');
    const videoStatusContainer = document.getElementById('video-status-container');
    const videoModelSelect = document.getElementById('video-model-select');
    const seedInput = document.getElementById('seed-input');
    const videoAspectRatioSelect = document.getElementById('video-aspect-ratio');
    const videoNegativePrompt = document.getElementById('video-negative-prompt');
    const historyTab = document.getElementById('history-tab');
    const historyList = document.getElementById('history-list');
    const refineControls = document.getElementById('refine-controls');
    const refineInstruction = document.getElementById('refine-instruction');
    const refinePromptBtn = document.getElementById('refine-prompt-btn');
    const themeToggle = document.getElementById('checkbox');
    const systemInstructionSelect = document.getElementById('system-instruction-select');
    const saveInstructionBtn = document.getElementById('save-instruction-btn');
    const saveInstructionName = document.getElementById('save-instruction-name');
    const deleteInstructionBtn = document.getElementById('delete-instruction-btn');
    const imageUpload = document.getElementById('image-upload');
    const imageAnimationPrompt = document.getElementById('image-animation-prompt');
    const imageNegativePrompt = document.getElementById('image-negative-prompt');
    const imageVideoModelSelect = document.getElementById('image-video-model-select');
    const imageSeedInput = document.getElementById('image-seed-input');
    const imageAspectRatioSelect = document.getElementById('image-aspect-ratio');
    const addToImageQueueBtn = document.getElementById('add-to-image-queue-btn');
    const imageVideoQueueContainer = document.getElementById('image-video-queue');
    const runParallelImageGenerationBtn = document.getElementById('run-parallel-image-generation-btn');
    const imageVideoStatusContainer = document.getElementById('image-video-status-container');
    const cropModal = new bootstrap.Modal(document.getElementById('cropModal'));
    const imageToCrop = document.getElementById('image-to-crop');
    const cropAndSaveBtn = document.getElementById('crop-and-save-btn');
    const cropAspectRatioSelect = document.getElementById('crop-aspect-ratio');
    const editorImageUpload = document.getElementById('editor-image-upload');
    const editorCanvas = document.getElementById('editor-canvas');
    const brushColorInput = document.getElementById('brush-color');
    const brushSizeInput = document.getElementById('brush-size');
    const textInput = document.getElementById('text-input');
    const textColorInput = document.getElementById('text-color');
    const fontSizeInput = document.getElementById('font-size');
    const addTextBtn = document.getElementById('add-text-btn');
    const clearEditsBtn = document.getElementById('clear-edits-btn');
    const sendToVideoTabBtn = document.getElementById('send-to-video-tab-btn');
    const editorPrompt = document.getElementById('editor-prompt');
    const editorNegativePrompt = document.getElementById('editor-negative-prompt');
    const editorSeed = document.getElementById('editor-seed');
    const editorAspectRatio = document.getElementById('editor-aspect-ratio');
    const generateEditorImageBtn = document.getElementById('generate-editor-image-btn');
    const customCursor = document.getElementById('custom-cursor');
    const projectIdInput = document.getElementById('project-id-input');
    const gcsBucketInput = document.getElementById('gcs-bucket-input');
    const saveValidateBtn = document.getElementById('save-validate-btn');
    const validationStatus = document.getElementById('validation-status');
    const usageDashboard = document.getElementById('usage-dashboard');
    const usageReport = document.getElementById('usage-report');
    const segmentationImageUpload = document.getElementById('segmentation-image-upload');
    const segmentationMode = document.getElementById('segmentation-mode');
    const segmentationPromptContainer = document.getElementById('segmentation-prompt-container');
    const segmentationPrompt = document.getElementById('segmentation-prompt');
    const runSegmentationBtn = document.getElementById('run-segmentation-btn');
    const segmentationOriginalImage = document.getElementById('segmentation-original-image');
    const segmentationMasksContainer = document.getElementById('segmentation-masks-container');
    const vtoMaskCheckbox = document.getElementById('vto-mask-checkbox');
    const vtoMaskContainer = document.getElementById('vto-mask-container');
    const runVtoBtn = document.getElementById('run-vto-btn');
    const vtoPersonImage = document.getElementById('vto-person-image');
    const vtoProductImage = document.getElementById('vto-product-image');
    const vtoMaskImage = document.getElementById('vto-mask-image');
    const vtoGeneratedImage = document.getElementById('vto-generated-image');
    const vtoPrompt = document.getElementById('vto-prompt');
    const vtoPersonDescription = document.getElementById('vto-person-description');
    const vtoProductDescription = document.getElementById('vto-product-description');
    const vtoPersonImageUri = document.getElementById('vto-person-image-uri');
    const vtoProductImageUri = document.getElementById('vto-product-image-uri');
    const vtoModelEndpoint = document.getElementById('vto-model-endpoint');
    const vtoSampleCount = document.getElementById('vto-sample-count');
    const vtoBaseSteps = document.getElementById('vto-base-steps');
    const vtoSeed = document.getElementById('vto-seed');
    const sendVtoToVideoTabBtn = document.getElementById('send-vto-to-video-tab-btn');
    const runRecontextBtn = document.getElementById('run-recontext-btn');
    const recontextImages = document.getElementById('recontext-images');
    const recontextImageUris = document.getElementById('recontext-image-uris');
    const recontextPrompt = document.getElementById('recontext-prompt');
    const recontextProductDescription = document.getElementById('recontext-product-description');
    const recontextDisablePromptEnhancement = document.getElementById('recontext-disable-prompt-enhancement');
    const recontextSampleCount = document.getElementById('recontext-sample-count');
    const recontextBaseSteps = document.getElementById('recontext-base-steps');
    const recontextSafetySetting = document.getElementById('recontext-safety-setting');
    const recontextPersonGeneration = document.getElementById('recontext-person-generation');
    const recontextGeneratedImages = document.getElementById('recontext-generated-images');
    const recontextAspectRatio = document.getElementById('recontext-aspect-ratio');
    const recontextResolution = document.getElementById('recontext-resolution');
    const recontextSeed = document.getElementById('recontext-seed');
    const runVeoEditBtn = document.getElementById('run-veo-edit-btn');
    const veoEditPrompt = document.getElementById('veo-edit-prompt');
    const veoEditVideoGcs = document.getElementById('veo-edit-video-gcs');
    const veoEditVideoFile = document.getElementById('veo-edit-video-file');
    const veoEditMaskGcs = document.getElementById('veo-edit-mask-gcs');
    const veoEditMaskFile = document.getElementById('veo-edit-mask-file');
    const veoEditMaskMimeType = document.getElementById('veo-edit-mask-mime-type');
    const veoEditMaskMode = document.getElementById('veo-edit-mask-mode');
    const veoEditAspectRatio = document.getElementById('veo-edit-aspect-ratio');
    const veoEditDuration = document.getElementById('veo-edit-duration');
    const veoEditEnhancePrompt = document.getElementById('veo-edit-enhance-prompt');
    const veoEditStatusContainer = document.getElementById('veo-edit-status-container');
    const runImagenEditBtn = document.getElementById('run-imagen-edit-btn');
    const imagenEditPrompt = document.getElementById('imagen-edit-prompt');
    const imagenEditOriginalImage = document.getElementById('imagen-edit-original-image');
    const imagenEditMaskImage = document.getElementById('imagen-edit-mask-image');
    const imagenEditMode = document.getElementById('imagen-edit-mode');
    const imagenMaskMode = document.getElementById('imagen-mask-mode');
    const imagenEditOriginalPreview = document.getElementById('imagen-edit-original-preview');
    const imagenEditEditedPreview = document.getElementById('imagen-edit-edited-preview');
    const runVeoAdvancedEditBtn = document.getElementById('run-veo-advanced-edit-btn');
    const veoAdvancedPrompt = document.getElementById('veo-advanced-prompt');
    const veoAdvancedCameraControl = document.getElementById('veo-advanced-camera-control');
    const veoAdvancedImageGcs = document.getElementById('veo-advanced-image-gcs');
    const veoAdvancedImageFile = document.getElementById('veo-advanced-image-file');
    const veoAdvancedVideoGcs = document.getElementById('veo-advanced-video-gcs');
    const veoAdvancedVideoFile = document.getElementById('veo-advanced-video-file');
    const veoAdvancedLastFrameGcs = document.getElementById('veo-advanced-last-frame-gcs');
    const veoAdvancedLastFrameFile = document.getElementById('veo-advanced-last-frame-file');
    const veoAdvancedAspectRatio = document.getElementById('veo-advanced-aspect-ratio');
    const veoAdvancedDuration = document.getElementById('veo-advanced-duration');
    const veoAdvancedEnhancePrompt = document.getElementById('veo-advanced-enhance-prompt');
    const veoAdvancedEditStatusContainer = document.getElementById('veo-advanced-edit-status-container');

    let promptsForGeneration = [];
    let imagePromptsForGeneration = [];
    let cropper;
    let currentFile;
    let croppedFile = null;
    const editorCtx = editorCanvas.getContext('2d');
    let isDrawing = false;
    let isDraggingText = false;
    let textElements = [];
    let shapes = [];
    let activeTextIndex = -1;
    let dragStartX, dragStartY;
    let currentTool = 'pen';
    let startX, startY;

    // 1. Generate Final Prompt
    generatePromptBtn.addEventListener('click', async () => {
        const userPrompt = userPromptTextarea.value;
        const systemInstructions = systemInstructionsTextarea.value;
        const imageFile = document.getElementById('prompt-image-upload').files[0];

        if (!userPrompt.trim() || !systemInstructions.trim()) {
            alert('Please provide both a user prompt and system instructions.');
            return;
        }

        let requestBody = {
            user_prompt: userPrompt,
            system_instructions: systemInstructions,
        };

        if (imageFile) {
            const reader = new FileReader();
            reader.onloadend = () => {
                requestBody.image_data = reader.result.split(',')[1]; // Get base64 part
                sendPromptRequest(requestBody);
            };
            reader.readAsDataURL(imageFile);
        } else {
            sendPromptRequest(requestBody);
        }
    });

    async function sendPromptRequest(body) {
        showLoading();
        try {
            const response = await fetch('/generate-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            finalPromptTextarea.value = data.final_prompt;
            refineControls.style.display = 'block';
        } catch (error) {
            console.error('Error generating prompt:', error);
            alert('Failed to generate prompt. See console for details.');
        } finally {
            hideLoading();
        }
    }

    // Refine the prompt with AI
    refinePromptBtn.addEventListener('click', async () => {
        const currentPrompt = finalPromptTextarea.value;
        const instruction = refineInstruction.value;

        if (!currentPrompt.trim() || !instruction.trim()) {
            alert('Please provide a prompt and a refinement instruction.');
            return;
        }
        showLoading();
        try {
            const response = await fetch('/refine-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_prompt: currentPrompt, refine_instruction: instruction }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            finalPromptTextarea.value = data.refined_prompt;
            refineInstruction.value = '';
        } catch (error) {
            console.error('Error refining prompt:', error);
            alert('Failed to refine prompt. See console for details.');
        } finally {
            hideLoading();
        }
    });

    // Add to Video Generation Queue
    addToQueueBtn.addEventListener('click', () => {
        const finalPrompt = finalPromptTextarea.value;
        if (!finalPrompt.trim()) {
            alert('Please generate a prompt first.');
            return;
        }
        promptsForGeneration.push(finalPrompt);
        renderPromptQueue();
        finalPromptTextarea.value = '';
    });

    // Render the prompt queue
    function renderPromptQueue() {
        promptQueueContainer.innerHTML = '';
        promptsForGeneration.forEach((prompt, index) => {
            const promptElement = document.createElement('div');
            promptElement.className = 'list-group-item d-flex justify-content-between align-items-center';
            promptElement.innerHTML = `<span>${prompt}</span><button class="btn btn-danger btn-sm" data-index="${index}">Remove</button>`;
            promptQueueContainer.appendChild(promptElement);
        });
        promptQueueContainer.querySelectorAll('.btn-danger').forEach(button => {
            button.addEventListener('click', (e) => {
                promptsForGeneration.splice(e.target.dataset.index, 1);
                renderPromptQueue();
            });
        });
    }

    // Run Parallel Generation
    runParallelBtn.addEventListener('click', async () => {
        if (promptsForGeneration.length === 0) {
            alert('Please add prompts to the queue first.');
            return;
        }
        try {
            const response = await fetch('/generate-videos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompts: promptsForGeneration,
                    model: videoModelSelect.value,
                    seed: parseInt(seedInput.value, 10),
                    aspect_ratio: videoAspectRatioSelect.value,
                    negative_prompt: videoNegativePrompt.value,
                }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            promptsForGeneration = [];
            renderPromptQueue();
            displayVideoStatuses(data.operation_ids, videoStatusContainer);
        } catch (error) {
            console.error('Error starting video generation:', error);
            alert('Failed to start video generation. See console for details.');
            hideLoading();
        }
    });

    // Display Video Statuses
    function displayVideoStatuses(operationIds, container) {
        container.innerHTML = '<h3>Generation Status</h3>';
        operationIds.forEach(opId => {
            const statusElement = document.createElement('div');
            statusElement.id = `status-${opId}`;
            statusElement.className = 'p-2 border rounded mb-2';
            statusElement.innerHTML = `<strong>Operation ID:</strong> ${opId} - <span class="status-badge">Queued</span>`;
            container.appendChild(statusElement);
            pollVideoStatus(opId);
        });
    }

    // Poll for Video Status
    function pollVideoStatus(operationId) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/video-status/${operationId}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                const statusElement = document.getElementById(`status-${operationId}`);
                const statusBadge = statusElement.querySelector('.status-badge');
                statusBadge.textContent = data.status;

                if (data.status === 'running') {
                    statusBadge.innerHTML = `running <div class="spinner"></div>`;
                } else if (data.status === 'failed') {
                    statusBadge.className = 'status-badge text-danger';
                    statusElement.innerHTML += `<br><small>${data.error_message}</small>`;
                    clearInterval(interval);
                    hideLoading();
                } else if (data.status === 'completed') {
                    statusBadge.className = 'status-badge text-success';
                    let mediaHtml = '';
                    if (data.image_path) {
                        mediaHtml += `<img src="${data.image_path}" class="img-fluid mb-2" style="max-height: 150px;">`;
                    }
                    mediaHtml += `
                        <video controls width="100%"><source src="${data.video_path}" type="video/mp4"></video>
                        <a href="${data.video_path}" class="btn btn-success mt-2" download>Download Video</a>
`;
                    statusElement.innerHTML = `<p><strong>Prompt:</strong> ${data.prompt}</p>${mediaHtml}`;
                    clearInterval(interval);
                    hideLoading();
                }
            } catch (error) {
                console.error(`Error polling status for ${operationId}:`, error);
                clearInterval(interval);
            }
        }, 5000);
    }

    // Fetch and display generation history
    async function fetchGenerationHistory() {
        try {
            const response = await fetch('/get-generation-history');
            const data = await response.json();
            historyList.innerHTML = '';
            data.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'accordion-item';
                const headerId = `header-${item.id}`;
                const collapseId = `collapse-${item.id}`;
                let bodyContent = `<p><strong>Status:</strong> ${item.status}</p>`;
                let mediaHtml = '<div class="history-media">';
                let hasMedia = false;

                // Handle initial image for video generations
                if (item.image_path && (item.operation_type !== 'vto' && item.operation_type !== 'recontext' && item.operation_type !== 'segmentation')) {
                    mediaHtml += `<div class="history-item"><h6>Initial Image</h6><img src="${item.image_path}" alt="Initial image" style="max-width: 100%; border-radius: 5px;"></div>`;
                    hasMedia = true;
                }

                // Handle generated video
                if (item.status === 'completed' && item.video_path) {
                    mediaHtml += `<div class="history-item"><h6>Generated Video</h6><video controls width="100%"><source src="${item.video_path}" type="video/mp4"></video><a href="${item.video_path}" class="btn btn-success mt-2" download>Download Video</a></div>`;
                    hasMedia = true;
                }

                // Handle generated image for VTO, recontext, etc.
                if (item.status === 'completed' && item.image_path && (item.operation_type === 'vto' || item.operation_type === 'recontext' || item.operation_type === 'segmentation')) {
                    mediaHtml += `<div class="history-item"><h6>Generated Image</h6><img src="${item.image_path}" alt="Generated image" style="max-width: 100%; border-radius: 5px;"><a href="${item.image_path}" class="btn btn-success mt-2" download>Download Image</a></div>`;
                    hasMedia = true;
                }
                
                // Handle segmentation masks
                if (item.operation_type === 'segmentation' && item.output_payload) {
                    try {
                        const output = JSON.parse(item.output_payload);
                        if (output.masks && output.masks.length > 0) {
                            mediaHtml += `<div class="history-item"><h6>Segmentation Masks</h6>`;
                            output.masks.forEach(maskUrl => {
                                mediaHtml += `<img src="${maskUrl}" alt="Segmentation Mask" style="max-width: 30%; border-radius: 5px; margin: 5px;">`;
                            });
                            mediaHtml += `</div>`;
                            hasMedia = true;
                        }
                    } catch(e) { console.error("Error parsing segmentation output payload", e); }
                }


                if (item.status === 'failed') {
                    mediaHtml += `<div class="history-item"><h6>Error</h6><p class="text-danger">${item.error_message || 'No error message provided.'}</p></div>`;
                    hasMedia = true;
                }

                mediaHtml += '</div>';
                if (hasMedia) {
                    bodyContent += mediaHtml;
                }

                historyItem.innerHTML = `
                    <h2 class="accordion-header" id="${headerId}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">${item.prompt}</button>
                    </h2>
                    <div id="${collapseId}" class="accordion-collapse collapse" data-bs-parent="#history-list">
                        <div class="accordion-body">${bodyContent}</div>
                    </div>`;
                historyList.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Error fetching generation history:', error);
        }
    }

    historyTab.addEventListener('click', fetchGenerationHistory);
    fetchGenerationHistory();

    // System Instruction Management
    let systemInstructions = [];

    async function loadSystemInstructions() {
        try {
            const response = await fetch('/get-system-instructions');
            const data = await response.json();
            systemInstructions = data.instructions;
            populateInstructionSelect();
        } catch (error) {
            console.error('Error loading system instructions:', error);
        }
    }

    function populateInstructionSelect() {
        systemInstructionSelect.innerHTML = '<option selected>Load a saved instruction...</option>';
        systemInstructions.forEach(inst => {
            const option = document.createElement('option');
            option.value = inst.id;
            option.textContent = inst.name;
            systemInstructionSelect.appendChild(option);
        });
    }

    systemInstructionSelect.addEventListener('change', () => {
        const selectedId = parseInt(systemInstructionSelect.value, 10);
        const selectedInstruction = systemInstructions.find(inst => inst.id === selectedId);
        if (selectedInstruction) {
            systemInstructionsTextarea.value = selectedInstruction.content;
        }
    });

    saveInstructionBtn.addEventListener('click', async () => {
        const name = saveInstructionName.value;
        const content = systemInstructionsTextarea.value;
        if (!name.trim() || !content.trim()) {
            alert('Please provide a name and content for the system instruction.');
            return;
        }
        try {
            const response = await fetch('/save-system-instruction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, content }),
            });
            const data = await response.json();
            if (data.success) {
                saveInstructionName.value = '';
                loadSystemInstructions();
            } else {
                alert('Error saving instruction: ' + data.error);
            }
        } catch (error) {
            console.error('Error saving system instruction:', error);
        }
    });

    deleteInstructionBtn.addEventListener('click', async () => {
        const selectedId = parseInt(systemInstructionSelect.value, 10);
        if (isNaN(selectedId)) {
            alert('Please select an instruction to delete.');
            return;
        }
        if (confirm('Are you sure you want to delete this instruction?')) {
            try {
                const response = await fetch(`/delete-system-instruction/${selectedId}`, {
                    method: 'DELETE',
                });
                const data = await response.json();
                if (data.success) {
                    loadSystemInstructions();
                } else {
                    alert('Error deleting instruction: ' + data.error);
                }
            } catch (error) {
                console.error('Error deleting system instruction:', error);
            }
        }
    });

    loadSystemInstructions();

    // Theme switcher logic
    themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('light-mode', themeToggle.checked);
    });

    // Image Cropping Logic
    imageUpload.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            currentFile = files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                imageToCrop.src = event.target.result;
                cropModal.show();
                if (cropper) {
                    cropper.destroy();
                }
                cropper = new Cropper(imageToCrop, {
                    aspectRatio: parseFloat(cropAspectRatioSelect.value),
                    viewMode: 1,
                });
            };
            reader.readAsDataURL(currentFile);
        }
    });

    cropAspectRatioSelect.addEventListener('change', () => {
        if (cropper) {
            cropper.setAspectRatio(parseFloat(cropAspectRatioSelect.value));
        }
    });

    cropAndSaveBtn.addEventListener('click', () => {
        cropper.getCroppedCanvas().toBlob((blob) => {
            croppedFile = new File([blob], currentFile.name, { type: currentFile.type });
            const previewUrl = URL.createObjectURL(croppedFile);
            document.getElementById('image-preview').src = previewUrl;
            document.getElementById('image-preview-container').style.display = 'block';
            
            // Enable the rest of the form
            imageAnimationPrompt.disabled = false;
            imageNegativePrompt.disabled = false;
            imageAspectRatioSelect.disabled = false;
            imageVideoModelSelect.disabled = false;
            imageSeedInput.disabled = false;
            addToImageQueueBtn.disabled = false;

            cropModal.hide();
        });
    });

    // Image to Video Generation Queueing
    addToImageQueueBtn.addEventListener('click', () => {
        if (!croppedFile) {
            alert('Please select and crop an image first.');
            return;
        }
        const prompt = imageAnimationPrompt.value;
        const negativePrompt = imageNegativePrompt.value;
        const model = imageVideoModelSelect.value;
        const seed = imageSeedInput.value;
        const aspectRatio = imageAspectRatioSelect.value;

        if (!prompt.trim()) {
            alert('Please provide an animation prompt.');
            return;
        }

        imagePromptsForGeneration.push({ file: croppedFile, prompt, negativePrompt, model, seed, aspectRatio, preview: URL.createObjectURL(croppedFile) });
        renderImagePromptQueue();
        
        // Reset the form
        imageUpload.value = '';
        imageAnimationPrompt.value = '';
        imageNegativePrompt.value = '';
        document.getElementById('image-preview-container').style.display = 'none';
        imageAnimationPrompt.disabled = true;
        imageNegativePrompt.disabled = true;
        imageAspectRatioSelect.disabled = true;
        imageVideoModelSelect.disabled = true;
        imageSeedInput.disabled = true;
        addToImageQueueBtn.disabled = true;
        croppedFile = null;
    });

    function renderImagePromptQueue() {
        imageVideoQueueContainer.innerHTML = '';
        imagePromptsForGeneration.forEach((item, index) => {
            const queueItem = document.createElement('div');
            queueItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            queueItem.innerHTML = `
                <div class="d-flex align-items-center">
                    <img src="${item.preview}" alt="Preview" width="50" class="me-3">
                    <div>
                        <p class="mb-0">${item.prompt}</p>
                        <small class="text-muted">${item.model}, Seed: ${item.seed}, Aspect: ${item.aspectRatio}, Negative: ${item.negativePrompt}</small>
                    </div>
                </div>
                <button class="btn btn-danger btn-sm" data-index="${index}">Remove</button>`;
            imageVideoQueueContainer.appendChild(queueItem);
        });
        imageVideoQueueContainer.querySelectorAll('.btn-danger').forEach(button => {
            button.addEventListener('click', (e) => {
                imagePromptsForGeneration.splice(e.target.dataset.index, 1);
                renderImagePromptQueue();
            });
        });
    }

    runParallelImageGenerationBtn.addEventListener('click', () => {
        if (imagePromptsForGeneration.length === 0) {
            alert('Please add items to the image generation queue first.');
            return;
        }
        imageVideoStatusContainer.innerHTML = '<h3>Image to Video Generation Status</h3>';
        const promises = imagePromptsForGeneration.map(item => {
            const formData = new FormData();
            formData.append('image', item.file);
            formData.append('prompt', item.prompt);
            formData.append('negative_prompt', item.negativePrompt);
            formData.append('model', item.model);
            formData.append('seed', item.seed);
            formData.append('aspect_ratio', item.aspectRatio);

            return fetch('/generate-image-video', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.operation_id) {
                    const statusElement = document.createElement('div');
                    statusElement.id = `status-${data.operation_id}`;
                    statusElement.className = 'p-2 border rounded mb-2';
                    statusElement.innerHTML = `<strong>Operation ID:</strong> ${data.operation_id} - <span class="status-badge">Queued</span>`;
                    imageVideoStatusContainer.appendChild(statusElement);
                    pollVideoStatus(data.operation_id);
                }
            })
            .catch(error => {
                console.error('Error starting image to video generation:', error);
            });
        });

        Promise.all(promises).finally(() => {
            // This will hide the loading indicator after all requests are initiated,
            // but polling will continue in the background.
            // The individual pollVideoStatus calls will hide the loader when they complete.
        });

        imagePromptsForGeneration = [];
        renderImagePromptQueue();
    });

    // New: Generate Image in Editor
    generateEditorImageBtn.addEventListener('click', async () => {
        const prompt = editorPrompt.value;
        const negativePrompt = editorNegativePrompt.value;
        const seed = parseInt(editorSeed.value, 10);
        const aspectRatio = editorAspectRatio.value;

        if (!prompt.trim()) {
            alert('Please provide a prompt for image generation.');
            return;
        }
        showLoading();
        try {
            const response = await fetch('/generate-editor-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    negative_prompt: negativePrompt,
                    seed: seed,
                    aspect_ratio: aspectRatio,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.image_data) {
                currentImage.onload = () => {
                    redrawEditorCanvas();
                    sendToVideoTabBtn.disabled = false;
                };
                currentImage.src = `data:image/png;base64,${data.image_data}`;
            } else {
                alert('Failed to generate image. See console for details.');
            }
        } catch (error) {
            console.error('Error generating image:', error);
            alert('Failed to generate image. See console for details.');
        } finally {
            hideLoading();
        }
    });

    // Image Editor Logic
    let currentImage = new Image();
    editorImageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                currentImage.onload = () => {
                    redrawEditorCanvas();
                    sendToVideoTabBtn.disabled = false;
                };
                currentImage.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    function redrawEditorCanvas() {
        editorCanvas.width = currentImage.width;
        editorCanvas.height = currentImage.height;
        editorCtx.drawImage(currentImage, 0, 0);

        shapes.forEach(shape => {
            editorCtx.strokeStyle = shape.color;
            editorCtx.lineWidth = shape.size;
            editorCtx.beginPath();
            if (shape.type === 'pen') {
                editorCtx.moveTo(shape.startX, shape.startY);
                editorCtx.lineTo(shape.endX, shape.endY);
            } else if (shape.type === 'arrow') {
                drawArrow(shape.startX, shape.startY, shape.endX, shape.endY);
            } else if (shape.type === 'box') {
                editorCtx.rect(shape.startX, shape.startY, shape.endX - shape.startX, shape.endY - shape.startY);
            }
            editorCtx.stroke();
        });

        textElements.forEach(text => {
            editorCtx.font = `${text.size}px sans-serif`;
            editorCtx.fillStyle = text.color;
            editorCtx.fillText(text.text, text.x, text.y);
        });
    }

    function getMousePos(canvas, evt) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        return {
            x: (evt.clientX - rect.left) * scaleX,
            y: (evt.clientY - rect.top) * scaleY
        };
    }

    editorCanvas.addEventListener('mousedown', (e) => {
        const pos = getMousePos(editorCanvas, e);
        startX = pos.x;
        startY = pos.y;
        isDrawing = true;
        
        // Check if clicking on existing text
        activeTextIndex = -1;
        textElements.forEach((text, index) => {
            editorCtx.font = `${text.size}px sans-serif`;
            const textWidth = editorCtx.measureText(text.text).width;
            if (pos.x >= text.x && pos.x <= text.x + textWidth && pos.y >= text.y - text.size && pos.y <= text.y) {
                activeTextIndex = index;
                isDrawing = false;
                isDraggingText = true;
                dragStartX = pos.x - text.x;
                dragStartY = pos.y - text.y;
            }
        });

        if (isDrawing && currentTool === 'pen') {
            editorCtx.beginPath();
            editorCtx.moveTo(pos.x, pos.y);
        }
    });

    editorCanvas.addEventListener('mousemove', (e) => {
        const pos = getMousePos(editorCanvas, e);
        updateCustomCursor(pos);
        if (isDrawing) {
            if (currentTool === 'pen') {
                shapes.push({
                    type: 'pen',
                    color: brushColorInput.value,
                    size: brushSizeInput.value,
                    startX: startX,
                    startY: startY,
                    endX: pos.x,
                    endY: pos.y
                });
                startX = pos.x;
                startY = pos.y;
                redrawEditorCanvas();
            }
        } else if (isDraggingText) {
            textElements[activeTextIndex].x = pos.x - dragStartX;
            textElements[activeTextIndex].y = pos.y - dragStartY;
            redrawEditorCanvas();
        }
    });

    editorCanvas.addEventListener('mouseup', (e) => {
        if (isDrawing) {
            const pos = getMousePos(editorCanvas, e);
            const shape = {
                type: currentTool,
                color: brushColorInput.value,
                size: brushSizeInput.value,
                startX: startX,
                startY: startY,
                endX: pos.x,
                endY: pos.y
            };
            shapes.push(shape);
            redrawEditorCanvas();
        }
        isDrawing = false;
        isDraggingText = false;
        activeTextIndex = -1;
    });

    editorCanvas.addEventListener('mouseout', () => {
        isDrawing = false;
        isDraggingText = false;
        activeTextIndex = -1;
        customCursor.style.display = 'none';
    });

    editorCanvas.addEventListener('mouseenter', () => {
        customCursor.style.display = 'block';
    });

    addTextBtn.addEventListener('click', () => {
        const text = textInput.value;
        if (text) {
            textElements.push({
                text: text,
                x: 50,
                y: 50,
                color: textColorInput.value,
                size: fontSizeInput.value
            });
            redrawEditorCanvas();
            textInput.value = '';
        }
    });

    clearEditsBtn.addEventListener('click', () => {
        textElements = [];
        shapes = [];
        redrawEditorCanvas();
    });

    sendToVideoTabBtn.addEventListener('click', () => {
        editorCanvas.toBlob((blob) => {
            const editedFile = new File([blob], 'edited-image.png', { type: 'image/png' });
            
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(editedFile);
            imageUpload.files = dataTransfer.files;
            
            const changeEvent = new Event('change');
            imageUpload.dispatchEvent(changeEvent);

            const imageVideoTab = new bootstrap.Tab(document.getElementById('image-video-tab'));
            imageVideoTab.show();
        });
    });

    document.querySelectorAll('input[name="editor-tool"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentTool = e.target.value;
        });
    });

    function drawArrow(fromx, fromy, tox, toy) {
        const headlen = 10; // length of head in pixels
        const dx = tox - fromx;
        const dy = toy - fromy;
        const angle = Math.atan2(dy, dx);
        editorCtx.moveTo(fromx, fromy);
        editorCtx.lineTo(tox, toy);
        editorCtx.lineTo(tox - headlen * Math.cos(angle - Math.PI / 6), toy - headlen * Math.sin(angle - Math.PI / 6));
        editorCtx.moveTo(tox, toy);
        editorCtx.lineTo(tox - headlen * Math.cos(angle + Math.PI / 6), toy - headlen * Math.sin(angle + Math.PI / 6));
    }

    function updateCustomCursor(pos) {
        const size = brushSizeInput.value;
        customCursor.style.width = `${size}px`;
        customCursor.style.height = `${size}px`;
        customCursor.style.backgroundColor = brushColorInput.value;
        customCursor.style.left = `${pos.x - size / 2}px`;
        customCursor.style.top = `${pos.y - size / 2}px`;
    }

    // Settings Logic
    async function loadSettings() {
        try {
            const response = await fetch('/get-settings');
            const data = await response.json();
            projectIdInput.value = data.project_id;
            gcsBucketInput.value = data.gcs_bucket;
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    saveValidateBtn.addEventListener('click', async () => {
        const projectId = projectIdInput.value;
        const gcsBucket = gcsBucketInput.value;

        try {
            const response = await fetch('/save-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId, gcs_bucket: gcsBucket }),
            });
            const data = await response.json();
            validationStatus.innerHTML = `
                <div class="alert alert-${data.success ? 'success' : 'danger'}">
                    ${data.message}
                </div>
            `;
            if (data.success) {
                usageDashboard.style.display = 'block';
                fetchUsageReport('1d'); // Default to 1 day
            } else {
                usageDashboard.style.display = 'none';
            }
        } catch (error) {
            validationStatus.innerHTML = `
                <div class="alert alert-danger">
                    An error occurred: ${error}
                </div>
            `;
        }
    });

    document.querySelectorAll('.report-range-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const range = e.target.dataset.range;
            fetchUsageReport(range);
        });
    });

    async function fetchUsageReport(range) {
        try {
            const response = await fetch(`/get-usage-report?range=${range}`);
            const data = await response.json();
            if (data.report) {
                usageReport.textContent = data.report;
            } else {
                usageReport.textContent = 'Failed to fetch usage report.';
            }
        } catch (error) {
            console.error('Error fetching usage report:', error);
            usageReport.textContent = 'Error fetching usage report.';
        }
    }

    loadSettings();

    // Segmentation Logic
    segmentationMode.addEventListener('change', () => {
        if (segmentationMode.value === 'semantic' || segmentationMode.value === 'prompt') {
            segmentationPromptContainer.style.display = 'block';
        } else {
            segmentationPromptContainer.style.display = 'none';
        }
    });

    segmentationImageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                segmentationOriginalImage.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    runSegmentationBtn.addEventListener('click', async () => {
        const imageFile = segmentationImageUpload.files[0];
        const mode = segmentationMode.value;
        const prompt = segmentationPrompt.value;

        if (!imageFile) {
            alert('Please upload an image for segmentation.');
            return;
        }

        if ((mode === 'semantic' || mode === 'prompt') && !prompt.trim()) {
            alert('Please provide a prompt for this segmentation mode.');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('mode', mode);
        if (prompt) {
            formData.append('prompt', prompt);
        }

        showLoading();
        try {
            const response = await fetch('/segment-image', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                segmentationMasksContainer.innerHTML = '';
                data.masks.forEach(maskUrl => {
                    const imgElement = document.createElement('img');
                    imgElement.src = maskUrl;
                    imgElement.className = 'img-fluid col-md-4';
                    segmentationMasksContainer.appendChild(imgElement);
                });
            }
        } catch (error) {
            console.error('Error during segmentation:', error);
            alert('Failed to segment image. See console for details.');
        } finally {
            hideLoading();
        }
    });

    // Virtual Try-On Logic
    vtoMaskCheckbox.addEventListener('change', () => {
        vtoMaskContainer.style.display = vtoMaskCheckbox.checked ? 'block' : 'none';
    });

    document.querySelectorAll('input[name="person-image-source"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'file') {
                document.getElementById('vto-person-image-file-container').style.display = 'block';
                document.getElementById('vto-person-image-uri-container').style.display = 'none';
            } else {
                document.getElementById('vto-person-image-file-container').style.display = 'none';
                document.getElementById('vto-person-image-uri-container').style.display = 'block';
            }
        });
    });

    document.querySelectorAll('input[name="product-image-source"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'file') {
                document.getElementById('vto-product-image-file-container').style.display = 'block';
                document.getElementById('vto-product-image-uri-container').style.display = 'none';
            } else {
                document.getElementById('vto-product-image-file-container').style.display = 'none';
                document.getElementById('vto-product-image-uri-container').style.display = 'block';
            }
        });
    });

    runVtoBtn.addEventListener('click', async () => {
        const personImageFile = vtoPersonImage.files[0];
        const productImageFile = vtoProductImage.files[0];
        const maskImageFile = vtoMaskImage.files[0];
        const personImageUri = vtoPersonImageUri.value;
        const productImageUri = vtoProductImageUri.value;

        const personImageSource = document.querySelector('input[name="person-image-source"]:checked').value;
        const productImageSource = document.querySelector('input[name="product-image-source"]:checked').value;

        if ((personImageSource === 'file' && !personImageFile) || (personImageSource === 'uri' && !personImageUri)) {
            alert('Please provide a person image (either file or URI).');
            return;
        }

        if ((productImageSource === 'file' && !productImageFile) || (productImageSource === 'uri' && !productImageUri)) {
            alert('Please provide a product image (either file or URI).');
            return;
        }

        if (vtoMaskCheckbox.checked && !maskImageFile) {
            alert('Please upload a mask image or uncheck the "Use Mask" box.');
            return;
        }

        const formData = new FormData();
        if (personImageSource === 'file') {
            formData.append('person_image', personImageFile);
        } else {
            formData.append('person_image_uri', personImageUri);
        }

        if (productImageSource === 'file') {
            formData.append('product_image', productImageFile);
        } else {
            formData.append('product_image_uri', productImageUri);
        }

        if (vtoMaskCheckbox.checked && maskImageFile) {
            formData.append('mask_image', maskImageFile);
        }

        formData.append('prompt', vtoPrompt.value);
        formData.append('person_description', vtoPersonDescription.value);
        formData.append('product_description', vtoProductDescription.value);
        formData.append('model_endpoint_name', vtoModelEndpoint.value);
        formData.append('sample_count', vtoSampleCount.value);
        formData.append('base_steps', vtoBaseSteps.value);
        formData.append('seed', vtoSeed.value);

        showLoading();
        try {
            const response = await fetch('/vto', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                vtoGeneratedImage.src = `data:image/png;base64,${data.generated_image}`;
                sendVtoToVideoTabBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error during Virtual Try-On:', error);
            alert('Failed to run Virtual Try-On. See console for details.');
        } finally {
            hideLoading();
        }
    });

    // Product Recontextualization Logic
    runRecontextBtn.addEventListener('click', async () => {
        const imageFiles = recontextImages.files;
        const imageUris = recontextImageUris.value.split(',').map(uri => uri.trim()).filter(uri => uri);

        if (imageFiles.length === 0 && imageUris.length === 0) {
            alert('Please provide at least one product image (either file or URI).');
            return;
        }

        if (imageFiles.length > 3) {
            alert('You can upload a maximum of 3 image files.');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < imageFiles.length; i++) {
            formData.append('images', imageFiles[i]);
        }
        imageUris.forEach(uri => {
            formData.append('image_uris', uri);
        });

        formData.append('prompt', recontextPrompt.value);
        formData.append('product_description', recontextProductDescription.value);
        formData.append('disable_prompt_enhancement', recontextDisablePromptEnhancement.checked);
        formData.append('sample_count', recontextSampleCount.value);
        if (recontextBaseSteps.value) {
            formData.append('base_steps', recontextBaseSteps.value);
        }
        formData.append('aspect_ratio', recontextAspectRatio.value);
        formData.append('resolution', recontextResolution.value);
        formData.append('seed', recontextSeed.value);
        formData.append('safety_setting', recontextSafetySetting.value);
        formData.append('person_generation', recontextPersonGeneration.value);

        showLoading();
        try {
            const response = await fetch('/product-recontext', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                recontextGeneratedImages.innerHTML = '';
                data.predictions.forEach(imgStr => {
                    const divElement = document.createElement('div');
                    divElement.className = 'col-md-12';
                    const imgElement = document.createElement('img');
                    imgElement.src = `data:image/png;base64,${imgStr}`;
                    imgElement.className = 'img-fluid';
                    const buttonElement = document.createElement('button');
                    buttonElement.className = 'btn btn-primary btn-sm mt-2';
                    buttonElement.textContent = 'Use this Image for Video';
                    buttonElement.onclick = () => sendImageToVideoTab(imgStr);
                    divElement.appendChild(imgElement);
                    divElement.appendChild(buttonElement);
                    recontextGeneratedImages.appendChild(divElement);
                });
            }
        } catch (error) {
            console.error('Error during Product Recontextualization:', error);
            alert('Failed to run Product Recontextualization. See console for details.');
        } finally {
            hideLoading();
        }
    });

    function sendImageToVideoTab(base64Image) {
        const byteCharacters = atob(base64Image);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {type: 'image/png'});
        const file = new File([blob], "generated-image.png", { type: "image/png" });

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageUpload.files = dataTransfer.files;

        const changeEvent = new Event('change');
        imageUpload.dispatchEvent(changeEvent);

        const imageVideoTab = new bootstrap.Tab(document.getElementById('image-video-tab'));
        imageVideoTab.show();
    }

    sendVtoToVideoTabBtn.addEventListener('click', () => {
        const base64Image = vtoGeneratedImage.src.split(',')[1];
        sendImageToVideoTab(base64Image);
    });

    runVeoEditBtn.addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('prompt', veoEditPrompt.value);
        formData.append('video_gcs', veoEditVideoGcs.value);
        formData.append('mask_gcs', veoEditMaskGcs.value);
        formData.append('mask_mime_type', veoEditMaskMimeType.value);
        formData.append('mask_mode', veoEditMaskMode.value);
        formData.append('aspect_ratio', veoEditAspectRatio.value);
        formData.append('duration', veoEditDuration.value);
        formData.append('enhance_prompt', veoEditEnhancePrompt.checked);

        if (veoEditVideoFile.files[0]) {
            formData.append('video_file', veoEditVideoFile.files[0]);
        }
        if (veoEditMaskFile.files[0]) {
            formData.append('mask_file', veoEditMaskFile.files[0]);
        }

        if (!veoEditVideoGcs.value && !veoEditVideoFile.files[0]) {
            alert('Please provide a video GCS URI or upload a video file.');
            return;
        }
        if (!veoEditMaskGcs.value && !veoEditMaskFile.files[0]) {
            alert('Please provide a mask GCS URI or upload a mask file.');
            return;
        }

        showLoading();
        try {
            const response = await fetch('/veo-edit', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else if (data.operation_id) {
                veoEditStatusContainer.innerHTML = ''; // Clear previous statuses
                displayVideoStatuses([data.operation_id], veoEditStatusContainer);
            }
        } catch (error) {
            console.error('Error during VEO Edit:', error);
            alert('Failed to run VEO Edit. See console for details.');
        } finally {
            hideLoading();
        }
    });

    runImagenEditBtn.addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('prompt', imagenEditPrompt.value);
        formData.append('edit_mode', imagenEditMode.value);
        formData.append('mask_mode', imagenMaskMode.value);

        if (imagenEditOriginalImage.files[0]) {
            formData.append('original_image', imagenEditOriginalImage.files[0]);
        } else {
            alert('Please upload an original image.');
            return;
        }

        if (imagenEditMaskImage.files[0]) {
            formData.append('mask_image', imagenEditMaskImage.files[0]);
        }

        showLoading();
        try {
            const response = await fetch('/imagen-edit', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                imagenEditOriginalPreview.src = data.original_image_url;
                imagenEditEditedPreview.src = data.edited_image_url;
            }
        } catch (error) {
            console.error('Error during Imagen Edit:', error);
            alert('Failed to run Imagen Edit. See console for details.');
        } finally {
            hideLoading();
        }
    });

    runVeoAdvancedEditBtn.addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('prompt', veoAdvancedPrompt.value);
        formData.append('camera_control', veoAdvancedCameraControl.value);
        formData.append('image_gcs', veoAdvancedImageGcs.value);
        formData.append('video_gcs', veoAdvancedVideoGcs.value);
        formData.append('last_frame_gcs', veoAdvancedLastFrameGcs.value);
        formData.append('aspect_ratio', veoAdvancedAspectRatio.value);
        formData.append('duration', veoAdvancedDuration.value);
        formData.append('enhance_prompt', veoAdvancedEnhancePrompt.checked);

        if (veoAdvancedImageFile.files[0]) {
            formData.append('image_file', veoAdvancedImageFile.files[0]);
        }
        if (veoAdvancedVideoFile.files[0]) {
            formData.append('video_file', veoAdvancedVideoFile.files[0]);
        }
        if (veoAdvancedLastFrameFile.files[0]) {
            formData.append('last_frame_file', veoAdvancedLastFrameFile.files[0]);
        }

        showLoading();
        try {
            const response = await fetch('/veo-advanced-edit', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else if (data.operation_id) {
                veoAdvancedEditStatusContainer.innerHTML = ''; // Clear previous statuses
                displayVideoStatuses([data.operation_id], veoAdvancedEditStatusContainer);
            }
        } catch (error) {
            console.error('Error during VEO Advanced Edit:', error);
            alert('Failed to run VEO Advanced Edit. See console for details.');
        } finally {
            hideLoading();
        }
    });
});
