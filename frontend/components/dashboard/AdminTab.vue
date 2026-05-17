<template>
  <div class="admin-shell">
    <section class="admin-summary">
      <div>
        <p class="admin-kicker">Администрирование</p>
        <h2>Почта и auth-ссылки</h2>
        <span>SMTP, адрес фронтенда и время жизни ссылок подтверждения.</span>
      </div>
      <button class="outline-btn" type="button" :disabled="loading || apiLoading" @click="loadAllSettings">
        <span v-if="loading || apiLoading" class="admin-spinner dark" />
        <template v-else>
          <i class="ri-refresh-line" />
          <span>Обновить</span>
        </template>
      </button>
    </section>

    <section class="admin-grid">
      <article class="admin-card admin-card-wide">
        <div class="card-head">
          <span class="card-icon"><i class="ri-mail-settings-line" /></span>
          <div>
            <h3>SMTP</h3>
            <p>{{ smtpStatus }}</p>
          </div>
        </div>

        <form class="admin-form" @submit.prevent="saveSettings">
          <label class="admin-toggle">
            <input v-model="form.enabled" type="checkbox">
            <span>Включить отправку писем</span>
          </label>

          <div class="admin-row">
            <label class="admin-field">
              <span>SMTP host</span>
              <input v-model="form.host" type="text" placeholder="smtp.example.com" autocomplete="off">
            </label>

            <label class="admin-field small">
              <span>Порт</span>
              <input v-model.number="form.port" type="number" min="1" max="65535">
            </label>
          </div>

          <div class="admin-row">
            <label class="admin-field">
              <span>Шифрование</span>
              <select v-model="encryptionMode">
                <option value="starttls">STARTTLS</option>
                <option value="ssl">SSL/TLS</option>
                <option value="plain">Без TLS</option>
              </select>
            </label>

            <label class="admin-field small">
              <span>Timeout, сек</span>
              <input v-model.number="form.timeout_seconds" type="number" min="1" max="120">
            </label>
          </div>

          <div class="admin-row">
            <label class="admin-field">
              <span>Логин</span>
              <input v-model="form.username" type="text" autocomplete="username" placeholder="smtp-user">
            </label>

            <label class="admin-field">
              <span>Пароль</span>
              <input v-model="smtpPassword" type="password" autocomplete="new-password" :placeholder="passwordPlaceholder">
            </label>
          </div>

          <div class="admin-row">
            <label class="admin-field">
              <span>From email</span>
              <input v-model="form.from_email" type="email" placeholder="no-reply@stellalink.app">
            </label>

            <label class="admin-field">
              <span>From name</span>
              <input v-model="form.from_name" type="text" placeholder="Stellalink">
            </label>
          </div>

          <div v-if="saveNotice" class="admin-note" :class="saveNoticeTone">{{ saveNotice }}</div>

          <button class="filled-btn" type="submit" :disabled="saving">
            <span v-if="saving" class="admin-spinner" />
            <span v-else>Сохранить настройки</span>
          </button>
        </form>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-links-line" /></span>
          <div>
            <h3>Ссылки</h3>
            <p>База для verify-email и reset-password.</p>
          </div>
        </div>

        <form class="admin-form" @submit.prevent="saveSettings">
          <label class="admin-field">
            <span>Frontend URL</span>
            <input v-model="form.frontend_base_url" type="url" placeholder="https://stellalink.app">
          </label>

          <label class="admin-field">
            <span>Подтверждение email, сек</span>
            <input v-model.number="form.email_verification_ttl_seconds" type="number" min="300" max="604800">
          </label>

          <label class="admin-field">
            <span>Сброс пароля, сек</span>
            <input v-model.number="form.password_reset_ttl_seconds" type="number" min="300" max="86400">
          </label>
        </form>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-key-2-line" /></span>
          <div>
            <h3>Steam и FACEIT API</h3>
            <p>{{ apiStatus }}</p>
          </div>
        </div>

        <form class="admin-form" @submit.prevent="saveApiSettings">
          <label class="admin-field">
            <span>Steam Web API key</span>
            <input v-model="apiSteamKey" type="password" autocomplete="new-password" :placeholder="steamKeyPlaceholder">
          </label>

          <label class="admin-field">
            <span>FACEIT Data API key</span>
            <input v-model="apiFaceitKey" type="password" autocomplete="new-password" :placeholder="faceitKeyPlaceholder">
          </label>

          <div class="admin-row">
            <label class="admin-field small">
              <span>Inventory AppID</span>
              <input v-model.number="apiForm.steam_inventory_app_id" type="number" min="1">
            </label>

            <label class="admin-field small">
              <span>Context ID</span>
              <input v-model="apiForm.steam_inventory_context_id" type="text" placeholder="2">
            </label>
          </div>

          <div class="admin-note">
            Steam не отдаёт цены предметов через обычный Web API. Для честного “самого дорогого предмета” нужен отдельный источник цен или publisher key с Economy permissions.
          </div>

          <div v-if="apiNotice" class="admin-note" :class="apiNoticeTone">{{ apiNotice }}</div>

          <button class="outline-btn" type="submit" :disabled="apiSaving">
            <span v-if="apiSaving" class="admin-spinner dark" />
            <template v-else>
              <i class="ri-save-3-line" />
              <span>Сохранить ключи</span>
            </template>
          </button>
        </form>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-send-plane-line" /></span>
          <div>
            <h3>Тест</h3>
            <p>Проверка текущей конфигурации.</p>
          </div>
        </div>

        <form class="admin-form" @submit.prevent="sendTestEmail">
          <label class="admin-field">
            <span>Получатель</span>
            <input v-model="testEmail" type="email" :placeholder="auth.user?.email || 'admin@example.com'">
          </label>

          <div v-if="testNotice" class="admin-note" :class="testNoticeTone">{{ testNotice }}</div>

          <button class="outline-btn" type="submit" :disabled="testing">
            <span v-if="testing" class="admin-spinner dark" />
            <template v-else>
              <i class="ri-mail-send-line" />
              <span>Отправить тест</span>
            </template>
          </button>
        </form>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { extractAuthError } from '~/utils/auth-feedback'

