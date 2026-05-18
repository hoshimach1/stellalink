<template>
  <main class="auth-page">
    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Новый пароль</h1>
      <p class="auth-subtitle">Придумайте новый пароль для своего аккаунта и подтвердите его.</p>

      <form class="auth-form" @submit.prevent="submit">
        <div class="auth-field">
          <label>Новый пароль</label>
          <div class="auth-input-wrap">
            <input
              v-model="password"
              class="auth-input auth-password-input"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              minlength="8"
              required
              placeholder="Минимум 8 символов"
            >
            <button type="button" class="auth-password-toggle" @click="showPassword = !showPassword">
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'" />
            </button>
          </div>
        </div>

        <div class="auth-field">
          <label>Повторите пароль</label>
          <input
            v-model="confirmPassword"
            class="auth-input"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            minlength="8"
            required
            placeholder="Повторите пароль"
          >
        </div>

        <button class="auth-btn auth-btn-primary" type="submit" :disabled="loading || !token">
          <span v-if="loading" class="auth-spinner" />
          <span v-else>Сохранить пароль</span>
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { extractAuthError } from '~/utils/auth-feedback'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Сброс пароля — Stellalink' })

const auth = useAuthStore()
const route = useRoute()
const { pushToast } = useAppToast()

const token = computed(() => {
  const raw = route.query.token
  if (typeof raw !== 'string') return ''
  return raw.trim()
})

const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)

onMounted(() => {
  if (!token.value) {
    pushToast('Ссылка для сброса пароля неполная или уже недействительна.', 'error')
  }
})

async function submit() {
  loading.value = true
  try {
    if (!token.value) {
      throw new Error('Ссылка для сброса пароля недействительна.')
    }
    if (password.value !== confirmPassword.value) {
      throw new Error('Пароли не совпадают')
    }

    await auth.resetPassword(token.value, password.value)
    pushToast('Пароль обновлён. Сейчас перенаправим вас на страницу входа.', 'success')
    setTimeout(() => {
      void navigateTo({ path: '/auth/login', query: { reset: '1' } })
    }, 900)
  } catch (err) {
    pushToast(extractAuthError(err, 'Не удалось сохранить новый пароль.'), 'error')
  } finally {
    loading.value = false
  }
}
</script>
