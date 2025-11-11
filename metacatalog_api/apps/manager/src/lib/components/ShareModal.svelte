<script lang="ts">
    import { onMount } from 'svelte';
    import { buildApiUrl } from '$lib/stores/settingsStore';

    // Props
    let { entryId, provider, isOpen, onClose } = $props<{
        entryId: number;
        provider: {provider: string, display_name: string, form_endpoint: string, submit_endpoint: string};
        isOpen: boolean;
        onClose: () => void;
    }>();

    let formSchema = $state<any>(null);
    let formData = $state<Record<string, any>>({});
    let isLoading = $state(false);
    let isSubmitting = $state(false);
    let error = $state<string | null>(null);
    let success = $state<string | null>(null);

    // Fetch form schema when modal opens
    onMount(() => {
        if (isOpen) {
            fetchFormSchema();
        }
    });

    // Watch for isOpen changes
    $effect(() => {
        if (isOpen) {
            fetchFormSchema();
        } else {
            // Reset state when modal closes
            formSchema = null;
            formData = {};
            error = null;
            success = null;
        }
    });

    async function fetchFormSchema() {
        isLoading = true;
        error = null;
        try {
            const response = await fetch(buildApiUrl(`${provider.form_endpoint}?entry_id=${entryId}`));
            if (response.ok) {
                const schema = await response.json();
                formSchema = schema;
                
                // Initialize form data with defaults
                if (schema.fields) {
                    const initialData: Record<string, any> = {};
                    for (const field of schema.fields) {
                        if (field.default !== undefined) {
                            initialData[field.name] = field.default;
                        } else if (field.type === 'checkbox') {
                            initialData[field.name] = false;
                        } else if (field.type === 'select' && field.multiple) {
                            initialData[field.name] = [];
                        } else {
                            initialData[field.name] = '';
                        }
                    }
                    formData = initialData;
                }
            } else {
                error = `Failed to load form: ${response.statusText}`;
            }
        } catch (err) {
            error = `Error loading form: ${err instanceof Error ? err.message : 'Unknown error'}`;
        } finally {
            isLoading = false;
        }
    }

    function handleFieldChange(fieldName: string, value: any) {
        formData[fieldName] = value;
    }

    async function handleSubmit() {
        isSubmitting = true;
        error = null;
        success = null;

        try {
            const response = await fetch(
                buildApiUrl(`${provider.submit_endpoint}?entry_id=${entryId}`),
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                }
            );

            if (response.ok) {
                // Check if response is a file download (download provider)
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/zip')) {
                    // Handle file download
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const contentDisposition = response.headers.get('content-disposition');
                    let filename = `entry_${entryId}_package.zip`;
                    if (contentDisposition) {
                        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                        if (filenameMatch) {
                            filename = filenameMatch[1];
                        }
                    }
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    success = 'Package downloaded successfully!';
                    // Close modal after a short delay
                    setTimeout(() => {
                        onClose();
                    }, 1500);
                } else {
                    // Handle JSON response (for future providers like Zenodo)
                    const result = await response.json();
                    success = result.message || 'Submitted successfully!';
                }
            } else {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                error = errorData.detail || `Error: ${response.statusText}`;
            }
        } catch (err) {
            error = `Error submitting form: ${err instanceof Error ? err.message : 'Unknown error'}`;
        } finally {
            isSubmitting = false;
        }
    }

    function handleBackdropClick(event: MouseEvent) {
        if (event.target === event.currentTarget) {
            onClose();
        }
    }
</script>

