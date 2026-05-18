<template>
  <main class="auth-page">
    <section class="auth-card">
      <NuxtLink class="auth-brand" to="/">
        <img src="/images/logos/logo.png" alt="Stellalink">
        <span>Stellalink</span>
      </NuxtLink>

      <h1 class="auth-headline">Создать аккаунт</h1>
      <p class="auth-subtitle">Регистрация займёт минуту. После этого можно будет сразу перейти к настройке профиля.</p>

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

        <button class="auth-btn auth-btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="auth-spinner" />
          <span v-else>Создать аккаунт</span>
        </button>
      </form>

      <p class="auth-foot">
        Уже есть аккаунт?
        <NuxtLink class="auth-link" to="/auth/login">Войти</NuxtLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { extractAuthError } from '~/utils/auth-feedback'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Регистрация — Stellalink' })

const auth = useAuthStore()
const route = useRoute()
const { pushToast } = useAppToast()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)

const redirectPath = computed(() => {
  const raw = route.query.redirect
  if (typeof raw === 'string' && raw.startsWith('/') && !raw.startsWith('/auth/')) {
    return raw
  }
  return '/dashboard'
})

function normalizeSlug(input?: string): string {
  if (!input) return ''
  return String(input)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '')
    .slice(0, 50)
}

async function submit() {
  loading.value = true
  try {
    if (password.value !== confirmPassword.value) {
      throw new Error('Пароли не совпадают')
    }

    await auth.register(email.value, password.value)

    const slug = normalizeSlug(route.query.slug as string | undefined)
    if (slug) {
      await navigateTo({ path: '/dashboard', query: { slug } })
      return
    }

    await navigateTo(redirectPath.value)
  } catch (err) {
    pushToast(extractAuthError(err, 'Не удалось создать аккаунт.'), 'error')
  } finally {
    loading.value = false
  }
}
</script>