interface SmtpSettings {
  enabled: boolean
  host: string | null
  port: number
  username: string | null
  password_set: boolean
  use_ssl: boolean
  use_tls: boolean
  force_ipv4: boolean
  timeout_seconds: number
  from_email: string
  from_name: string
  frontend_base_url: string
  email_verification_ttl_seconds: number
  password_reset_ttl_seconds: number
}

interface ApiSettings {
  steam_api_key_set: boolean
  steam_api_key_hint: string | null
  faceit_api_key_set: boolean
  faceit_api_key_hint: string | null
  steam_inventory_app_id: number
  steam_inventory_context_id: string
  steam_inventory_price_source: string
}

const auth = useAuthStore()
const config = useRuntimeConfig()

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const apiLoading = ref(false)
const apiSaving = ref(false)
const passwordSet = ref(false)
const steamKeySet = ref(false)
const faceitKeySet = ref(false)
const steamKeyHint = ref('(****)')
const faceitKeyHint = ref('(****)')
const smtpPassword = ref('')
const apiSteamKey = ref('')
const apiFaceitKey = ref('')
const testEmail = ref('')
const saveNotice = ref('')
const testNotice = ref('')
const apiNotice = ref('')
const saveNoticeTone = ref<'success' | 'error'>('success')
const testNoticeTone = ref<'success' | 'error'>('success')
const apiNoticeTone = ref<'success' | 'error'>('success')

const form = reactive({
  enabled: true,
  host: '',
  port: 587,
  username: '',
  use_ssl: false,
  use_tls: true,
  timeout_seconds: 15,
  from_email: 'no-reply@stellalink.app',
  from_name: 'Stellalink',
  frontend_base_url: 'http://localhost:3000',
  email_verification_ttl_seconds: 86400,
  password_reset_ttl_seconds: 3600,
})

const apiForm = reactive({
  steam_inventory_app_id: 730,
  steam_inventory_context_id: '2',
})

const encryptionMode = computed({
  get() {
    if (form.use_ssl) return 'ssl'
    if (form.use_tls) return 'starttls'
    return 'plain'
  },
  set(value: string) {
    form.use_ssl = value === 'ssl'
    form.use_tls = value === 'starttls'
  },
})

