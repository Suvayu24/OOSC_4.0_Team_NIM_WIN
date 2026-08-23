export default function SimulateButton({onClick,loading}) { return <button className="primary" onClick={onClick} disabled={loading}>{loading ? 'Running model…' : 'Run simulation'}</button>; }
