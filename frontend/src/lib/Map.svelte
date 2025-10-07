<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    
    const dispatch = createEventDispatcher();
    
    export let stateMapData = null;
    export let selectedDraftId = null;
    export let fetchFromApi = false;
    
    let map;
    let layerGroup;
    let L;
    
    const stateCentroids = {
        'Karnataka': [12.9716, 77.5946],
        'Delhi': [28.7041, 77.1025],
        'Maharashtra': [19.7515, 75.7139],
        'Gujarat': [22.2587, 71.1924],
        'Telangana': [17.3850, 78.4867],
        'Tamil Nadu': [13.0827, 80.2707],
        'Haryana': [29.0588, 76.0856],
        'West Bengal': [22.9868, 87.8550],
        'Uttar Pradesh': [26.8467, 80.9462],
        'Rajasthan': [27.0238, 74.2179],
        'Madhya Pradesh': [22.9734, 78.6569],
        'Kerala': [10.8505, 76.2711],
        'Andhra Pradesh': [15.9129, 79.73999]
    };
    
    function getColor(d) {
        if (!d || !d.total) return '#AAAAAA';
        const score = ((d.positive || 0) - (d.negative || 0)) / d.total * 100;
        if (score < -5) return '#FF4136';
        if (score > 5) return '#3D9970';
        return '#00A2E8';
    }
    
    function radiusFromTotal(total) {
        return 6 + Math.sqrt(total || 0) * 3;
    }
    
    async function initMap() {
        const leafletModule = await import('leaflet');
        L = leafletModule.default || leafletModule;
        await import('leaflet/dist/leaflet.css');
        
        map = L.map('leaflet-map', {
            center: [22.0, 80.0],
            zoom: 5,
            attributionControl: false
        });
        
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
        
        layerGroup = L.layerGroup().addTo(map);
        
        if (fetchFromApi && selectedDraftId) {
            await fetchData();
        } else {
            renderFromProp();
        }
    }
    
    async function fetchData() {
        if (!selectedDraftId) return;
        try {
            const resp = await fetch(`/api/map-data/${selectedDraftId}`);
            if (!resp.ok) return;
            const arr = await resp.json();
            const obj = {};
            arr.forEach(it => {
                obj[it.state] = {
                    total: it.total,
                    positive: it.positive,
                    neutral: it.neutral,
                    negative: it.negative,
                    lat: it.lat,
                    lon: it.lon
                };
            });
            stateMapData = obj;
            renderFromProp();
        } catch (err) {
            console.error('Error fetching map-data:', err);
        }
    }
    
    function renderFromProp() {
        if (!layerGroup || !stateMapData) return;
        layerGroup.clearLayers();
        
        Object.entries(stateMapData).forEach(([state, d]) => {
            let lat = d.lat, lon = d.lon;
            if ((lat === undefined || lon === undefined) && stateCentroids[state]) {
                [lat, lon] = stateCentroids[state];
            }
            if (!lat || !lon) return;
            
            const circle = L.circleMarker([lat, lon], {
                radius: radiusFromTotal(d.total),
                fillColor: getColor(d),
                color: '#FFFFFF',
                weight: 2,
                fillOpacity: 0.85
            }).addTo(layerGroup);
            
            circle.bindPopup(`
                <strong>${state}</strong><br/>
                Total: ${d.total || 0}<br/>
                Positive: ${d.positive || 0}<br/>
                Neutral: ${d.neutral || 0}<br/>
                Negative: ${d.negative || 0}<br/>
                <em style="color: #0d6efd; font-size: 0.85em;">Click marker to filter by state</em>
            `);
            
            // Add click event for cross-filtering
            circle.on('click', () => {
                dispatch('stateClick', state);
            });
            
            // Add hover effect
            circle.on('mouseover', function() {
                this.setStyle({
                    weight: 3,
                    fillOpacity: 1
                });
            });
            
            circle.on('mouseout', function() {
                this.setStyle({
                    weight: 2,
                    fillOpacity: 0.85
                });
            });
        });
    }
    
    $: if (!fetchFromApi && stateMapData && layerGroup) {
        renderFromProp();
    }
    
    $: if (fetchFromApi && selectedDraftId && layerGroup) {
        fetchData();
    }
    
    onMount(() => {
        initMap();
    });
    
    onDestroy(() => {
        if (map) map.remove();
    });
</script>

<style>
    #leaflet-map {
        width: 100%;
        height: 100%;
        border-radius: 8px;
        cursor: pointer;
    }
</style>

<div id="leaflet-map"></div>