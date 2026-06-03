<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="auth-overlay" @click.self="close">
        <div class="auth-modal" role="dialog" aria-modal="true">
          <button class="auth-close" aria-label="Закрыть" @click="close">
            <i class="ri-close-line" />
          </button>

          <img src="/images/logos/logo.png" alt="Stellalink" class="auth-logo">

          <div class="auth-tabs">
            <button :class="{ active: tab === 'register' }" @click="switchTab('register')">Регистрация</button>
            <button :class="{ active: tab === 'login' }" @click="switchTab('login')">Войти</button>
          </div>

          <form @submit.prevent="submit">
            <div class="auth-field">
              <label>Email</label>
              <input
                v-model="email"
                type="email"
                placeholder="you@example.com"
                autocomplete="email"
                required
              >
            </div>

            <div class="auth-field">
              <label>Пароль</label>
              <div class="pass-wrap">
                <input
                  v-model="password"
                  :type="showPass ? 'text' : 'password'"
                  placeholder="••••••••"
                  :autocomplete="tab === 'login' ? 'current-password' : 'new-password'"
                  required
                  minlength="8"
                >
                <button type="button" class="pass-toggle" @click="showPass = !showPass">
                  <i :class="showPass ? 'ri-eye-off-line' : 'ri-eye-line'" />
                </button>
              </div>
              <p v-if="tab === 'register'" class="auth-hint">Минимум 8 символов</p>
            </div>

            <div v-if="tab === 'register'" class="auth-field">
              <label>Повтори пароль</label>
              <div class="pass-wrap">
                <input
                  v-model="confirmPassword"
                  :type="showPass ? 'text' : 'password'"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  required
                  minlength="8"
                >
                <button type="button" class="pass-toggle" @click="showPass = !showPass">
                  <i :class="showPass ? 'ri-eye-off-line' : 'ri-eye-line'" />
                </button>
              </div>
            </div>

            <button type="submit" class="btn-primary auth-submit" :disabled="loading">
              <span v-if="loading" class="auth-spinner" />
              <span v-else>{{ tab === 'login' ? 'Войти' : 'Создать профиль' }}</span>
            </button>
          </form>

          <p class="auth-switch">
            <template v-if="tab === 'login'">
              Нет аккаунта?
              <button type="button" @click="switchTab('register')">Регистрация</button>
            </template>
            <template v-else>
              Уже есть аккаунт?
              <button type="button" @click="switchTab('login')">Войти</button>
            </template>
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const props = defineProps<{
  modelValue: boolean
  initialSlug?: string
  initialTab?: 'login' | 'register'
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const auth = useAuthStore()
const router = useRouter()
const { pushToast } = useAppToast()

const tab = ref<'login' | 'register'>('register')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPass = ref(false)
const loading = ref(false)

watch(() => props.modelValue, (val) => {
  if (val) {
    tab.value = props.initialTab ?? 'register'
    password.value = ''
    confirmPassword.value = ''
  }
})

function normalizeSlug(input?: string): string {
  if (!input) return ''
  return input
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '')
    .slice(0, 50)
}

function switchTab(next: 'login' | 'register') {
  tab.value = next
}

function close() {
  emit('update:modelValue', false)
}

function extractError(err: unknown): string {
  if (!err || typeof err !== 'object') return 'Что-то пошло не так'
  const e = err as {
    data?: { detail?: unknown }
    message?: string
    status?: number
    statusCode?: number
  }

  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    return first.msg ?? 'Ошибка валидации'
  }

  return e.message ?? 'Что-то пошло не так'
}

async function submit() {
  loading.value = true
  try {
    if (tab.value === 'login') {
      await auth.login(email.value, password.value)
    } else {
      if (password.value !== confirmPassword.value) {
        throw new Error('Пароли не совпадают')
      }
      await auth.register(email.value, password.value)
    }

    close()
    const slug = normalizeSlug(props.initialSlug)
    if (tab.value === 'register' && slug) {
      await router.push({ path: '/dashboard', query: { slug } })
    } else {
      await router.push('/dashboard')
    }
  } catch (err) {
    pushToast(extractError(err), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}

.auth-modal {
  position: relative;
  background: #0f0f12;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 40px 36px 32px;
  width: 100%; max-width: 420px;
  box-shadow: 0 40px 100px rgba(0, 0, 0, 0.7);
}

.auth-close {
  position: absolute; top: 14px; right: 14px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  color: #71717a; cursor: pointer; font-size: 18px;
  transition: background 0.2s, color 0.2s;
}
.auth-close:hover { background: rgba(255,255,255,0.10); color: #ececef; }

.auth-logo {
  display: block; margin: 0 auto 20px;
  width: 48px; height: 48px; object-fit: contain;
  mix-blend-mode: screen; filter: brightness(1.15);
}

.auth-tabs {
  display: flex; gap: 4px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 4px;
  margin-bottom: 28px;
}
.auth-tabs button {
  flex: 1; padding: 8px;
  background: transparent; border: none; border-radius: 7px;
  font-size: 14px; font-weight: 600; color: #71717a;
  cursor: pointer; transition: background 0.2s, color 0.2s;
  font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
}
.auth-tabs button.active {
  background: rgba(255,255,255,0.08);
  color: #ececef;
}

.auth-field {
  margin-bottom: 16px;
}
.auth-field label {
  display: block; font-size: 13px; font-weight: 600; color: #71717a;
  margin-bottom: 6px;
}
.auth-field input {
  width: 100%; padding: 11px 14px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; color: #ececef;
  font-size: 14px; font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
  outline: none; transition: border-color 0.2s, background 0.2s;
}
.auth-field input:focus {
  border-color: rgba(255,255,255,0.20);
  background: rgba(255,255,255,0.06);
}
.auth-field input::placeholder { color: #3f3f46; }

.pass-wrap { position: relative; }
.pass-wrap input { padding-right: 44px; }
.pass-toggle {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: #71717a; cursor: pointer; font-size: 17px;
  display: flex; align-items: center;
  transition: color 0.2s;
}
.pass-toggle:hover { color: #ececef; }

.auth-hint { font-size: 11px; color: #3f3f46; margin-top: 5px; }

.auth-submit {
  width: 100%; margin-top: 6px; padding: 13px;
  font-size: 15px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.auth-spinner {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.15);
  border-top-color: #09090b;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

.auth-switch {
  text-align: center; margin-top: 20px;
  font-size: 13px; color: #71717a;
}
.auth-switch button {
  background: none; border: none; color: #d4d4d8;
  font-size: 13px; font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
  cursor: pointer; text-decoration: underline;
}

.modal-enter-active,
.modal-leave-active { transition: opacity 0.22s ease; }
.modal-enter-active .auth-modal,
.modal-leave-active .auth-modal { transition: transform 0.22s ease, opacity 0.22s ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-from .auth-modal { transform: scale(0.95) translateY(12px); opacity: 0; }
.modal-leave-to .auth-modal { transform: scale(0.97) translateY(6px); opacity: 0; }
</style>
