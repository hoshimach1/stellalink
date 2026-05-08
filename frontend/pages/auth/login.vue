<template>
  <main class="auth-page">
    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Войти</h1>
      <p class="auth-subtitle">Войдите, чтобы управлять своим профилем, ссылками и настройками.</p>

      <div v-if="notice" class="auth-alert auth-alert-success" role="status">{{ notice }}</div>
      <div v-if="error" class="auth-alert auth-alert-error" role="alert">{{ error }}</div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="auth-field">
          <label>Email</label>
          <input
            v-model="email"
            class="auth-input"
            type="email"
            autocomplete="email"
            required
            placeholder="you@example.com"
          >
        </div>

        <div class="auth-field">
          <label>Пароль</label>
          <div class="auth-input-wrap">
            <input
              v-model="password"
              class="auth-input auth-password-input"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
              placeholder="••••••••"
            >
            <button type="button" class="auth-password-toggle" @click="showPassword = !showPassword">
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'" />
            </button>
          </div>
        </div>

        <div class="auth-row">
          <NuxtLink class="auth-link" to="/auth/forgot-password">Забыли пароль?</NuxtLink>
          <NuxtLink class="auth-link" to="/auth/register">Создать аккаунт</NuxtLink>
        </div>

        <button class="auth-btn auth-btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="auth-spinner" />
          <span v-else>Войти</span>
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { extractAuthError } from '~/utils/auth-feedback'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Вход — Stellalink' })

const auth = useAuthStore()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const notice = computed(() => {
  if (route.query.verified === '1') return 'Email успешно подтверждён. Теперь можно войти.'
  if (route.query.reset === '1') return 'Пароль обновлён. Войдите с новым паролем.'
  return ''
})

const redirectPath = computed(() => {
  const raw = route.query.redirect
  if (typeof raw === 'string' && raw.startsWith('/')) {
    return raw
  }
  return '/dashboard'
})

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    await navigateTo(redirectPath.value)
  } catch (err) {
    error.value = extractAuthError(err, 'Не удалось выполнить вход.')
  } finally {
    loading.value = false
  }
}
</script>
