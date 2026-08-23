import { useCallback, useEffect, useRef, useState } from 'react';
import { corridors as fallbackCorridors } from '../data/demoData';
import { api, WS_URL } from '../services/api';
import { toUiCorridor } from '../utils/adapters';

const HISTORY_LENGTH = 8;
const ACTIVITY_LIMIT = 12;

// Live corridor list: GET /corridors on mount, then patched in place by
// /ws/risk-updates broadcasts ({type:'risk_update', corridorId, riskScore})
// so risk scores move on screen without a full refetch. Falls back to the
// bundled demo fixture if the backend can't be reached, so the UI never
// renders blank -- same "never go blank" philosophy as the backend's own
// advisory fallback.
//
// Also maintains two session-only, genuinely-live derived views (no
// fabricated numbers): a rolling per-corridor risk-reading history for the
// trend chart, and a capped activity log of what's actually happened this
// session, for the trigger-event feed.
export default function useRiskData() {
  const [data, setData] = useState(fallbackCorridors);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState('demo');
  const [wsConnected, setWsConnected] = useState(false);
  const [history, setHistory] = useState({});
  const [activity, setActivity] = useState([]);
  const wsRef = useRef(null);
  const dataRef = useRef(fallbackCorridors);

  const logActivity = useCallback((text) => {
    setActivity((current) => [{ id: `${Date.now()}-${Math.random()}`, text, ts: new Date() }, ...current].slice(0, ACTIVITY_LIMIT));
  }, []);

  useEffect(() => {
    let active = true;
    api
      .corridors()
      .then((rows) => {
        if (!active || !Array.isArray(rows) || !rows.length) return;
        const ui = rows.map(toUiCorridor);
        setData(ui);
        dataRef.current = ui;
        setSource('live');
        setHistory(Object.fromEntries(ui.map((c) => [c.id, [c.risk]])));
      })
      .catch(() => {})
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (source !== 'live') return undefined;
    let ws;
    try {
      ws = new WebSocket(WS_URL);
    } catch {
      return undefined;
    }
    wsRef.current = ws;
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (evt) => {
      let msg;
      try {
        msg = JSON.parse(evt.data);
      } catch {
        return;
      }
      if (msg.type !== 'risk_update') return;
      const fraction = Math.max(0, Math.min(1, msg.riskScore / 100));
      setData((current) => {
        const next = current.map((c) =>
          c.id === msg.corridorId ? { ...c, risk_score: msg.riskScore, risk: fraction } : c
        );
        dataRef.current = next;
        return next;
      });
      setHistory((current) => {
        const prev = current[msg.corridorId] || [];
        return { ...current, [msg.corridorId]: [...prev, fraction].slice(-HISTORY_LENGTH) };
      });
      const corridor = dataRef.current.find((c) => c.id === msg.corridorId);
      if (corridor) logActivity(`${corridor.name}: risk updated to ${msg.riskScore}%`);
    };
    return () => ws.close();
  }, [source, logActivity]);

  return { data, loading, source, wsConnected, history, activity, logActivity };
}
