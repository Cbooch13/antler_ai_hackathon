import { Icon } from './Icon';

interface BtnProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost';
  loading?: boolean;
  icon?: string;
  iconRight?: string | null;
  size?: 'sm' | 'lg';
  children?: React.ReactNode;
}

export function Btn({ variant = 'default', loading, disabled, icon, iconRight, size, children, ...props }: BtnProps) {
  const cls = ['btn'];
  if (variant === 'primary') cls.push('btn-primary');
  if (variant === 'ghost') cls.push('btn-ghost');
  if (size === 'sm') cls.push('btn-sm');
  if (size === 'lg') cls.push('btn-lg');
  return (
    <button className={cls.join(' ')} disabled={disabled || loading} {...props}>
      {loading ? <span className="spinner" /> : (icon && <Icon name={icon} size={13} />)}
      {children}
      {iconRight && !loading && <Icon name={iconRight} size={13} />}
    </button>
  );
}
