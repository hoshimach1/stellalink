import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  const ok = await auth.bootstrap()
  if (ok) {
    return navigateTo('/dashboard')
  }
})
