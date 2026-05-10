interface BannerProps {
  kind?: 'warning' | 'info' | 'fail' | 'neutral';
  title: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export function Banner({ kind = 'warning', title, children, action, icon }: BannerProps) {
  const defaultIcon = kind === 'warning' ? '!' : kind === 'info' ? 'i' : kind === 'fail' ? '×' : '·';
  return (
    <div className={`banner ${kind}`}>
      <div className="banner-icon">{icon ?? defaultIcon}</div>
      <div>
        <div className="banner-title">{title}</div>
        {children && <div className="banner-body">{children}</div>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
