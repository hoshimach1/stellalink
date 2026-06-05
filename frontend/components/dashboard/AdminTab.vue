<template>
  <div class="admin-shell">
    <header class="admin-page-head">
      <div class="admin-title">
        <p class="admin-kicker">Админка</p>
        <h2>Системный центр</h2>
        <span>Критичные настройки сгруппированы по задачам: доставка писем, ссылки авторизации и внешние интеграции.</span>
      </div>

      <div class="admin-hero-actions">
        <span class="admin-sync-state">
          <i class="ri-pulse-line" />
          {{ loading || apiLoading ? 'Синхронизация...' : 'Данные из backend' }}
        </span>
        <button class="admin-refresh-button" type="button" :disabled="loading || apiLoading" @click="loadAllSettings">
          <span v-if="loading || apiLoading" class="admin-spinner" />
          <template v-else>
            <i class="ri-refresh-line" />
            <span>Обновить</span>
          </template>
        </button>
      </div>
    </header>

    <section class="admin-status-console" aria-label="Состояние системных настроек">
      <article class="admin-status-card" :class="smtpHealth.tone">
        <span class="admin-status-icon"><i class="ri-mail-check-line" /></span>
        <div>
          <span class="admin-status-label">SMTP</span>
          <strong>{{ smtpHealth.label }}</strong>
          <p>{{ smtpHealth.detail }}</p>
        </div>
      </article>

      <article class="admin-status-card" :class="authLinksHealth.tone">
        <span class="admin-status-icon"><i class="ri-links-line" /></span>
        <div>
          <span class="admin-status-label">Auth links</span>
          <strong>{{ authLinksHealth.label }}</strong>
          <p>{{ authLinksHealth.detail }}</p>
        </div>
      </article>

      <article class="admin-status-card" :class="integrationHealth.tone">
        <span class="admin-status-icon"><i class="ri-plug-2-line" /></span>
        <div>
          <span class="admin-status-label">Интеграции</span>
          <strong>{{ integrationHealth.label }}</strong>
          <p>{{ integrationHealth.detail }}</p>
        </div>
      </article>
    </section>

    <section class="admin-section" aria-labelledby="admin-communication-title">
      <header class="admin-section-head">
        <div>
          <h3 id="admin-communication-title">Коммуникации</h3>
          <p>Письма, публичная база ссылок и быстрая проверка доставки без лишней модалки.</p>
        </div>
      </header>

      <div class="admin-card-grid admin-card-grid-communication">
        <article class="admin-panel-card admin-panel-card-primary">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-mail-settings-line" /></span>
            <div>
              <span class="admin-card-overline">SMTP</span>
              <h4>Почта</h4>
              <p>{{ smtpStatus }}</p>
            </div>
            <span class="admin-status-chip" :class="smtpHealth.tone">{{ smtpHealth.label }}</span>
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

          <button class="admin-card-action" type="button" @click="openDialog('smtp')">
            <i class="ri-edit-line" />
            <span>Редактировать</span>
          </button>
        </article>

        <article class="admin-panel-card">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-links-line" /></span>
            <div>
              <span class="admin-card-overline">Auth links</span>
              <h4>Ссылки и TTL</h4>
              <p>{{ form.frontend_base_url || 'Frontend URL не задан' }}</p>
            </div>
            <span class="admin-status-chip" :class="authLinksHealth.tone">{{ authLinksHealth.label }}</span>
          </div>

          <dl class="admin-facts">
            <div>
              <dt>Email</dt>
              <dd>{{ formatDuration(form.email_verification_ttl_seconds) }}</dd>
            </div>
            <div>
              <dt>Reset</dt>
              <dd>{{ formatDuration(form.password_reset_ttl_seconds) }}</dd>
            </div>
            <div>
              <dt>Base URL</dt>
              <dd>{{ form.frontend_base_url ? 'задан' : 'не задан' }}</dd>
            </div>
          </dl>

          <button class="admin-card-action" type="button" @click="openDialog('links')">
            <i class="ri-time-line" />
            <span>Настроить</span>
          </button>
        </article>

        <article class="admin-panel-card admin-delivery-card">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-send-plane-line" /></span>
            <div>
              <span class="admin-card-overline">Delivery</span>
              <h4>Тест письма</h4>
              <p>Быстрая отправка без перехода в отдельную форму.</p>
            </div>
          </div>

          <dl class="admin-facts">
            <div>
              <dt>Получатель</dt>
              <dd>{{ testEmail || auth.user?.email || 'не выбран' }}</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>{{ form.enabled ? 'готово' : 'выключено' }}</dd>
            </div>
          </dl>

          <form class="admin-inline-action" @submit.prevent="sendTestEmail">
            <label class="admin-field admin-field-compact">
              <span>Email получателя</span>
              <input v-model="testEmail" type="email" :placeholder="auth.user?.email || 'admin@example.com'">
            </label>
            <button class="admin-card-action" type="submit" :disabled="testing || !form.enabled">
              <span v-if="testing" class="admin-spinner" />
              <template v-else>
                <i class="ri-mail-send-line" />
                <span>Отправить</span>
              </template>
            </button>
          </form>

          <div v-if="testNotice" class="admin-note admin-inline-note" :class="testNoticeTone">{{ testNotice }}</div>
        </article>
      </div>
    </section>

    <section class="admin-section" aria-labelledby="admin-integrations-title">
      <header class="admin-section-head">
        <div>
          <h3 id="admin-integrations-title">Интеграции</h3>
          <p>Ключи внешних сервисов разделены по доменам, чтобы не смешивать игровые данные, музыку и Git OAuth.</p>
        </div>
      </header>

      <div class="admin-card-grid">
        <article class="admin-panel-card">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-gamepad-line" /></span>
            <div>
              <span class="admin-card-overline">Games</span>
              <h4>Steam и FACEIT</h4>
              <p>{{ apiStatus }}</p>
            </div>
            <span class="admin-status-chip" :class="gameHealth.tone">{{ gameHealth.label }}</span>
          </div>

          <dl class="admin-facts">
            <div>
              <dt>Steam</dt>
              <dd>{{ steamKeySet ? 'ключ сохранен' : 'без ключа' }}</dd>
            </div>
            <div>
              <dt>FACEIT</dt>
              <dd>{{ faceitKeySet ? 'ключ сохранен' : 'без ключа' }}</dd>
            </div>
            <div>
              <dt>Inventory</dt>
              <dd>{{ apiForm.steam_inventory_app_id }} / {{ apiForm.steam_inventory_context_id }}</dd>
            </div>
          </dl>

          <button class="admin-card-action" type="button" @click="openDialog('games')">
            <i class="ri-key-2-line" />
            <span>Настроить</span>
          </button>
        </article>

        <article class="admin-panel-card">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-spotify-fill" /></span>
            <div>
              <span class="admin-card-overline">Music</span>
              <h4>Spotify</h4>
              <p>OAuth и сервисный токен для музыкальных блоков.</p>
            </div>
            <span class="admin-status-chip" :class="spotifyHealth.tone">{{ spotifyHealth.label }}</span>
          </div>

          <dl class="admin-facts">
            <div>
              <dt>Client ID</dt>
              <dd>{{ oauthForm.spotifyClientId ? 'задан' : 'не задан' }}</dd>
            </div>
            <div>
              <dt>Secret</dt>
              <dd>{{ oauthSecretState.spotifySet ? 'сохранен' : 'не задан' }}</dd>
            </div>
            <div>
              <dt>Token</dt>
              <dd>{{ oauthSecretState.spotifyTokenSet ? 'сохранен' : 'не задан' }}</dd>
            </div>
          </dl>

          <button class="admin-card-action" type="button" @click="openDialog('spotify')">
            <i class="ri-music-2-line" />
            <span>Настроить</span>
          </button>
        </article>

        <article class="admin-panel-card">
          <div class="admin-card-top">
            <span class="admin-card-icon"><i class="ri-git-branch-line" /></span>
            <div>
              <span class="admin-card-overline">Code OAuth</span>
              <h4>Git providers</h4>
              <p>GitHub, GitLab и Gitea для публичных и self-hosted инстансов.</p>
            </div>
            <span class="admin-status-chip" :class="gitHealth.tone">{{ gitHealth.label }}</span>
          </div>

          <div class="provider-strip" aria-label="Статус OAuth провайдеров">
            <span :class="{ ready: oauthSecretState.githubSet }"><i class="ri-github-fill" /> GitHub</span>
            <span :class="{ ready: oauthSecretState.gitlabSet }"><i class="ri-gitlab-fill" /> GitLab</span>
            <span :class="{ ready: oauthSecretState.giteaSet }"><GiteaLogo class="provider-strip-logo" /> Gitea</span>
          </div>

          <button class="admin-card-action" type="button" @click="openDialog('oauth')">
            <i class="ri-lock-password-line" />
            <span>Редактировать</span>
          </button>
        </article>
      </div>
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

          <template v-else-if="activeDialog === 'games'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon"><i class="ri-gamepad-line" /></span>
              <div>
                <p class="admin-kicker">Games</p>
                <h3 id="games-dialog-title">Steam и FACEIT</h3>
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

          <template v-else-if="activeDialog === 'spotify'">
            <header class="admin-dialog-head">
              <span class="admin-dialog-icon"><i class="ri-spotify-fill" /></span>
              <div>
                <p class="admin-kicker">Music</p>
                <h3 id="spotify-dialog-title">Spotify</h3>
                <span>OAuth, API endpoints и сервисный access token.</span>
              </div>
            </header>

            <form class="admin-form" @submit.prevent="saveApiSettings">
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

              <div v-if="apiNotice" class="admin-note" :class="apiNoticeTone">{{ apiNotice }}</div>

              <div class="admin-form-actions">
                <button class="text-btn" type="button" @click="closeDialog">Закрыть</button>
                <button class="filled-btn" type="submit" :disabled="apiSaving">
                  <span v-if="apiSaving" class="admin-spinner" />
                  <span v-else>Сохранить Spotify</span>
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

