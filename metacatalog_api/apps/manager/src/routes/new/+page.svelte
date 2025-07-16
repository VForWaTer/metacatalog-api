<script>
    import Accordion from "./Accordion.svelte";

</script>
<div class="w-9/10 mx-auto bg-white rounded-lg p-4">
    <h1 class="text-2xl font-bold">
        Create new Metadata Entry
    </h1>

    <div class="mt-4">
        <Accordion title="Main Metadata" open>
            <p>Main Metadata</p>
        </Accordion>

        <Accordion title="Authors">
            <p>Authors</p>
        </Accordion>
        
    </div>
</div>