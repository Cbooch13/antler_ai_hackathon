// Shared components for ABF prototype.
// All exported to window at the bottom for cross-script access.

const { useState, useEffect, useMemo, useRef, useCallback } = React;

// ---------- Icons (minimal stroke set) ----------
const Icon = ({ name, size = 14, stroke = 1.5 }) => {
  const s = size;
  const props = { width: s, height: s, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: stroke, strokeLinecap: 'round', strokeLinejoin: 'round' };
  switch (name) {
    case 'check':       return <svg {...props}><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>;
    case 'x':           return <svg {...props}><path d="M6 6l12 12M18 6L6 18"/></svg>;
    case 'lock':        return <svg {...props}><rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>;
    case 'arrow-right': return <svg {...props}><path d="M5 12h14M13 6l6 6-6 6"/></svg>;
    case 'chevron-r':   return <svg {...props}><path d="M9 6l6 6-6 6"/></svg>;
    case 'chevron-d':   return <svg {...props}><path d="M6 9l6 6 6-6"/></svg>;
    case 'chevron-u':   return <svg {...props}><path d="M6 15l6-6 6 6"/></svg>;
    case 'plus':        return <svg {...props}><path d="M12 5v14M5 12h14"/></svg>;
    case 'minus':       return <svg {...props}><path d="M5 12h14"/></svg>;
    case 'save':        return <svg {...props}><path d="M5 5h11l3 3v11H5z"/><path d="M8 5v5h7V5M8 19v-5h8v5"/></svg>;
    case 'export':      return <svg {...props}><path d="M12 15V4M7 9l5-5 5 5"/><path d="M5 15v4h14v-4"/></svg>;
    case 'share':       return <svg {...props}><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8 11l8-4M8 13l8 4"/></svg>;
    case 'doc':         return <svg {...props}><path d="M7 4h7l4 4v12H7z"/><path d="M14 4v4h4"/></svg>;
    case 'map':         return <svg {...props}><path d="M9 4l-5 2v14l5-2 6 2 5-2V4l-5 2z"/><path d="M9 4v16M15 6v16"/></svg>;
    case 'home':        return <svg {...props}><path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/></svg>;
    case 'list':        return <svg {...props}><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/></svg>;
    case 'pin':         return <svg {...props}><path d="M12 21s-7-7-7-12a7 7 0 0 1 14 0c0 5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/></svg>;
    case 'shield':      return <svg {...props}><path d="M12 3l8 3v5c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6z"/></svg>;
    case 'plan':        return <svg {...props}><rect x="3.5" y="3.5" width="17" height="17" rx="1"/><path d="M3.5 11h10v9.5M13.5 3.5v8h7"/></svg>;
    case 'pkg':         return <svg {...props}><path d="M3.5 7.5L12 4l8.5 3.5v9L12 20l-8.5-3.5z"/><path d="M3.5 7.5L12 11l8.5-3.5M12 11v9"/></svg>;
    case 'phone':       return <svg {...props}><rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/></svg>;
    case 'monitor':     return <svg {...props}><rect x="3" y="4" width="18" height="13" rx="1.5"/><path d="M9 21h6M12 17v4"/></svg>;
    case 'help':        return <svg {...props}><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-2.5 1.8-2.5 3.5"/><circle cx="12" cy="17" r="0.4" fill="currentColor"/></svg>;
    case 'info':        return <svg {...props}><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><circle cx="12" cy="8" r="0.4" fill="currentColor"/></svg>;
    case 'warn':        return <svg {...props}><path d="M12 3l10 17H2z"/><path d="M12 10v5"/><circle cx="12" cy="17.5" r="0.4" fill="currentColor"/></svg>;
    case 'send':        return <svg {...props}><path d="M5 12l15-8-5 17-3.5-7z"/></svg>;
    case 'refresh':     return <svg {...props}><path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/></svg>;
    case 'menu':        return <svg {...props}><path d="M4 7h16M4 12h16M4 17h16"/></svg>;
    case 'back':        return <svg {...props}><path d="M19 12H5M11 6l-6 6 6 6"/></svg>;
    case 'circle':      return <svg {...props}><circle cx="12" cy="12" r="9"/></svg>;
    case 'tree':        return <svg {...props}><path d="M12 3v18M7 8l5-5 5 5M5 13l7-7 7 7M3 18l9-9 9 9"/></svg>;
    case 'water':       return <svg {...props}><path d="M12 3c4 5 7 9 7 12a7 7 0 0 1-14 0c0-3 3-7 7-12z"/></svg>;
    case 'tag':         return <svg {...props}><path d="M3 13V4h9l9 9-9 9z"/><circle cx="8" cy="8" r="1.2"/></svg>;
    default:            return <svg {...props}><circle cx="12" cy="12" r="3"/></svg>;
  }
};

