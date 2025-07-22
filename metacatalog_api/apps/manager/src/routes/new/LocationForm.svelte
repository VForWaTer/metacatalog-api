<script lang="ts">
    import { onMount } from 'svelte';
    import L from 'leaflet';
    import 'leaflet/dist/leaflet.css';
    import { metadataEntry, metadataActions } from '$lib/stores/metadataStore';

    // @ts-ignore declare const L: any;

    let mapContainer: HTMLDivElement;
    let map: L.Map;
    let marker: L.Marker | null = null;
    let currentLocation: [number, number] | null = null;
    let isMapLoaded = $state(false);
    let displayLocation = $derived($metadataEntry.location ? $metadataEntry.location.coordinates : null);

    const defaultLat = 51.505;
    const defaultLng = -0.09;

    onMount(() => {
        // Initialize map
        initMap();
        
        // Load existing location from store
        loadExistingLocation();
    });

    function initMap() {
        if (!mapContainer) return;

        // Initialize map
        map = L.map(mapContainer).setView([defaultLat, defaultLng], 10);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Add click handler
        map.on('click', (e: L.LeafletMouseEvent) => {
            const { lat, lng } = e.latlng;
            setLocation([lng, lat]); // GeoJSON uses [lng, lat] order
        });

        // Add right-click handler to remove location
        map.on('contextmenu', (e: L.LeafletMouseEvent) => {
            e.originalEvent.preventDefault();
            if (currentLocation) {
                clearLocation();
            }
        });

        isMapLoaded = true;
    }

    function loadExistingLocation() {
        const entry = $metadataEntry;
        if (entry.location) {
            // Convert from PointModel to coordinates
            if (entry.location.coordinates) {
                const [lng, lat] = entry.location.coordinates;
                setLocation([lng, lat]);
            }
        }
    }

    function setLocation(coordinates: [number, number]) {
        currentLocation = coordinates;
        
        // Update marker
        if (marker) {
            map.removeLayer(marker);
        }
        
        const [lng, lat] = coordinates;
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        
        // Add drag event listener
        marker.on('dragend', (e: L.DragEndEvent) => {
            const { lat, lng } = e.target.getLatLng();
            const newCoordinates: [number, number] = [lng, lat]; // GeoJSON uses [lng, lat]
            currentLocation = newCoordinates;
            metadataActions.updateLocation(newCoordinates);
        });
        
        // Update metadata store
        metadataActions.updateLocation(coordinates);
    }

    function clearLocation() {
        currentLocation = null;
        
        if (marker) {
            map.removeLayer(marker);
            marker = null;
        }
        
        metadataActions.updateLocation(undefined);
    }
</script>

<div class="space-y-4">
    <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900">Location</h3>
        {#if currentLocation}
            <span class="text-sm text-gray-500">
                {currentLocation[1].toFixed(4)}, {currentLocation[0].toFixed(4)}
            </span>
        {/if}
    </div>

    <p class="text-sm text-gray-600">
        Click on the map to set a location. Drag the marker to adjust, or right-click to remove.
    </p>

    <!-- Map Container -->
    <div 
        bind:this={mapContainer}
        class="w-full h-64 rounded-md border border-gray-300"
        style="cursor: {currentLocation ? 'default' : 'crosshair'};"
    ></div>

    {#if displayLocation}
        <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">
                Lon: {displayLocation[0].toFixed(4)}, Lat: {displayLocation[1].toFixed(4)}
            </span>
            <button
                type="button"
                onmousedown={clearLocation}
                class="px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md"
            >
                Clear Location
            </button>
        </div>
    {/if}
</div> 