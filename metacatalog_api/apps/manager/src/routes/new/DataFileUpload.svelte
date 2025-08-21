<script lang="ts">
    import { buildApiUrl, devFetch } from '$lib/stores/settingsStore';
    import { apiKey, isLocalhost, getDefaultAdminKey } from '$lib/stores/apiKeyStore';
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import type { DatasourceTypeBase, TemporalScaleBase, SpatialScaleBase } from '$lib/models';
    import TemporalScaleForm from './TemporalScaleForm.svelte';
    import SpatialScaleForm from './SpatialScaleForm.svelte';

    let dropzone: HTMLDivElement;
    let fileInput: HTMLInputElement;
    let isDragOver = $state(false);
    let isUploading = $state(false);
    let uploadResult = $state<any>(null);
    let uploadError = $state<string | null>(null);
    let showManualForm = $state(false);
    let manualPath = $state('');
    let previewData = $state<any>(null);
    let isGettingPreview = $state(false);
    
    // Datasource configuration fields
    let datasourceTypes = $state<DatasourceTypeBase[]>([]);
    let selectedType = $state<number | string>('');
    let encoding = $state('utf-8');
    let variableNamesInput = $state('');
    let argsInput = $state('{}');
    
    // Scale configuration
    let showTemporalScale = $state(false);
    let showSpatialScale = $state(false);

    // Component states:
    // 1. Initial: dropzone only
    // 2. File uploaded: dropzone + manual form (path disabled)
    // 3. Manual mode: manual form only (path enabled)

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
        isDragOver = true;
    }

    function handleDragLeave(event: DragEvent) {
        event.preventDefault();
        isDragOver = false;
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        isDragOver = false;
        
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            handleFileUpload(files[0]);
        }
    }

    function handleFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            handleFileUpload(target.files[0]);
        }
    }

    async function handleFileUpload(file: File) {
        isUploading = true;
        uploadError = null;
        uploadResult = null;

        try {
            // Get API key - use default admin key for localhost
            let currentApiKey = $apiKey;
            if (!currentApiKey && isLocalhost()) {
                currentApiKey = getDefaultAdminKey();
                apiKey.set(currentApiKey);
            }
            
            if (!currentApiKey) {
                throw new Error('No API key available. Please set an API key for authentication.');
            }

            const formData = new FormData();
            formData.append('file', file);

            const uploadUrl = buildApiUrl('/uploads');
            const response = await devFetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'X-API-Key': currentApiKey
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `Upload failed: ${response.status} ${response.statusText}`);
            }

            uploadResult = await response.json();
            
            // Create basic datasource from upload
            metadataActions.createDatasourceFromUpload(
                uploadResult.file_hash,
                uploadResult.filename,
                uploadResult.size
            );
            
            // Show manual form for additional configuration
            showManualForm = true;
            manualPath = uploadResult.file_hash; // Set path to file hash
            
        } catch (error) {
            console.error('Upload error:', error);
            uploadError = error instanceof Error ? error.message : 'Upload failed';
        } finally {
            isUploading = false;
        }
    }

    function enableManualMode() {
        showManualForm = true;
        uploadResult = null;
        manualPath = '';
        
        // Reset datasource configuration fields
        selectedType = '';
        encoding = 'utf-8';
        variableNamesInput = '';
        argsInput = '{}';
        
        // Create empty datasource for manual entry
        metadataActions.createDatasourceFromUpload('', '', 0);
    }

    function clearAll() {
        uploadResult = null;
        uploadError = null;
        showManualForm = false;
        manualPath = '';
        
        // Reset datasource configuration fields
        selectedType = '';
        encoding = 'utf-8';
        variableNamesInput = '';
        argsInput = '{}';
        
        // Reset scale configuration
        showTemporalScale = false;
        showSpatialScale = false;
        
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Clear datasource from store
        metadataActions.clearDatasource();
    }

    function handleManualPathChange() {
        if (showManualForm && manualPath) {
            metadataActions.updateDatasourcePath(manualPath);
        }
    }

    // Initialize API key for localhost
    $effect(() => {
        if (isLocalhost() && !$apiKey) {
            apiKey.set(getDefaultAdminKey());
        }
    });

    // Helper function to format file size
    function formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Load datasource types on component mount
    async function loadDatasourceTypes() {
        try {
            const response = await devFetch(buildApiUrl('/datasource-types'));
            if (response.ok) {
                datasourceTypes = await response.json();
            }
        } catch (error) {
            console.error('Error loading datasource types:', error);
        }
    }

    // Handler functions for datasource configuration
    function handleTypeChange() {
        if (selectedType) {
            metadataActions.updateDatasourceType(selectedType);
        }
    }

    function handleEncodingChange() {
        metadataActions.updateDatasourceEncoding(encoding);
    }

    function handleVariableNamesChange() {
        const names = variableNamesInput.split(',').map(name => name.trim()).filter(name => name.length > 0);
        metadataActions.updateDatasourceVariableNames(names);
    }

    function handleArgsChange() {
        try {
            const args = JSON.parse(argsInput);
            metadataActions.updateDatasourceArgs(args);
        } catch (error) {
            // Invalid JSON, don't update
            console.warn('Invalid JSON in args field:', error);
        }
    }

    // Load datasource types when component mounts
    $effect(() => {
        loadDatasourceTypes();
    });

    // Scale handler functions
    function addTemporalScale() {
        showTemporalScale = true;
        // Create a default temporal scale
        const temporalScale: TemporalScaleBase = {
            resolution: 'P1D', // 1 day in ISO 8601
            observation_start: new Date().toISOString(),
            observation_end: new Date().toISOString(),
            support: 1.0,
            dimension_names: ['time']
        };
        metadataActions.updateDatasourceTemporalScale(temporalScale);
    }

    function addSpatialScale() {
        showSpatialScale = true;
        // Create a default spatial scale with a simple extent
        const spatialScale: SpatialScaleBase = {
            resolution: 1000, // 1km in meters
            extent: {
                type: 'Polygon',
                coordinates: [[
                    [-180, -90], // bottom-left
                    [180, -90],  // bottom-right
                    [180, 90],   // top-right
                    [-180, 90],  // top-left
                    [-180, -90]  // close the polygon
                ]]
            },
            support: 1.0,
            dimension_names: ['latitude', 'longitude']
        };
        metadataActions.updateDatasourceSpatialScale(spatialScale);
    }

    // Listen for scale removal and hide forms
    $effect(() => {
        const entry = $metadataEntry;
        if (entry.datasource) {
            if (!entry.datasource.temporal_scale && showTemporalScale) {
                showTemporalScale = false;
            }
            if (!entry.datasource.spatial_scale && showSpatialScale) {
                showSpatialScale = false;
            }
        }
    });
