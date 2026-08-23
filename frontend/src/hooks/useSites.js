import { useEffect, useState } from 'react';
import { sites as fallbackSites } from '../data/demoData';
import { api } from '../services/api';
import { splitCorridorName } from '../utils/adapters';

// The real backend has no single "sites" endpoint -- refineries come from
// GET /procurement/refineries, reserve depots from GET /procurement/reserves,
// and "oil selling locations" (ports) aren't a modeled entity at all, just
// each corridor's origin point. This composes all three into the
// {name, coords, type} shape SupplyChainMap/Sidebar already render.
export default function useSites(corridors) {
  const [refineries, setRefineries] = useState([]);
  const [reserveDepots, setReserveDepots] = useState([]);
  const [live, setLive] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([api.refineries(), api.reserves()])
      .then(([refs, res]) => {
        if (!active) return;
        setRefineries(Array.isArray(refs) ? refs : []);
        setReserveDepots(Array.isArray(res?.depots) ? res.depots : []);
        setLive(true);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  if (!live) return fallbackSites;

  const ports = [];
  const seen = new Set();
  for (const c of corridors || []) {
    const label = c.originLabel || splitCorridorName(c.name).originLabel;
    if (!c.origin || seen.has(label)) continue;
    seen.add(label);
    ports.push({ name: label, coords: [c.origin.lat, c.origin.lng], type: 'port' });
  }

  const refinerySites = refineries.map((r) => ({
    name: r.name,
    coords: [r.location.lat, r.location.lng],
    type: 'refinery',
  }));

  const reserveSites = reserveDepots.map((d) => ({
    name: d.name,
    coords: [d.location.lat, d.location.lng],
    type: 'reserve',
  }));

  return [...ports, ...refinerySites, ...reserveSites];
}
