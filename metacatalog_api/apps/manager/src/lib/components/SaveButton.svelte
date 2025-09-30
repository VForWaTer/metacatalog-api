<script lang="ts">
    import { isFormValid, submissionState, submissionError, cleanEntry, dirtySections } from '$lib/stores/metadataStore';
    import { buildApiUrl, devFetch } from '$lib/stores/settingsStore';
    import { apiKey, isLocalhost, getDefaultAdminKey } from '$lib/stores/apiKeyStore';
    import { goto } from '$app/navigation';
    import { appPath } from '$lib/utils';

    async function saveMetadata() {
        if (!$isFormValid) return;

        submissionState.set('submitting');
        submissionError.set('');

        try {
            const payload = $cleanEntry;
            
            // Get API key - use default admin key for localhost
            let currentApiKey = $apiKey;
            if (!currentApiKey && isLocalhost()) {
                currentApiKey = getDefaultAdminKey();
                apiKey.set(currentApiKey);
            }
            
            if (!currentApiKey) {
                throw new Error('No API key available. Please set an API key for authentication.');
            }
            
            const createUrl = buildApiUrl('/entries');
            console.log('🔍 Save URL:', createUrl, 'Environment:', typeof window !== 'undefined' ? 'browser' : 'server');
            const response = await devFetch(createUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-API-Key': currentApiKey
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Metadata saved successfully:', result);
            
            submissionState.set('success');
            
            // Clear dirty sections since we've saved
            dirtySections.set(new Set());
            
            // Redirect to the newly created entry's detail page
            if (result && result.id) {
                goto(appPath(`datasets/${result.id}`));
            }
            
        } catch (error) {
            console.error('Error saving metadata:', error);
            submissionError.set(error instanceof Error ? error.message : 'Unknown error occurred');
            submissionState.set('error');
        }
    }

    // Initialize API key for localhost
    $effect(() => {
        if (isLocalhost() && !$apiKey) {
            apiKey.set(getDefaultAdminKey());
        }
    });
</script>

<div class="mt-6 flex justify-end">
    <button
        type="button"
        onmousedown={saveMetadata}
        disabled={!$isFormValid || $submissionState === 'submitting'}
        class="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
    >
        {#if $submissionState === 'submitting'}
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Saving...</span>
        {:else}
            <span>Save Metadata Entry</span>
        {/if}
    </button>
</div>

<!-- Error Message -->
{#if $submissionState === 'error'}
    <div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
        <p class="text-sm text-red-600">Error: {$submissionError}</p>
    </div>
{/if}

<!-- Success Message -->
{#if $submissionState === 'success'}
    <div class="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
        <p class="text-sm text-green-600">✓ Metadata entry saved successfully!</p>
    </div>
{/if} 