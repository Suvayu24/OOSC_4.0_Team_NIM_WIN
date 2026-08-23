export default function RefineryMarker({site}){return <g><rect x={site.x-6} y={site.y-6} width="12" height="12" className="refinery"/><text x={site.x+10} y={site.y-10}>{site.name}</text></g>}
