/**
 * 前端埋点工具 — fire-and-forget，不阻塞主流程
 */
import API_BASE from './api';

export function track(event, payload = {}) {
  try {
    const sid = typeof window !== 'undefined' ? localStorage.getItem('quote_session_id') || '' : '';
    fetch(`${API_BASE}/api/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, payload }),
      signal: AbortSignal.timeout(2000),  // 2s timeout, don't block
    }).catch(() => {});  // silent fail
  } catch (e) {}  // never throw
}
