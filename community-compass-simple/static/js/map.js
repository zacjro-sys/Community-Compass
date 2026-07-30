// Community Compass — Simple map helpers.
// Deliberately basic: plain Leaflet markers, minimal geolocation support.
// initMap() draws a map of many resources from a JSON endpoint, plus an
// optional "you are here" pin when the caller knows the user's location.
// initResourceMap() draws a single-pin map for one resource's detail page.

async function initMap(elementId, mapDataUrl, userLocation) {
    const map = L.map(elementId).setView([40.07, -74.43], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const boundsPoints = [];

    if (userLocation && userLocation.lat != null && userLocation.lon != null) {
        const youAreHereIcon = L.divIcon({
            className: 'user-location-marker',
            html: '<span class="user-location-dot"></span>',
            iconSize: [18, 18],
            iconAnchor: [9, 9],
        });
        L.marker([userLocation.lat, userLocation.lon], { icon: youAreHereIcon, zIndexOffset: 1000 })
            .addTo(map)
            .bindPopup('<strong>You are here</strong>');
        boundsPoints.push([userLocation.lat, userLocation.lon]);
    }

    try {
        const response = await fetch(mapDataUrl);
        if (!response.ok) {
            throw new Error(`Map data failed: ${response.status}`);
        }
        const resources = await response.json();

        resources.forEach((resource) => {
            if (resource.latitude == null || resource.longitude == null) {
                return;
            }
            const marker = L.marker([resource.latitude, resource.longitude]).addTo(map);
            const distanceLine = (resource.distance_miles !== null && resource.distance_miles !== undefined)
                ? `<br><small>${resource.distance_miles} mi away</small>`
                : '';
            marker.bindPopup(`
                <strong><a href="/resources/${resource.id}">${resource.name}</a></strong><br>
                <small>${resource.category || ''}</small><br>
                <small>${resource.city || ''}${resource.city && resource.state ? ', ' : ''}${resource.state || ''}</small>${distanceLine}
            `);
            boundsPoints.push([resource.latitude, resource.longitude]);
        });

        if (boundsPoints.length) {
            map.fitBounds(L.latLngBounds(boundsPoints), { padding: [30, 30], maxZoom: 14 });
        }
    } catch (error) {
        console.error('Failed to load map markers:', error);
    }
}

function initResourceMap(options = {}) {
    const map = L.map('resource-map').setView([options.latitude, options.longitude], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    L.marker([options.latitude, options.longitude])
        .addTo(map)
        .bindPopup(`<strong>${options.title}</strong><br><small>${options.category}</small>`)
        .openPopup();
}
