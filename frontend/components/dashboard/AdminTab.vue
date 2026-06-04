<template>
  <div class="admin-shell">
    <section class="admin-hero">
      <div class="admin-title">
        <p class="admin-kicker">Админка</p>
        <h2>Система и интеграции</h2>
        <span>Критичные параметры вынесены в отдельные редакторы, а главный экран показывает текущее состояние.</span>
      </div>

      <div class="admin-hero-actions">
        <span class="admin-state-pill" :class="{ active: form.enabled }">
          <i :class="form.enabled ? 'ri-mail-check-line' : 'ri-mail-close-line'" />
          <span>{{ form.enabled ? 'Почта включена' : 'Почта выключена' }}</span>
        </span>
        <button class="outline-btn refresh-btn" type="button" :disabled="loading || apiLoading" @click="loadAllSettings">
          <span v-if="loading || apiLoading" class="admin-spinner dark" />
          <template v-else>
            <i class="ri-refresh-line" />
            <span>Обновить</span>
          </template>
        </button>
      </div>
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

    <section class="admin-actions" aria-label="Редакторы настроек">
      <article class="admin-card feature-card">
        <div class="card-head">
          <div>
            <span class="card-overline">SMTP</span>
            <h3>Почта</h3>
            <p>{{ smtpStatus }}</p>
          </div>
          <span class="card-icon"><i class="ri-mail-settings-line" /></span>
        </div>

        <dl class="admin-facts">
          <div>
            <dt>Host</dt>
            <dd>{{ form.host || 'не задан' }}</dd>
          </div>
          <div>
            <dt>Порт</dt>
            <dd>{{ form.port }}</dd>
          </div>
          <div>
            <dt>TLS</dt>
            <dd>{{ encryptionMode.toUpperCase() }}</dd>
          </div>
        </dl>

        <button class="filled-btn card-action" type="button" @click="openDialog('smtp')">
          <i class="ri-edit-line" />
          <span>Редактировать почту</span>
        </button>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <div>
            <span class="card-overline">Auth links</span>
            <h3>Ссылки и TTL</h3>
            <p>{{ form.frontend_base_url || 'Frontend URL не задан' }}</p>
          </div>
          <span class="card-icon tertiary"><i class="ri-links-line" /></span>
        </div>

        <dl class="admin-facts compact">
          <div>
            <dt>Email</dt>
            <dd>{{ formatDuration(form.email_verification_ttl_seconds) }}</dd>
          </div>
          <div>
            <dt>Reset</dt>
            <dd>{{ formatDuration(form.password_reset_ttl_seconds) }}</dd>
          </div>
        </dl>

        <button class="outline-btn card-action" type="button" @click="openDialog('links')">
          <i class="ri-time-line" />
          <span>Настроить ссылки</span>
        </button>
      </article>

      <article class="admin-card">
        <div class="card-head">
          <div>
            <span class="card-overline">Games</span>
            <h3>Игровые API</h3>
            <p>{{ apiStatus }}</p>
          </div>
          <span class="card-icon secondary"><i class="ri-key-2-line" /></span>
        </div>

        <dl class="admin-facts compact">
          <div>
            <dt>Steam</dt>
            <dd>{{ steamKeySet ? 'ключ сохранен' : 'без ключа' }}</dd>
          </div>
          <div>
            <dt>FACEIT</dt>
            <dd>{{ faceitKeySet ? 'ключ сохранен' : 'без ключа' }}</dd>
          </div>
        </dl>

        <button class="outline-btn card-action" type="button" @click="openDialog('api')">
          <i class="ri-gamepad-line" />
          <span>Настроить API</span>
        </button>
      </article>

      <article class="admin-card feature-card">
        <div class="card-head">
          <div>
            <span class="card-overline">OAuth</span>
            <h3>Git provider auth</h3>
            <p>GitHub, GitLab и Gitea для публичных и self-hosted инстансов.</p>
          </div>
          <span class="card-icon"><i class="ri-git-branch-line" /></span>
        </div>

        <div class="provider-strip" aria-label="Статус OAuth провайдеров">
          <span :class="{ ready: oauthSecretState.githubSet }"><i class="ri-github-fill" /> GitHub</span>
          <span :class="{ ready: oauthSecretState.gitlabSet }"><i class="ri-gitlab-fill" /> GitLab</span>
          <span :class="{ ready: oauthSecretState.giteaSet }"><GiteaLogo class="provider-strip-logo" /> Gitea</span>
        </div>

        <button class="filled-btn card-action" type="button" @click="openDialog('oauth')">
          <i class="ri-lock-password-line" />
          <span>Редактировать OAuth</span>
        </button>
      </article>

      <article class="admin-card test-card">
        <div class="card-head">
          <div>
            <span class="card-overline">Delivery</span>
            <h3>Тест письма</h3>
            <p>Отправка проверочного письма на выбранный адрес.</p>
          </div>
          <span class="card-icon tertiary"><i class="ri-send-plane-line" /></span>
        </div>

        <button class="outline-btn card-action" type="button" @click="openDialog('test')">
          <i class="ri-mail-send-line" />
          <span>Открыть тест</span>
        </button>
      </article>
    </section>

    <Transition name="admin-dialog">
      <div v-if="activeDialog" class="admin-dialog-overlay" @click.self="closeDialog" @keyup.esc="closeDialog">
        <section class="admin-dialog" role="dialog" aria-modal="true" :aria-labelledby="`${activeDialog}-dialog-title`">
          <button class="admin-dialog-close" type="button" aria-label="Закрыть" @click="closeDialog">
            <i class="ri-close-line" />
          </button>

          <template v-if="activeDialog === 'smtp'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon"><i class="ri-mail-settings-line" /></span>
              <div>
                <p class="admin-kicker">SMTP</p>
                <h3 id="smtp-dialog-title">Почта</h3>
                <span>Отправка подтверждений и сброса пароля.</span>
              </div>
            </header>

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

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="saving">
                  <span v-if="saving" class="admin-spinner" />
                  <span v-else>Сохранить настройки</span>
                </button>
              </div>
            </form>
          </template>

          <template v-else-if="activeDialog === 'links'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon tertiary"><i class="ri-links-line" /></span>
              <div>
                <p class="admin-kicker">Auth links</p>
                <h3 id="links-dialog-title">Ссылки и TTL</h3>
                <span>База для verify-email и reset-password.</span>
              </div>
            </header>

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

              <div v-if="saveNotice" class="admin-note" :class="saveNoticeTone">{{ saveNotice }}</div>

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="saving">
                  <span v-if="saving" class="admin-spinner" />
                  <span v-else>Сохранить ссылки</span>
                </button>
              </div>
            </form>
          </template>

          <template v-else-if="activeDialog === 'api'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon secondary"><i class="ri-key-2-line" /></span>
              <div>
                <p class="admin-kicker">Games</p>
                <h3 id="api-dialog-title">Игровые API</h3>
                <span>{{ apiStatus }}</span>
              </div>
            </header>

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

              <label class="admin-field">
                <span>Spotify API access token</span>
                <input v-model="apiSpotifyToken" type="password" autocomplete="new-password" :placeholder="spotifyTokenPlaceholder">
              </label>

              <div class="admin-row">
                <label class="admin-field">
                  <span>Spotify Web API URL</span>
                  <input v-model="apiForm.spotify_api_base_url" type="url" autocomplete="off" placeholder="https://api.spotify.com/v1">
                </label>

                <label class="admin-field">
                  <span>Spotify Accounts URL</span>
                  <input v-model="apiForm.spotify_accounts_base_url" type="url" autocomplete="off" placeholder="https://accounts.spotify.com">
                </label>
              </div>

              <div class="admin-note muted">
                Now playing uses each user's Spotify OAuth token. The admin token is stored as a service secret and does not replace user consent.
              </div>

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

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="apiSaving">
                  <span v-if="apiSaving" class="admin-spinner" />
                  <span v-else>Сохранить ключи</span>
                </button>
              </div>
            </form>
          </template>

          <template v-else-if="activeDialog === 'oauth'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon"><i class="ri-git-branch-line" /></span>
              <div>
                <p class="admin-kicker">OAuth</p>
                <h3 id="oauth-dialog-title">Git provider auth</h3>
                <span>OAuth для GitHub, GitLab и Gitea, включая self-hosted инстансы.</span>
              </div>
            </header>

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

              <div v-if="apiNotice" class="admin-note" :class="apiNoticeTone">{{ apiNotice }}</div>

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="apiSaving">
                  <span v-if="apiSaving" class="admin-spinner" />
                  <span v-else>Сохранить OAuth</span>
                </button>
              </div>
            </form>
          </template>

          <template v-else>
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon tertiary"><i class="ri-send-plane-line" /></span>
              <div>
                <p class="admin-kicker">Delivery</p>
                <h3 id="test-dialog-title">Тест письма</h3>
                <span>Проверка текущей конфигурации.</span>
              </div>
            </header>

            <form class="admin-form" @submit.prevent="sendTestEmail">
              <label class="admin-field">
                <span>Получатель</span>
                <input v-model="testEmail" type="email" :placeholder="auth.user?.email || 'admin@example.com'">
              </label>

              <div v-if="testNotice" class="admin-note" :class="testNoticeTone">{{ testNotice }}</div>

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="testing">
                  <span v-if="testing" class="admin-spinner" />
                  <span v-else>Отправить тест</span>
                </button>
              </div>
            </form>
          </template>
        </section>
      </div>
    </Transition>
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
  spotify_access_token_set: boolean
  spotify_access_token_hint: string | null
  spotify_api_base_url: string
  spotify_accounts_base_url: string
  code_provider_token_auth_enabled: boolean
  steam_inventory_app_id: number
  steam_inventory_context_id: string
  steam_inventory_price_source: string
}