type AdminDialog = 'smtp' | 'links' | 'games' | 'spotify' | 'oauth'
type AdminTone = 'ready' | 'warn' | 'danger' | 'neutral'

interface AdminHealth {
  label: string
  detail: string
  tone: AdminTone
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
const smtpHealth = computed<AdminHealth>(() => {
  if (!form.enabled) {
    return {
      label: 'Выключена',
      detail: 'Письма не отправляются, backend оставит ссылки в логах.',
      tone: 'warn',
    }
  }
  if (!form.host.trim()) {
    return {
      label: 'Нужен host',
      detail: 'Заполните SMTP host, порт и учетные данные.',
      tone: 'danger',
    }
  }
  return {
    label: 'Готова',
    detail: `${form.host}:${form.port} · ${encryptionMode.value.toUpperCase()}`,
    tone: 'ready',
  }
})
const authLinksHealth = computed<AdminHealth>(() => {
  if (!form.frontend_base_url.trim()) {
    return {
      label: 'Нет URL',
      detail: 'Нужен публичный frontend URL для email-ссылок.',
      tone: 'danger',
    }
  }
  if (form.email_verification_ttl_seconds < 900 || form.password_reset_ttl_seconds < 900) {
    return {
      label: 'Короткий TTL',
      detail: 'Проверьте время жизни ссылок, чтобы пользователи успевали завершать вход.',
      tone: 'warn',
    }
  }
  return {
    label: 'Настроены',
    detail: `${formatDuration(form.email_verification_ttl_seconds)} email · ${formatDuration(form.password_reset_ttl_seconds)} reset`,
    tone: 'ready',
  }
})
const gameHealth = computed<AdminHealth>(() => {
  if (steamKeySet.value && faceitKeySet.value) {
    return {
      label: 'Готово',
      detail: 'Steam и FACEIT ключи сохранены.',
      tone: 'ready',
    }
  }
  if (steamKeySet.value || faceitKeySet.value) {
    return {
      label: 'Частично',
      detail: 'Один из игровых API ключей еще не сохранен.',
      tone: 'warn',
    }
  }
  return {
    label: 'Без ключей',
    detail: 'Steam и FACEIT профили не смогут обновляться автоматически.',
    tone: 'danger',
  }
})
const spotifyHealth = computed<AdminHealth>(() => {
  const oauthReady = Boolean(oauthForm.spotifyClientId.trim() && oauthSecretState.spotifySet)
  if (oauthReady && oauthSecretState.spotifyTokenSet) {
    return {
      label: 'Готово',
      detail: 'OAuth и сервисный токен сохранены.',
      tone: 'ready',
    }
  }
  if (oauthReady || oauthSecretState.spotifyTokenSet) {
    return {
      label: 'Частично',
      detail: 'Проверьте Client ID, Secret и сервисный token.',
      tone: 'warn',
    }
  }
  return {
    label: 'Не задан',
    detail: 'Музыкальные блоки ждут Spotify OAuth настройки.',
    tone: 'neutral',
  }
})
const gitHealth = computed<AdminHealth>(() => {
  const readyCount = [
    oauthForm.githubClientId.trim() && oauthSecretState.githubSet,
    oauthForm.gitlabClientId.trim() && oauthSecretState.gitlabSet,
    oauthForm.giteaClientId.trim() && oauthSecretState.giteaSet,
  ].filter(Boolean).length

  if (readyCount === 3) {
    return {
      label: '3 провайдера',
      detail: 'GitHub, GitLab и Gitea готовы к OAuth.',
      tone: 'ready',
    }
  }
  if (readyCount > 0 || apiForm.code_provider_token_auth_enabled) {
    return {
      label: readyCount > 0 ? `${readyCount} OAuth` : 'Token auth',
      detail: readyCount > 0 ? 'Часть провайдеров готова.' : 'OAuth можно дополнить позже.',
      tone: 'warn',
    }
  }
  return {
    label: 'Не задан',
    detail: 'Добавьте OAuth или включите token auth для Git-интеграций.',
    tone: 'neutral',
  }
})
const integrationHealth = computed<AdminHealth>(() => {
  const readyCount = [gameHealth.value, spotifyHealth.value, gitHealth.value].filter((item) => item.tone === 'ready').length
  if (readyCount === 3) {
    return {
      label: 'Все готовы',
      detail: 'Игры, музыка и Git-интеграции закрыты.',
      tone: 'ready',
    }
  }
  if (readyCount > 0) {
    return {
      label: `${readyCount}/3 готово`,
      detail: 'Остальные домены можно дозаполнить в карточках ниже.',
      tone: 'warn',
    }
  }
  return {
    label: 'Нужна настройка',
    detail: 'Ключи и OAuth еще не закрывают публичные блоки профиля.',
    tone: 'neutral',
  }
})
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
  if (dialog === 'games' || dialog === 'spotify' || dialog === 'oauth') apiNotice.value = ''
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
  width: min(1160px, 100%);
  display: grid;
  gap: var(--md-sys-space-5);
  margin: 0 auto;
}