const passwordPlaceholder = computed(() => passwordSet.value ? 'Пароль сохранен' : 'SMTP пароль')
const steamKeyPlaceholder = computed(() => steamKeySet.value ? `Сохранен ${steamKeyHint.value}` : 'Введите ключ Steam')
const faceitKeyPlaceholder = computed(() => faceitKeySet.value ? `Сохранен ${faceitKeyHint.value}` : 'Введите ключ FACEIT')
const smtpStatus = computed(() => {
  if (!form.enabled) return 'Письма выключены, ссылки будут только в логах.'
  if (!form.host) return 'Host не задан, письма будут записываться в лог backend.'
  return `${form.host}:${form.port}`
})
const apiStatus = computed(() => {
  if (steamKeySet.value && faceitKeySet.value) return 'Steam подключен, FACEIT будет подтягиваться по Steam ID.'
  if (steamKeySet.value) return 'Steam подключен. Добавьте FACEIT key для автоподтягивания ELO и уровня.'
  return 'Добавьте Steam key, чтобы валидировать Steam ID и получать профильные данные.'
})
onMounted(() => {
  void loadAllSettings()
})

function applySettings(data: SmtpSettings) {
  form.enabled = data.enabled
  form.host = data.host ?? ''
  form.port = data.port
  form.username = data.username ?? ''
  form.use_ssl = data.use_ssl
  form.use_tls = data.use_tls
  form.timeout_seconds = data.timeout_seconds
  form.from_email = data.from_email
  form.from_name = data.from_name
  form.frontend_base_url = data.frontend_base_url
  form.email_verification_ttl_seconds = data.email_verification_ttl_seconds
  form.password_reset_ttl_seconds = data.password_reset_ttl_seconds
  passwordSet.value = data.password_set
  smtpPassword.value = ''
}

function applyApiSettings(data: ApiSettings) {
  steamKeySet.value = data.steam_api_key_set
  faceitKeySet.value = data.faceit_api_key_set
  apiForm.steam_inventory_app_id = data.steam_inventory_app_id
  apiForm.steam_inventory_context_id = data.steam_inventory_context_id
  apiSteamKey.value = ''
  apiFaceitKey.value = ''
  steamKeyHint.value = data.steam_api_key_hint ?? '(****)'
  faceitKeyHint.value = data.faceit_api_key_hint ?? '(****)'
}

async function loadAllSettings() {
  await Promise.all([loadSettings(), loadApiSettings()])
}

async function loadSettings() {
  loading.value = true
  saveNotice.value = ''
  try {
    const data = await auth.authorizedFetch<SmtpSettings>(`${config.public.apiBase}/admin/smtp-settings`)
    applySettings(data)
  } catch (error) {
    saveNoticeTone.value = 'error'
    saveNotice.value = extractAuthError(error, 'Не удалось загрузить настройки.')
  } finally {
    loading.value = false
  }
}

async function loadApiSettings() {
  apiLoading.value = true
  apiNotice.value = ''
  try {
    const data = await auth.authorizedFetch<ApiSettings>(`${config.public.apiBase}/admin/api-settings`)
    applyApiSettings(data)
  } catch (error) {
    apiNoticeTone.value = 'error'
    apiNotice.value = extractAuthError(error, 'Не удалось загрузить API-настройки.')
  } finally {
    apiLoading.value = false
  }
}

async function saveApiSettings() {
  apiSaving.value = true
  apiNotice.value = ''
  try {
    const body: Record<string, unknown> = {
      steam_inventory_app_id: apiForm.steam_inventory_app_id,
      steam_inventory_context_id: apiForm.steam_inventory_context_id.trim() || '2',
    }
    if (apiSteamKey.value.trim()) {
      body.steam_api_key = apiSteamKey.value.trim()
    }
    if (apiFaceitKey.value.trim()) {
      body.faceit_api_key = apiFaceitKey.value.trim()
    }

    const data = await auth.authorizedFetch<ApiSettings>(`${config.public.apiBase}/admin/api-settings`, {
      method: 'PUT',
      body,
    })
    applyApiSettings(data)
    apiNoticeTone.value = 'success'
    apiNotice.value = 'API-настройки сохранены.'
  } catch (error) {
    apiNoticeTone.value = 'error'
    apiNotice.value = extractAuthError(error, 'Не удалось сохранить API-настройки.')
  } finally {
    apiSaving.value = false
  }
}

