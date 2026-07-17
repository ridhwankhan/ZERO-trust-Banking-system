import { useEffect, useRef } from 'react'
import { onDataRefresh, RefreshScope } from '../utils/refreshBus'

type Options = {
  intervalMs?: number
  scope?: RefreshScope
  enabled?: boolean
  deps?: unknown[]
}

/**
 * Poll + refetch on focus and when other parts of the app emit refresh events.
 */
export function useAutoRefresh(
  refreshFn: () => void | Promise<void>,
  { intervalMs = 5000, scope = 'all', enabled = true, deps = [] }: Options = {}
) {
  const fnRef = useRef(refreshFn)
  fnRef.current = refreshFn

  useEffect(() => {
    if (!enabled) return

    const run = () => {
      void fnRef.current()
    }

    run()

    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') run()
    }, intervalMs)

    const onFocus = () => run()
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onFocus)

    const stopBus = onDataRefresh((eventScope) => {
      if (eventScope === 'all' || eventScope === scope) run()
    })

    return () => {
      window.clearInterval(timer)
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onFocus)
      stopBus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs, scope, ...deps])
}