.admin-shell,
.admin-shell * {
  box-sizing: border-box;
}

.admin-page-head {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: var(--md-sys-space-4);
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-extra-large);
  background:
    radial-gradient(circle at 12% 0%, color-mix(in srgb, var(--md-sys-color-primary-container) 64%, transparent) 0 32%, transparent 54%),
    linear-gradient(135deg, var(--md-sys-color-surface-container-high) 0%, var(--md-sys-color-surface-container-low) 100%);
  padding: var(--md-sys-space-8);
  overflow: hidden;
}

.admin-title,
.admin-section-head > div,
.admin-card-top > div,
.admin-status-card > div,
.admin-dialog-head > div,
.oauth-provider-head > div {
  min-width: 0;
}

.admin-kicker,
.admin-title h2,
.admin-title span,
.admin-section-head h3,
.admin-section-head p,
.admin-card-overline,
.admin-status-label,
.admin-card-top h4,
.admin-card-top p,
.admin-status-card strong,
.admin-status-card p,
.admin-dialog-head h3,
.admin-dialog-head span {
  margin: 0;
}

.admin-kicker,
.admin-card-overline {
  color: var(--md-sys-color-primary);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
  letter-spacing: 0;
}

.admin-title h2 {
  margin-top: 2px;
  color: var(--md-sys-color-on-surface);
  font: var(--md-sys-typescale-headline-small-weight) var(--md-sys-typescale-headline-small-size) / var(--md-sys-typescale-headline-small-line-height) var(--md-sys-typescale-headline-small-font);
}

