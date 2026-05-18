<template>
  <main class="auth-page">
    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Восстановление пароля</h1>
      <p class="auth-subtitle">Если аккаунт с таким email существует, мы отправим письмо со ссылкой для сброса пароля.</p>

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
import { extractAuthError } from '~/utils/auth-feedback'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Восстановление пароля — Stellalink' })

const auth = useAuthStore()
const { pushToast } = useAppToast()

const email = ref('')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await auth.forgotPassword(email.value)
    pushToast('Если аккаунт с таким email существует, письмо уже отправлено. Проверьте входящие и папку "Спам".', 'success')
  } catch (err) {
    pushToast(extractAuthError(err, 'Не удалось отправить письмо для восстановления.'), 'error')
  } finally {
    loading.value = false
  }
}
</script>