type AdminDialog = 'smtp' | 'links' | 'api' | 'oauth' | 'test'

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
const apiSpotifyToken = ref('')
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
const activeDialog = ref<AdminDialog | null>(null)

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
  spotify_api_base_url: 'https://api.spotify.com/v1',
  spotify_accounts_base_url: 'https://accounts.spotify.com',
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
  spotifyTokenSet: false,
  spotifyTokenHint: '(****)',
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
const spotifyTokenPlaceholder = computed(() => oauthSecretState.spotifyTokenSet ? `Saved ${oauthSecretState.spotifyTokenHint}` : 'Spotify access token')
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

function openDialog(dialog: AdminDialog) {
  activeDialog.value = dialog
  if (dialog === 'smtp' || dialog === 'links') saveNotice.value = ''
  if (dialog === 'api' || dialog === 'oauth') apiNotice.value = ''
  if (dialog === 'test') testNotice.value = ''
}

function closeDialog() {
  activeDialog.value = null
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
  apiForm.spotify_api_base_url = data.spotify_api_base_url || 'https://api.spotify.com/v1'
  apiForm.spotify_accounts_base_url = data.spotify_accounts_base_url || 'https://accounts.spotify.com'
  oauthForm.githubClientId = data.github_oauth_client_id ?? ''
  oauthForm.gitlabClientId = data.gitlab_oauth_client_id ?? ''
  oauthForm.giteaClientId = data.gitea_oauth_client_id ?? ''
  oauthForm.spotifyClientId = data.spotify_oauth_client_id ?? ''
  apiSteamKey.value = ''
  apiFaceitKey.value = ''
  apiSpotifyToken.value = ''
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
  oauthSecretState.spotifyTokenSet = data.spotify_access_token_set
  oauthSecretState.spotifyTokenHint = data.spotify_access_token_hint ?? '(****)'
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
      spotify_api_base_url: apiForm.spotify_api_base_url.trim() || 'https://api.spotify.com/v1',
      spotify_accounts_base_url: apiForm.spotify_accounts_base_url.trim() || 'https://accounts.spotify.com',
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
    if (apiSpotifyToken.value.trim()) {
      body.spotify_access_token = apiSpotifyToken.value.trim()
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
  gap: 16px;
  margin: 0 auto;
  --md-sys-color-primary: var(--primary);
  --md-sys-color-on-primary: var(--on-primary);
  --md-sys-color-primary-container: var(--primary-container);
  --md-sys-color-on-primary-container: var(--on-primary-container);
  --md-sys-color-secondary: var(--secondary);
  --md-sys-color-on-secondary: var(--on-secondary);
  --md-sys-color-secondary-container: var(--secondary-container);
  --md-sys-color-on-secondary-container: var(--on-secondary-container);
  --md-sys-color-tertiary: var(--tertiary);
  --md-sys-color-on-tertiary: var(--on-tertiary);
  --md-sys-color-tertiary-container: var(--tertiary-container);
  --md-sys-color-on-tertiary-container: var(--on-tertiary-container);
  --md-sys-color-error: var(--error);
  --md-sys-color-error-container: var(--error-container);
  --md-sys-color-on-error-container: var(--on-error-container);
  --md-sys-color-surface: var(--surface);
  --md-sys-color-surface-container-lowest: var(--surface-container-lowest);
  --md-sys-color-surface-container-low: var(--surface-container-low);
  --md-sys-color-surface-container: var(--surface-container);
  --md-sys-color-surface-container-high: var(--surface-container-high);
  --md-sys-color-surface-container-highest: var(--surface-container-highest);
  --md-sys-color-on-surface: var(--text-1);
  --md-sys-color-on-surface-variant: var(--on-surface-variant);
  --md-sys-color-outline: var(--outline);
  --md-sys-color-outline-variant: var(--outline-variant);
  --md-sys-color-inverse-surface: var(--inverse-surface);
  --md-sys-color-success: var(--success);
  --md-sys-color-success-container: var(--success-container);
  --md-sys-color-warning: var(--warning);
  --md-sys-color-warning-container: var(--warning-container);
  --md-sys-shape-corner-small: 8px;
  --md-sys-shape-corner-medium: 12px;
  --md-sys-shape-corner-large: 16px;
  --md-sys-shape-corner-large-increased: 20px;
  --md-sys-shape-corner-extra-large: 28px;
  --md-sys-shape-corner-extra-large-increased: 32px;
  --md-sys-shape-corner-full: 9999px;
  --md-sys-typescale-label-medium-size: 12px;
  --md-sys-typescale-label-medium-line-height: 16px;
  --md-sys-typescale-body-medium-size: 14px;
  --md-sys-typescale-body-medium-line-height: 20px;
  --md-sys-typescale-title-medium-size: 18px;
  --md-sys-typescale-title-medium-line-height: 24px;
  --md-sys-typescale-title-large-size: 24px;
  --md-sys-typescale-title-large-line-height: 30px;
  --admin-motion-standard: var(--ease-standard);
  --admin-motion-expressive: var(--ease-spring);
}

.admin-shell,
.admin-shell * {
  box-sizing: border-box;
}

.admin-hero,
.health-card,
.admin-card {
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-large);
  background: var(--md-sys-color-surface-container);
  color: var(--md-sys-color-on-surface);
  box-shadow: none;
}

