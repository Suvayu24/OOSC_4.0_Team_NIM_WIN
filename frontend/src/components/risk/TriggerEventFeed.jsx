export default function TriggerEventFeed({ routes, activity = [] }) {
  const items = activity.length ? activity : routes.slice(0, 3).map((r) => ({ id: r.id, text: `${r.name}: ${r.event}` }));
  return <div className="panel feed"><p className="eyebrow">TRIGGER EVENT FEED</p>{items.slice(0, 4).map((item) => <div key={item.id}><span className="pulse"/><p>{item.text}</p></div>)}</div>;
}
