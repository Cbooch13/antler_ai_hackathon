import type { StatusKind } from '../types';

const STATUS_LABEL: Record<StatusKind, string> = {
  passes: 'Passes',
  warning: 'Warning',
  fail: 'Fail',
  unknown: 'Unknown',
  info: 'Info',
};

interface StatusProps {
  kind: StatusKind;
  label?: string;
}

export function Status({ kind, label }: StatusProps) {
  return (
    <span className={`badge ${kind}`}>
      <span className="d" />
      {label ?? STATUS_LABEL[kind] ?? kind}
    </span>
  );
}