.admin-title span,
.admin-section-head p,
.admin-card-top p,
.admin-dialog-head span {
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-body-medium-weight) var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
}

.admin-title span {
  display: block;
  max-width: 720px;
  margin-top: 4px;
}

.admin-hero-actions {
  display: flex;
  align-items: center;
  gap: var(--md-sys-space-3);
  justify-self: end;
}

.admin-sync-state {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: var(--md-sys-space-2);
  border-radius: var(--md-sys-shape-corner-full);
  background: color-mix(in srgb, var(--md-sys-color-surface-container-lowest) 72%, transparent);
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 var(--md-sys-space-3);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
  white-space: nowrap;
}

.admin-refresh-button,
.admin-card-action,
.filled-btn,
.text-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--md-sys-space-2);
  border: 1px solid transparent;
  border-radius: var(--md-sys-shape-corner-full);
  padding: 0 var(--md-sys-space-4);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
  cursor: pointer;
  transition:
    transform 220ms var(--md-sys-motion-expressive),
    background 200ms var(--md-sys-motion-standard),
    border-color 200ms var(--md-sys-motion-standard),
    color 200ms var(--md-sys-motion-standard);
}

.admin-refresh-button {
  flex: 0 0 auto;
  border-color: color-mix(in srgb, var(--md-sys-color-primary) 24%, var(--md-sys-color-outline));
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
}

