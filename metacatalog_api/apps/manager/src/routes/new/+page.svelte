<script lang="ts">
    import Accordion from "./Accordion.svelte";
    import MetadataForm from "./MetadataForm.svelte";
    import AuthorForm from "./AuthorForm.svelte";
    import type { PageData } from './$types';
    import { metadataEntry, dirtySections, isFormValid, metadataActions } from '$lib/stores/metadataStore';
    import { settings, devLog } from '$lib/stores/settingsStore';
    import { MetadataService } from '$lib/services/metadataService';
    import type { MetadataEntryCreate, AuthorCreate } from '$lib/models';
    
    let { data } = $props<{ data: PageData }>();

    let isSaving = $state(false);
    let saveError = $state<string | null>(null);
    let saveSuccess = $state(false);

    function debugStore() {
        console.log('=== METADATA STORE DEBUG ===');
        console.log('Current Entry:', $metadataEntry);
        console.log('Dirty Sections:', Array.from($dirtySections));
        console.log('Form Valid:', $isFormValid);
        console.log('===========================');
    }

    async function saveMetadata() {
        if (!$isFormValid) {
            saveError = 'Please fill in all required fields before saving.';
            return;
        }

        isSaving = true;
        saveError = null;
        saveSuccess = false;

        try {
            // Convert the store data to the API format
            const entryData: MetadataEntryCreate = {
                title: $metadataEntry.title,
                abstract: $metadataEntry.abstract,
                external_id: $metadataEntry.external_id,
                comment: $metadataEntry.comment,
                embargo: $metadataEntry.embargo,
                variable: $metadataEntry.variable!,
                license: $metadataEntry.license!,
                author: $metadataEntry.author as AuthorCreate,
                coAuthors: $metadataEntry.coAuthors as AuthorCreate[]
            };

            devLog.info('Saving metadata entry:', entryData);
            
            const result = await MetadataService.createEntry(entryData);
            
            devLog.info('Metadata entry saved successfully:', result);
            saveSuccess = true;
            
            // Clear dirty flags
            metadataActions.clearDirty();
            
            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                saveSuccess = false;
            }, 3000);
            
        } catch (error) {
            saveError = error instanceof Error ? error.message : 'Failed to save metadata entry';
            devLog.error('Save error:', error);
        } finally {
            isSaving = false;
        }
    }
</script>

<div class="w-9/10 mx-auto bg-white rounded-lg p-4">
    <h1 class="text-2xl font-bold">
        Create new Metadata Entry
    </h1>

    <div class="mt-4">
        <Accordion title="Main Metadata" open>
            <MetadataForm licenses={data.licenses} variables={data.variables} />
        </Accordion>

        <Accordion title="Authors">
            <AuthorForm authors={data.authors} />
        </Accordion>

        <!-- Save Section -->
        <div class="mt-8 border-t pt-6">
            <!-- Status Messages -->
            {#if saveSuccess}
                <div class="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-green-800">
                                Metadata entry saved successfully!
                            </p>
                        </div>
                    </div>
                </div>
            {/if}

            {#if saveError}
                <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-red-800">
                                Error saving metadata entry
                            </p>
                            <p class="text-sm text-red-700 mt-1">
                                {saveError}
                            </p>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Form Status and Save Button -->
            <div class="flex items-center justify-between">
                <div class="text-sm text-gray-600">
                    <div class="flex items-center space-x-4">
                        <div>
                            {#if $dirtySections.size > 0}
                                <span class="text-orange-600">●</span> Unsaved changes
                            {:else}
                                <span class="text-green-600">●</span> All changes saved
                            {/if}
                        </div>
                        <div>
                            Form valid: {#if $isFormValid}<span class="text-green-600">✓</span>{:else}<span class="text-red-600">✗</span>{/if}
                        </div>
                    </div>
                </div>
                
                <button
                    type="button"
                    onmousedown={saveMetadata}
                    disabled={!$isFormValid || isSaving}
                    class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                    {#if isSaving}
                        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Saving...</span>
                    {:else}
                        <span>Save Metadata Entry</span>
                    {/if}
                </button>
            </div>
        </div>
        
        {#if $settings.isDev}
            <div class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <button
                    type="button"
                    onmousedown={debugStore}
                    class="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                >
                    🐛 Debug Store State
                </button>
                <p class="mt-2 text-sm text-yellow-700">
                    Click to log current metadata store state to console
                </p>
            </div>
        {/if}
        
    </div>
</div>