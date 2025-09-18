<script lang="ts">
    import Accordion from "./Accordion.svelte";
    import AuthorForm from "./AuthorForm.svelte";
    import LocationForm from "./LocationForm.svelte";
    import KeywordsForm from "./KeywordsForm.svelte";
    import DetailForm from "./DetailForm.svelte";
    import DataFileUpload from "./DataFileUpload.svelte";
    import SaveButton from "$lib/components/SaveButton.svelte";
    import type { PageData } from './$types';
    import { metadataEntry, dirtySections, isFormValid, metadataActions } from '$lib/stores/metadataStore';
    import { settings } from '$lib/stores/settingsStore';
    import { apiKey, apiKeyStatus, validateApiKey, isLocalhost } from '$lib/stores/apiKeyStore';
    import { appPath } from '$lib/utils';
    
    let { data } = $props<{ data: PageData }>();

    function debugStore() {
        console.log('=== METADATA STORE DEBUG ===');
        console.log('Current Entry:', $metadataEntry);
        console.log('Dirty Sections:', Array.from($dirtySections));
        console.log('Form Valid:', $isFormValid);
        console.log('===========================');
    }


</script>

<div class="w-9/10 mx-auto bg-white rounded-lg p-4">
    <!-- Back Button -->
    <div class="mb-6">
        <a href={appPath('')} class="inline-flex items-center text-blue-600 hover:text-blue-800">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Back to Home
        </a>
    </div>

    <h1 class="text-2xl font-bold">
        Create new Metadata Entry
    </h1>

    <div class="mt-4">
        <Accordion title="Core Metadata" open>
            <div class="space-y-6">
                <!-- Mandatory fields from MetadataForm -->
                <div>
                    <label for="title" class="block text-sm font-medium text-gray-700 mb-2">
                        Title <span class="text-red-500">*</span>
                    </label>
                    <input
                        type="text"
                        id="title"
                        name="title"
                        value={$metadataEntry.title}
                        oninput={(e) => metadataActions.updateBasicInfo({ title: (e.target as HTMLInputElement).value })}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Enter the title of your dataset"
                        required
                    />
                </div>

                <div>
                    <label for="abstract" class="block text-sm font-medium text-gray-700 mb-2">
                        Abstract <span class="text-red-500">*</span>
                    </label>
                    <textarea
                        id="abstract"
                        name="abstract"
                        value={$metadataEntry.abstract}
                        oninput={(e) => metadataActions.updateBasicInfo({ abstract: (e.target as HTMLTextAreaElement).value })}
                        rows="4"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Provide a detailed description of your dataset"
                        required
                    ></textarea>
                </div>

                <div>
                    <label for="license" class="block text-sm font-medium text-gray-700 mb-2">
                        License <span class="text-red-500">*</span>
                    </label>
                    <select
                        id="license"
                        name="license"
                        value={$metadataEntry.license}
                        onchange={(e) => metadataActions.updateLicense(parseInt((e.target as HTMLSelectElement).value))}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        required
                    >
                        <option value="">Select a license</option>
                        {#each data.licenses as license}
                            <option value={license.id}>{license.short_title} - {license.title}</option>
                        {/each}
                    </select>
                </div>

                <div>
                    <label for="variable" class="block text-sm font-medium text-gray-700 mb-2">
                        Variable <span class="text-red-500">*</span>
                    </label>
                    <select
                        id="variable"
                        name="variable"
                        value={$metadataEntry.variable}
                        onchange={(e) => metadataActions.updateVariable(parseInt((e.target as HTMLSelectElement).value))}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        required
                    >
                        <option value="">Select a variable</option>
                        {#each data.variables as variable}
                            <option value={variable.id}>{variable.name} ({variable.symbol})</option>
                        {/each}
                    </select>
                </div>

                <!-- Author section -->
                <AuthorForm authors={data.authors} />
            </div>
        </Accordion>

        <Accordion title="Optional Metadata">
            <div class="space-y-6">
                <KeywordsForm />
                <LocationForm />
                
                <hr class="border-gray-300">
                
                <!-- Optional fields from MetadataForm -->
                <div>
                    <label for="external_id" class="block text-sm font-medium text-gray-700 mb-2">
                        External ID
                    </label>
                    <input
                        type="text"
                        id="external_id"
                        name="external_id"
                        value={$metadataEntry.external_id || ''}
                        oninput={(e) => metadataActions.updateBasicInfo({ external_id: (e.target as HTMLInputElement).value })}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="External identifier (optional)"
                    />
                </div>

                <div>
                    <label for="comment" class="block text-sm font-medium text-gray-700 mb-2">
                        Comment
                    </label>
                    <textarea
                        id="comment"
                        name="comment"
                        value={$metadataEntry.comment || ''}
                        oninput={(e) => metadataActions.updateBasicInfo({ comment: (e.target as HTMLTextAreaElement).value })}
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Additional comments or notes"
                    ></textarea>
                </div>

                <div class="flex items-center">
                    <input
                        type="checkbox"
                        id="embargo"
                        name="embargo"
                        checked={$metadataEntry.embargo}
                        onchange={(e) => metadataActions.updateBasicInfo({ embargo: (e.target as HTMLInputElement).checked })}
                        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label for="embargo" class="ml-2 text-sm text-gray-700">
                        Apply embargo (restrict access for 2 years)
                    </label>
                </div>

                <DetailForm />
            </div>
        </Accordion>

        <Accordion title="Data/File">
            <DataFileUpload />
        </Accordion>

        <SaveButton />
        
        <!-- API Key Management (Dev Only) -->
        {#if $settings.isDev}
            <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <h4 class="text-sm font-medium text-blue-800 mb-2">API Key Management (Development)</h4>
                <div class="space-y-2">
                    <div class="flex items-center space-x-2">
                        <input
                            type="text"
                            bind:value={$apiKey}
                            placeholder="Enter API key"
                            class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button
                            type="button"
                            onmousedown={() => validateApiKey($apiKey, 'http://localhost:8001').then(valid => apiKeyStatus.set(valid ? 'valid' : 'invalid'))}
                            class="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-sm"
                        >
                            Validate
                        </button>
                    </div>
                    <div class="flex items-center space-x-4 text-xs">
                        <span class="text-gray-600">Status: 
                            {#if $apiKeyStatus === 'valid'}
                                <span class="text-green-600">✓ Valid</span>
                            {:else if $apiKeyStatus === 'invalid'}
                                <span class="text-red-600">✗ Invalid</span>
                            {:else if $apiKeyStatus === 'checking'}
                                <span class="text-yellow-600">Checking...</span>
                            {:else}
                                <span class="text-gray-500">Unknown</span>
                            {/if}
                        </span>
                        {#if isLocalhost()}
                            <span class="text-blue-600">Running on localhost - using default admin key</span>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
        
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