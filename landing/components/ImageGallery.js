'use client';

import { useState, useEffect } from 'react';

export default function ImageGallery({ images, initialIndex = 0, onClose }) {
  const [index, setIndex] = useState(initialIndex);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') setIndex(i => Math.max(0, i - 1));
      if (e.key === 'ArrowRight') setIndex(i => Math.min(images.length - 1, i + 1));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [images.length, onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
      <div className="relative max-w-[90vw] max-h-[90vh]" onClick={e => e.stopPropagation()}>
        <img src={images[index]} alt="" className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg" />
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 text-white px-3 py-1 rounded-full text-xs">
          {index + 1} / {images.length}
        </div>
        {images.length > 1 && (
          <>
            <button onClick={() => setIndex(i => Math.max(0, i - 1))} disabled={index === 0}
              className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 hover:bg-white/40 text-white text-xl flex items-center justify-center disabled:opacity-30 transition-colors">
              ←
            </button>
            <button onClick={() => setIndex(i => Math.min(images.length - 1, i + 1))} disabled={index === images.length - 1}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 hover:bg-white/40 text-white text-xl flex items-center justify-center disabled:opacity-30 transition-colors">
              →
            </button>
          </>
        )}
        <button onClick={onClose}
          className="absolute -top-10 right-0 w-8 h-8 rounded-full bg-white/20 hover:bg-white/40 text-white flex items-center justify-center transition-colors">
          ✕
        </button>
      </div>
    </div>
  );
}
