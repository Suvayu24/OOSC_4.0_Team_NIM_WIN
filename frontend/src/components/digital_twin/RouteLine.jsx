import { Polyline, Popup } from 'react-leaflet';
import { riskColor } from '../../utils/mapConfig';

function normalizeRisk(route) {
  if (typeof route.risk === 'number') return route.risk;
  if (typeof route.risk_score === 'number') return route.risk_score / 100;
  return 0;
}

export function routePositions(route = {}) {
  if (Array.isArray(route.coords) && route.coords.length) return route.coords;
  if (Array.isArray(route.points) && route.points.length) return route.points;

  if (Array.isArray(route.waypoints) && route.waypoints.length) {
    return route.waypoints
      .map((point) => {
        if (Array.isArray(point)) {
          const [lng, lat] = point;
          return [lat, lng];
        }
        if (point && typeof point.lat === 'number' && typeof point.lng === 'number') {
          return [point.lat, point.lng];
        }
        return null;
      })
      .filter(Boolean);
  }

  if (route.origin && route.destination) {
    return [
      [route.origin.lat, route.origin.lng],
      [route.destination.lat, route.destination.lng],
    ];
  }

  return [];
}

export default function RouteLine({ route, selected, closed, onClick }) {
  const positions = routePositions(route);
  if (positions.length < 2) return null;

  const risk = normalizeRisk(route);
  const isSelected = selected?.id === route.id || selected === route.id;

  return (
    <Polyline
      positions={positions}
      pathOptions={{
        className: 'route',
        color: closed ? '#64748b' : riskColor(risk),
        weight: isSelected ? 8 : 5,
        opacity: 0.95,
        dashArray: closed ? '10 8' : undefined,
        lineCap: 'round',
        lineJoin: 'round',
      }}
      eventHandlers={onClick ? { click: () => onClick(route) } : undefined}
    >
      <Popup>
        <b>{route.name}</b>
        <br />
        {Math.round(risk * 100)}% risk{route.oil ? ` / ${route.oil}` : ''}
      </Popup>
    </Polyline>
  );
}
