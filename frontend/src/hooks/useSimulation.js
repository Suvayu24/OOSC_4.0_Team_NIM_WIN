import { useState } from 'react';
import { api } from '../services/api';

// Drives the Simulation tab's two-step flow against the real backend:
//   1. block(req)               -> POST /procurement/scenario/block
//                                   { corridor_ids?, choke_points?, top_n?, horizon_days? }
//                                   returns { gap_bpd, blocked_corridors, alternates[], advisory, warning? }
//   2. openReservePlan(altId)   -> POST /procurement/scenario/reserve-plan for ONE alternate
//                                   from the block() result's alternates list.
// No demo-fixture fallback here on purpose: these numbers (costs, risk,
// reserve drawdown) are exactly what the backend's math produced, and
// silently swapping in a canned fixture on failure would misrepresent a
// real disruption scenario as a computed one. A failed call surfaces as
// `error` instead.
export default function useSimulation() {
  const [blockResult, setBlockResult] = useState(null);
  const [reservePlan, setReservePlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastRequest, setLastRequest] = useState(null);

  const block = async (req) => {
    setLoading(true);
    setError('');
    setReservePlan(null);
    try {
      const result = await api.blockScenario(req);
      if (result.error) throw new Error(result.error);
      setBlockResult(result);
      setLastRequest(req);
      return result;
    } catch (e) {
      setError(e.message || 'Backend unavailable -- start the FastAPI server to run a simulation.');
      setBlockResult(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const openReservePlan = async (alternateCorridorId, horizonDays) => {
    if (!lastRequest) return null;
    setPlanLoading(true);
    setError('');
    try {
      const result = await api.reservePlan({
        corridor_ids: lastRequest.corridor_ids,
        choke_points: lastRequest.choke_points,
        alternate_corridor_id: alternateCorridorId,
        horizon_days: horizonDays ?? lastRequest.horizon_days ?? 15,
      });
      if (result.error) throw new Error(result.error);
      setReservePlan(result);
      return result;
    } catch (e) {
      setError(e.message || 'Could not load the reserve plan for that route.');
      return null;
    } finally {
      setPlanLoading(false);
    }
  };

  const reset = () => {
    setBlockResult(null);
    setReservePlan(null);
    setError('');
  };

  return { blockResult, reservePlan, loading, planLoading, error, block, openReservePlan, reset };
}
