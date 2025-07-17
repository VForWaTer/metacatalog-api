<script lang="ts">
    import { metadataEntry, metadataActions, isFormValid, dirtySections } from '$lib/stores/metadataStore';
    import type { License, Variable } from '$lib/models';
    import VariableAutocomplete from './VariableAutocomplete.svelte';

    // Props
    let { licenses, variables } = $props<{ licenses: License[]; variables: Variable[] }>();

    // Reactive variables for form validation
    const titleError = $derived($metadataEntry.title.trim() === '' && $dirtySections.has('basic'));
    const abstractError = $derived($metadataEntry.abstract.trim() === '' && $dirtySections.has('basic'));
    
    // Get current variable object
    const currentVariable = $derived(variables.find((v: Variable) => v.id === $metadataEntry.variable) || null);

    // Handle form updates
    function updateTitle(event: Event) {
        const target = event.target as HTMLInputElement;
        metadataActions.updateBasicInfo({ title: target.value });
    }

    function updateAbstract(event: Event) {
        const target = event.target as HTMLTextAreaElement;
        metadataActions.updateBasicInfo({ abstract: target.value });
    }

    function updateExternalId(event: Event) {
        const target = event.target as HTMLInputElement;
        metadataActions.updateBasicInfo({ external_id: target.value });
    }

    function updateComment(event: Event) {
        const target = event.target as HTMLTextAreaElement;
        metadataActions.updateBasicInfo({ comment: target.value });
    }

    function updateEmbargo(event: Event) {
        const target = event.target as HTMLInputElement;
        metadataActions.updateBasicInfo({ embargo: target.checked });
    }

    function updateVariable(event: Event) {
        const target = event.target as HTMLSelectElement;
        metadataActions.updateVariable(parseInt(target.value));
    }

    function updateVariableFromAutocomplete(event: CustomEvent<[Variable | null]>) {
        metadataActions.updateVariableObject(event.detail[0]);
    }

    function updateLicense(event: Event) {
        const target = event.target as HTMLSelectElement;
        const licenseId = parseInt(target.value);
        metadataActions.updateLicense(licenseId);
    }
</script>

<form class="space-y-6">
    <!-- Title -->
    <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-2">
            Title <span class="text-red-500">*</span>
        </label>
                            <input
                        type="text"
                        id="title"
                        name="title"
                        value={$metadataEntry.title}
                        oninput={updateTitle}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {titleError ? 'border-red-500' : ''}"
                        placeholder="Enter the title of your dataset"
                        required
                    />
        {#if titleError}
            <p class="mt-1 text-sm text-red-600">Title is required</p>
        {/if}
    </div>

    <!-- Abstract -->
    <div>
        <label for="abstract" class="block text-sm font-medium text-gray-700 mb-2">
            Abstract <span class="text-red-500">*</span>
        </label>
                            <textarea
                        id="abstract"
                        name="abstract"
                        value={$metadataEntry.abstract}
                        oninput={updateAbstract}
                        rows="4"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 {abstractError ? 'border-red-500' : ''}"
                        placeholder="Provide a detailed description of your dataset"
                        required
                    ></textarea>
        {#if abstractError}
            <p class="mt-1 text-sm text-red-600">Abstract is required</p>
        {/if}
    </div>

    <!-- External ID -->
    <div>
        <label for="external_id" class="block text-sm font-medium text-gray-700 mb-2">
            External ID
        </label>
                            <input
                        type="text"
                        id="external_id"
                        name="external_id"
                        value={$metadataEntry.external_id || ''}
                        oninput={updateExternalId}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="External identifier (optional)"
                    />
    </div>

    <!-- Variable Selection -->
    <div class="border-t pt-6">
        <VariableAutocomplete
            variables={variables}
            value={currentVariable}
            label="Variable"
            required={true}
            on:change={updateVariableFromAutocomplete}
            maxResults={15}
        />
    </div>

    <!-- License Selection -->
    <div class="border-t pt-6">
        <label for="license" class="block text-sm font-medium text-gray-700 mb-2">
            License <span class="text-red-500">*</span>
        </label>
        <select
            id="license"
            name="license"
            value={$metadataEntry.license}
            onchange={updateLicense}
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            required
        >
            <option value="">Select a license</option>
            {#each licenses as license}
                <option value={license.id}>{license.short_title} - {license.title}</option>
            {/each}
        </select>
    </div>

    <!-- Additional Options -->
    <div class="border-t pt-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Additional Options</h3>
        
        <div class="space-y-4">
            <!-- Embargo -->
            <div class="flex items-center">
                <input
                    type="checkbox"
                    id="embargo"
                    name="embargo"
                    checked={$metadataEntry.embargo}
                    onchange={updateEmbargo}
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label for="embargo" class="ml-2 text-sm text-gray-700">
                    Apply embargo (restrict access for 2 years)
                </label>
            </div>
        </div>
    </div>

    <!-- Comment -->
    <div>
        <label for="comment" class="block text-sm font-medium text-gray-700 mb-2">
            Comment
        </label>
                            <textarea
                        id="comment"
                        name="comment"
                        value={$metadataEntry.comment || ''}
                        oninput={updateComment}
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Additional comments or notes"
                    ></textarea>
    </div>

    <!-- Form Status -->
    <div class="border-t pt-6">
        <div class="flex items-center justify-between">
            <div class="text-sm text-gray-600">
                {#if $dirtySections.has('basic')}
                    <span class="text-orange-600">●</span> Unsaved changes
                {:else}
                    <span class="text-green-600">●</span> All changes saved
                {/if}
            </div>
            <div class="text-sm text-gray-600">
                Form valid: {#if $isFormValid}<span class="text-green-600">✓</span>{:else}<span class="text-red-600">✗</span>{/if}
            </div>
        </div>
    </div>
</form> 