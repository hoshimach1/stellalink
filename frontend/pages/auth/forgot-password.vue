<template>
  <main class="auth-page">
    <NuxtLink class="auth-top-right-link" to="/auth/login">Вход</NuxtLink>

    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Восстановление пароля</h1>
      <p class="auth-subtitle">Отправим ссылку для сброса пароля на указанный email.</p>

      <div v-if="error" class="auth-alert auth-alert-error">{{ error }}</div>
      <div v-if="success" class="auth-alert auth-alert-success">{{ success }}</div>
      <div v-if="debugResetLink" class="auth-alert auth-alert-info">
        Debug reset link:
        <NuxtLink :to="debugResetLink" class="auth-link">{{ debugResetLink }}</NuxtLink>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="auth-field">
          <label>Email</label>
          <input v-model="email" class="auth-input" type="email" autocomplete="email" required placeholder="you@example.com">
        </div>

        <button class="auth-btn auth-btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="auth-spinner" />
          <span v-else>Отправить ссылку</span>
        </button>
      </form>

      <p class="auth-foot">
        Вспомнили пароль?
        <NuxtLink class="auth-link" to="/auth/login">Вернуться ко входу</NuxtLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Восстановление пароля — Stellalink' })

const auth = useAuthStore()

const email = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const debugResetLink = ref('')

function extractError(err: unknown): string {
  if (!err || typeof err !== 'object') return 'Не удалось отправить ссылку'
  const e = err as {
    data?: { detail?: unknown }
    message?: string
  }
  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (first?.msg) return first.msg
  }
  return e.message ?? 'Не удалось отправить ссылку'
}

async function submit() {
  loading.value = true
  error.value = ''
  success.value = ''
  debugResetLink.value = ''
  try {
    const response = await auth.forgotPassword(email.value)
    success.value = response.detail
    if (response.reset_token) {
      debugResetLink.value = `/auth/reset-password?token=${encodeURIComponent(response.reset_token)}`
    }
  } catch (err) {
    error.value = extractError(err)
  } finally {
    loading.value = false
  }
}
</script>
