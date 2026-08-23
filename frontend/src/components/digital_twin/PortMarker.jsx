export default function PortMarker({site}){return <g><circle cx={site.x} cy={site.y} r="7" className="port"/><text x={site.x+10} y={site.y-10}>{site.name}</text></g>}
