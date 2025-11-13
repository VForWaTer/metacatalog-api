<script lang="ts">
    import { onMount } from 'svelte';
    import { buildApiUrl } from '$lib/stores/settingsStore';

    // Props
    let { entryId, buttonClass = "px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-b border-gray-200 flex items-center gap-1" } = $props<{
        entryId: number;
        buttonClass?: string;
    }>();

    let exportFormats = $state<Array<{format: string, display_name: string, path: string, methods: string[]}>>([]);

    // Fetch available export formats
    async function fetchExportFormats() {
        try {
            const response = await fetch(buildApiUrl('/export-formats'));
            if (response.ok) {
                const data = await response.json();
                // Remove duplicates based on format name
                const uniqueFormats = data.export_formats.filter((format: any, index: number, self: any[]) => 
                    index === self.findIndex(f => f.format === format.format)
                );
                exportFormats = uniqueFormats;
            }
        } catch (error) {
            console.error('Failed to fetch export formats:', error);
        }
    }

    // Handle dropdown functionality
    onMount(() => {
        // Fetch export formats on component mount
        fetchExportFormats();

        function handleClickOutside(event: MouseEvent) {
            const target = event.target as Element;
            if (!target.closest('.relative.group')) {
                // Close all dropdowns
                document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
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
        document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
            if (dropdown !== (event.target as Element)?.closest('.relative')?.querySelector('.dropdown-menu')) {
                dropdown.classList.add('hidden');
            }
        });
        
        // Toggle current dropdown
        const dropdown = (event.target as Element)?.closest('.relative')?.querySelector('.dropdown-menu');
        dropdown?.classList.toggle('hidden');
    }
</script>

<div class="relative group">
    <button 
        class={buttonClass}
        onclick={toggleDropdown}
    >
        Export
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
    </button>
    <div class="dropdown-menu hidden absolute right-0 top-full bg-white border border-gray-200 rounded-md shadow-lg z-[1000] min-w-[160px]">
        {#each exportFormats as format}
            <a 
                href={buildApiUrl(`/export/${entryId}/${format.format}`)}
                class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                onclick={(e) => e.stopPropagation()}
                target="_blank"
            >
                {format.display_name}
            </a>
        {/each}
        {#if exportFormats.length === 0}
            <div class="px-3 py-2 text-sm text-gray-500">
                Loading...
            </div>
        {/if}
    </div>
</div>
