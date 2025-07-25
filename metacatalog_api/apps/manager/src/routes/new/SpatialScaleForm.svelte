<script lang="ts">
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import type { SpatialScaleBase, Polygon } from '$lib/models';

    let resolution = $state(1000); // meters
    let dimensionNamesInput = $state('latitude, longitude');
    let showExtentMap = $state(false);
    let extentPolygon = $state<Polygon | undefined>(undefined);
    let isActive = $state(true);

    // Load existing values from store
    $effect(() => {
        const entry = $metadataEntry;
        if (entry.datasource?.spatial_scale) {
            const scale = entry.datasource.spatial_scale;
            resolution = scale.resolution;
            dimensionNamesInput = scale.dimension_names.join(', ');
            extentPolygon = scale.extent;
        }
    });

    function updateSpatialScale() {
        const spatialScale: SpatialScaleBase = {
            resolution,
            extent: extentPolygon,
            support: 1.0,
            dimension_names: dimensionNamesInput.split(',').map(name => name.trim()).filter(name => name.length > 0)
        };
        metadataActions.updateDatasourceSpatialScale(spatialScale);
    }

    function removeSpatialScale() {
        isActive = false;
        metadataActions.updateDatasourceSpatialScale(undefined);
    }

    function setExtentFromMap(polygon: Polygon) {
        extentPolygon = polygon;
        updateSpatialScale();
    }

    // Event handlers for field changes
    function handleResolutionChange() {
        if (isActive) {
            updateSpatialScale();
        }
    }



    function handleDimensionNamesChange() {
        if (isActive) {
            updateSpatialScale();
        }
    }
</script>

<div class="space-y-4 p-4 bg-green-50 border border-green-200 rounded-md">
    <div class="flex items-center justify-between">
        <h4 class="text-sm font-medium text-green-900">Spatial Scale Configuration</h4>
        <button
            type="button"
            onmousedown={removeSpatialScale}
            class="text-sm text-red-600 hover:text-red-800"
        >
            Remove
        </button>
    </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Resolution -->
        <div class="space-y-2">
            <label for="spatial-resolution" class="block text-sm font-medium text-green-800">
                Resolution (meters)
            </label>
            <input
                id="spatial-resolution"
                type="number"
                bind:value={resolution}
                oninput={handleResolutionChange}
                step="100"
                min="0"
                class="w-full px-3 py-2 border border-green-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
            />
            <p class="text-xs text-green-600">Spatial resolution in meters</p>
        </div>

        <!-- Dimension Names -->
        <div class="space-y-2">
            <label for="spatial-dimensions" class="block text-sm font-medium text-green-800">
                Dimension Names (comma-separated)
            </label>
            <input
                id="spatial-dimensions"
                type="text"
                bind:value={dimensionNamesInput}
                oninput={handleDimensionNamesChange}
                placeholder="latitude, longitude, x, y"
                class="w-full px-3 py-2 border border-green-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
            />
            <p class="text-xs text-green-600">Names of spatial dimensions in your data</p>
        </div>
    </div>

    <!-- Extent Configuration -->
    <div class="space-y-3">
                    <div class="flex items-center justify-between">
                <label for="spatial-extent" class="block text-sm font-medium text-green-800">
                    Spatial Extent (Required)
                </label>
            <button
                type="button"
                onmousedown={() => showExtentMap = !showExtentMap}
                class="text-sm text-green-600 hover:text-green-800"
            >
                {showExtentMap ? 'Hide Map' : 'Show Map'}
            </button>
        </div>
        
        {#if showExtentMap}
            <div class="p-4 bg-white border border-green-300 rounded-md">
                <p class="text-sm text-green-700 mb-3">
                    Use the map below to define the spatial extent of your data. 
                    Click to add points and create a polygon boundary. This is required for spatial scales.
                </p>
                <!-- Placeholder for map component -->
                <div class="h-64 bg-gray-100 border border-gray-300 rounded-md flex items-center justify-center">
                    <p class="text-gray-500">Map component will be implemented here</p>
                </div>
                <p class="text-xs text-green-600 mt-2">
                    Map integration will be added in a future update
                </p>
            </div>
        {/if}

        {#if extentPolygon}
            <div class="p-3 bg-green-100 border border-green-300 rounded-md">
                <p class="text-sm text-green-800">
                    <strong>Current Extent:</strong> Polygon with {extentPolygon.coordinates[0].length} points
                </p>
                <button
                    type="button"
                    onmousedown={() => extentPolygon = undefined}
                    class="text-xs text-red-600 hover:text-red-800 mt-1"
                >
                    Clear Extent
                </button>
            </div>
        {/if}
    </div>
</div> 