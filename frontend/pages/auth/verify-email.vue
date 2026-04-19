<template>
  <main class="auth-page">
    <NuxtLink class="auth-top-right-link" to="/">Главная</NuxtLink>

    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Подтверждение email</h1>
      <p class="auth-subtitle">Подтвердите email, чтобы повысить доверие к профилю и защитить аккаунт.</p>

      <div v-if="status === 'loading'" class="auth-alert auth-alert-info">Проверяем токен подтверждения…</div>
      <div v-if="status === 'success'" class="auth-alert auth-alert-success">{{ message }}</div>
      <div v-if="status === 'error'" class="auth-alert auth-alert-error">{{ message }}</div>
      <div v-if="status === 'idle' && message" class="auth-alert auth-alert-info">{{ message }}</div>

      <div class="auth-form">
        <button v-if="canResend" class="auth-btn auth-btn-secondary" :disabled="resendLoading" @click="resend">
          <span v-if="resendLoading" class="auth-spinner" />
          <span v-else>Отправить письмо повторно</span>
        </button>

        <button class="auth-btn auth-btn-primary" @click="goNext">
          {{ auth.isAuthenticated ? 'Перейти в dashboard' : 'Перейти ко входу' }}
        </button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth' })
useHead({ title: 'Подтверждение email — Stellalink' })

const auth = useAuthStore()
const route = useRoute()

const status = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const message = ref('')
const resendLoading = ref(false)

const token = computed(() => {
  const raw = route.query.token
  if (typeof raw !== 'string') return ''
  return raw.trim()
})

const canResend = computed(() => auth.isAuthenticated && !auth.isEmailVerified)

function extractError(err: unknown): string {
  if (!err || typeof err !== 'object') return 'Не удалось подтвердить email'
  const e = err as {
    data?: { detail?: unknown }
    message?: string
  }
  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  return e.message ?? 'Не удалось подтвердить email'
}

onMounted(async () => {
  await auth.bootstrap()

  if (token.value) {
    status.value = 'loading'
    try {
      await auth.verifyEmail(token.value)
      status.value = 'success'
      message.value = 'Email успешно подтверждён.'
    } catch (err) {
      status.value = 'error'
      message.value = extractError(err)
    }
    return
  }

  if (route.query.sent === '1') {
    message.value = 'Письмо для подтверждения отправлено. Проверьте входящие и спам.'
    status.value = 'idle'
    return
  }

  if (auth.isEmailVerified) {
    status.value = 'success'
    message.value = 'Email уже подтверждён.'
    return
  }

  status.value = 'idle'
  message.value = 'Откройте ссылку из письма для подтверждения.'
})

async function resend() {
  resendLoading.value = true
  try {
    const response = await auth.requestEmailVerification()
    status.value = 'success'
    message.value = response.detail
  } catch (err) {
    status.value = 'error'
    message.value = extractError(err)
  } finally {
    resendLoading.value = false
  }
}

async function goNext() {
  if (auth.isAuthenticated) {
    await navigateTo('/dashboard')
    return
  }
  await navigateTo('/auth/login')
}
</script>
