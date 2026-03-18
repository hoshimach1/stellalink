import { defineStore } from 'pinia'

interface User {
  id: string
  email: string
  email_verified: boolean
  avatar_url: string | null
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },

  actions: {
    init() {
      if (import.meta.client) {
        this.accessToken = localStorage.getItem('sl_access') ?? null
        this.refreshToken = localStorage.getItem('sl_refresh') ?? null
      }
    },

    async login(email: string, password: string) {
      const config = useRuntimeConfig()
      const data = await $fetch<{ access_token: string; refresh_token: string }>(
        `${config.public.apiBase}/auth/login`,
        { method: 'POST', body: { email, password } }
      )
      this._saveTokens(data.access_token, data.refresh_token)
      await this.fetchMe()
    },

    async register(email: string, password: string) {
      const config = useRuntimeConfig()
      const data = await $fetch<{ access_token: string; refresh_token: string }>(
        `${config.public.apiBase}/auth/register`,
        { method: 'POST', body: { email, password } }
      )
      this._saveTokens(data.access_token, data.refresh_token)
      await this.fetchMe()
    },

    _saveTokens(access: string, refresh: string) {
      this.accessToken = access
      this.refreshToken = refresh
      if (import.meta.client) {
        localStorage.setItem('sl_access', access)
        localStorage.setItem('sl_refresh', refresh)
      }
    },

    async fetchMe() {
      if (!this.accessToken) return
      const config = useRuntimeConfig()
      this.user = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${this.accessToken}` },
      })
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      if (import.meta.client) {
        localStorage.removeItem('sl_access')
        localStorage.removeItem('sl_refresh')
      }
    },
  },
})