</script>

<div class="space-y-4">
    <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900">Data/File</h3>
        {#if uploadResult || showManualForm}
            <button
                type="button"
                onmousedown={clearAll}
                class="text-sm text-red-600 hover:text-red-800"
            >
                Clear
            </button>
        {/if}
    </div>

    <!-- Dropzone (hidden in manual mode) -->
    {#if !showManualForm}
        <div
            bind:this={dropzone}
            class="relative border-2 border-dashed rounded-lg p-6 text-center transition-colors"
            class:border-blue-400={isDragOver}
            class:border-gray-300={!isDragOver}
            class:bg-blue-50={isDragOver}
            class:bg-gray-50={!isDragOver}
            ondragover={handleDragOver}
            ondragleave={handleDragLeave}
            ondrop={handleDrop}
            role="button"
            tabindex="0"
        >
            <input
                bind:this={fileInput}
                type="file"
                class="hidden"
                onchange={handleFileSelect}
                accept="*/*"
            />

            {#if isUploading}
                <div class="space-y-2">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                    <p class="text-sm text-gray-600">Uploading file...</p>
                </div>
            {:else if uploadResult}
                <div class="space-y-2">
                    <div class="text-green-600">
                        <svg class="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-900">File uploaded successfully!</p>
                    <p class="text-xs text-gray-500">{uploadResult.filename}</p>
                </div>
            {:else}
                <div class="space-y-2">
                    <svg class="h-8 w-8 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                    <p class="text-sm text-gray-600">
                        <button
                            type="button"
                            onmousedown={() => fileInput?.click()}
                            class="text-blue-600 hover:text-blue-800 font-medium"
                        >
                            Click to upload
                        </button>
                        <span class="text-gray-500"> or drag and drop</span>
                    </p>
                    <p class="text-xs text-gray-500">Any file type supported</p>
                </div>
            {/if}
        </div>

        <!-- Manual editing link (only visible when no file uploaded) -->
        {#if !uploadResult}
            <div class="text-center">
                <button
                    type="button"
                    onmousedown={enableManualMode}
                    class="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                    Or specify data source manually
                </button>
            </div>
        {/if}
    {/if}

    <!-- Manual Form (shown when file uploaded or manual mode enabled) -->
    {#if showManualForm}
        <div class="space-y-4 p-4 bg-gray-50 rounded-md">
            <h4 class="text-sm font-medium text-gray-700">Data Source Configuration</h4>
            
            <div class="space-y-2">
                <label for="datasource-path" class="block text-sm font-medium text-gray-700">
                    Data Source Path
                </label>
                <input
                    id="datasource-path"
                    type="text"
                    bind:value={manualPath}
                    oninput={handleManualPathChange}
                    disabled={!!uploadResult}
                    placeholder={uploadResult ? "File path (auto-filled)" : "Enter file path or URL"}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                />
                {#if uploadResult}
                    <p class="text-xs text-gray-500">Path is automatically set from uploaded file</p>
                {:else}
                    <p class="text-xs text-gray-500">Enter the path to your data file or URL</p>
                {/if}
            </div>

            <!-- Datasource Type -->
            <div class="space-y-2">
                <label for="datasource-type" class="block text-sm font-medium text-gray-700">
                    Data Source Type
                </label>
                <select
                    id="datasource-type"
                    bind:value={selectedType}
                    onchange={handleTypeChange}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="">Select a type...</option>
                    {#each datasourceTypes as type}
                        <option value={type.id}>{type.title}</option>
                    {/each}
                </select>
            </div>

            <!-- Encoding -->
            <div class="space-y-2">
                <label for="datasource-encoding" class="block text-sm font-medium text-gray-700">
                    Encoding
                </label>
                <input
                    id="datasource-encoding"
                    type="text"
                    bind:value={encoding}
                    oninput={handleEncodingChange}
                    placeholder="utf-8"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            </div>

            <!-- Variable Names -->
            <div class="space-y-2">
                <label for="datasource-variable-names" class="block text-sm font-medium text-gray-700">
                    Variable Names (comma-separated)
                </label>
                <input
                    id="datasource-variable-names"
                    type="text"
                    bind:value={variableNamesInput}
                    oninput={handleVariableNamesChange}
                    placeholder="var1, var2, var3"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            </div>

            <!-- Additional Arguments (JSON) -->
            <div class="space-y-2">
                <label for="datasource-args" class="block text-sm font-medium text-gray-700">
                    Additional Arguments (JSON)
                </label>
                <textarea
                    id="datasource-args"
                    bind:value={argsInput}
                    oninput={handleArgsChange}
                    placeholder="Enter JSON object"
                    rows="3"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                ></textarea>
                <p class="text-xs text-gray-500">Optional JSON object for additional configuration</p>
            </div>

            <!-- Scale Configuration Buttons -->
            <div class="space-y-3 pt-4 border-t border-gray-200">
                <h5 class="text-sm font-medium text-gray-700">Scale Configuration (Optional)</h5>
                <div class="flex space-x-3">
                    <button
                        type="button"
                        onmousedown={addTemporalScale}
                        class="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        + Add Temporal Scale
                    </button>
                    <button
                        type="button"
                        onmousedown={addSpatialScale}
                        class="px-3 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                        + Add Spatial Scale
                    </button>
                </div>
            </div>

            <!-- Scale Forms -->
            {#if showTemporalScale}
                <TemporalScaleForm />
            {/if}

            {#if showSpatialScale}
                <SpatialScaleForm />
            {/if}
        </div>
    {/if}

    <!-- Upload Result Display -->
    {#if uploadResult}
        <div class="space-y-3">
            <h4 class="text-sm font-medium text-gray-700">Uploaded File:</h4>
            <div class="bg-green-50 border border-green-200 rounded-md p-4">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2">
                            <svg class="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            <span class="text-sm font-medium text-green-900">{uploadResult.filename}</span>
                        </div>
                        <div class="mt-2 space-y-1 text-xs text-green-700">
                            <div class="flex items-center space-x-2">
                                <span class="font-medium">File Hash:</span>
                                <code class="bg-green-100 px-1 py-0.5 rounded text-green-800 font-mono">{uploadResult.file_hash}</code>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="font-medium">Size:</span>
                                <span>{formatFileSize(uploadResult.size)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    {/if}

    <!-- Error Display -->
    {#if uploadError}
        <div class="bg-red-50 border border-red-200 rounded-md p-3">
            <p class="text-sm text-red-800">Error: {uploadError}</p>
        </div>
    {/if}
</div> 