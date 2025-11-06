<script lang="ts">
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';
    import type { SpatialScaleBase, Polygon } from '$lib/models';
    import SpatialExtentMap from './SpatialExtentMap.svelte';

    let resolution = $state(1000); // meters
    let dimensionNamesInput = $state('latitude, longitude');
    let extentPolygon = $state<Polygon | undefined>(undefined);
    let isActive = $state(true);
    let showWKT = $state(false); // Toggle between GeoJSON and WKT display

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

    function setExtentFromMap(polygon: Polygon | undefined) {
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

    // Convert GeoJSON Polygon to WKT format
    function polygonToWKT(polygon: Polygon): string {
        if (!polygon || !polygon.coordinates || !polygon.coordinates[0]) {
            return '';
        }
        
        const coords = polygon.coordinates[0];
        // Format: POLYGON((lng lat, lng lat, ...))
        const coordString = coords.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
        return `POLYGON((${coordString}))`;
    }

    // Format GeoJSON for display
    function formatGeoJSON(polygon: Polygon): string {
        return JSON.stringify(polygon, null, 2);
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
        <label for="spatial-extent" class="block text-sm font-medium text-green-800">
            Spatial Extent (Required)
        </label>
        
        <div class="p-4 bg-white border border-green-300 rounded-md">
            <SpatialExtentMap 
                extentPolygon={extentPolygon} 
                onExtentChange={setExtentFromMap}
            />
        </div>

        {#if extentPolygon}
            <div class="p-3 bg-green-100 border border-green-300 rounded-md space-y-2">
                <div class="flex items-center justify-between">
                    <p class="text-sm font-medium text-green-800">
                        Spatial Extent Data
                    </p>
                    <button
                        type="button"
                        onmousedown={() => showWKT = !showWKT}
                        class="text-xs text-green-700 hover:text-green-900 px-2 py-1 border border-green-400 rounded"
                    >
                        {showWKT ? 'Show GeoJSON' : 'Show WKT'}
                    </button>
                </div>
                {#if showWKT}
                    <div class="mt-2">
                        <code class="block text-xs bg-white p-2 rounded border border-green-200 overflow-x-auto font-mono text-green-900">
                            {polygonToWKT(extentPolygon)}
                        </code>
                    </div>
                {:else}
                    <div class="mt-2">
                        <code class="block text-xs bg-white p-2 rounded border border-green-200 overflow-x-auto font-mono text-green-900 whitespace-pre">
                            {formatGeoJSON(extentPolygon)}
                        </code>
                    </div>
                {/if}
            </div>
        {:else}
            <div class="p-3 bg-yellow-50 border border-yellow-300 rounded-md">
                <p class="text-sm text-yellow-800">
                    <strong>No extent defined.</strong> Please draw a polygon or rectangle on the map above.
                </p>
            </div>
        {/if}
    </div>
</div> 