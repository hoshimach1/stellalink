import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()

  try {
    const ok = await auth.bootstrap()
    if (ok) return
  } catch {
    auth.clearSession()
  }

  return navigateTo('/')
})
