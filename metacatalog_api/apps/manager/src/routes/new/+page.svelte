<script lang="ts">
    import Accordion from "./Accordion.svelte";
    import MetadataForm from "./MetadataForm.svelte";
    import AuthorForm from "./AuthorForm.svelte";
    import LocationForm from "./LocationForm.svelte";
    import KeywordsForm from "./KeywordsForm.svelte";
    import DetailForm from "./DetailForm.svelte";
    import SaveButton from "$lib/components/SaveButton.svelte";
    import type { PageData } from './$types';
    import { metadataEntry, dirtySections, isFormValid } from '$lib/stores/metadataStore';
    import { settings } from '$lib/stores/settingsStore';
    import { apiKey, apiKeyStatus, validateApiKey, isLocalhost, getDefaultAdminKey } from '$lib/stores/apiKeyStore';
    
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

        <Accordion title="Optional Metadata">
            <div class="space-y-6">
                <LocationForm />
                <KeywordsForm />
            </div>
        </Accordion>

        <Accordion title="Details">
            <DetailForm />
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