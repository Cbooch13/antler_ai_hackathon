import { useState } from 'react';
import type { GeneratedImage } from '../types';

interface ImageGalleryProps {
  images: GeneratedImage[];
}

export function ImageGallery({ images }: ImageGalleryProps) {
  const [lightbox, setLightbox] = useState<GeneratedImage | null>(null);

  return (
    <>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 8,
      }}>
        {images.map((img, i) => (
          <div
            key={i}
            style={{ position: 'relative', cursor: 'zoom-in', borderRadius: 6, overflow: 'hidden', border: '1px solid var(--border)', aspectRatio: '16/9', background: 'var(--bg-alt)' }}
            onClick={() => setLightbox(img)}
          >
            <img
              src={img.url}
              alt={img.label}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            />
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              background: 'linear-gradient(transparent, rgba(0,0,0,0.55))',
              padding: '16px 8px 6px',
              fontSize: 10.5, color: '#fff', fontFamily: 'var(--font-mono)',
              letterSpacing: '0.01em',
            }}>
              {img.label}
            </div>
          </div>
        ))}
      </div>

      {lightbox && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 900,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'zoom-out',
          }}
          onClick={() => setLightbox(null)}
        >
          <div style={{ maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
            <img
              src={lightbox.url}
              alt={lightbox.label}
              style={{ maxWidth: '90vw', maxHeight: '80vh', objectFit: 'contain', borderRadius: 8, display: 'block' }}
            />
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11, marginTop: 8, fontFamily: 'var(--font-mono)', textAlign: 'center' }}>
              {lightbox.label}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
