import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

  try {
    const ok = await auth.bootstrap()
    if (ok) return
  } catch {
    auth.clearSession()
  }

  return navigateTo({
    path: '/auth/login',
    query: { redirect: to.fullPath },
  })
})
