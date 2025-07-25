<script lang="ts">
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import type { TemporalScaleBase } from '$lib/models';

    let resolution = $state('P1D'); // ISO 8601 duration string
    let observationStart = $state(new Date().toISOString().slice(0, 16)); // datetime-local format
    let observationEnd = $state(new Date().toISOString().slice(0, 16));
    let dimensionNamesInput = $state('time');
    let isActive = $state(true);

    // Load existing values from store
    $effect(() => {
        const entry = $metadataEntry;
        if (entry.datasource?.temporal_scale) {
            const scale = entry.datasource.temporal_scale;
            resolution = scale.resolution;
            observationStart = scale.observation_start.slice(0, 16);
            observationEnd = scale.observation_end.slice(0, 16);
            dimensionNamesInput = scale.dimension_names.join(', ');
        }
    });

    function updateTemporalScale() {
        const temporalScale: TemporalScaleBase = {
            resolution,
            observation_start: new Date(observationStart).toISOString(),
            observation_end: new Date(observationEnd).toISOString(),
            support: 1.0,
            dimension_names: dimensionNamesInput.split(',').map(name => name.trim()).filter(name => name.length > 0)
        };
        metadataActions.updateDatasourceTemporalScale(temporalScale);
    }

    function removeTemporalScale() {
        isActive = false;
        metadataActions.updateDatasourceTemporalScale(undefined);
    }

    // Event handlers for field changes
    function handleResolutionChange() {
        if (isActive) {
            updateTemporalScale();
        }
    }

    function handleObservationStartChange() {
        if (isActive) {
            updateTemporalScale();
        }
    }

    function handleObservationEndChange() {
        if (isActive) {
            updateTemporalScale();
        }
    }



    function handleDimensionNamesChange() {
        if (isActive) {
            updateTemporalScale();
        }
    }
</script>

<div class="space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
    <div class="flex items-center justify-between">
        <h4 class="text-sm font-medium text-blue-900">Temporal Scale Configuration</h4>
        <button
            type="button"
            onmousedown={removeTemporalScale}
            class="text-sm text-red-600 hover:text-red-800"
        >
            Remove
        </button>
    </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Resolution -->
        <div class="space-y-2">
            <label for="temporal-resolution" class="block text-sm font-medium text-blue-800">
                Resolution (ISO 8601)
            </label>
            <input
                id="temporal-resolution"
                type="text"
                bind:value={resolution}
                oninput={handleResolutionChange}
                placeholder="P1D (1 day), PT1H (1 hour), etc."
                class="w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <p class="text-xs text-blue-600">ISO 8601 duration format (e.g., P1D for 1 day, PT1H for 1 hour)</p>
        </div>

        <!-- Dimension Names -->
        <div class="space-y-2">
            <label for="temporal-dimensions" class="block text-sm font-medium text-blue-800">
                Dimension Names (comma-separated)
            </label>
            <input
                id="temporal-dimensions"
                type="text"
                bind:value={dimensionNamesInput}
                oninput={handleDimensionNamesChange}
                placeholder="time, date, timestamp"
                class="w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <p class="text-xs text-blue-600">Names of temporal dimensions in your data</p>
        </div>

        <!-- Observation Start -->
        <div class="space-y-2">
            <label for="temporal-start" class="block text-sm font-medium text-blue-800">
                Observation Start
            </label>
            <input
                id="temporal-start"
                type="datetime-local"
                bind:value={observationStart}
                onchange={handleObservationStartChange}
                class="w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
        </div>

        <!-- Observation End -->
        <div class="space-y-2">
            <label for="temporal-end" class="block text-sm font-medium text-blue-800">
                Observation End
            </label>
            <input
                id="temporal-end"
                type="datetime-local"
                bind:value={observationEnd}
                onchange={handleObservationEndChange}
                class="w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
        </div>
    </div>
</div> 