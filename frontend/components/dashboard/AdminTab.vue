<template>
  <div class="admin-shell">
    <section class="admin-toolbar">
      <div class="admin-title">
        <h2>Система</h2>
        <span>Почта, auth-ссылки и игровые API.</span>
      </div>
      <button class="outline-btn" type="button" :disabled="loading || apiLoading" @click="loadAllSettings">
        <span v-if="loading || apiLoading" class="admin-spinner dark" />
        <template v-else>
          <i class="ri-refresh-line" />
          <span>Обновить</span>
        </template>
      </button>
    </section>

    <section class="admin-health" aria-label="Статус системы">
      <article class="health-card" :class="smtpHealthTone">
        <span class="health-icon"><i class="ri-mail-check-line" /></span>
        <div>
          <strong>{{ smtpHealthLabel }}</strong>
          <span>{{ smtpStatus }}</span>
        </div>
      </article>

      <article class="health-card" :class="apiHealthTone">
        <span class="health-icon"><i class="ri-gamepad-line" /></span>
        <div>
          <strong>{{ apiHealthLabel }}</strong>
          <span>{{ apiStatus }}</span>
        </div>
      </article>

      <article class="health-card">
        <span class="health-icon"><i class="ri-timer-flash-line" /></span>
        <div>
          <strong>{{ ttlSummary }}</strong>
          <span>{{ form.frontend_base_url || 'Frontend URL не задан' }}</span>
        </div>
      </article>
    </section>

    <section class="admin-grid">
      <article class="admin-card admin-card-wide">
        <div class="card-head">
          <div>
            <h3>Почта</h3>
            <p>Отправка подтверждений и сброса пароля.</p>
          </div>
          <span class="card-icon"><i class="ri-mail-settings-line" /></span>
        </div>

        <form class="admin-form" @submit.prevent="saveSettings">
          <label class="admin-switch">
            <input v-model="form.enabled" type="checkbox">
            <span>
              <strong>Отправка писем</strong>
              <small>{{ form.enabled ? 'Включена' : 'Выключена, ссылки останутся в логах backend' }}</small>
            </span>
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
          <div>
            <h3>Ссылки и TTL</h3>
            <p>База для verify-email и reset-password.</p>
          </div>
          <span class="card-icon"><i class="ri-links-line" /></span>
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

          <button class="outline-btn" type="submit" :disabled="saving">
            <span v-if="saving" class="admin-spinner dark" />
            <template v-else>
              <i class="ri-save-3-line" />
              <span>Сохранить ссылки</span>
            </template>
          </button>
        </form>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <div>
            <h3>Игровые API</h3>
            <p>{{ apiStatus }}</p>
          </div>
          <span class="card-icon"><i class="ri-key-2-line" /></span>
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

          <div class="admin-note muted">
            Spotify callback URL: <strong>{{ spotifyCallbackUrl }}</strong>
          </div>

          <label class="admin-field">
            <span>Spotify Client ID</span>
            <input v-model="oauthForm.spotifyClientId" type="text" autocomplete="off" placeholder="Spotify client id">
          </label>

          <label class="admin-field">
            <span>Spotify Client Secret</span>
            <input v-model="oauthSecrets.spotify" type="password" autocomplete="new-password" :placeholder="spotifySecretPlaceholder">
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

          <div class="admin-note muted">
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

      <article class="admin-card admin-card-wide">
        <div class="card-head">
          <div>
            <h3>Git provider auth</h3>
            <p>OAuth для GitHub, GitLab и Gitea, включая self-hosted инстансы.</p>
          </div>
          <span class="card-icon"><i class="ri-git-branch-line" /></span>
        </div>

        <form class="admin-form" @submit.prevent="saveApiSettings">
          <div class="admin-note muted">
            Callback URL: <strong>{{ oauthCallbackUrl }}</strong>
          </div>
          <label class="admin-switch compact">
            <input v-model="apiForm.code_provider_token_auth_enabled" type="checkbox">
            <span>
              <strong>Token auth</strong>
              <small>Показывать пользователям вариант подключения через personal access token. Self-hosted Git-среды подключаются только так; если выключено, кнопка сразу ведет в OAuth публичного провайдера.</small>
            </span>
          </label>

          <section v-for="provider in oauthProviders" :key="provider.key" class="oauth-provider">
            <div class="oauth-provider-head">
              <span class="oauth-provider-icon">
                <GiteaLogo v-if="provider.key === 'gitea'" class="gitea-logo" />
                <i v-else :class="provider.icon" />
              </span>
              <div>
                <strong>{{ provider.label }}</strong>
                <span>{{ provider.hint }}</span>
              </div>
            </div>

            <div class="admin-row">
              <label class="admin-field">
                <span>Client ID</span>
                <input v-model="oauthForm[provider.clientIdKey]" type="text" autocomplete="off" :placeholder="`${provider.label} client id`">
              </label>

              <label class="admin-field">
                <span>Client Secret</span>
                <input v-model="oauthSecrets[provider.secretKey]" type="password" autocomplete="new-password" :placeholder="provider.secretPlaceholder">
              </label>
            </div>
          </section>

          <button class="outline-btn" type="submit" :disabled="apiSaving">
            <span v-if="apiSaving" class="admin-spinner dark" />
            <template v-else>
              <i class="ri-save-3-line" />
              <span>Сохранить OAuth</span>
            </template>
          </button>
        </form>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <div>
            <h3>Тест письма</h3>
            <p>Проверка текущей конфигурации.</p>
          </div>
          <span class="card-icon"><i class="ri-send-plane-line" /></span>
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
  github_oauth_client_id: string | null
  github_oauth_client_secret_set: boolean
  github_oauth_client_secret_hint: string | null
  gitlab_oauth_client_id: string | null
  gitlab_oauth_client_secret_set: boolean
  gitlab_oauth_client_secret_hint: string | null
  gitea_oauth_client_id: string | null
  gitea_oauth_client_secret_set: boolean
  gitea_oauth_client_secret_hint: string | null
  spotify_oauth_client_id: string | null
  spotify_oauth_client_secret_set: boolean
  spotify_oauth_client_secret_hint: string | null
  code_provider_token_auth_enabled: boolean
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
const oauthSecrets = reactive({
  github: '',
  gitlab: '',
  gitea: '',
  spotify: '',
})
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
  code_provider_token_auth_enabled: true,
})

