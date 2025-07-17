<script>
    let { title, children, open = false } = $props();
</script>

<div class="border border-gray-200 rounded-lg">
    <button 
        type="button" 
        class="w-full flex justify-between bg-gray-300 p-2 rounded cursor-pointer hover:bg-gray-400" 
        onclick={() => open = !open}
    >
        <span class="text-gray-900 font-bold">{title}</span>
        <span class="text-gray-900">
            {#if open}
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
            {:else}
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
            {/if}
        </span>
    </button>

    {#if open}
        <div class="py-4 px-2">
            {@render children?.()}
        </div>
    {/if}
</div>