async function saveSettings() {
  saving.value = true
  saveNotice.value = ''
  try {
    const body: Record<string, unknown> = {
      ...form,
      host: form.host.trim() || null,
      username: form.username.trim() || null,
      frontend_base_url: form.frontend_base_url.trim(),
    }
    if (smtpPassword.value) {
      body.password = smtpPassword.value
    }

    const data = await auth.authorizedFetch<SmtpSettings>(`${config.public.apiBase}/admin/smtp-settings`, {
      method: 'PUT',
      body,
    })
    applySettings(data)
    saveNoticeTone.value = 'success'
    saveNotice.value = 'Настройки сохранены.'
  } catch (error) {
    saveNoticeTone.value = 'error'
    saveNotice.value = extractAuthError(error, 'Не удалось сохранить настройки.')
  } finally {
    saving.value = false
  }
}

async function sendTestEmail() {
  testing.value = true
  testNotice.value = ''
  try {
    const response = await auth.authorizedFetch<{ detail: string }>(`${config.public.apiBase}/admin/smtp-settings/test`, {
      method: 'POST',
      body: { to_email: testEmail.value.trim() || null },
    })
    testNoticeTone.value = 'success'
    testNotice.value = response.detail
  } catch (error) {
    testNoticeTone.value = 'error'
    testNotice.value = extractAuthError(error, 'Не удалось отправить тестовое письмо.')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.admin-shell {
  display: grid;
  width: min(1120px, 100%);
  gap: 12px;
  margin: 0 auto;
}

.admin-shell,
.admin-shell * {
  box-sizing: border-box;
}

.admin-summary,
.admin-card {
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 92%, transparent);
  box-shadow: 0 10px 28px rgba(48, 63, 92, 0.08);
}

.admin-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px;
}

.admin-kicker,
.admin-summary h2,
.admin-summary span,
.card-head h3,
.card-head p {
  margin: 0;
}

.admin-kicker {
  color: var(--dash-accent-strong, #163E86);
  font-size: 12px;
  font-weight: 900;
}

.admin-summary h2 {
  margin-top: 4px;
  font-size: 30px;
  line-height: 1.08;
}

.admin-summary span,
.card-head p {
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.admin-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr);
  gap: 12px;
}

.admin-card {
  display: grid;
  align-content: start;
  gap: 16px;
  min-width: 0;
  padding: 16px;
}

.admin-card-wide {
  grid-row: span 2;
}

.card-head {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-icon {
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 19px;
}

.card-head h3 {
  color: var(--dash-text-1, #10182b);
  font-size: 18px;
}

.admin-form {
  display: grid;
  gap: 12px;
}

.admin-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(160px, 0.46fr);
  gap: 12px;
}

.admin-field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.admin-field.small {
  min-width: 140px;
}

.admin-field > span {
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.admin-field input,
.admin-field select {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  outline: none;
  padding: 0 12px;
  transition: border-color 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.admin-field input:focus,
.admin-field select:focus {
  border-color: var(--dash-accent, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 16%, transparent);
}

.admin-toggle {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--dash-text-1, #10182b);
  font-weight: 900;
}

.admin-toggle input {
  width: 18px;
  height: 18px;
  accent-color: var(--dash-accent, #345EA8);
}

.outline-btn,
.filled-btn {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 16px;
  font: inherit;
  font-weight: 900;
  cursor: pointer;
}

.outline-btn {
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
}

.filled-btn {
  background: var(--dash-accent, #345EA8);
  color: #fff;
  border-color: transparent;
}

.outline-btn:disabled,
.filled-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.admin-note {
  padding: 11px 13px;
  border-radius: 8px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.admin-note.success {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.admin-note.error {
  background: var(--dash-red-soft, #FFE5E7);
  color: var(--dash-red, #B3323A);
}

.admin-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid rgba(255,255,255,0.38);
  border-top-color: #fff;
  border-radius: 50%;
  animation: admin-spin 0.78s linear infinite;
}

.admin-spinner.dark {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 26%, transparent);
  border-top-color: var(--dash-accent, #345EA8);
}

@keyframes admin-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 980px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }

  .admin-card-wide {
    grid-row: auto;
  }
}

@media (max-width: 680px) {
  .admin-summary {
    align-items: stretch;
    flex-direction: column;
  }

  .admin-summary h2 {
    font-size: 24px;
  }

  .admin-row {
    grid-template-columns: 1fr;
  }

  .outline-btn,
  .filled-btn {
    width: 100%;
  }
}
</style>
