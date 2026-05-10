interface SkelProps {
  w?: string | number;
  h?: string | number;
  style?: React.CSSProperties;
}

export function Skel({ w = '100%', h = 12, style }: SkelProps) {
  return <div className="skeleton" style={{ width: w, height: h, ...style }} />;
}
