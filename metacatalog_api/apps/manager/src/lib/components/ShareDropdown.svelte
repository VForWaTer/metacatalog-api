<script lang="ts">
    import { onMount } from 'svelte';
    import { buildApiUrl } from '$lib/stores/settingsStore';
    import ShareModal from './ShareModal.svelte';

    // Props
    let { entryId, buttonClass = "px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-b border-gray-200 flex items-center gap-1" } = $props<{
        entryId: number;
        buttonClass?: string;
    }>();

    let shareProviders = $state<Array<{provider: string, display_name: string, form_endpoint: string, submit_endpoint: string}>>([]);
    let showModal = $state(false);
    let selectedProvider = $state<{provider: string, display_name: string, form_endpoint: string, submit_endpoint: string} | null>(null);

    // Fetch available share providers
    async function fetchShareProviders() {
        try {
            const response = await fetch(buildApiUrl('/share-providers'));
            if (response.ok) {
                const data = await response.json();
                shareProviders = data.share_providers || [];
            }
        } catch (error) {
            console.error('Failed to fetch share providers:', error);
        }
    }

    // Handle dropdown functionality
    onMount(() => {
        // Fetch share providers on component mount
        fetchShareProviders();

        function handleClickOutside(event: MouseEvent) {
            const target = event.target as Element;
            if (!target.closest('.relative.group')) {
                // Close all dropdowns
                document.querySelectorAll('.share-dropdown-menu').forEach(dropdown => {
                    dropdown.classList.add('hidden');
                });
            }
        }

        document.addEventListener('click', handleClickOutside);
        
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    });

    function toggleDropdown(event: MouseEvent) {
        event.preventDefault();
        event.stopPropagation();
        
        // Close all other dropdowns first
        document.querySelectorAll('.share-dropdown-menu').forEach(dropdown => {
            if (dropdown !== (event.target as Element)?.closest('.relative')?.querySelector('.share-dropdown-menu')) {
                dropdown.classList.add('hidden');
            }
        });
        
        // Toggle current dropdown
        const dropdown = (event.target as Element)?.closest('.relative')?.querySelector('.share-dropdown-menu');
        dropdown?.classList.toggle('hidden');
    }

    function openShareModal(provider: {provider: string, display_name: string, form_endpoint: string, submit_endpoint: string}) {
        selectedProvider = provider;
        showModal = true;
        // Close all dropdowns
        document.querySelectorAll('.share-dropdown-menu').forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
    }

    function closeModal() {
        showModal = false;
        selectedProvider = null;
    }
</script>

<div class="relative group">
    <button 
        class={buttonClass}
        onclick={toggleDropdown}
    >
        Share
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
    </button>
    <div class="share-dropdown-menu hidden absolute right-0 top-full bg-white border border-gray-200 rounded-md shadow-lg z-[1000] min-w-[160px]">
        {#each shareProviders as provider}
            <button
                onclick={() => openShareModal(provider)}
                class="w-full text-left block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
                {provider.display_name}
            </button>
        {/each}
        {#if shareProviders.length === 0}
            <div class="px-3 py-2 text-sm text-gray-500">
                Loading...
            </div>
        {/if}
    </div>
</div>

{#if showModal && selectedProvider}
    <ShareModal 
        entryId={entryId}
        provider={selectedProvider}
        isOpen={showModal}
        onClose={closeModal}
    />
{/if}

