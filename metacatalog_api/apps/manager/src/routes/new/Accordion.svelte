<script>
    let { title, children, open = false, color='gray' } = $props();
</script>

<div class="border border-gray-200 rounded-lg">
    <button 
        type="button" 
        class="w-full flex justify-between bg-{color}-500 p-2 rounded cursor-pointer hover:bg-{color}-600" 
        onclick={() => open = !open}
    >
        <span class="text-white font-bold">{title}</span>
        <span class="text-white">
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