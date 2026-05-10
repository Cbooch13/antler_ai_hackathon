import { Fragment } from 'react';

function renderJson(obj: unknown, indent = 0): React.ReactNode {
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
          <Fragment key={i}>
            {pad}{'  '}{renderJson(v, indent + 1)}{i < obj.length - 1 ? <span className="punct">,</span> : null}{'\n'}
          </Fragment>
        ))}
        {pad}<span className="punct">]</span>
      </span>
    );
  }
  if (typeof obj === 'object') {
    const entries = Object.entries(obj as Record<string, unknown>);
    if (entries.length === 0) return <span className="punct">{'{}'}</span>;
    return (
      <span>
        <span className="punct">{'{'}</span>{'\n'}
        {entries.map(([k, v], i) => (
          <Fragment key={k}>
            {pad}{'  '}<span className="key">"{k}"</span><span className="punct">: </span>{renderJson(v, indent + 1)}{i < entries.length - 1 ? <span className="punct">,</span> : null}{'\n'}
          </Fragment>
        ))}
        {pad}<span className="punct">{'}'}</span>
      </span>
    );
  }
  return null;
}

export function JsonView({ data }: { data: unknown }) {
  return <pre className="json"><code>{renderJson(data)}</code></pre>;
}
