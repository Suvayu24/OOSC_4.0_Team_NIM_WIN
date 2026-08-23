export default function ReserveTerminalMarker({site}){return <g><path d={`M${site.x} ${site.y-8}l8 8-8 8-8-8z`} className="reserve"/><text x={site.x+10} y={site.y-10}>{site.name}</text></g>}
