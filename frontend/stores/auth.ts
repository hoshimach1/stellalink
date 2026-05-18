import { defineStore } from 'pinia'

interface User {
  id: string
  email: string
  email_verified: boolean
  is_admin: boolean
  avatar_url: string | null
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  initialized: boolean
}

interface TokenPair {
  access_token: string
  refresh_token: string
}

interface ForgotPasswordResponse {
  detail: string
  reset_token?: string | null
}

interface RequestEmailVerificationResponse {
  detail: string
  verification_token?: string | null
}

type RequestOptions = {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

const ACCESS_COOKIE_KEY = 'sl_access'
const REFRESH_COOKIE_KEY = 'sl_refresh'
const TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
const ACCESS_COOKIE_OPTIONS = {
  sameSite: 'lax' as const,
  path: '/',
  maxAge: TOKEN_MAX_AGE_SECONDS,
}
const REFRESH_COOKIE_OPTIONS = {
  sameSite: 'lax' as const,
  path: '/',
  maxAge: TOKEN_MAX_AGE_SECONDS,
}

let refreshPromise: Promise<boolean> | null = null
let bootstrapPromise: Promise<boolean> | null = null

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase()
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    initialized: false,
  }),

  getters: {
    isAuthenticated: state => Boolean(state.accessToken),
    isEmailVerified: state => Boolean(state.user?.email_verified),
  },

  actions: {
    init(force = false) {
      const canRecoverFromClientStorage = import.meta.client
        && this.initialized
        && !force
        && !this.accessToken
        && !this.refreshToken

      if (this.initialized && !force && !canRecoverFromClientStorage) {
        return
      }

      const accessCookie = useCookie<string | null>(ACCESS_COOKIE_KEY, ACCESS_COOKIE_OPTIONS)
      const refreshCookie = useCookie<string | null>(REFRESH_COOKIE_KEY, REFRESH_COOKIE_OPTIONS)

      const localAccess = import.meta.client ? localStorage.getItem(ACCESS_COOKIE_KEY) : null
      const localRefresh = import.meta.client ? localStorage.getItem(REFRESH_COOKIE_KEY) : null

      this.accessToken = accessCookie.value ?? localAccess ?? null
      this.refreshToken = refreshCookie.value ?? localRefresh ?? null

      if (import.meta.client) {
        if (this.accessToken) {
          localStorage.setItem(ACCESS_COOKIE_KEY, this.accessToken)
          accessCookie.value = this.accessToken
        }
        if (this.refreshToken) {
          localStorage.setItem(REFRESH_COOKIE_KEY, this.refreshToken)
          refreshCookie.value = this.refreshToken
        }
      }

      this.initialized = true
    },

    _persistTokens(access: string, refresh: string) {
      this.accessToken = access
      this.refreshToken = refresh

      const accessCookie = useCookie<string | null>(ACCESS_COOKIE_KEY, ACCESS_COOKIE_OPTIONS)
      const refreshCookie = useCookie<string | null>(REFRESH_COOKIE_KEY, REFRESH_COOKIE_OPTIONS)
      accessCookie.value = access
      refreshCookie.value = refresh

      if (import.meta.client) {
        localStorage.setItem(ACCESS_COOKIE_KEY, access)
        localStorage.setItem(REFRESH_COOKIE_KEY, refresh)
      }
    },

    _clearSessionState() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null

      const accessCookie = useCookie<string | null>(ACCESS_COOKIE_KEY, ACCESS_COOKIE_OPTIONS)
      const refreshCookie = useCookie<string | null>(REFRESH_COOKIE_KEY, REFRESH_COOKIE_OPTIONS)
      accessCookie.value = null
      refreshCookie.value = null

      if (import.meta.client) {
        localStorage.removeItem(ACCESS_COOKIE_KEY)
        localStorage.removeItem(REFRESH_COOKIE_KEY)
      }
    },

    clearSession() {
      this._clearSessionState()
    },

    _isUnauthorized(err: unknown): boolean {
      if (!err || typeof err !== 'object') return false
      const maybe = err as {
        status?: number
        statusCode?: number
        response?: { status?: number }
      }
      const status = maybe.status ?? maybe.statusCode ?? maybe.response?.status
      return status === 401
    },

    async register(email: string, password: string) {
      const config = useRuntimeConfig()
      const data = await $fetch<TokenPair>(`${config.public.apiBase}/auth/register`, {
        method: 'POST',
        body: { email: normalizeEmail(email), password },
      })
      this._persistTokens(data.access_token, data.refresh_token)
      await this.fetchMe(false)
    },

    async login(email: string, password: string) {
      const config = useRuntimeConfig()
      const data = await $fetch<TokenPair>(`${config.public.apiBase}/auth/login`, {
        method: 'POST',
        body: { email: normalizeEmail(email), password },
      })
      this._persistTokens(data.access_token, data.refresh_token)
      await this.fetchMe(false)
    },

    async refresh(): Promise<boolean> {
      this.init()
      if (!this.refreshToken) {
        return false
      }

      if (refreshPromise) {
        return refreshPromise
      }

      const config = useRuntimeConfig()

      refreshPromise = (async () => {
        try {
          const data = await $fetch<TokenPair>(`${config.public.apiBase}/auth/refresh`, {
            method: 'POST',
            body: { refresh_token: this.refreshToken },
          })
          this._persistTokens(data.access_token, data.refresh_token)
          return true
        } catch {
          this._clearSessionState()
          return false
        } finally {
          refreshPromise = null
        }
      })()

      return refreshPromise
    },

    async bootstrap(force = false): Promise<boolean> {
      this.init()

      if (!force && bootstrapPromise) {
        return bootstrapPromise
      }
      if (!force && this.user && this.accessToken) {
        return true
      }
      if (!this.accessToken && !this.refreshToken) {
        this.user = null
        return false
      }

      bootstrapPromise = (async () => {
        if (this.accessToken) {
          try {
            await this.fetchMe(false)
            return true
          } catch (err) {
            if (!this._isUnauthorized(err)) {
              throw err
            }
          }
        }

        const refreshed = await this.refresh()
        if (!refreshed) {
          this._clearSessionState()
          return false
        }

        try {
          await this.fetchMe(false)
          return true
        } catch {
          this._clearSessionState()
          return false
        }
      })()

      try {
        return await bootstrapPromise
      } finally {
        bootstrapPromise = null
      }
    },

    async fetchMe(allowRefresh = true) {
      const config = useRuntimeConfig()
      if (!this.accessToken) {
        if (!allowRefresh || !(await this.refresh())) {
          this.user = null
          return
        }
      }

      try {
        this.user = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
          headers: { Authorization: `Bearer ${this.accessToken}` },
        })
      } catch (err) {
        if (allowRefresh && this._isUnauthorized(err) && await this.refresh()) {
          this.user = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
            headers: { Authorization: `Bearer ${this.accessToken}` },
          })
          return
        }
        throw err
      }
    },

    async authorizedFetch<T>(url: string, options: RequestOptions = {}, allowRefresh = true): Promise<T> {
      this.init()

      if (!this.accessToken) {
        const restored = allowRefresh && await this.refresh()
        if (!restored) {
          throw new Error('Not authenticated')
        }
      }

      const headers: Record<string, string> = {
        ...(options.headers ?? {}),
        Authorization: `Bearer ${this.accessToken}`,
      }

      try {
        return await $fetch<T>(url, { ...options, headers })
      } catch (err) {
        if (allowRefresh && this._isUnauthorized(err) && await this.refresh()) {
          return this.authorizedFetch<T>(url, options, false)
        }
        throw err
      }
    },

    async uploadAvatar(file: File) {
      const config = useRuntimeConfig()
      const form = new FormData()
      form.append('file', file)

      this.user = await this.authorizedFetch<User>(`${config.public.apiBase}/auth/avatar`, {
        method: 'POST',
        body: form,
      })
    },

    async deleteAvatar() {
      const config = useRuntimeConfig()
      await this.authorizedFetch(`${config.public.apiBase}/auth/avatar`, {
        method: 'DELETE',
      })
      if (this.user) this.user.avatar_url = null
    },

    async changePassword(oldPassword: string, newPassword: string) {
      const config = useRuntimeConfig()
      await this.authorizedFetch(`${config.public.apiBase}/auth/change-password`, {
        method: 'POST',
        body: {
          old_password: oldPassword,
          new_password: newPassword,
          refresh_token: this.refreshToken,
        },
      })
    },

    async changeEmail(email: string, currentPassword: string) {
      const config = useRuntimeConfig()
      this.user = await this.authorizedFetch<User>(`${config.public.apiBase}/auth/change-email`, {
        method: 'POST',
        body: {
          email: normalizeEmail(email),
          current_password: currentPassword,
        },
      })
    },

    async requestEmailVerification(): Promise<RequestEmailVerificationResponse> {
      const config = useRuntimeConfig()
      return this.authorizedFetch<RequestEmailVerificationResponse>(
        `${config.public.apiBase}/auth/request-email-verification`,
        { method: 'POST' },
      )
    },

    async verifyEmail(token: string): Promise<void> {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/auth/verify-email`, {
        method: 'POST',
        body: { token },
      })
      if (this.user) {
        this.user.email_verified = true
      }
    },

    async forgotPassword(email: string): Promise<ForgotPasswordResponse> {
      const config = useRuntimeConfig()
      return $fetch<ForgotPasswordResponse>(`${config.public.apiBase}/auth/forgot-password`, {
        method: 'POST',
        body: { email: normalizeEmail(email) },
      })
    },

    async resetPassword(token: string, newPassword: string): Promise<void> {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/auth/reset-password`, {
        method: 'POST',
        body: {
          token,
          new_password: newPassword,
        },
      })
    },

    async logout() {
      const config = useRuntimeConfig()
      const refreshToken = this.refreshToken
      try {
        if (refreshToken) {
          await $fetch(`${config.public.apiBase}/auth/logout`, {
            method: 'POST',
            body: { refresh_token: refreshToken },
          })
        }
      } finally {
        this.clearSession()
      }
    },
  },
})