.admin-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background:
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--md-sys-color-primary-container) 48%, transparent),
      color-mix(in srgb, var(--md-sys-color-tertiary-container) 38%, transparent)
    ),
    var(--md-sys-color-surface-container-high);
}

.admin-title,
.card-head > div,
.health-card > div,
.admin-dialog-head > div {
  min-width: 0;
}

.admin-kicker,
.admin-title h2,
.admin-title span,
.card-overline,
.card-head h3,
.card-head p,
.health-card strong,
.health-card span,
.admin-dialog-head h3,
.admin-dialog-head span {
  margin: 0;
}

.admin-kicker,
.card-overline {
  color: var(--md-sys-color-primary);
  font-size: var(--md-sys-typescale-label-medium-size);
  line-height: var(--md-sys-typescale-label-medium-line-height);
  font-weight: 900;
  letter-spacing: 0;
}

.admin-title h2,
.admin-dialog-head h3 {
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-title-large-size);
  line-height: var(--md-sys-typescale-title-large-line-height);
  font-weight: 900;
}

.admin-title span,
.card-head p,
.health-card span,
.admin-dialog-head span {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
}

.admin-title span {
  display: block;
  margin-top: 4px;
}

.admin-hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
}

.admin-state-pill {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 14px;
  font-size: var(--md-sys-typescale-body-medium-size);
  font-weight: 800;
  white-space: nowrap;
}

