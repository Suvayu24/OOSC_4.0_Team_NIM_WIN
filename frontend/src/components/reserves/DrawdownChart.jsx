import './DrawdownChart.css';

export default function DrawdownChart({ schedule = [] }) {
  const values = schedule.length ? schedule : [0];
  const max = Math.max(...values, 0.1);
  const axisMax = Math.ceil(max * 10) / 10;

  return (
    <div className="panel draw">
      <p className="eyebrow">OPTIMAL DRAWDOWN / MB/D</p>
      <div className="draw-chart" aria-label="Optimal reserve drawdown in million barrels per day">
        <div className="draw-axis" aria-hidden="true">
          <span>{axisMax.toFixed(1)} mb/d</span>
          <span>{(axisMax / 2).toFixed(1)} mb/d</span>
          <span>0 mb/d</span>
        </div>
        <div className="draw-bars">
          {schedule.map((value, index) => {
            const pct = Math.max(4, (value / axisMax) * 100);
            const label = `${value.toFixed(2)} mb/d`;
            return (
              <div key={index} title={`Day ${index + 1}: ${label}`} aria-label={`Day ${index + 1}: ${label}`}>
                <b>{value.toFixed(2)}</b>
                <i style={{ height: `${pct}%` }} />
                <span>D{index + 1}</span>
              </div>
            );
          })}
        </div>
      </div>
      <small>Each bar shows daily reserve release in mb/d. Tapered release preserves the safety floor for longer.</small>
    </div>
  );
}