const oauthForm = reactive({
  githubClientId: '',
  gitlabClientId: '',
  giteaClientId: '',
  spotifyClientId: '',
})

const oauthSecretState = reactive({
  githubSet: false,
  githubHint: '(****)',
  gitlabSet: false,
  gitlabHint: '(****)',
  giteaSet: false,
  giteaHint: '(****)',
  spotifySet: false,
  spotifyHint: '(****)',
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
const oauthCallbackUrl = computed(() => `${form.frontend_base_url.replace(/\/$/, '')}/api/integrations/code/oauth/callback`)
const spotifyCallbackUrl = computed(() => `${form.frontend_base_url.replace(/\/$/, '')}/api/integrations/spotify/oauth/callback`)
const spotifySecretPlaceholder = computed(() => oauthSecretState.spotifySet ? `Сохранен ${oauthSecretState.spotifyHint}` : 'Spotify client secret')
const oauthProviders = computed(() => [
  {
    key: 'github',
    label: 'GitHub',
    icon: 'ri-github-fill',
    hint: 'github.com или GitHub Enterprise Server',
    clientIdKey: 'githubClientId' as const,
    secretKey: 'github' as const,
    secretPlaceholder: oauthSecretState.githubSet ? `Сохранен ${oauthSecretState.githubHint}` : 'GitHub client secret',
  },
  {
    key: 'gitlab',
    label: 'GitLab',
    icon: 'ri-gitlab-fill',
    hint: 'gitlab.com или self-managed GitLab',
    clientIdKey: 'gitlabClientId' as const,
    secretKey: 'gitlab' as const,
    secretPlaceholder: oauthSecretState.gitlabSet ? `Сохранен ${oauthSecretState.gitlabHint}` : 'GitLab client secret',
  },
  {
    key: 'gitea',
    label: 'Gitea',
    icon: '',
    hint: 'gitea.com или self-hosted Gitea',
    clientIdKey: 'giteaClientId' as const,
    secretKey: 'gitea' as const,
    secretPlaceholder: oauthSecretState.giteaSet ? `Сохранен ${oauthSecretState.giteaHint}` : 'Gitea client secret',
  },
])
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
const smtpHealthTone = computed(() => {
  if (!form.enabled) return 'muted'
  return form.host ? 'ok' : 'warn'
})
const smtpHealthLabel = computed(() => {
  if (!form.enabled) return 'Почта выключена'
  return form.host ? 'Почта готова' : 'Нужен SMTP host'
})
const apiHealthTone = computed(() => {
  if (steamKeySet.value && faceitKeySet.value) return 'ok'
  if (steamKeySet.value || faceitKeySet.value) return 'warn'
  return 'muted'
})
const apiHealthLabel = computed(() => {
  if (steamKeySet.value && faceitKeySet.value) return 'API готовы'
  if (steamKeySet.value || faceitKeySet.value) return 'API частично'
  return 'API не настроены'
})
const ttlSummary = computed(() =>
  `Email ${formatDuration(form.email_verification_ttl_seconds)} · Reset ${formatDuration(form.password_reset_ttl_seconds)}`,
)
onMounted(() => {
  void loadAllSettings()
})

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '—'
  const hours = seconds / 3600
  if (hours >= 24 && Number.isInteger(hours / 24)) return `${hours / 24} д`
  if (hours >= 1) return `${Math.round(hours)} ч`
  return `${Math.round(seconds / 60)} мин`
}

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
  apiForm.code_provider_token_auth_enabled = data.code_provider_token_auth_enabled
  oauthForm.githubClientId = data.github_oauth_client_id ?? ''
  oauthForm.gitlabClientId = data.gitlab_oauth_client_id ?? ''
  oauthForm.giteaClientId = data.gitea_oauth_client_id ?? ''
  oauthForm.spotifyClientId = data.spotify_oauth_client_id ?? ''
  apiSteamKey.value = ''
  apiFaceitKey.value = ''
  oauthSecrets.github = ''
  oauthSecrets.gitlab = ''
  oauthSecrets.gitea = ''
  oauthSecrets.spotify = ''
  steamKeyHint.value = data.steam_api_key_hint ?? '(****)'
  faceitKeyHint.value = data.faceit_api_key_hint ?? '(****)'
  oauthSecretState.githubSet = data.github_oauth_client_secret_set
  oauthSecretState.githubHint = data.github_oauth_client_secret_hint ?? '(****)'
  oauthSecretState.gitlabSet = data.gitlab_oauth_client_secret_set
  oauthSecretState.gitlabHint = data.gitlab_oauth_client_secret_hint ?? '(****)'
  oauthSecretState.giteaSet = data.gitea_oauth_client_secret_set
  oauthSecretState.giteaHint = data.gitea_oauth_client_secret_hint ?? '(****)'
  oauthSecretState.spotifySet = data.spotify_oauth_client_secret_set
  oauthSecretState.spotifyHint = data.spotify_oauth_client_secret_hint ?? '(****)'
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
      code_provider_token_auth_enabled: apiForm.code_provider_token_auth_enabled,
    }
    if (apiSteamKey.value.trim()) {
      body.steam_api_key = apiSteamKey.value.trim()
    }
    if (apiFaceitKey.value.trim()) {
      body.faceit_api_key = apiFaceitKey.value.trim()
    }
    if (oauthForm.githubClientId.trim()) {
      body.github_oauth_client_id = oauthForm.githubClientId.trim()
    }
    if (oauthSecrets.github.trim()) {
      body.github_oauth_client_secret = oauthSecrets.github.trim()
    }
    if (oauthForm.gitlabClientId.trim()) {
      body.gitlab_oauth_client_id = oauthForm.gitlabClientId.trim()
    }
    if (oauthSecrets.gitlab.trim()) {
      body.gitlab_oauth_client_secret = oauthSecrets.gitlab.trim()
    }
    if (oauthForm.giteaClientId.trim()) {
      body.gitea_oauth_client_id = oauthForm.giteaClientId.trim()
    }
    if (oauthSecrets.gitea.trim()) {
      body.gitea_oauth_client_secret = oauthSecrets.gitea.trim()
    }
    if (oauthForm.spotifyClientId.trim()) {
      body.spotify_oauth_client_id = oauthForm.spotifyClientId.trim()
    }
    if (oauthSecrets.spotify.trim()) {
      body.spotify_oauth_client_secret = oauthSecrets.spotify.trim()
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
  width: min(1060px, 100%);
  gap: 12px;
  margin: 0 auto;
}