.admin-state-pill.active {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.admin-health {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.health-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
  padding: 16px;
  background: var(--md-sys-color-surface-container-low);
}

.health-icon,
.card-icon,
.admin-dialog-icon,
.oauth-provider-icon {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.health-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-large);
  font-size: 20px;
}

.health-card strong {
  display: block;
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
  font-weight: 900;
}

.health-card span {
  display: -webkit-box;
  margin-top: 2px;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.health-card.ok .health-icon {
  background: var(--md-sys-color-success-container);
  color: var(--md-sys-color-success);
}

.health-card.warn .health-icon {
  background: var(--md-sys-color-warning-container);
  color: var(--md-sys-color-warning);
}

.health-card.muted .health-icon {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
}

.admin-actions {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.admin-card {
  grid-column: span 2;
  display: grid;
  align-content: start;
  gap: 16px;
  min-width: 0;
  min-height: 236px;
  padding: 18px;
  background: var(--md-sys-color-surface-container-low);
}

.admin-card.feature-card {
  grid-column: span 3;
  background: var(--md-sys-color-surface-container-high);
}

.admin-card.test-card {
  min-height: 176px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.card-head h3 {
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-title-medium-size);
  line-height: var(--md-sys-typescale-title-medium-line-height);
  font-weight: 900;
}

.card-head p {
  display: -webkit-box;
  margin-top: 4px;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--md-sys-shape-corner-large-increased);
  font-size: 22px;
}

.card-icon.secondary,
.admin-dialog-icon.secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.card-icon.tertiary,
.admin-dialog-icon.tertiary {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.admin-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.admin-facts.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.admin-facts div {
  min-width: 0;
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-highest);
  padding: 12px;
}

.admin-facts dt {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-label-medium-size);
  line-height: var(--md-sys-typescale-label-medium-line-height);
  font-weight: 800;
}

