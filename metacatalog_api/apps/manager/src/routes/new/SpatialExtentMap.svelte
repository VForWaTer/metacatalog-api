<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import L from 'leaflet';
    import 'leaflet/dist/leaflet.css';
    import type { Polygon } from '$lib/models';
    
    // Import leaflet-draw CSS
    import 'leaflet-draw/dist/leaflet.draw.css';

    // Props
    let { extentPolygon, onExtentChange } = $props<{
        extentPolygon?: Polygon;
        onExtentChange?: (polygon: Polygon | undefined) => void;
    }>();

    let mapContainer: HTMLDivElement;
    let map: L.Map;
    let drawnItems: L.FeatureGroup;
    let drawControl: any;
    let currentLayer: L.Polygon | L.Rectangle | null = null;

    const defaultLat = 51.505;
    const defaultLng = -0.09;
    const defaultZoom = 2;

    // Convert Leaflet LatLng to GeoJSON coordinates [lng, lat]
    function latLngToGeoJSON(latLng: L.LatLng): [number, number] {
        return [latLng.lng, latLng.lat];
    }

    // Convert GeoJSON coordinates [lng, lat] to Leaflet LatLng
    function geoJSONToLatLng(coord: [number, number]): L.LatLng {
        return L.latLng(coord[1], coord[0]);
    }

    // Convert Leaflet Polygon to GeoJSON Polygon
    function leafletPolygonToGeoJSON(layer: L.Polygon): Polygon {
        const latlngs = layer.getLatLngs()[0] as L.LatLng[];
        const coordinates = latlngs.map(latLngToGeoJSON);
        
        // Ensure polygon is closed (first == last)
        if (coordinates.length > 0) {
            const first = coordinates[0];
            const last = coordinates[coordinates.length - 1];
            if (first[0] !== last[0] || first[1] !== last[1]) {
                coordinates.push([first[0], first[1]]);
            }
        }
        
        return {
            type: 'Polygon',
            coordinates: [coordinates]
        };
    }

    // Convert GeoJSON Polygon to Leaflet Polygon
    function geoJSONToLeafletPolygon(polygon: Polygon): L.Polygon {
        const coords = polygon.coordinates[0];
        const latlngs = coords.map(geoJSONToLatLng);
        return L.polygon(latlngs, {
            color: '#3388ff',
            fillColor: '#3388ff',
            fillOpacity: 0.2,
            weight: 2
        });
    }

    // Convert Leaflet Rectangle bounds to GeoJSON Polygon
    function rectangleToPolygon(bounds: L.LatLngBounds): Polygon {
        const south = bounds.getSouth();
        const west = bounds.getWest();
        const north = bounds.getNorth();
        const east = bounds.getEast();
        
        // Create polygon coordinates: [[west, south], [east, south], [east, north], [west, north], [west, south]]
        return {
            type: 'Polygon',
            coordinates: [[
                [west, south],
                [east, south],
                [east, north],
                [west, north],
                [west, south] // Close the polygon
            ]]
        };
    }

    async function initMap() {
        if (!mapContainer) return;

        // Ensure leaflet-draw is loaded and extends Leaflet namespace
        await import('leaflet-draw');
        
        // Verify Draw namespace is available
        if (!(L as any).Draw) {
            console.error('Leaflet.draw failed to load properly');
            return;
        }

        // Initialize map
        map = L.map(mapContainer).setView([defaultLat, defaultLng], defaultZoom);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Initialize feature group for drawn items
        drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        // Wait a tick to ensure map is fully initialized
        await new Promise(resolve => setTimeout(resolve, 100));

        // Configure draw controls
        const drawOptions: any = {
            draw: {
                polygon: {
                    allowIntersection: true, // Allow self-intersecting polygons
                    showArea: false, // Disable area calculation to avoid errors
                    drawError: {
                        color: '#e1e100',
                        message: '<strong>Oh snap!</strong> you can\'t draw that!'
                    },
                    shapeOptions: {
                        color: '#3388ff',
                        fillColor: '#3388ff',
                        fillOpacity: 0.2
                    }
                },
                rectangle: {
                    showArea: false, // Disable area calculation to avoid errors
                    metric: false, // Disable metric display
                    shapeOptions: {
                        color: '#3388ff',
                        fillColor: '#3388ff',
                        fillOpacity: 0.2
                    }
                },
                circle: false,
                marker: false,
                circlemarker: false,
                polyline: false
            },
            edit: {
                featureGroup: drawnItems,
                remove: true
            }
        };

        // Add draw controls - use any to avoid type issues
        drawControl = new (L.Control as any).Draw(drawOptions);
        map.addControl(drawControl);

        // Handle drawing events - use any to access Draw namespace
        const Draw = (L as any).Draw;
        if (!Draw || !Draw.Event) {
            console.error('Leaflet.draw Draw namespace not available');
            return;
        }
        
        map.on(Draw.Event.CREATED, (e: any) => {
            const layer = e.layer;
            const type = e.layerType;

            // Clear existing layer
            if (currentLayer) {
                drawnItems.removeLayer(currentLayer);
            }

            // Add new layer
            drawnItems.addLayer(layer);
            
            // Convert to GeoJSON based on type
            let polygon: Polygon;
            if (type === 'rectangle') {
                currentLayer = layer as L.Rectangle;
                const bounds = (layer as L.Rectangle).getBounds();
                polygon = rectangleToPolygon(bounds);
            } else if (type === 'polygon') {
                currentLayer = layer as L.Polygon;
                polygon = leafletPolygonToGeoJSON(layer as L.Polygon);
            } else {
                return;
            }

            // Emit change
            if (onExtentChange) {
                onExtentChange(polygon);
            }

            // Fit map to show the drawn geometry
            map.fitBounds(layer.getBounds().pad(0.1));
        });

        // Handle edit events
        map.on(Draw.Event.EDITED, (e: any) => {
            const layers = e.layers;
            layers.eachLayer((layer: any) => {
                if (layer instanceof L.Polygon) {
                    currentLayer = layer;
                    const polygon = leafletPolygonToGeoJSON(layer);
                    if (onExtentChange) {
                        onExtentChange(polygon);
                    }
                } else if (layer instanceof L.Rectangle) {
                    currentLayer = layer;
                    const bounds = layer.getBounds();
                    const polygon = rectangleToPolygon(bounds);
                    if (onExtentChange) {
                        onExtentChange(polygon);
                    }
                }
            });
        });

        // Handle delete events
        map.on(Draw.Event.DELETED, () => {
            currentLayer = null;
            if (onExtentChange) {
                onExtentChange(undefined);
            }
        });

        // Load existing polygon if provided
        loadExistingPolygon();
    }

    function loadExistingPolygon() {
        if (!map || !extentPolygon) return;

        // Clear existing
        if (currentLayer) {
            drawnItems.removeLayer(currentLayer);
            currentLayer = null;
        }

        // Add existing polygon
        const layer = geoJSONToLeafletPolygon(extentPolygon);
        drawnItems.addLayer(layer);
        currentLayer = layer;

        // Fit map to show the polygon
        map.fitBounds(layer.getBounds().pad(0.1));
    }

    function clearExtent() {
        if (currentLayer) {
            drawnItems.removeLayer(currentLayer);
            currentLayer = null;
        }
        if (onExtentChange) {
            onExtentChange(undefined);
        }
    }

    // React to prop changes
    $effect(() => {
        if (map && extentPolygon) {
            loadExistingPolygon();
        } else if (map && !extentPolygon && currentLayer) {
            // Clear if extentPolygon is removed
            drawnItems.removeLayer(currentLayer);
            currentLayer = null;
        }
    });

    onMount(async () => {
        await initMap();
    });

    onDestroy(() => {
        if (map) {
            map.remove();
        }
    });
</script>

<div class="space-y-2">
    <div class="flex items-center justify-between">
        <p class="text-xs text-gray-600">
            Use the drawing tools above the map to draw a polygon or rectangle (bounding box) for the spatial extent.
        </p>
        {#if currentLayer}
            <button
                type="button"
                onmousedown={clearExtent}
                class="text-xs text-red-600 hover:text-red-800 px-2 py-1 border border-red-300 rounded"
            >
                Clear
            </button>
        {/if}
    </div>
    <div 
        bind:this={mapContainer}
        class="w-full rounded-md border border-gray-300"
        style="height: 400px;"
    ></div>
</div>

