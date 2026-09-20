export default function HistorySidebar({ title, items, onSelect, renderItem }) {
  return (
    <aside className="history-sidebar">
      <div className="history-heading">
        <span className="eyebrow">SAVED WORK</span>
        <h3>{title}</h3>
      </div>
      {items.length ? items.map((item) => (
        <button key={item.id} type="button" className="history-item" onClick={() => onSelect(item)}>
          {renderItem(item)}
        </button>
      )) : <p className="history-empty">Your generated reports will appear here.</p>}
    </aside>
  );
}