<script lang="ts">
    import type { DetailCreate } from '$lib/models';
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';

    // Local state for new detail form
    let newDetail = $state<DetailCreate>({
        key: '',
        raw_value: {},
        thesaurus: undefined
    });

    // Value type options
    const valueTypes = [
        { value: 'text', label: 'Text' },
        { value: 'integer', label: 'Integer' },
        { value: 'float', label: 'Float' },
        { value: 'boolean', label: 'Boolean' },
        { value: 'json', label: 'JSON' }
    ];

    let selectedValueType = $state('text');
    let valueInput = $state('');

    // Handle value type change
    function handleValueTypeChange() {
        // Reset value input when type changes
        valueInput = '';
        newDetail.raw_value = {};
    }

    // Handle value input change
    function handleValueInputChange() {
        try {
            switch (selectedValueType) {
                case 'text':
                    newDetail.raw_value = { '__literal__': valueInput };
                    break;
                case 'integer':
                    const intValue = parseInt(valueInput);
                    if (!isNaN(intValue)) {
                        newDetail.raw_value = { '__literal__': intValue };
                    }
                    break;
                case 'float':
                    const floatValue = parseFloat(valueInput);
                    if (!isNaN(floatValue)) {
                        newDetail.raw_value = { '__literal__': floatValue };
                    }
                    break;
                case 'boolean':
                    const boolValue = valueInput.toLowerCase() === 'true';
                    newDetail.raw_value = { '__literal__': boolValue };
                    break;
                case 'json':
                    const jsonValue = JSON.parse(valueInput);
                    newDetail.raw_value = jsonValue;
                    break;
            }
        } catch (error) {
            // Invalid input - keep raw_value as empty object
            newDetail.raw_value = {};
        }
    }

    // Add new detail
    function addDetail() {
        if (newDetail.key.trim()) {
            metadataActions.addDetail({...newDetail});
            
            // Reset form
            newDetail = {
                key: '',
                raw_value: {},
                thesaurus: undefined
            };
            selectedValueType = 'text';
            valueInput = '';
        }
    }

    // Remove detail
    function removeDetail(index: number) {
        metadataActions.removeDetail(index);
    }

    // Get display value for a detail
    function getDisplayValue(detail: DetailCreate): string {
        if (detail.raw_value && '__literal__' in detail.raw_value) {
            return String(detail.raw_value.__literal__);
        } else if (detail.raw_value && Object.keys(detail.raw_value).length > 0) {
            return JSON.stringify(detail.raw_value);
        }
        return '';
    }

    // Get value type for a detail
    function getValueType(detail: DetailCreate): string {
        if (detail.raw_value && '__literal__' in detail.raw_value) {
            const value = detail.raw_value.__literal__;
            if (typeof value === 'number') {
                return Number.isInteger(value) ? 'integer' : 'float';
            } else if (typeof value === 'boolean') {
                return 'boolean';
            } else {
                return 'text';
            }
        } else if (detail.raw_value && Object.keys(detail.raw_value).length > 0) {
            return 'json';
        }
        return 'text';
    }
</script>

<div class="space-y-6">
    <!-- Add New Detail Form -->
    <div class="bg-gray-50 p-4 rounded-md">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Add New Detail</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Key -->
            <div>
                <label for="detail-key" class="block text-sm font-medium text-gray-700 mb-1">
                    Key *
                </label>
                <input
                    type="text"
                    id="detail-key"
                    bind:value={newDetail.key}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="e.g., sensor_type"
                />
            </div>

            <!-- Value Type -->
            <div>
                <label for="value-type" class="block text-sm font-medium text-gray-700 mb-1">
                    Value Type
                </label>
                <select
                    id="value-type"
                    bind:value={selectedValueType}
                    onchange={handleValueTypeChange}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                    {#each valueTypes as type}
                        <option value={type.value}>{type.label}</option>
                    {/each}
                </select>
            </div>

            <!-- Value Input -->
            <div>
                <label for="value-input" class="block text-sm font-medium text-gray-700 mb-1">
                    Value
                </label>
                {#if selectedValueType === 'boolean'}
                    <select
                        id="value-input"
                        bind:value={valueInput}
                        onchange={handleValueInputChange}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    >
                        <option value="">Select...</option>
                        <option value="true">True</option>
                        <option value="false">False</option>
                    </select>
                {:else if selectedValueType === 'json'}
                    <textarea
                        id="value-input"
                        bind:value={valueInput}
                        oninput={handleValueInputChange}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder="Enter JSON object"
                        rows="2"
                    ></textarea>
                {:else}
                    <input
                        type={selectedValueType === 'integer' || selectedValueType === 'float' ? 'number' : 'text'}
                        id="value-input"
                        bind:value={valueInput}
                        oninput={handleValueInputChange}
                        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                        placeholder={selectedValueType === 'integer' ? '123' : selectedValueType === 'float' ? '123.45' : 'Enter value'}
                    />
                {/if}
            </div>

            <!-- Add Button -->
            <div class="flex items-end">
                <button
                    type="button"
                    onmousedown={addDetail}
                    disabled={!newDetail.key.trim()}
                    class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Add Detail
                </button>
            </div>
        </div>


    </div>

    <!-- Details Table -->
    <div>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Extra Metadata Details</h3>
        
        {#if ($metadataEntry.details || []).length > 0}
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Key
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Type
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Value
                            </th>

                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {#each ($metadataEntry.details || []) as detail, index}
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {detail.key}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {getValueType(detail)}
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 max-w-xs">
                                    <div class="truncate" title={getDisplayValue(detail)}>
                                        {getDisplayValue(detail)}
                                    </div>
                                </td>

                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <button
                                        type="button"
                                        onmousedown={() => removeDetail(index)}
                                        class="text-red-600 hover:text-red-900"
                                    >
                                        Remove
                                    </button>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {:else}
            <p class="text-gray-500 italic">No extra metadata details added yet.</p>
        {/if}
    </div>
</div> 