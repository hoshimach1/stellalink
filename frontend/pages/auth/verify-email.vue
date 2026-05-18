<template>
  <main class="auth-page">
    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Подтверждение email</h1>
      <p class="auth-subtitle">Подтвердите email, чтобы защитить аккаунт и получать важные уведомления.</p>

      <div class="auth-form">
        <button v-if="canResend" class="auth-btn auth-btn-secondary" :disabled="resendLoading" @click="resend">
          <span v-if="resendLoading" class="auth-spinner auth-spinner-dark" />
          <span v-else>Отправить письмо ещё раз</span>
        </button>

        <button class="auth-btn auth-btn-primary" @click="goNext">
          {{ auth.isAuthenticated ? 'Перейти в кабинет' : 'Перейти ко входу' }}
        </button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { extractAuthError, translateAuthMessage } from '~/utils/auth-feedback'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth' })
useHead({ title: 'Подтверждение email — Stellalink' })

const auth = useAuthStore()
const route = useRoute()
const { pushToast } = useAppToast()

const status = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const message = ref('')
const resendLoading = ref(false)

const token = computed(() => {
  const raw = route.query.token
  if (typeof raw !== 'string') return ''
  return raw.trim()
})

const canResend = computed(() => auth.isAuthenticated && !auth.isEmailVerified)

onMounted(async () => {
  await auth.bootstrap()

  if (token.value) {
    status.value = 'loading'
    try {
      await auth.verifyEmail(token.value)
      status.value = 'success'
      message.value = 'Email успешно подтверждён.'
      pushToast(message.value, 'success')
    } catch (err) {
      status.value = 'error'
      message.value = extractAuthError(err, 'Не удалось подтвердить email.')
      pushToast(message.value, 'error')
    }
    return
  }

  if (route.query.sent === '1') {
    message.value = 'Письмо с подтверждением отправлено. Проверьте входящие и папку "Спам".'
    status.value = 'idle'
    pushToast(message.value, 'info')
    return
  }

  if (auth.isEmailVerified) {
    status.value = 'success'
    message.value = 'Email уже подтверждён.'
    pushToast(message.value, 'success')
    return
  }

  status.value = 'idle'
  message.value = 'Откройте ссылку из письма, чтобы завершить подтверждение email.'
  pushToast(message.value, 'info')
})

async function resend() {
  resendLoading.value = true
  try {
    const response = await auth.requestEmailVerification()
    status.value = 'success'
    message.value = translateAuthMessage(
      response.detail,
      'Письмо с подтверждением отправлено ещё раз. Проверьте почту и папку "Спам".',
    )
    pushToast(message.value, 'success')
  } catch (err) {
    status.value = 'error'
    message.value = extractAuthError(err, 'Не удалось отправить письмо повторно.')
    pushToast(message.value, 'error')
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
