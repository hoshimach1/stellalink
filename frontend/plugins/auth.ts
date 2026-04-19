import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  auth.init()

  try {
    await auth.bootstrap()
  } catch {
    auth.clearSession()
  }
})
