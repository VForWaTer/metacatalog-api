<script lang="ts">
    import Accordion from "./Accordion.svelte";
    import MetadataForm from "./MetadataForm.svelte";
    import AuthorForm from "./AuthorForm.svelte";
    import type { PageData } from './$types';
    import { metadataEntry, dirtySections, isFormValid } from '$lib/stores/metadataStore';
    import { settings } from '$lib/stores/settingsStore';
    
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