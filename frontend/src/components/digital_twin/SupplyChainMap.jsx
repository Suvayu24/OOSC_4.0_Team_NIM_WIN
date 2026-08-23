import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { corridors as fallbackCorridors, sites as fallbackSites } from '../../data/demoData';
import RouteLine from './RouteLine';
import 'leaflet/dist/leaflet.css';

const colors = { port: '#fbbf24', refinery: '#60a5fa', reserve: '#c084fc' };

// Leaflet sizes its tile grid and projects every marker/route using the
// container's pixel size at the moment it mounts. This map can mount before
// the grid column has fully settled, so invalidate once after layout and on
// resize to keep tiles and vector layers aligned.
function FixMapSize() {
  const map = useMap();

  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 100);
    const onResize = () => map.invalidateSize();
    window.addEventListener('resize', onResize);
    return () => {
      clearTimeout(t);
      window.removeEventListener('resize', onResize);
    };
  }, [map]);

  return null;
}

export default function SupplyChainMap({ selected, onSelect, closed, routes = fallbackCorridors, sites = fallbackSites }) {
  const isClosed = (id) => (Array.isArray(closed) ? closed.includes(id) : closed === id);

  return (
    <div className="map real-map">
      <MapContainer
        center={[18, 52]}
        zoom={3}
        scrollWheelZoom
        attributionControl={false}
        className="leaflet-map"
      >
        <FixMapSize />
        <TileLayer attribution="" url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        {routes.map((route) => (
          <RouteLine
            key={route.id}
            route={route}
            selected={selected}
            closed={isClosed(route.id)}
            onClick={onSelect}
          />
        ))}
        {sites.map((site) => (
          <CircleMarker
            key={site.name}
            center={site.coords}
            radius={site.type === 'refinery' ? 7 : 6}
            pathOptions={{ color: colors[site.type], fillColor: colors[site.type], fillOpacity: 1 }}
          >
            <Popup>
              <b>{site.name}</b>
              <br />
              {site.type}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <div className="map-tip">Interactive OpenStreetMap / click a corridor or marker {closed && '/ dashed = closed'}</div>
    </div>
  );
}
