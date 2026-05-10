import { Icon } from './Icon';

interface LockedStateProps {
  title: string;
  body: string;
  action?: React.ReactNode;
}

export function LockedState({ title, body, action }: LockedStateProps) {
  return (
    <div className="locked-state">
      <div className="icon"><Icon name="lock" size={16} /></div>
      <h3>{title}</h3>
      <p>{body}</p>
      {action && <div style={{ marginTop: 6 }}>{action}</div>}
    </div>
  );
}