.admin-facts dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
  font-weight: 900;
}

.provider-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.provider-strip span {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 12px;
  font-size: var(--md-sys-typescale-label-medium-size);
  font-weight: 900;
}

.provider-strip span.ready {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.provider-strip-logo {
  width: 18px;
  height: 18px;
}

.outline-btn,
.filled-btn,
.text-btn {
  min-height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: var(--md-sys-shape-corner-full);
  padding: 0 18px;
  font: inherit;
  font-size: var(--md-sys-typescale-body-medium-size);
  font-weight: 900;
  border: 1px solid transparent;
  cursor: pointer;
  transition:
    transform 220ms var(--admin-motion-expressive),
    background 200ms var(--admin-motion-standard),
    border-color 200ms var(--admin-motion-standard),
    color 200ms var(--admin-motion-standard);
}

.outline-btn {
  border-color: var(--md-sys-color-outline);
  background: var(--md-sys-color-surface-container-lowest);
  color: var(--md-sys-color-primary);
}

.filled-btn {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.text-btn {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.card-action {
  align-self: end;
  justify-self: start;
  margin-top: auto;
}

.refresh-btn {
  white-space: nowrap;
}

.outline-btn:disabled,
.filled-btn:disabled,
.text-btn:disabled {
  cursor: not-allowed;
  opacity: 0.56;
  transform: none;
}

.admin-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 24px;
  background: color-mix(in srgb, var(--md-sys-color-inverse-surface) 40%, transparent);
  backdrop-filter: blur(10px);
}

.admin-dialog {
  position: relative;
  width: min(720px, 100%);
  max-height: min(760px, calc(100vh - 48px));
  display: grid;
  gap: 20px;
  overflow: auto;
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 80%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-large-increased);
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  padding: 24px;
  box-shadow: var(--shadow-mid);
}

.admin-dialog-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
}

.admin-dialog-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding-right: 44px;
}

.admin-dialog-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--md-sys-shape-corner-large-increased);
  font-size: 24px;
}

.admin-form {
  display: grid;
  gap: 14px;
}

.admin-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 0.46fr);
  gap: 12px;
}

.admin-field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.admin-field.small {
  min-width: 132px;
}

.admin-field > span {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-label-medium-size);
  line-height: var(--md-sys-typescale-label-medium-line-height);
  font-weight: 900;
}

.admin-field input,
.admin-field select {
  width: 100%;
  min-height: 48px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: var(--md-sys-shape-corner-small);
  background: var(--md-sys-color-surface-container-lowest);
  color: var(--md-sys-color-on-surface);
  font: inherit;
  outline: none;
  padding: 0 14px;
  transition:
    border-color 200ms var(--admin-motion-standard),
    box-shadow 200ms var(--admin-motion-standard),
    background 200ms var(--admin-motion-standard);
}

.admin-field input:focus,
.admin-field select:focus {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--md-sys-color-primary) 18%, transparent);
}

.admin-switch {
  min-height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  padding: 12px;
  cursor: pointer;
}

.admin-switch input {
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  accent-color: var(--md-sys-color-primary);
}

.admin-switch span {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.admin-switch strong {
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
  font-weight: 900;
}

.admin-switch small {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-label-medium-size);
  line-height: var(--md-sys-typescale-label-medium-line-height);
}