.admin-shell,
.admin-shell * {
  box-sizing: border-box;
}

.admin-toolbar,
.health-card,
.admin-card {
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 86%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #fff) 94%, transparent);
  box-shadow: 0 10px 28px color-mix(in srgb, var(--text-1, #10182b) 7%, transparent);
}

.admin-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
}

.admin-title,
.card-head > div,
.health-card > div {
  min-width: 0;
}

.admin-title h2,
.admin-title span,
.card-head h3,
.card-head p,
.health-card strong,
.health-card span {
  margin: 0;
}

.admin-title h2 {
  color: var(--text-1, #10182b);
  font-size: 22px;
  line-height: 1.12;
}

.admin-title span,
.card-head p,
.health-card span {
  color: var(--text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.admin-title span {
  display: block;
  margin-top: 4px;
}

.admin-health {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.health-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 13px;
}

.health-icon {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 18px;
}

.health-card strong {
  display: block;
  color: var(--text-1, #10182b);
  font-size: 14px;
  line-height: 1.25;
  font-weight: 900;
}

.health-card span {
  display: -webkit-box;
  margin-top: 3px;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.health-card.ok .health-icon {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.health-card.warn .health-icon {
  background: var(--warning-container, #FFF0CF);
  color: var(--warning, #9B6200);
}

.health-card.muted .health-icon {
  background: var(--surface-low, #F2F4F8);
  color: var(--text-3, #66789c);
}

.admin-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.28fr) minmax(300px, 0.86fr);
  gap: 12px;
}

.admin-card {
  display: grid;
  align-content: start;
  gap: 14px;
  min-width: 0;
  padding: 16px;
}

.admin-card-wide {
  grid-row: span 2;
}

.card-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.card-icon {
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 19px;
}

.card-head h3 {
  color: var(--text-1, #10182b);
  font-size: 17px;
  line-height: 1.2;
}

.admin-form {
  display: grid;
  gap: 12px;
}

.oauth-provider {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 84%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 72%, transparent);
}

.oauth-provider-head {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.oauth-provider-icon {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 18px;
}

.gitea-logo {
  width: 22px;
  height: 22px;
  display: block;
}

.oauth-provider-head strong,
.oauth-provider-head span {
  display: block;
}

.oauth-provider-head strong {
  color: var(--text-1, #10182b);
  font-size: 14px;
  line-height: 1.25;
}

.oauth-provider-head span {
  margin-top: 2px;
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.admin-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 0.45fr);
  gap: 12px;
}

.admin-field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.admin-field.small {
  min-width: 130px;
}

.admin-field > span {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.admin-field input,
.admin-field select {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #fff) 96%, transparent);
  color: var(--text-1, #10182b);
  font: inherit;
  outline: none;
  padding: 0 12px;
  transition:
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    box-shadow 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.admin-field input:focus,
.admin-field select:focus {
  border-color: var(--primary, #345EA8);
  background: var(--surface, #fff);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 15%, transparent);
}

.admin-switch {
  min-height: 52px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 82%, transparent);
  border-radius: 16px;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-1, #10182b);
  cursor: pointer;
}

.admin-switch input {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  accent-color: var(--primary, #345EA8);
}

.admin-switch span {
  display: grid;
  gap: 1px;
}

.admin-switch strong {
  font-size: 13px;
  line-height: 1.25;
}

.admin-switch small {
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.outline-btn,
.filled-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 16px;
  font: inherit;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.outline-btn {
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
}

.filled-btn {
  background: var(--primary, #345EA8);
  color: #fff;
  border-color: transparent;
}

.outline-btn:disabled,
.filled-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.admin-note {
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.admin-note strong {
  color: var(--text-1, #10182b);
  overflow-wrap: anywhere;
}

.admin-note.muted {
  color: var(--text-3, #66789c);
}

.admin-note.success {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.admin-note.error {
  background: var(--error-container, #FFE5E7);
  color: var(--error, #B3323A);
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
  border-color: color-mix(in srgb, var(--primary, #345EA8) 26%, transparent);
  border-top-color: var(--primary, #345EA8);
}

.outline-btn:focus-visible,
.filled-btn:focus-visible,
.admin-switch:focus-within,
.admin-field input:focus-visible,
.admin-field select:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--primary, #345EA8) 32%, transparent);
  outline-offset: 2px;
}

@media (hover: hover) {
  .outline-btn:hover:not(:disabled),
  .filled-btn:hover:not(:disabled) {
    transform: translateY(-1px);
  }
}

@keyframes admin-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 980px) {
  .admin-shell {
    max-width: 760px;
  }

  .admin-health,
  .admin-grid {
    grid-template-columns: 1fr;
  }

  .admin-card-wide {
    grid-row: auto;
  }
}

@media (max-width: 680px) {
  .admin-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .admin-title h2 {
    font-size: 20px;
  }

  .admin-row {
    grid-template-columns: 1fr;
  }

  .admin-field.small {
    min-width: 0;
  }

  .outline-btn,
  .filled-btn {
    width: 100%;
  }

  .admin-toolbar,
  .health-card,
  .admin-card {
    border-radius: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .admin-shell *,
  .admin-shell *::before,
  .admin-shell *::after {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
  }
}
</style>
