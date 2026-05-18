export type AppToastTone = 'success' | 'error' | 'info' | 'warning'

export interface AppToast {
  id: number
  message: string
  tone: AppToastTone
  title: string
  timeout: number
}

type AppToastOptions = {
  title?: string
  timeout?: number
}

const DEFAULT_TIMEOUT = 4600
const TOAST_LIMIT = 4
let nextToastId = 0
const timers = new Map<number, ReturnType<typeof setTimeout>>()

const DEFAULT_TITLES: Record<AppToastTone, string> = {
  success: 'Готово',
  error: 'Ошибка',
  info: 'Уведомление',
  warning: 'Внимание',
}

export function useAppToast() {
  const toasts = useState<AppToast[]>('app-toasts', () => [])

  function clearTimer(id: number) {
    const timer = timers.get(id)
    if (!timer) return
    clearTimeout(timer)
    timers.delete(id)
  }

  function removeToast(id: number) {
    clearTimer(id)
    toasts.value = toasts.value.filter(toast => toast.id !== id)
  }

  function pushToast(message: string, tone: AppToastTone = 'info', options: AppToastOptions = {}) {
    const trimmedMessage = message.trim()
    if (!trimmedMessage) return null

    const toast: AppToast = {
      id: ++nextToastId,
      message: trimmedMessage,
      tone,
      title: options.title ?? DEFAULT_TITLES[tone],
      timeout: options.timeout ?? DEFAULT_TIMEOUT,
    }

    const visibleToasts = [...toasts.value, toast]
    const overflow = Math.max(visibleToasts.length - TOAST_LIMIT, 0)
    for (const removedToast of visibleToasts.slice(0, overflow)) {
      clearTimer(removedToast.id)
    }
    toasts.value = visibleToasts.slice(overflow)

    if (import.meta.client && toast.timeout > 0) {
      timers.set(toast.id, setTimeout(() => removeToast(toast.id), toast.timeout))
    }

    return toast.id
  }

  function clearToasts() {
    for (const toast of toasts.value) {
      clearTimer(toast.id)
    }
    toasts.value = []
  }

  return {
    clearToasts,
    pushToast,
    removeToast,
    toasts,
  }
}