.oauth-provider {
  display: grid;
  gap: 12px;
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-high);
  padding: 14px;
}

.oauth-provider-head {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.oauth-provider-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-large);
  font-size: 20px;
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
  color: var(--md-sys-color-on-surface);
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
  font-weight: 900;
}

.oauth-provider-head span {
  color: var(--md-sys-color-on-surface-variant);
  font-size: var(--md-sys-typescale-label-medium-size);
  line-height: var(--md-sys-typescale-label-medium-line-height);
}

.admin-note {
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  padding: 12px 14px;
  font-size: var(--md-sys-typescale-body-medium-size);
  line-height: var(--md-sys-typescale-body-medium-line-height);
}

.admin-note strong {
  color: var(--md-sys-color-on-surface);
  overflow-wrap: anywhere;
}

.admin-note.muted {
  color: var(--md-sys-color-on-surface-variant);
}

.admin-note.success {
  background: var(--md-sys-color-success-container);
  color: var(--md-sys-color-success);
}

.admin-note.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.admin-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 4px;
}

.admin-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid color-mix(in srgb, currentColor 34%, transparent);
  border-top-color: currentColor;
  border-radius: var(--md-sys-shape-corner-full);
  animation: admin-spin 0.78s linear infinite;
}

.admin-spinner.dark {
  color: var(--md-sys-color-primary);
}

.outline-btn:focus-visible,
.filled-btn:focus-visible,
.text-btn:focus-visible,
.admin-dialog-close:focus-visible,
.admin-switch:focus-within,
.admin-field input:focus-visible,
.admin-field select:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--md-sys-color-primary) 34%, transparent);
  outline-offset: 2px;
}

@media (hover: hover) {
  .outline-btn:hover:not(:disabled),
  .filled-btn:hover:not(:disabled),
  .text-btn:hover:not(:disabled),
  .admin-dialog-close:hover {
    transform: translateY(-1px);
  }
}

.admin-dialog-enter-active,
.admin-dialog-leave-active {
  transition: opacity 220ms var(--admin-motion-standard);
}

.admin-dialog-enter-active .admin-dialog,
.admin-dialog-leave-active .admin-dialog {
  transition:
    opacity 240ms var(--admin-motion-standard),
    transform 300ms var(--admin-motion-expressive);
}

.admin-dialog-enter-from,
.admin-dialog-leave-to {
  opacity: 0;
}

.admin-dialog-enter-from .admin-dialog,
.admin-dialog-leave-to .admin-dialog {
  opacity: 0;
  transform: translateY(18px) scale(0.96);
}

@keyframes admin-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 980px) {
  .admin-shell {
    max-width: 760px;
  }

  .admin-health {
    grid-template-columns: 1fr;
  }

  .admin-actions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-card,
  .admin-card.feature-card {
    grid-column: span 1;
  }
}

@media (max-width: 680px) {
  .admin-shell {
    gap: 12px;
  }

  .admin-hero {
    grid-template-columns: 1fr;
    padding: 16px;
    border-radius: var(--md-sys-shape-corner-large-increased);
  }

  .admin-hero-actions {
    justify-content: stretch;
    flex-wrap: wrap;
  }

  .admin-state-pill,
  .refresh-btn,
  .card-action,
  .admin-form-actions .outline-btn,
  .admin-form-actions .filled-btn,
  .admin-form-actions .text-btn {
    width: 100%;
  }

  .admin-actions,
  .admin-row,
  .admin-facts,
  .admin-facts.compact {
    grid-template-columns: 1fr;
  }

  .admin-card {
    grid-column: span 1;
    min-height: 0;
    border-radius: var(--md-sys-shape-corner-large-increased);
    padding: 16px;
  }

  .admin-field.small {
    min-width: 0;
  }

  .admin-dialog-overlay {
    align-items: end;
    padding: 8px;
  }

  .admin-dialog {
    width: 100%;
    max-height: min(92vh, 840px);
    border-radius: var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-large) var(--md-sys-shape-corner-large);
    padding: 20px 16px 16px;
  }

  .admin-dialog-head {
    padding-right: 44px;
  }

  .admin-form-actions {
    flex-direction: column-reverse;
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

/* Legacy pre-modal admin layout disabled after the M3 Expressive redesign.
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
*/
</style>
