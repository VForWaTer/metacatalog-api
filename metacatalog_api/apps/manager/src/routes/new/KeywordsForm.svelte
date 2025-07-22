<script lang="ts">
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import { settings } from '$lib/stores/settingsStore';
    import type { Keyword } from '$lib/models';

    let searchTerm = $state('');
    let showDropdown = $state(false);
    let selectedKeywords = $state<Keyword[]>([]);
    let filteredKeywords = $state<Keyword[]>([]);
    let isLoading = $state(false);
    let searchError = $state<string | null>(null);
    let searchTimeout: number | null = null;

    // Debounced search function
    async function searchKeywords(term: string) {
        if (term.length < 2) {
            filteredKeywords = [];
            return;
        }

        isLoading = true;
        searchError = null;

        try {
            const response = await fetch(`${$settings.backendUrl}/keywords?search=${encodeURIComponent(term)}&limit=20`);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch keywords: ${response.status}`);
            }

            const keywords = await response.json();
            filteredKeywords = keywords;
        } catch (error) {
            console.error('Error searching keywords:', error);
            searchError = error instanceof Error ? error.message : 'Failed to search keywords';
            filteredKeywords = [];
        } finally {
            isLoading = false;
        }
    }

    // Debounced search input handler
    function handleSearchInput() {
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        showDropdown = searchTerm.length > 0;

        // Set new timeout for debounced search
        searchTimeout = setTimeout(() => {
            searchKeywords(searchTerm);
        }, 300);
    }

    // Load existing keywords from store
    $effect(() => {
        const entry = $metadataEntry;
        if (entry.keywords && entry.keywords.length > 0) {
            // Load existing keywords by ID
            loadExistingKeywords(entry.keywords);
        }
    });

    // Load existing keywords by their IDs
    async function loadExistingKeywords(keywordIds: number[]) {
        try {
            const promises = keywordIds.map(async (id) => {
                const response = await fetch(`${$settings.backendUrl}/keywords/${id}`);
                if (response.ok) {
                    return await response.json();
                }
                return null;
            });

            const keywords = await Promise.all(promises);
            selectedKeywords = keywords.filter((k): k is Keyword => k !== null);
        } catch (error) {
            console.error('Error loading existing keywords:', error);
        }
    }

    function addKeyword(keyword: Keyword) {
        if (!selectedKeywords.some(k => k.id === keyword.id)) {
            selectedKeywords = [...selectedKeywords, keyword];
            if (keyword.id) {
                metadataActions.addKeyword(keyword.id);
            }
        }
        searchTerm = '';
        showDropdown = false;
        filteredKeywords = [];
    }

    function removeKeyword(keywordId: number) {
        selectedKeywords = selectedKeywords.filter(k => k.id !== keywordId);
        metadataActions.removeKeyword(keywordId);
    }

    function handleSearchBlur() {
        // Delay hiding dropdown to allow for clicks
        setTimeout(() => {
            showDropdown = false;
        }, 200);
    }

    // Cleanup timeout on component destroy
    $effect(() => {
        return () => {
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
        };
    });
</script>

<div class="space-y-4">
    <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900">Keywords</h3>
        <span class="text-sm text-gray-500">
            {selectedKeywords.length} selected
        </span>
    </div>

    <!-- Search Input -->
    <div class="relative">
        <input
            type="text"
            bind:value={searchTerm}
            oninput={handleSearchInput}
            onblur={handleSearchBlur}
            placeholder="Search keywords by full path..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
        />
        
        <!-- Loading indicator -->
        {#if isLoading}
            <div class="absolute right-3 top-2.5">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            </div>
        {/if}
        
        <!-- Dropdown -->
        {#if showDropdown && (filteredKeywords.length > 0 || isLoading || searchError)}
            <div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                {#if isLoading}
                    <div class="px-4 py-2 text-sm text-gray-500">Searching...</div>
                {:else if searchError}
                    <div class="px-4 py-2 text-sm text-red-600">Error: {searchError}</div>
                {:else if filteredKeywords.length === 0}
                    <div class="px-4 py-2 text-sm text-gray-500">No keywords found</div>
                {:else}
                    {#each filteredKeywords as keyword}
                        <button
                            type="button"
                            onmousedown={() => addKeyword(keyword)}
                            class="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                        >
                            <div class="text-sm font-medium text-gray-900">{keyword.value}</div>
                            <div class="text-xs text-gray-500">{keyword.full_path}</div>
                        </button>
                    {/each}
                {/if}
            </div>
        {/if}
    </div>

    <!-- Selected Keywords -->
    {#if selectedKeywords.length > 0}
        <div class="space-y-2">
            <h4 class="text-sm font-medium text-gray-700">Selected Keywords:</h4>
            <div class="space-y-2">
                {#each selectedKeywords as keyword}
                    <div class="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <div class="flex-1">
                            <div class="text-sm font-medium text-blue-900">{keyword.value}</div>
                            <div class="text-xs text-blue-700">{keyword.full_path}</div>
                        </div>
                        <button
                            type="button"
                            onmousedown={() => keyword.id && removeKeyword(keyword.id)}
                            class="ml-2 text-blue-600 hover:text-blue-800"
                        >
                            Remove
                        </button>
                    </div>
                {/each}
            </div>
        </div>
    {:else}
        <div class="text-center py-4 text-gray-500">
            No keywords selected. Search and add keywords to categorize this metadata entry.
        </div>
    {/if}
</div> 