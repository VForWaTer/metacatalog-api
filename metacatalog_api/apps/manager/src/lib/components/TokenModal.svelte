<script lang="ts">
    import { getBackendUrlFromStore } from '$lib/stores/settingsStore';
    import {
        apiKey,
        apiKeyStatus,
        validateApiKey,
        storeAdminToken,
        hasStoredToken
    } from '$lib/stores/apiKeyStore';

    let { isOpen, onClose } = $props<{ isOpen: boolean; onClose: () => void }>();

    let inputValue = $state('');
    let error = $state<string | null>(null);

    $effect(() => {
        if (isOpen) {
            inputValue = '';
            error = null;
            apiKeyStatus.set('unknown');
            if (hasStoredToken()) {
                inputValue = localStorage.getItem('metacatalog_admin_token') ?? '';
            }
        }
    });

    async function handleValidate() {
        const key = inputValue.trim();
        if (!key) {
            error = 'Enter a token to validate.';
            return;
        }
        error = null;
        apiKeyStatus.set('checking');
        const backendUrl = getBackendUrlFromStore();
        const valid = await validateApiKey(key, backendUrl);
        apiKeyStatus.set(valid ? 'valid' : 'invalid');
        if (!valid) {
            error = 'Token is invalid.';
        }
    }

    async function handleSave() {
        const key = inputValue.trim();
        if (!key) {
            error = 'Enter a token to save.';
            return;
        }
        error = null;
        apiKeyStatus.set('checking');
        const backendUrl = getBackendUrlFromStore();
        const valid = await validateApiKey(key, backendUrl);
        if (!valid) {
            apiKeyStatus.set('invalid');
            error = 'Token is invalid. Save aborted.';
            return;
        }
        apiKeyStatus.set('valid');
        storeAdminToken(key);
        apiKey.set(key);
        onClose();
    }

    function handleBackdropClick(event: MouseEvent) {
        if (event.target === event.currentTarget) {
            onClose();
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            onClose();
        }
    }
</script>

{#if isOpen}
    <div
        class="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000] flex items-center justify-center"
        onclick={handleBackdropClick}
        onkeydown={handleKeydown}
        role="dialog"
        aria-modal="true"
        aria-labelledby="token-modal-title"
        tabindex="-1"
    >
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
            class="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 overflow-hidden"
            onclick={(e) => e.stopPropagation()}
            onkeydown={(e) => e.stopPropagation()}
        >
            <div class="flex justify-between items-center p-4 border-b border-gray-200">
                <h2 id="token-modal-title" class="text-lg font-semibold text-gray-900">
                    API key
                </h2>
                <button
                    type="button"
                    onclick={onClose}
                    class="text-gray-400 hover:text-gray-600 focus:outline-none"
                    aria-label="Close"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            <div class="p-4 space-y-4">
                {#if error}
                    <p class="text-sm text-red-600">{error}</p>
                {/if}
                <div>
                    <label for="token-input" class="block text-sm font-medium text-gray-700 mb-1">Token</label>
                    <input
                        id="token-input"
                        type="password"
                        bind:value={inputValue}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Enter API key"
                        autocomplete="off"
                    />
                </div>
                <div class="flex items-center gap-2 text-sm">
                    <span class="text-gray-600">Status:</span>
                    {#if $apiKeyStatus === 'valid'}
                        <span class="text-green-600">Valid</span>
                    {:else if $apiKeyStatus === 'invalid'}
                        <span class="text-red-600">Invalid</span>
                    {:else if $apiKeyStatus === 'checking'}
                        <span class="text-amber-600">Checking...</span>
                    {:else}
                        <span class="text-gray-500">Unknown</span>
                    {/if}
                </div>
                <div class="flex flex-wrap gap-2 pt-2">
                    <button
                        type="button"
                        onclick={handleValidate}
                        class="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm"
                    >
                        Validate
                    </button>
                    <button
                        type="button"
                        onclick={handleSave}
                        class="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                        Save
                    </button>
                    <button
                        type="button"
                        onclick={onClose}
                        class="px-3 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}
