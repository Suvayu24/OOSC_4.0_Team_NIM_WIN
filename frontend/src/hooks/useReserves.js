import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';

// Current state of India's strategic reserve pool -- GET /procurement/reserves.
// Exposes a refetch() so the Simulation tab can pull a fresh snapshot after
// running a scenario (a block/reserve-plan call doesn't itself mutate stock
// in this demo backend, but keeping a refetch seam here means it's a
// one-line change if/when it does).
export default function useReserves() {
  const [reserves, setReserves] = useState(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    setLoading(true);
    return api
      .reserves()
      .then(setReserves)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { reserves, loading, refetch };
}
