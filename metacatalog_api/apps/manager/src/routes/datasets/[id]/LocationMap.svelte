<script lang="ts">
    import { onMount } from 'svelte';
    import L from 'leaflet';
    import 'leaflet/dist/leaflet.css';

    // Props
    let { location, spatialExtent } = $props<{
        location?: { coordinates: [number, number] };
        spatialExtent?: { type: string; coordinates: number[][][] };
    }>();

    let mapContainer: HTMLDivElement;
    let map: L.Map;
    let marker: L.Marker | null = null;
    let polygon: L.Polygon | null = null;

    const defaultLat = 51.505;
    const defaultLng = -0.09;

    onMount(() => {
        initMap();
        loadLocationData();
    });

    function initMap() {
        if (!mapContainer) return;

        // Initialize map
        map = L.map(mapContainer).setView([defaultLat, defaultLng], 2);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }

    function loadLocationData() {
        // Clear existing markers and polygons
        if (marker) {
            map.removeLayer(marker);
            marker = null;
        }
        if (polygon) {
            map.removeLayer(polygon);
            polygon = null;
        }

        // Add point location marker
        if (location && location.coordinates) {
            const [lng, lat] = location.coordinates;
            marker = L.marker([lat, lng]).addTo(map);
            map.setView([lat, lng], 10);
        }

        // Add spatial extent polygon
        if (spatialExtent && spatialExtent.coordinates) {
            // Convert GeoJSON coordinates to Leaflet format
            const leafletCoords = spatialExtent.coordinates[0].map((coord: number[]) => [coord[1], coord[0]]); // [lat, lng]
            
            polygon = L.polygon(leafletCoords, {
                color: 'blue',
                fillColor: 'lightblue',
                fillOpacity: 0.3,
                weight: 2
            }).addTo(map);

            // Fit map to show the polygon
            map.fitBounds(polygon.getBounds());
        }

        // If we have both location and spatial extent, show both
        if (location && spatialExtent) {
            // Fit to show both marker and polygon
            const group = new L.FeatureGroup();
            if (marker) group.addLayer(marker);
            if (polygon) group.addLayer(polygon);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    // React to prop changes
    $effect(() => {
        if (map) {
            loadLocationData();
        }
    });
</script>

<div 
    bind:this={mapContainer}
    class="w-full h-48 rounded-md border border-gray-300"
    style="height: 200px;"
></div>
