<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { onMount } from 'svelte';
    import type { Variable } from '$lib/models';

    // Props
    let { 
        variables, 
        value, 
        placeholder = "Type to search variables...",
        label = "Variable",
        required = false,
        disabled = false,
        error = false,
        errorMessage = "",
        maxResults = 10
    } = $props<{
        variables: Variable[];
        value: Variable | null;
        placeholder?: string;
        label?: string;
        required?: boolean;
        disabled?: boolean;
        error?: boolean;
        errorMessage?: string;
        maxResults?: number;
    }>();

    const dispatch = createEventDispatcher<{
        change: [Variable | null];
        input: [string];
    }>();

    // Local state
    let searchTerm = $state('');
    let isOpen = $state(false);
    let highlightedIndex = $state(-1);
    let inputElement: HTMLInputElement;

    // Computed values
    const filteredVariables = $derived(variables.filter((variable: Variable) => {
        if (!searchTerm.trim()) return true;
        
        const searchLower = searchTerm.toLowerCase();
        return variable.name.toLowerCase().includes(searchLower) ||
               variable.symbol.toLowerCase().includes(searchLower) ||
               (variable.unit?.symbol && variable.unit.symbol.toLowerCase().includes(searchLower));
    }).slice(0, maxResults));

    const displayValue = $derived(value ? `${value.name} (${value.symbol}) - ${value.unit?.symbol || 'no unit'}` : searchTerm);

    // Methods
    function handleInput(event: Event) {
        const target = event.target as HTMLInputElement;
        searchTerm = target.value;
        isOpen = true;
        highlightedIndex = -1;
        dispatch('input', [searchTerm]);
    }

    function handleKeydown(event: KeyboardEvent) {
        if (!isOpen) return;

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                highlightedIndex = Math.min(highlightedIndex + 1, filteredVariables.length - 1);
                break;
            case 'ArrowUp':
                event.preventDefault();
                highlightedIndex = Math.max(highlightedIndex - 1, -1);
                break;
            case 'Enter':
                event.preventDefault();
                if (highlightedIndex >= 0 && filteredVariables[highlightedIndex]) {
                    selectVariable(filteredVariables[highlightedIndex]);
                }
                break;
            case 'Escape':
                event.preventDefault();
                closeDropdown();
                break;
        }
    }

    function selectVariable(variable: Variable) {
        value = variable;
        searchTerm = variable.name;
        isOpen = false;
        highlightedIndex = -1;
        dispatch('change', [variable]);
    }

    function clearSelection() {
        value = null;
        searchTerm = '';
        isOpen = false;
        highlightedIndex = -1;
        dispatch('change', [null]);
        inputElement?.focus();
    }

    function closeDropdown() {
        isOpen = false;
        highlightedIndex = -1;
    }

    function handleFocus() {
        if (!disabled) {
            isOpen = true;
        }
    }

    function handleBlur() {
        // Delay closing to allow for clicks on dropdown items
        setTimeout(closeDropdown, 150);
    }

    // Close dropdown when clicking outside
    onMount(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (inputElement && !inputElement.contains(event.target as Node)) {
                closeDropdown();
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    });
</script>

<div class="relative">
    {#if label}
        <label for="variable-autocomplete" class="block text-sm font-medium text-gray-700 mb-2">
            {label} {#if required}<span class="text-red-500">*</span>{/if}
        </label>
    {/if}

    <div class="relative">
        <input
            bind:this={inputElement}
            type="text"
            id="variable-autocomplete"
            value={displayValue}
            oninput={handleInput}
            onkeydown={handleKeydown}
            onfocus={handleFocus}
            onblur={handleBlur}
            {placeholder}
            {disabled}
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {error ? 'border-red-500' : ''} {disabled ? 'bg-gray-100 cursor-not-allowed' : ''}"
        />
        
        {#if value && !disabled}
            <button
                type="button"
                onmousedown={clearSelection}
                class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                title="Clear selection"
                aria-label="Clear variable selection"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        {:else}
            <div class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </div>
        {/if}
    </div>

    {#if error && errorMessage}
        <p class="mt-1 text-sm text-red-600">{errorMessage}</p>
    {/if}

    <!-- Dropdown -->
    {#if isOpen && filteredVariables.length > 0}
        <div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {#each filteredVariables as variable, index}
                <button
                    type="button"
                    onmousedown={() => selectVariable(variable)}
                    class="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none {index === highlightedIndex ? 'bg-blue-50' : ''}"
                >
                    <div class="font-medium">{variable.name} ({variable.symbol})</div>
                    <div class="text-sm text-gray-500">{variable.unit?.symbol || 'no unit'}</div>
                </button>
            {/each}
        </div>
    {:else if isOpen && searchTerm.trim() && filteredVariables.length === 0}
        <div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
            <div class="px-3 py-2 text-gray-500">No variables found</div>
        </div>
    {/if}
</div> 