/** Lightweight app-wide refresh signaling for live UI updates */
export const DATA_REFRESH_EVENT = 'fiducia:data-refresh'

export type RefreshScope =
  | 'all'
  | 'dashboard'
  | 'history'
  | 'security'
  | 'profile'
  | 'notifications'
  | 'transfer'

export function emitDataRefresh(scope: RefreshScope = 'all') {
  window.dispatchEvent(new CustomEvent(DATA_REFRESH_EVENT, { detail: { scope } }))
}

export function onDataRefresh(handler: (scope: RefreshScope) => void) {
  const listener = (event: Event) => {
    const scope = ((event as CustomEvent).detail?.scope as RefreshScope) || 'all'
    handler(scope)
  }
  window.addEventListener(DATA_REFRESH_EVENT, listener)
  return () => window.removeEventListener(DATA_REFRESH_EVENT, listener)
}
