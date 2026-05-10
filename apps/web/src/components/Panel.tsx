interface PanelProps {
  title?: string;
  sub?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  foot?: React.ReactNode;
  flush?: boolean;
  badge?: React.ReactNode;
}

export function Panel({ title, sub, action, children, foot, flush, badge }: PanelProps) {
  return (
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
}
