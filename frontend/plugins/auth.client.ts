import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  auth.init()
  if (auth.accessToken) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
    }
  }
})