// ---------- Spinner button ----------
const Btn = ({ variant = 'default', loading, disabled, icon, iconRight, children, size, ...props }) => {
  const cls = ['btn'];
  if (variant === 'primary') cls.push('btn-primary');
  if (variant === 'ghost') cls.push('btn-ghost');
  if (size === 'sm') cls.push('btn-sm');
  if (size === 'lg') cls.push('btn-lg');
  return (
    <button className={cls.join(' ')} disabled={disabled || loading} {...props}>
      {loading ? <span className="spinner"/> : (icon && <Icon name={icon} size={13}/>)}
      {children}
      {iconRight && !loading && <Icon name={iconRight} size={13}/>}
    </button>
  );
};

// ---------- Status badge ----------
const STATUS_LABEL = { passes: 'Passes', warning: 'Warning', fail: 'Fail', unknown: 'Unknown', info: 'Info' };
const Status = ({ kind, label }) => (
  <span className={`badge ${kind}`}>
    <span className="d" />
    {label || STATUS_LABEL[kind] || kind}
  </span>
);

// ---------- Banner ----------
const Banner = ({ kind = 'warning', title, children, action, icon }) => (
  <div className={`banner ${kind}`}>
    <div className="banner-icon">{icon || (kind === 'warning' ? '!' : kind === 'info' ? 'i' : kind === 'fail' ? '×' : '·')}</div>
    <div>
      <div className="banner-title">{title}</div>
      {children && <div className="banner-body">{children}</div>}
    </div>
    {action && <div>{action}</div>}
  </div>
);

// ---------- Panel ----------
const Panel = ({ title, sub, action, children, foot, flush, badge }) => (
  <div className="panel">
    {(title || action) && (
      <div className="panel-h">
        {title && <h3>{title}</h3>}
        {badge}
        {sub && <span className="sub">{sub}</span>}
        <div className="panel-h-spacer" />
        {action}
      </div>
    )}
    <div className={'panel-body' + (flush ? ' flush' : '')}>{children}</div>
    {foot && <div className="panel-foot">{foot}</div>}
  </div>
);

// ---------- JSON-like viewer ----------
function renderJson(obj, indent = 0) {
  const pad = '  '.repeat(indent);
  if (obj === null) return <span className="num">null</span>;
  if (typeof obj === 'string') return <span className="str">"{obj}"</span>;
  if (typeof obj === 'number' || typeof obj === 'boolean') return <span className="num">{String(obj)}</span>;
  if (Array.isArray(obj)) {
    if (obj.length === 0) return <span className="punct">[]</span>;
    return (
      <span className="arr">
        <span className="punct">[</span>{'\n'}
        {obj.map((v, i) => (
          <React.Fragment key={i}>
            {pad}{'  '}{renderJson(v, indent + 1)}{i < obj.length - 1 ? <span className="punct">,</span> : null}{'\n'}
          </React.Fragment>
        ))}
        {pad}<span className="punct">]</span>
      </span>
    );
  }
  if (typeof obj === 'object') {
    const entries = Object.entries(obj);
    if (entries.length === 0) return <span className="punct">{'{}'}</span>;
    return (
      <span>
        <span className="punct">{'{'}</span>{'\n'}
        {entries.map(([k, v], i) => (
          <React.Fragment key={k}>
            {pad}{'  '}<span className="key">"{k}"</span><span className="punct">: </span>{renderJson(v, indent + 1)}{i < entries.length - 1 ? <span className="punct">,</span> : null}{'\n'}
          </React.Fragment>
        ))}
        {pad}<span className="punct">{'}'}</span>
      </span>
    );
  }
  return null;
}
const JsonView = ({ data }) => <pre className="json"><code>{renderJson(data)}</code></pre>;

// ---------- Locked state ----------
const LockedState = ({ title, body, action }) => (
  <div className="locked-state">
    <div className="icon"><Icon name="lock" size={16}/></div>
    <h3>{title}</h3>
    <p>{body}</p>
    {action && <div style={{ marginTop: 6 }}>{action}</div>}
  </div>
);

// ---------- Loading skeleton ----------
const Skel = ({ w = '100%', h = 12, style }) => <div className="skeleton" style={{ width: w, height: h, ...style }} />;

// ---------- Number formatting ----------
const fmt = {
  money: (n) => '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 }),
  num: (n) => n.toLocaleString('en-US'),
};

Object.assign(window, {
  Icon, Btn, Status, Banner, Panel, JsonView, LockedState, Skel, fmt, renderJson,
});
