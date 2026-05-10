import { useState, useRef } from 'react';
import type { VideoClip } from '../types';

interface VideoPlayerProps {
  clips: VideoClip[];
  posterUrl?: string;
}

export function VideoPlayer({ clips, posterUrl }: VideoPlayerProps) {
  const [current, setCurrent] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  if (!clips.length) return null;

  const clip = clips[current];
  const hasPrev = current > 0;
  const hasNext = current < clips.length - 1;

  const goTo = (idx: number) => {
    setCurrent(idx);
    setTimeout(() => videoRef.current?.play(), 50);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ position: 'relative', aspectRatio: '16/9', background: '#000', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
        <video
          ref={videoRef}
          key={clip.url}
          src={clip.url}
          poster={current === 0 ? posterUrl : undefined}
          controls
          autoPlay
          style={{ width: '100%', height: '100%', display: 'block' }}
          preload="auto"
          onEnded={() => { if (hasNext) goTo(current + 1); }}
        />
        <div style={{
          position: 'absolute', bottom: 48, left: 0, right: 0,
          textAlign: 'center', pointerEvents: 'none',
        }}>
          <span style={{
            fontSize: 11, fontFamily: 'var(--font-mono)',
            background: 'rgba(0,0,0,0.55)', color: '#fff',
            padding: '3px 10px', borderRadius: 4,
          }}>{clip.label}</span>
        </div>
      </div>

      {/* Clip strip */}
      <div style={{ display: 'flex', gap: 6, overflowX: 'auto' }}>
        {clips.map((c, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            style={{
              flexShrink: 0, padding: '4px 10px', fontSize: 11,
              fontFamily: 'var(--font-mono)', borderRadius: 4, cursor: 'pointer',
              border: '1px solid var(--border)',
              background: i === current ? 'var(--teal-soft)' : 'var(--bg-alt)',
              color: i === current ? 'var(--text)' : 'var(--text-3)',
              fontWeight: i === current ? 600 : 400,
            }}
          >
            {i + 1}. {c.label.replace('Interior — ', '').replace('Exterior — ', '')}
          </button>
        ))}
      </div>
    </div>
  );
}