{#if isOpen}
    <!-- Modal Backdrop -->
    <div 
        class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
        onclick={handleBackdropClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
    >
        <!-- Modal Content -->
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <!-- Modal Header -->
            <div class="flex justify-between items-center p-6 border-b border-gray-200">
                <h2 id="modal-title" class="text-xl font-semibold text-gray-900">
                    {provider.display_name}
                </h2>
                <button
                    onclick={onClose}
                    class="text-gray-400 hover:text-gray-600 focus:outline-none"
                    aria-label="Close modal"
                >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6">
                {#if isLoading}
                    <div class="text-center py-8">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p class="text-gray-600">Loading form...</p>
                    </div>
                {:else if error && !formSchema}
                    <div class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                        <p class="text-red-800 text-sm">{error}</p>
                    </div>
                {:else if formSchema}
                    <!-- Error Message -->
                    {#if error}
                        <div class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                            <p class="text-red-800 text-sm">{error}</p>
                        </div>
                    {/if}

                    <!-- Success Message -->
                    {#if success}
                        <div class="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                            <p class="text-green-800 text-sm">{success}</p>
                        </div>
                    {/if}

                    <!-- Form Fields -->
                    <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
                        <div class="space-y-4">
                            {#each formSchema.fields as field}
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        {field.label}
                                        {#if field.required}
                                            <span class="text-red-500">*</span>
                                        {/if}
                                    </label>

                                    {#if field.type === 'select' && field.multiple}
                                        <!-- Multiple Select -->
                                        <select
                                            multiple
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            onchange={(e) => {
                                                const selected = Array.from((e.target as HTMLSelectElement).selectedOptions, option => option.value);
                                                handleFieldChange(field.name, selected);
                                            }}
                                            required={field.required}
                                        >
                                            {#each field.options as option}
                                                <option value={option.value} selected={formData[field.name]?.includes(option.value)}>
                                                    {option.label}
                                                </option>
                                            {/each}
                                        </select>
                                    {:else if field.type === 'select'}
                                        <!-- Single Select -->
                                        <select
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            value={formData[field.name] || ''}
                                            onchange={(e) => handleFieldChange(field.name, (e.target as HTMLSelectElement).value)}
                                            required={field.required}
                                        >
                                            {#each field.options as option}
                                                <option value={option.value}>{option.label}</option>
                                            {/each}
                                        </select>
                                    {:else if field.type === 'checkbox'}
                                        <!-- Checkbox -->
                                        <div class="flex items-center">
                                            <input
                                                type="checkbox"
                                                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                                checked={formData[field.name] || false}
                                                onchange={(e) => handleFieldChange(field.name, (e.target as HTMLInputElement).checked)}
                                            />
                                            <span class="ml-2 text-sm text-gray-700">{field.label}</span>
                                        </div>
                                    {:else if field.type === 'password'}
                                        <!-- Password Input -->
                                        <input
                                            type="password"
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            value={formData[field.name] || ''}
                                            oninput={(e) => handleFieldChange(field.name, (e.target as HTMLInputElement).value)}
                                            required={field.required}
                                        />
                                    {:else if field.type === 'textarea'}
                                        <!-- Textarea -->
                                        <textarea
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            rows="4"
                                            value={formData[field.name] || ''}
                                            oninput={(e) => handleFieldChange(field.name, (e.target as HTMLTextAreaElement).value)}
                                            required={field.required}
                                        ></textarea>
                                    {:else}
                                        <!-- Text Input -->
                                        <input
                                            type="text"
                                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            value={formData[field.name] || ''}
                                            oninput={(e) => handleFieldChange(field.name, (e.target as HTMLInputElement).value)}
                                            required={field.required}
                                        />
                                    {/if}

                                    {#if field.help}
                                        <p class="mt-1 text-xs text-gray-500">{field.help}</p>
                                    {/if}
                                </div>
                            {/each}
                        </div>

                        <!-- Form Actions -->
                        <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                            <button
                                type="button"
                                onclick={onClose}
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                disabled={isSubmitting}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                disabled={isSubmitting}
                            >
                                {#if isSubmitting}
                                    <span class="flex items-center">
                                        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Processing...
                                    </span>
                                {:else}
                                    Submit
                                {/if}
                            </button>
                        </div>
                    </form>
                {/if}
            </div>
        </div>
    </div>
{/if}

