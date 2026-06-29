'use client';

import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';

const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    if (timers.current[id]) { clearTimeout(timers.current[id]); delete timers.current[id]; }
  }, []);

  const addToast = useCallback((message, options = {}) => {
    const id = ++toastId;
    const { type = 'info', duration = 4000, action } = options;
    setToasts(prev => [...prev, { id, message, type, action }]);
    if (duration > 0) {
      timers.current[id] = setTimeout(() => removeToast(id), duration);
    }
    return id;
  }, [removeToast]);

  const confirm = useCallback((message, onConfirm, options = {}) => {
    const id = ++toastId;
    const handleConfirm = () => {
      removeToast(id);
      if (onConfirm) onConfirm();
    };
    setToasts(prev => [...prev, {
      id, message, type: 'confirm',
      onConfirm: handleConfirm,
      onCancel: () => removeToast(id),
    }]);
    return id;
  }, [removeToast]);

  useEffect(() => {
    return () => {
      Object.values(timers.current).forEach(t => clearTimeout(t));
    };
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, confirm, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map(t => (
          <div key={t.id} className={`toast-item animate-slide-up rounded-lg shadow-lg p-3 text-sm flex items-start gap-2 ${
            t.type === 'error' ? 'bg-red-50 border border-red-200 text-red-800' :
            t.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' :
            t.type === 'confirm' ? 'bg-white border border-[var(--border)] text-[var(--text)]' :
            'bg-[var(--navy)] text-white'
          }`}>
            {t.type === 'error' && <span className="mt-0.5">⚠️</span>}
            {t.type === 'success' && <span className="mt-0.5">✅</span>}
            {t.type === 'confirm' && <span className="mt-0.5">❓</span>}
            {t.type === 'info' && <span className="mt-0.5">ℹ️</span>}
            <span className="flex-1">{t.message}</span>
            {t.type === 'confirm' ? (
              <div className="flex gap-1 shrink-0">
                <button onClick={t.onConfirm} className="px-2 py-0.5 text-xs rounded bg-[var(--navy)] text-white hover:bg-[var(--navy-light)]">确认</button>
                <button onClick={t.onCancel} className="px-2 py-0.5 text-xs rounded border border-[var(--border)] hover:bg-gray-100">取消</button>
              </div>
            ) : (
              <button onClick={() => removeToast(t.id)} className="text-current opacity-50 hover:opacity-100 ml-1">&times;</button>
            )}
          </div>
        ))}
      </div>
      <style jsx global>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-up { animation: slide-up 0.2s ease-out; }
      `}</style>
    </ToastContext.Provider>
  );
}
