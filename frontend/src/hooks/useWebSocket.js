import { useEffect } from 'react';
// Optional live-risk update seam. The UI remains usable when the backend has no websocket.
export default function useWebSocket(url, onMessage) { useEffect(() => { if (!url) return undefined; const ws = new WebSocket(url); ws.onmessage = e => onMessage?.(JSON.parse(e.data)); return () => ws.close(); }, [url, onMessage]); }