.admin-status-console {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--md-sys-space-3);
}

.admin-status-card {
  min-width: 0;
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  gap: var(--md-sys-space-3);
  align-items: center;
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 82%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-large);
  background: var(--md-sys-color-surface-container-low);
  padding: var(--md-sys-space-4);
}

.admin-status-icon {
  width: 46px;
  height: 46px;
  display: inline-grid;
  place-items: center;
  border-radius: var(--md-sys-shape-corner-large-increased);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-primary);
  font-size: 21px;
}

.admin-status-label {
  display: block;
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.admin-status-card strong {
  display: block;
  color: var(--md-sys-color-on-surface);
  font: var(--md-sys-typescale-title-medium-weight) var(--md-sys-typescale-title-medium-size) / var(--md-sys-typescale-title-medium-line-height) var(--md-sys-typescale-title-medium-font);
}

.admin-status-card p {
  margin-top: 2px;
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.admin-status-card.ready,
.admin-status-chip.ready {
  border-color: color-mix(in srgb, var(--md-sys-color-success) 22%, var(--md-sys-color-outline-variant));
}

.admin-status-card.ready .admin-status-icon,
.admin-status-chip.ready {
  background: var(--md-sys-color-success-container);
  color: var(--md-sys-color-success);
}

.admin-status-card.warn,
.admin-status-chip.warn {
  border-color: color-mix(in srgb, var(--md-sys-color-warning) 26%, var(--md-sys-color-outline-variant));
}

.admin-status-card.warn .admin-status-icon,
.admin-status-chip.warn {
  background: var(--md-sys-color-warning-container);
  color: var(--md-sys-color-warning);
}

.admin-status-card.danger,
.admin-status-chip.danger {
  border-color: color-mix(in srgb, var(--md-sys-color-error) 24%, var(--md-sys-color-outline-variant));
}

.admin-status-card.danger .admin-status-icon,
.admin-status-chip.danger {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.admin-status-card.neutral .admin-status-icon,
.admin-status-chip.neutral {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.admin-section {
  display: grid;
  gap: var(--md-sys-space-3);
}

.admin-section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--md-sys-space-4);
  padding: 0 var(--md-sys-space-1);
}

.admin-section-head h3 {
  color: var(--md-sys-color-on-surface);
  font: var(--md-sys-typescale-title-medium-weight) var(--md-sys-typescale-title-medium-size) / var(--md-sys-typescale-title-medium-line-height) var(--md-sys-typescale-title-medium-font);
}

.admin-card-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--md-sys-space-4);
  width: 100%;
}

.admin-panel-card {
  grid-column: span 4;
  min-width: 0;
  display: grid;
  align-content: start;
  gap: var(--md-sys-space-4);
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-large);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--md-sys-color-surface-container-lowest) 46%, transparent), transparent),
    var(--md-sys-color-surface-container-low);
  color: var(--md-sys-color-on-surface);
  padding: var(--md-sys-space-5);
  transition:
    transform 260ms var(--md-sys-motion-expressive),
    border-color 200ms var(--md-sys-motion-standard),
    background 200ms var(--md-sys-motion-standard);
}

.admin-panel-card-primary {
  grid-column: span 5;
}

.admin-delivery-card {
  grid-column: span 3;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--md-sys-color-tertiary-container) 28%, transparent), transparent 64%),
    var(--md-sys-color-surface-container-low);
}

.admin-card-top {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  align-items: start;
  gap: var(--md-sys-space-3);
}

.admin-card-icon,
.admin-dialog-icon,
.oauth-provider-icon {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.admin-card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--md-sys-shape-corner-large);
  font-size: 21px;
}

.admin-card-top h4,
.admin-dialog-head h3 {
  color: var(--md-sys-color-on-surface);
  font: var(--md-sys-typescale-title-medium-weight) var(--md-sys-typescale-title-medium-size) / var(--md-sys-typescale-title-medium-line-height) var(--md-sys-typescale-title-medium-font);
}

.admin-card-top p {
  display: -webkit-box;
  margin-top: 3px;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.admin-status-chip {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: start;
  border: 1px solid transparent;
  border-radius: var(--md-sys-shape-corner-full);
  padding: 0 var(--md-sys-space-3);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
  white-space: nowrap;
}

.admin-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--md-sys-space-2);
  margin: 0;
}

.admin-facts div {
  min-width: 0;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  padding: var(--md-sys-space-3);
}

.admin-facts dt {
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.admin-facts dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: var(--md-sys-color-on-surface);
  font: 850 var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
}

.provider-strip {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-sys-space-2);
}

.provider-strip span {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: var(--md-sys-space-2);
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 var(--md-sys-space-3);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.provider-strip span.ready {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.provider-strip-logo {
  width: 18px;
  height: 18px;
}

.admin-card-action {
  align-self: end;
  justify-self: start;
  margin-top: auto;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.admin-inline-action {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--md-sys-space-3);
}

.admin-field-compact input {
  min-height: 44px;
}

.admin-inline-note {
  margin-top: calc(var(--md-sys-space-2) * -1);
}

.filled-btn {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.text-btn {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.admin-refresh-button:disabled,
.admin-card-action:disabled,
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
  place-items: center end;
  padding: var(--md-sys-space-6);
  background: color-mix(in srgb, var(--md-sys-color-inverse-surface) 42%, transparent);
  backdrop-filter: blur(10px);
}

.admin-dialog {
  position: relative;
  width: min(760px, 100%);
  max-height: calc(100vh - 48px);
  display: grid;
  gap: var(--md-sys-space-5);
  overflow: auto;
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 82%, transparent);
  border-radius: var(--md-sys-shape-corner-extra-large-increased);
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  padding: var(--md-sys-space-6);
  box-shadow: var(--shadow-mid);
}

.admin-dialog-close {
  position: absolute;
  top: var(--md-sys-space-4);
  right: var(--md-sys-space-4);
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
  gap: var(--md-sys-space-3);
  padding-right: 44px;
}

.admin-dialog-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--md-sys-shape-corner-large);
  font-size: 24px;
}

.admin-form {
  display: grid;
  gap: var(--md-sys-space-3);
}

.admin-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 0.46fr);
  gap: var(--md-sys-space-3);
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
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
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
  padding: 0 var(--md-sys-space-3);
  transition:
    border-color 200ms var(--md-sys-motion-standard),
    box-shadow 200ms var(--md-sys-motion-standard),
    background 200ms var(--md-sys-motion-standard);
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
  gap: var(--md-sys-space-3);
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  padding: var(--md-sys-space-3);
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
  font: 850 var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
}

.admin-switch small {
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.oauth-provider {
  display: grid;
  gap: var(--md-sys-space-3);
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 88%, transparent);
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-high);
  padding: var(--md-sys-space-3);
}

.oauth-provider-head {
  display: flex;
  align-items: center;
  gap: var(--md-sys-space-3);
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
  font: 850 var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
}

.oauth-provider-head span {
  color: var(--md-sys-color-on-surface-variant);
  font: var(--md-sys-typescale-label-medium-weight) var(--md-sys-typescale-label-medium-size) / var(--md-sys-typescale-label-medium-line-height) var(--md-sys-typescale-label-medium-font);
}

.admin-note {
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  padding: var(--md-sys-space-3) var(--md-sys-space-4);
  font: var(--md-sys-typescale-body-medium-weight) var(--md-sys-typescale-body-medium-size) / var(--md-sys-typescale-body-medium-line-height) var(--md-sys-typescale-body-medium-font);
}

.admin-note strong {
  color: var(--md-sys-color-on-surface);
  overflow-wrap: anywhere;
}

.admin-note.success {
  background: var(--md-sys-color-success-container);
  color: var(--md-sys-color-success);
}

.admin-note.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.admin-note.muted {
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
}

.admin-form-actions {
  position: sticky;
  bottom: calc(var(--md-sys-space-6) * -1);
  display: flex;
  justify-content: flex-end;
  gap: var(--md-sys-space-2);
  margin: 0 calc(var(--md-sys-space-6) * -1) calc(var(--md-sys-space-6) * -1);
  padding: var(--md-sys-space-3) var(--md-sys-space-6) var(--md-sys-space-5);
  border-top: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 72%, transparent);
  background: color-mix(in srgb, var(--md-sys-color-surface-container-highest) 92%, transparent);
  backdrop-filter: blur(14px);
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

.admin-refresh-button:focus-visible,
.admin-card-action:focus-visible,
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
  .admin-refresh-button:hover:not(:disabled),
  .admin-card-action:hover:not(:disabled),
  .filled-btn:hover:not(:disabled),
  .text-btn:hover:not(:disabled),
  .admin-dialog-close:hover {
    transform: translateY(-1px);
  }

  .admin-panel-card:hover {
    transform: translateY(-2px);
    border-color: color-mix(in srgb, var(--md-sys-color-primary) 28%, var(--md-sys-color-outline-variant));
  }
}

.admin-dialog-enter-active,
.admin-dialog-leave-active {
  transition: opacity 220ms var(--md-sys-motion-standard);
}

.admin-dialog-enter-active .admin-dialog,
.admin-dialog-leave-active .admin-dialog {
  transition:
    opacity 240ms var(--md-sys-motion-standard),
    transform 300ms var(--md-sys-motion-expressive);
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

  .admin-page-head,
  .admin-status-console {
    grid-template-columns: 1fr;
  }

  .admin-hero-actions {
    justify-self: stretch;
  }

  .admin-card-grid {
    grid-template-columns: 1fr;
  }

  .admin-panel-card,
  .admin-panel-card-primary,
  .admin-delivery-card {
    grid-column: auto;
    min-height: 0;
  }
}

@media (max-width: 680px) {
  .admin-shell {
    gap: var(--md-sys-space-4);
  }

  .admin-page-head {
    padding: var(--md-sys-space-4);
    border-radius: var(--md-sys-shape-corner-large-increased);
  }

  .admin-hero-actions,
  .admin-sync-state {
    width: 100%;
  }

  .admin-hero-actions {
    display: grid;
    grid-template-columns: 1fr;
  }

  .admin-refresh-button,
  .admin-card-action,
  .admin-form-actions .filled-btn,
  .admin-form-actions .text-btn {
    width: 100%;
  }

  .admin-card-top {
    grid-template-columns: 44px minmax(0, 1fr);
  }

  .admin-card-icon {
    width: 44px;
    height: 44px;
  }

  .admin-status-chip {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .admin-facts,
  .admin-row {
    grid-template-columns: 1fr;
  }

  .admin-field.small {
    min-width: 0;
  }

  .admin-dialog-overlay {
    place-items: end center;
    padding: var(--md-sys-space-2);
  }

  .admin-dialog {
    width: 100%;
    max-height: min(92vh, 840px);
    border-radius: var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-large) var(--md-sys-shape-corner-large);
    padding: var(--md-sys-space-5) var(--md-sys-space-4) var(--md-sys-space-4);
  }

  .admin-dialog-head {
    padding-right: 44px;
  }

  .admin-form-actions {
    flex-direction: column-reverse;
    bottom: calc(var(--md-sys-space-4) * -1);
    margin: 0 calc(var(--md-sys-space-4) * -1) calc(var(--md-sys-space-4) * -1);
    padding: var(--md-sys-space-3) var(--md-sys-space-4) var(--md-sys-space-4);
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
