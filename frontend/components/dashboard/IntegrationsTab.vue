<template>
  <div class="integrations-shell" :class="{ 'is-loading': loading }">
    <section class="integrations-summary" aria-label="Сводка сервисов">
      <div class="summary-copy">
        <span class="summary-icon" aria-hidden="true">
          <i class="ri-plug-line" />
        </span>
        <div class="summary-text">
          <h2>Сервисы</h2>
          <p>Подключения, которые могут автоматически наполнять публичный профиль.</p>
        </div>
      </div>

      <div class="summary-stats">
        <span class="summary-pill strong">
          <strong>{{ connectedCount }}</strong>
          подключено
        </span>
        <span class="summary-pill">
          {{ inactiveCount }} доступно
        </span>
      </div>
    </section>

    <div class="integration-notice" :class="{ visible: loading }" aria-live="polite">
      <span class="integration-spinner dark" />
      Загружаем подключения...
    </div>

    <section class="service-list" aria-label="Сервисы">
      <article
        v-for="service in serviceCards"
        :key="service.type"
        class="service-card"
        :class="[{ connected: service.connected, available: service.canConnect }, service.type]"
      >
        <div class="service-main">
          <span class="service-icon">
            <FaceitLogo v-if="service.type === 'widget_faceit'" class="faceit-logo" />
            <GiteaLogo v-else-if="service.type === 'code_gitea'" class="gitea-logo" />
            <i aria-hidden="true" v-else :class="service.icon" />
          </span>

          <div class="service-copy">
            <div class="service-title-row">
              <h3>{{ service.label }}</h3>
              <Transition name="service-data" mode="out-in">
                <span :key="`${service.type}:${service.statusLabel}`" class="service-status" :class="service.statusTone">
                  <i aria-hidden="true" :class="service.statusIcon" />
                  {{ service.statusLabel }}
                </span>
              </Transition>
            </div>
            <Transition name="service-data" mode="out-in">
              <span v-if="service.accountLabel" :key="`${service.type}:${service.accountLabel}`" class="service-account">{{ service.accountLabel }}</span>
            </Transition>
            <p>{{ service.description }}</p>
          </div>
        </div>

        <div class="service-controls">
          <Transition name="service-swap" mode="out-in">
          <div v-if="service.type === 'widget_steam'" :key="`${service.type}:${service.connected}:${service.canConnect}:${service.accountLabel}`" class="steam-connect">
            <button v-if="!steamAccount" class="steam-login" type="button" :disabled="steamOauthBusy" @click="startSteamLogin">
              <span v-if="steamOauthBusy" class="integration-spinner" />
              <i aria-hidden="true" v-else class="ri-steam-fill" />
              <span>Войти через Steam</span>
            </button>

            <div v-if="steamAccount" class="steam-actions">
              <button class="service-action danger" type="button" :disabled="steamBusy" @click="disconnectSteamConnection">
                <i aria-hidden="true" class="ri-link-unlink-m" />
                <span>Отключить</span>
              </button>
            </div>
          </div>

          <div v-else-if="service.type === 'widget_faceit'" :key="`${service.type}:${service.connected}:${service.canConnect}:${service.accountLabel}`" class="faceit-block">
            <span class="service-hint">Автопоиск</span>
          </div>

          <div v-else-if="service.type === 'widget_spotify'" :key="`${service.type}:${service.connected}:${service.canConnect}:${service.accountLabel}`" class="spotify-connect">
            <div v-if="spotifyAccount" class="steam-actions">
              <button class="service-action danger" type="button" :disabled="spotifyBusy" @click="disconnectSpotifyConnection">
                <i aria-hidden="true" class="ri-link-unlink-m" />
                <span>Отключить</span>
              </button>
            </div>

            <button
              v-else
              class="spotify-login"
              type="button"
              :disabled="spotifyOauthBusy || !spotifyOAuthReady"
              @click="startSpotifyLogin"
            >
              <span v-if="spotifyOauthBusy" class="integration-spinner" />
              <i aria-hidden="true" v-else class="ri-spotify-fill" />
              <span>{{ spotifyOAuthReady ? 'Войти через Spotify' : 'OAuth не настроен' }}</span>
            </button>
          </div>

          <div v-else-if="service.provider" :key="`${service.type}:${service.connected}:${service.canConnect}:${service.accountLabel}`" class="code-provider-block">
            <div v-if="codeProviderAccount(service.provider)" class="steam-actions">
              <button class="service-action danger" type="button" :disabled="codeBusy === `${service.provider}:disconnect`" @click="disconnectCodeProvider(service.provider)">
                <i aria-hidden="true" class="ri-link-unlink-m" />
                <span>Отключить</span>
              </button>
            </div>

            <button
              v-else
              class="service-action primary"
              type="button"
              :disabled="codeBusy === `${service.provider}:connect`"
              @click="startCodeProviderConnect(service.provider)"
            >
              <span v-if="codeBusy === `${service.provider}:connect`" class="integration-spinner" />
              <template v-else>
                <i aria-hidden="true" class="ri-link-m" />
                <span>Подключить</span>
              </template>
            </button>
          </div>

          <button
            v-else
            :key="`${service.type}:${service.connected}:${service.canConnect}:${service.accountLabel}`"
            class="service-action"
            :class="{ primary: service.canConnect, complete: service.connected }"
            type="button"
            :disabled="!service.canConnect || connectingType === service.type"
            @click="connectService(service.type)"
          >
            <span v-if="connectingType === service.type" class="integration-spinner" />
            <i aria-hidden="true" v-else :class="service.actionIcon" />
            <span>{{ service.actionLabel }}</span>
          </button>
          </Transition>
        </div>
      </article>
    </section>

    <Teleport to="body">
      <Transition name="integration-modal">
        <div v-if="codeProviderModal.provider && activeCodeProvider" class="integration-modal-overlay" @click.self="closeCodeProviderModal">
          <section class="integration-modal" role="dialog" aria-modal="true" :aria-labelledby="`code-provider-title-${activeCodeProvider.provider}`">
            <button class="integration-modal-close" type="button" aria-label="Закрыть" @click="closeCodeProviderModal">
              <i aria-hidden="true" class="ri-close-line" />
            </button>

            <div class="integration-modal-head">
              <span class="integration-modal-icon">
                <GiteaLogo v-if="activeCodeProvider.provider === 'gitea'" class="gitea-logo" />
                <i aria-hidden="true" v-else :class="activeCodeProvider.icon" />
              </span>
              <h2 :id="`code-provider-title-${activeCodeProvider.provider}`">
                {{ codeProviderModal.step === 'choice' ? activeCodeProvider.label : 'Через token' }}
              </h2>
              <p>{{ codeProviderModalSubtitle }}</p>
            </div>

            <div v-if="codeProviderModal.step === 'choice'" class="integration-modal-actions">
              <button
                class="modal-auth-button primary"
                type="button"
                :disabled="!canStartCodeProviderOAuth(activeCodeProvider.provider) || codeBusy === `${activeCodeProvider.provider}:connect`"
                @click="startCodeProviderOAuth(activeCodeProvider.provider)"
              >
                <span v-if="codeBusy === `${activeCodeProvider.provider}:connect`" class="integration-spinner dark" />
                <template v-else>
                  <span>Авторизоваться {{ activeCodeProvider.label }}</span>
                  <i aria-hidden="true" :class="activeCodeProvider.provider === 'gitea' ? 'ri-login-circle-line' : activeCodeProvider.icon" />
                </template>
              </button>

              <button class="modal-auth-button secondary" type="button" @click="showCodeProviderTokenServer(activeCodeProvider.provider)">
                <i aria-hidden="true" class="ri-key-2-line" />
                <span>Привязать через token</span>
              </button>

              <span v-if="!codeProviderOAuthReady(activeCodeProvider.provider)" class="modal-hint">
                OAuth app не настроен в админке.
              </span>
            </div>

            <div v-else-if="codeProviderModal.step === 'server'" class="integration-modal-form">
              <label class="provider-field modal-field">
                <span>Git server</span>
                <input
                  v-model="codeProviderInputs[activeCodeProvider.provider].base_url"
                  type="text"
                  inputmode="url"
                  placeholder="git.example.com"
                >
              </label>

              <button
                class="modal-auth-button secondary"
                type="button"
                :disabled="!codeProviderBaseInput(activeCodeProvider.provider)"
                @click="openTokenCreateUrl(activeCodeProvider.provider)"
              >
                <i aria-hidden="true" class="ri-external-link-line" />
                <span>Создать token</span>
              </button>
            </div>

            <div v-else class="integration-modal-form">
              <label class="provider-field modal-field">
                <span>Access token</span>
                <input v-model="codeProviderInputs[activeCodeProvider.provider].token" type="password" autocomplete="new-password" placeholder="...">
              </label>

              <button
                class="modal-auth-button secondary"
                type="button"
                :disabled="!canSubmitCodeProvider(activeCodeProvider.provider) || codeBusy === `${activeCodeProvider.provider}:connect`"
                @click="connectCodeProvider(activeCodeProvider.provider)"
              >
                <span v-if="codeBusy === `${activeCodeProvider.provider}:connect`" class="integration-spinner dark" />
                <template v-else>
                  <i aria-hidden="true" class="ri-link-m" />
                  <span>Привязать</span>
                </template>
              </button>
            </div>

            <button v-if="codeProviderModal.step !== 'choice'" class="integration-modal-back" type="button" @click="codeProviderModal.step = 'choice'">
              <i aria-hidden="true" class="ri-arrow-left-line" />
              <span>Назад</span>
            </button>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { BLOCK_LIBRARY, createDefaultBlockConfig } from '~/utils/dashboard-studio'
import { useProfileStore, type Block } from '~/stores/profile'
import { useAuthStore } from '~/stores/auth'
import { extractAuthError } from '~/utils/auth-feedback'

const profile = useProfileStore()
const auth = useAuthStore()
const config = useRuntimeConfig()
const route = useRoute()
const { pushToast } = useAppToast()

type CodeProvider = 'github' | 'gitlab' | 'gitea'
type IntegrationType = 'widget_steam' | 'widget_lastfm' | 'widget_faceit' | 'widget_spotify'
type NoticeTone = 'success' | 'error'
type CodeProviderMode = 'token' | 'oauth'
const TOKEN_NAME = 'Stellalink'
const TOKEN_SCOPES: Record<CodeProvider, string[]> = {
  github: ['read:user', 'repo'],
  gitlab: ['read_user', 'read_api'],
  gitea: ['read:user', 'read:repository'],
}
type ConnectedAccount = {
  id: string
  provider: string
  provider_uid: string
  display_name: string | null
  is_active: boolean
  last_synced_at: string | null
  sync_error: string | null
  metadata: Record<string, any>
}
type IntegrationsResponse = {
  accounts: ConnectedAccount[]
  capabilities: {
    steam_api_key_set: boolean
    faceit_api_key_set: boolean
    steam_inventory_prices_supported: boolean
    github_oauth_ready: boolean
    gitlab_oauth_ready: boolean
    gitea_oauth_ready: boolean
    spotify_oauth_ready: boolean
    code_provider_token_auth_enabled: boolean
  }
}

const integrationTypes = new Set<IntegrationType>(['widget_steam', 'widget_faceit', 'widget_spotify', 'widget_lastfm'])
const integrationOrder: IntegrationType[] = ['widget_steam', 'widget_faceit', 'widget_spotify', 'widget_lastfm']
const connectableTypes = new Set<IntegrationType>(['widget_lastfm'])
const codeProviderDefinitions = [
  {
    type: 'code_github',
    provider: 'github' as const,
    icon: 'ri-github-fill',
    label: 'GitHub',
    defaultBaseUrl: 'https://github.com',
    description: 'Подключите GitHub через personal access token или OAuth, включая GitHub Enterprise Server.',
  },
  {
    type: 'code_gitlab',
    provider: 'gitlab' as const,
    icon: 'ri-gitlab-fill',
    label: 'GitLab',
    defaultBaseUrl: 'https://gitlab.com',
    description: 'Подключите GitLab.com или self-managed GitLab через token/OAuth.',
  },
  {
    type: 'code_gitea',
    provider: 'gitea' as const,
    icon: '',
    label: 'Gitea',
    defaultBaseUrl: 'https://gitea.com',
    description: 'Подключите Gitea.com или self-hosted Gitea через token/OAuth.',
  },
]
const integrations = ref<IntegrationsResponse | null>(null)
const loading = ref(false)
const steamBusy = ref(false)
const steamOauthBusy = ref(false)
const spotifyBusy = ref(false)
const spotifyOauthBusy = ref(false)
const connectingType = ref<IntegrationType | null>(null)
const codeBusy = ref<string | null>(null)
const codeProviderInputs = reactive<Record<CodeProvider, { mode: CodeProviderMode; base_url: string; token: string }>>({
  github: { mode: 'token', base_url: '', token: '' },
  gitlab: { mode: 'token', base_url: '', token: '' },
  gitea: { mode: 'token', base_url: '', token: '' },
})
type CodeProviderModalStep = 'choice' | 'server' | 'token'
const codeProviderModal = reactive<{ provider: CodeProvider | null; step: CodeProviderModalStep }>({
  provider: null,
  step: 'choice',
})

const steamAccount = computed(() => integrations.value?.accounts.find(account => account.provider === 'steam' && account.is_active) ?? null)
const faceitAccount = computed(() => integrations.value?.accounts.find(account => account.provider === 'faceit' && account.is_active) ?? null)
const spotifyAccount = computed(() => integrations.value?.accounts.find(account => account.provider === 'spotify' && account.is_active) ?? null)
const spotifyOAuthReady = computed(() => Boolean(integrations.value?.capabilities.spotify_oauth_ready))
const spotifyDisplayName = computed(() => String(spotifyAccount.value?.display_name || spotifyAccount.value?.metadata?.spotify_profile?.display_name || 'Spotify'))
const spotifyPlaybackLabel = computed(() => {
  const playback = spotifyAccount.value?.metadata?.playback
  const track = playback?.track
  if (!playback) return 'Статистика ещё не синхронизирована'
  if (!track) return playback.message || 'Сейчас ничего не слушает'
  const artist = track.artist_names ? ` · ${track.artist_names}` : ''
  return `${playback.status_label || 'Spotify'}: ${track.name}${artist}`
})
const blockConnectedTypes = computed(() => new Set(profile.profile?.blocks.map(block => block.block_type) ?? []))
const connectedTypes = computed(() => {
  const set = new Set<string>()
  if (blockConnectedTypes.value.has('widget_lastfm')) set.add('widget_lastfm')
  if (steamAccount.value) set.add('widget_steam')
  if (faceitAccount.value) set.add('widget_faceit')
  if (spotifyAccount.value) set.add('widget_spotify')
  for (const provider of codeProviderDefinitions) {
    if (codeProviderAccount(provider.provider)) set.add(provider.type)
  }
  return set
})
const serviceCards = computed(() => {
  const baseCards = BLOCK_LIBRARY
    .filter(item => integrationTypes.has(item.type as IntegrationType))
    .sort((a, b) => integrationOrder.indexOf(a.type as IntegrationType) - integrationOrder.indexOf(b.type as IntegrationType))
    .map((item) => {
      const type = item.type as IntegrationType
      const connected = connectedTypes.value.has(type)
      const apiReady = integrations.value?.capabilities
      const steamDescription = steamAccount.value
        ? `${steamAccount.value.display_name || steamAccount.value.provider_uid}: профиль, последние игры и Steam-статистика синхронизированы.`
        : apiReady?.steam_api_key_set
          ? 'Войдите через Steam, чтобы подтвердить владение аккаунтом и подтянуть Steam и FACEIT-данные.'
          : 'Администратору нужно добавить Steam Web API key, после этого профиль можно будет привязать.'
      const faceitDescription = faceitAccount.value
        ? `${faceitAccount.value.display_name || 'FACEIT'} подключен через Steam: уровень, ELO и статистика доступны для блока.`
        : apiReady?.faceit_api_key_set
          ? 'FACEIT подключится автоматически после входа через Steam.'
          : 'FACEIT подключается автоматически после Steam, когда сервис доступен.'
      const spotifyDescription = spotifyAccount.value
        ? `${spotifyDisplayName.value}: текущий трек, недавние прослушивания и топы Spotify доступны для блока.`
        : apiReady?.spotify_oauth_ready
          ? 'Войдите через Spotify, чтобы показывать текущий трек в реальном времени и музыкальную статистику.'
          : 'Администратору нужно добавить Spotify Client ID и Client Secret.'
      const descriptions: Partial<Record<IntegrationType, string>> = {
        widget_steam: steamDescription,
        widget_faceit: faceitDescription,
        widget_spotify: spotifyDescription,
        widget_lastfm: 'Подключите Last.fm, чтобы показывать текущий трек и музыкальную активность.',
      }
      return {
        ...item,
        actionIcon: connected ? 'ri-checkbox-circle-line' : 'ri-plug-line',
        accountLabel: type === 'widget_steam'
          ? steamAccount.value?.display_name || steamAccount.value?.provider_uid || ''
          : type === 'widget_faceit'
            ? faceitAccount.value?.display_name || ''
            : type === 'widget_spotify'
              ? spotifyDisplayName.value
              : '',
        actionLabel: connected ? 'Подключено' : 'Подключиться',
        canConnect: (type === 'widget_spotify' ? Boolean(apiReady?.spotify_oauth_ready) : connectableTypes.has(type)) && !connected,
        connected,
        description: descriptions[type] ?? item.description,
        statusIcon: connected ? 'ri-checkbox-circle-line' : 'ri-circle-line',
        statusLabel: connected ? 'Подключено' : 'Не подключено',
        statusTone: connected ? 'connected' : 'default',
      }
    })
  const codeCards = codeProviderDefinitions.map((item) => {
    const connected = Boolean(codeProviderAccount(item.provider))
    return {
      ...item,
      actionIcon: connected ? 'ri-checkbox-circle-line' : 'ri-key-2-line',
      accountLabel: connected ? codeProviderUsername(item.provider) : '',
      actionLabel: connected ? 'Подключено' : 'Подключиться',
      canConnect: !connected,
      connected,
      statusIcon: connected ? 'ri-checkbox-circle-line' : 'ri-circle-line',
      statusLabel: connected ? 'Подключено' : 'Не подключено',
      statusTone: connected ? 'connected' : 'default',
    }
  })
  const byType = new Map([...baseCards, ...codeCards].map(card => [card.type, card]))
  return ['widget_steam', 'widget_faceit', 'widget_spotify', 'code_github', 'code_gitlab', 'code_gitea', 'widget_lastfm']
    .map(type => byType.get(type))
    .filter(Boolean)
})
const connectedCount = computed(() => serviceCards.value.filter(service => service.connected).length)
const inactiveCount = computed(() => Math.max(serviceCards.value.length - connectedCount.value, 0))
const activeCodeProvider = computed(() => (
  codeProviderModal.provider
    ? codeProviderDefinitions.find(item => item.provider === codeProviderModal.provider) ?? null
    : null
))
const codeProviderModalSubtitle = computed(() => {
  if (!codeProviderModal.provider) return ''
  if (codeProviderModal.step === 'server') return `Введите ссылку на ваш ${codeProviderLabel(codeProviderModal.provider)} Server`
  if (codeProviderModal.step === 'token') return 'Введите token, который вы получили'
  return 'Выберите вариант авторизации'
})

onMounted(() => {
  readSteamRedirectResult()
  readSpotifyRedirectResult()
  readIntegrationRedirectResult()
  void loadIntegrations()
})

function readSteamRedirectResult() {
  if (route.query.steam === 'connected') {
    setIntegrationNotice('Steam привязан через официальный вход.', 'success')
    return
  }
  if (route.query.steam === 'error') {
    setIntegrationNotice(typeof route.query.steam_error === 'string'
      ? route.query.steam_error
      : 'Не удалось завершить вход через Steam.', 'error')
  }
}

function readSpotifyRedirectResult() {
  if (route.query.spotify === 'connected') {
    setIntegrationNotice('Spotify подключён через OAuth.', 'success')
    return
  }
  if (route.query.spotify === 'error') {
    setIntegrationNotice(typeof route.query.spotify_error === 'string'
      ? route.query.spotify_error
      : 'Не удалось завершить подключение Spotify.', 'error')
  }
}

function readIntegrationRedirectResult() {
  if (route.query.integration_status === 'connected' && typeof route.query.integration === 'string') {
    setIntegrationNotice(`${codeProviderLabel(route.query.integration)} подключён через OAuth.`, 'success')
    return
  }
  if (route.query.integration_status === 'error') {
    setIntegrationNotice(typeof route.query.integration_error === 'string'
      ? route.query.integration_error
      : 'Не удалось завершить OAuth-подключение.', 'error')
  }
}

function setIntegrationNotice(message: string, tone: NoticeTone) {
  pushToast(message, tone)
}

function applyIntegrations(data: IntegrationsResponse) {
  integrations.value = data
}

async function loadIntegrations() {
  loading.value = true
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/me`)
    applyIntegrations(data)
    if (steamAccount.value) {
      await ensureSteamBlock()
    }
    if (spotifyAccount.value) {
      await ensureSpotifyBlock()
    }
    const firstGitProvider = codeProviderDefinitions.find(item => codeProviderAccount(item.provider))?.provider
    if (firstGitProvider) {
      await ensureGitBlock(firstGitProvider)
    }
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось загрузить подключения.'), 'error')
  } finally {
    loading.value = false
  }
}

async function ensureGitBlock(provider: CodeProvider) {
  if (!profile.profile) return
  const account = codeProviderAccount(provider)
  if (!account) return
  const existing = profile.profile?.blocks.find((block: Block) => block.block_type === 'widget_github' && gitBlockProvider(block) === provider)
  const currentConfig = existing ? sanitizedGitBlockConfig(existing.config) : null
  const username = account.metadata?.username || account.display_name || ''
  const nextConfig: Record<string, unknown> = {
    ...(currentConfig ?? createDefaultBlockConfig('widget_github')),
    use_connected_account: true,
    provider,
    username,
    show_contributions: currentConfig?.show_contributions ?? true,
    contributions_days: currentConfig?.contributions_days ?? 30,
    show_repository_stats: currentConfig?.show_repository_stats ?? true,
    show_pinned_repos: currentConfig?.show_pinned_repos ?? true,
    include_private_repositories: currentConfig?.include_private_repositories ?? false,
  }

  if (existing) {
    if (JSON.stringify(currentConfig) !== JSON.stringify(nextConfig)) {
      await profile.updateBlock(existing.id, { config: nextConfig })
    }
  } else {
    await profile.createBlock('widget_github', nextConfig)
  }
}

function gitBlockProvider(block: Block): CodeProvider {
  const provider = String(block.config.provider || block.config.git_provider || 'github')
  return ['github', 'gitlab', 'gitea'].includes(provider) ? provider as CodeProvider : 'github'
}

function sanitizedGitBlockConfig(value: Record<string, unknown>) {
  const clean = { ...value }
  delete clean.git_provider
  delete clean.git_provider_label
  delete clean.git_display_name
  delete clean.git_profile
  delete clean.git_repository_stats
  delete clean.git_pinned_repositories
  delete clean.git_repositories
  delete clean.git_contributions
  delete clean.git_activity_sync_error
  delete clean.git_sync_error
  delete clean.git_last_synced_at
  delete clean.connected_account_id
  delete clean.github_display_name
  delete clean.github_profile
  delete clean.github_sync_error
  delete clean.github_last_synced_at
  return clean
}

async function ensureSteamBlock() {
  if (!profile.profile) return
  const existing = profile.profile?.blocks.find((block: Block) => block.block_type === 'widget_steam')
  const currentConfig = existing ? sanitizedSteamBlockConfig(existing.config) : null
  const nextConfig: Record<string, unknown> = {
    ...(currentConfig ?? createDefaultBlockConfig('widget_steam')),
    use_connected_account: true,
    show_recent_games: currentConfig?.show_recent_games ?? true,
    show_profile_stats: currentConfig?.show_profile_stats ?? true,
    show_inventory_highlight: currentConfig?.show_inventory_highlight ?? true,
  }

  if (existing) {
    if (JSON.stringify(currentConfig) !== JSON.stringify(nextConfig)) {
      await profile.updateBlock(existing.id, { config: nextConfig })
    }
  } else {
    await profile.createBlock('widget_steam', nextConfig)
  }
}

function sanitizedSteamBlockConfig(value: Record<string, unknown>) {
  const clean = { ...value }
  delete clean.steam_id
  delete clean.steam_display_name
  delete clean.connected_account_id
  delete clean.steam_profile
  delete clean.steam_recent_games
  delete clean.steam_profile_stats
  delete clean.steam_inventory_highlight
  delete clean.steam_sync_error
  delete clean.steam_last_synced_at
  delete clean.faceit_profile
  return clean
}

async function ensureSpotifyBlock() {
  if (!profile.profile) return
  const existing = profile.profile?.blocks.find((block: Block) => block.block_type === 'widget_spotify')
  const currentConfig = existing ? sanitizedSpotifyBlockConfig(existing.config) : null
  const nextConfig: Record<string, unknown> = {
    ...(currentConfig ?? createDefaultBlockConfig('widget_spotify')),
    use_connected_account: true,
    show_now_playing: currentConfig?.show_now_playing ?? true,
    show_recent_tracks: currentConfig?.show_recent_tracks ?? true,
    show_top_tracks: currentConfig?.show_top_tracks ?? true,
    show_top_artists: currentConfig?.show_top_artists ?? true,
    show_stats: currentConfig?.show_stats ?? true,
  }

  if (existing) {
    if (JSON.stringify(currentConfig) !== JSON.stringify(nextConfig)) {
      await profile.updateBlock(existing.id, { config: nextConfig })
    }
  } else {
    await profile.createBlock('widget_spotify', nextConfig)
  }
}

function sanitizedSpotifyBlockConfig(value: Record<string, unknown>) {
  const clean = { ...value }
  delete clean.spotify_display_name
  delete clean.spotify_profile
  delete clean.spotify_playback
  delete clean.spotify_recent_tracks
  delete clean.spotify_top_tracks
  delete clean.spotify_top_artists
  delete clean.spotify_stats
  delete clean.spotify_sync_error
  delete clean.spotify_last_synced_at
  delete clean.connected_account_id
  return clean
}

async function startSteamLogin() {
  steamOauthBusy.value = true
  try {
    const response = await auth.authorizedFetch<{ auth_url: string }>(
      `${config.public.apiBase}/integrations/steam/openid/start`,
      { method: 'POST' },
    )
    window.location.assign(response.auth_url)
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось начать вход через Steam.'), 'error')
    steamOauthBusy.value = false
  }
}

async function disconnectSteamConnection() {
  steamBusy.value = true
  try {
    await auth.authorizedFetch(`${config.public.apiBase}/integrations/steam`, { method: 'DELETE' })
    await loadIntegrations()
    await profile.fetch()
    setIntegrationNotice('Steam отключён от аккаунта.', 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось отключить Steam.'), 'error')
  } finally {
    steamBusy.value = false
  }
}

async function startSpotifyLogin() {
  if (!spotifyOAuthReady.value) {
    setIntegrationNotice('Spotify OAuth не настроен в админке.', 'error')
    return
  }
  spotifyOauthBusy.value = true
  try {
    const response = await auth.authorizedFetch<{ auth_url: string }>(
      `${config.public.apiBase}/integrations/spotify/oauth/start`,
      { method: 'POST' },
    )
    window.location.assign(response.auth_url)
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось начать вход через Spotify.'), 'error')
    spotifyOauthBusy.value = false
  }
}

async function disconnectSpotifyConnection() {
  spotifyBusy.value = true
  try {
    await auth.authorizedFetch(`${config.public.apiBase}/integrations/spotify`, { method: 'DELETE' })
    await loadIntegrations()
    await profile.fetch()
    setIntegrationNotice('Spotify отключён от аккаунта.', 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось отключить Spotify.'), 'error')
  } finally {
    spotifyBusy.value = false
  }
}

function codeProviderLabel(provider: string) {
  const labels: Record<string, string> = {
    github: 'GitHub',
    gitlab: 'GitLab',
    gitea: 'Gitea',
    code: 'Интеграция',
  }
  return labels[provider] ?? provider
}

function codeProviderAccount(provider: CodeProvider): ConnectedAccount | null {
  return integrations.value?.accounts.find(account => account.provider === provider && account.is_active) ?? null
}

function codeProviderUsername(provider: CodeProvider): string {
  const account = codeProviderAccount(provider)
  return String(account?.metadata?.username || account?.display_name || account?.provider_uid || codeProviderLabel(provider))
}

function codeProviderBaseUrl(provider: CodeProvider): string {
  const account = codeProviderAccount(provider)
  const definition = codeProviderDefinitions.find(item => item.provider === provider)
  return String(account?.metadata?.base_url || definition?.defaultBaseUrl || '')
}

function codeProviderOAuthReady(provider: CodeProvider): boolean {
  const capabilities = integrations.value?.capabilities
  if (provider === 'github') return Boolean(capabilities?.github_oauth_ready)
  if (provider === 'gitlab') return Boolean(capabilities?.gitlab_oauth_ready)
  return Boolean(capabilities?.gitea_oauth_ready)
}

function codeProviderTokenAuthEnabled(): boolean {
  return integrations.value?.capabilities.code_provider_token_auth_enabled ?? true
}

function normalizedCodeProviderBaseUrl(provider: CodeProvider, rawValue?: string): string {
  const definition = codeProviderDefinitions.find(item => item.provider === provider)
  const fallback = definition?.defaultBaseUrl ?? ''
  const raw = (rawValue ?? codeProviderInputs[provider].base_url).trim() || fallback
  try {
    const url = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`)
    return `${url.protocol}//${url.host}${url.pathname.replace(/\/+$/, '')}`.replace(/\/+$/, '')
  } catch {
    return raw.replace(/\/+$/, '')
  }
}

function canStartCodeProviderOAuth(provider: CodeProvider): boolean {
  return codeProviderOAuthReady(provider)
}

function closeCodeProviderModal() {
  codeProviderModal.provider = null
  codeProviderModal.step = 'choice'
}

function startCodeProviderConnect(provider: CodeProvider) {
  if (codeProviderTokenAuthEnabled()) {
    codeProviderInputs[provider].mode = 'oauth'
    codeProviderModal.provider = provider
    codeProviderModal.step = 'choice'
    return
  }

  if (!canStartCodeProviderOAuth(provider)) {
    setIntegrationNotice(`OAuth для ${codeProviderLabel(provider)} не готов.`, 'error')
    return
  }
  void startCodeProviderOAuth(provider)
}

function startCodeProviderOAuth(provider: CodeProvider) {
  codeProviderInputs[provider].mode = 'oauth'
  void connectCodeProvider(provider)
}

function showCodeProviderTokenServer(provider: CodeProvider) {
  codeProviderInputs[provider].mode = 'token'
  codeProviderModal.step = 'server'
}

function codeProviderTokenCreateUrl(provider: CodeProvider): string {
  const baseUrl = normalizedCodeProviderBaseUrl(provider)
  const name = encodeURIComponent(TOKEN_NAME)
  if (provider === 'gitlab') {
    const scopes = encodeURIComponent(TOKEN_SCOPES.gitlab.join(','))
    return `${baseUrl}/-/user_settings/personal_access_tokens?name=${name}&scopes=${scopes}`
  }
  if (provider === 'github') {
    const scopes = encodeURIComponent(TOKEN_SCOPES.github.join(','))
    return `${baseUrl}/settings/tokens/new?description=${name}&scopes=${scopes}`
  }
  return `${baseUrl}/user/settings/applications`
}

function openTokenCreateUrl(provider: CodeProvider) {
  window.open(codeProviderTokenCreateUrl(provider), '_blank', 'noopener,noreferrer')
  if (codeProviderModal.provider === provider) {
    codeProviderModal.step = 'token'
  }
}

function canSubmitCodeProvider(provider: CodeProvider): boolean {
  const input = codeProviderInputs[provider]
  if (input.mode === 'oauth') {
    return codeProviderOAuthReady(provider)
  }
  return Boolean(input.token.trim())
}

function codeProviderBaseInput(provider: CodeProvider): string | null {
  const value = codeProviderInputs[provider].base_url.trim()
  return value || null
}

async function connectCodeProvider(provider: CodeProvider) {
  if (!canSubmitCodeProvider(provider)) return
  codeBusy.value = `${provider}:connect`
  try {
    const input = codeProviderInputs[provider]
    if (input.mode === 'oauth') {
      const response = await auth.authorizedFetch<{ auth_url: string }>(
        `${config.public.apiBase}/integrations/code/oauth/start`,
        {
          method: 'POST',
          body: {
            provider,
            base_url: codeProviderBaseInput(provider),
          },
        },
      )
      window.location.assign(response.auth_url)
      return
    }

    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/code/token`, {
      method: 'POST',
      body: {
        provider,
        access_token: input.token.trim(),
        base_url: codeProviderBaseInput(provider),
      },
    })
    input.token = ''
    applyIntegrations(data)
    await ensureGitBlock(provider)
    await profile.fetch()
    setIntegrationNotice(`${codeProviderLabel(provider)} подключён через token.`, 'success')
    closeCodeProviderModal()
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, `Не удалось подключить ${codeProviderLabel(provider)}.`), 'error')
  } finally {
    codeBusy.value = null
  }
}

async function disconnectCodeProvider(provider: CodeProvider) {
  codeBusy.value = `${provider}:disconnect`
  try {
    await auth.authorizedFetch(`${config.public.apiBase}/integrations/code/${provider}`, { method: 'DELETE' })
    await loadIntegrations()
    await profile.fetch()
    setIntegrationNotice(`${codeProviderLabel(provider)} отключён от аккаунта.`, 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, `Не удалось отключить ${codeProviderLabel(provider)}.`), 'error')
  } finally {
    codeBusy.value = null
  }
}

async function connectService(type: IntegrationType) {
  if (!connectableTypes.has(type) || connectedTypes.value.has(type)) return
  connectingType.value = type
  try {
    await profile.createBlock(type, createDefaultBlockConfig(type))
    setIntegrationNotice('Last.fm подключён. Блок добавлен в публичный профиль.', 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось подключить интеграцию.'), 'error')
  } finally {
    connectingType.value = null
  }
}
</script>

<style scoped>
.integrations-shell {
  --integration-radius: var(--md-sys-shape-corner-extra-large, 28px);
  --integration-radius-strong: var(--md-sys-shape-corner-extra-large-increased, 32px);
  --integration-radius-compact: var(--md-sys-shape-corner-large, 16px);
  --integration-motion: var(--md-sys-motion-expressive, var(--m3-motion, cubic-bezier(0.34, 1.56, 0.64, 1)));
  --integration-standard: var(--md-sys-motion-standard, cubic-bezier(0.2, 0, 0, 1));
  --integration-state-layer: 0.08;
  width: min(100%, 1100px);
  position: relative;
  display: grid;
  gap: 14px;
  margin: 0 auto;
}

.integrations-shell.is-loading {
  cursor: progress;
}

.integrations-shell,
.integrations-shell * {
  box-sizing: border-box;
}

.integrations-summary,
.service-card,
.integration-notice {
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant, var(--outline, #d4dbe8)) 88%, transparent);
  border-radius: var(--integration-radius);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface, #fff) 96%, transparent), color-mix(in srgb, var(--surface-low, #F2F4F8) 72%, transparent));
  box-shadow:
    0 16px 42px color-mix(in srgb, var(--text-1, #10182b) 8%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 72%, transparent);
}

.integrations-summary {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: clamp(16px, 2vw, 22px);
  border-radius: var(--integration-radius-strong);
  background:
    radial-gradient(circle at 18% 0%, color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 78%, transparent) 0 32%, transparent 58%),
    linear-gradient(135deg, color-mix(in srgb, var(--surface, #fff) 96%, transparent), color-mix(in srgb, var(--tertiary-container, #fbd7fc) 34%, var(--surface-low, #F2F4F8)));
}

.integrations-summary::after {
  content: "";
  position: absolute;
  right: 18px;
  bottom: -46px;
  width: 160px;
  height: 160px;
  border: 1px solid color-mix(in srgb, var(--primary, #345EA8) 14%, transparent);
  border-radius: 999px;
  opacity: 0.55;
  pointer-events: none;
}

.summary-copy {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.summary-icon {
  width: 58px;
  height: 58px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 20px;
  background: var(--primary, #345EA8);
  color: var(--on-primary, #fff);
  font-size: 27px;
  box-shadow:
    0 12px 26px color-mix(in srgb, var(--primary, #345EA8) 24%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 32%, transparent);
}

.summary-text {
  min-width: 0;
}

.summary-copy h2,
.summary-copy p,
.service-copy h3,
.service-copy p {
  margin: 0;
}

.summary-copy h2 {
  color: var(--text-1, #10182b);
  font-size: clamp(24px, 2vw, 32px);
  line-height: 1.05;
  letter-spacing: -0.01em;
  font-weight: 950;
}

.summary-copy p {
  max-width: 560px;
  margin-top: 6px;
  color: var(--text-2, #475778);
  font-size: 14px;
  line-height: 1.45;
}

.summary-stats {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.summary-pill {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface, #fff) 82%, transparent);
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  backdrop-filter: blur(12px) saturate(140%);
}

.summary-pill.strong {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 18%, transparent);
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 78%, var(--surface, #fff));
  color: var(--on-primary-container, #163E86);
}

.summary-pill strong {
  font-size: 21px;
  line-height: 1;
}

.service-list {
  display: grid;
  gap: 12px;
}

.service-card {
  position: relative;
  min-width: 0;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: clamp(14px, 1.6vw, 18px);
  border-radius: var(--integration-radius);
  transition:
    transform 240ms var(--integration-motion),
    border-color 200ms var(--integration-standard),
    background 200ms var(--integration-standard),
    box-shadow 200ms var(--integration-standard);
}

.service-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: currentColor;
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms var(--integration-standard);
}

.service-card > * {
  position: relative;
  z-index: 1;
}

.service-card.connected {
  border-color: color-mix(in srgb, var(--success, #188A55) 32%, var(--outline, #d4dbe8));
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--success-container, #E1F6EA) 50%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--surface, #fff) 96%, transparent), color-mix(in srgb, var(--surface-low, #F2F4F8) 76%, transparent));
}

.service-card.available {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 24%, var(--outline, #d4dbe8));
}

.service-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.service-icon {
  width: 52px;
  height: 52px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 18px;
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 82%, var(--surface, #fff));
  color: var(--on-primary-container, #163E86);
  font-size: 25px;
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 60%, transparent);
}

.service-card.connected .service-icon {
  background: color-mix(in srgb, var(--success-container, #E1F6EA) 84%, var(--surface, #fff));
  color: var(--success, #188A55);
}

.service-card.widget_steam:not(.connected) .service-icon {
  background: color-mix(in srgb, #171a21 14%, var(--surface, #fff));
  color: #171a21;
}

.service-card.widget_spotify:not(.connected) .service-icon {
  background: color-mix(in srgb, #1db954 18%, var(--surface, #fff));
  color: color-mix(in srgb, #1db954 70%, #06140b);
}

.service-card.code_github:not(.connected) .service-icon {
  background: color-mix(in srgb, var(--text-1, #10182b) 10%, var(--surface, #fff));
  color: var(--text-1, #10182b);
}

.service-card.code_gitlab:not(.connected) .service-icon {
  background: color-mix(in srgb, #fc6d26 16%, var(--surface, #fff));
  color: #9b3400;
}

.service-card.code_gitea:not(.connected) .service-icon {
  background: color-mix(in srgb, #609926 16%, var(--surface, #fff));
  color: #3f6f15;
}

.service-card.widget_faceit:not(.connected) .service-icon {
  background: color-mix(in srgb, #ff5500 16%, var(--surface, #fff));
  color: #9b3200;
}

.faceit-logo {
  width: 24px;
  height: 24px;
  display: block;
}

.gitea-logo {
  width: 28px;
  height: 28px;
  display: block;
}

.service-copy {
  min-width: 0;
}

.service-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.service-copy h3 {
  color: var(--text-1, #10182b);
  font-size: 18px;
  line-height: 1.2;
  font-weight: 920;
  overflow-wrap: anywhere;
}

.service-copy p {
  max-width: 660px;
  margin-top: 5px;
  color: var(--text-2, #475778);
  font-size: 13.5px;
  line-height: 1.45;
}

.service-status {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 82%, transparent);
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 8%, transparent);
}

.service-status.connected {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.service-status.available {
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 82%, var(--surface, #fff));
  color: var(--on-primary-container, #163E86);
}

.service-status.derived {
  background: color-mix(in srgb, var(--tertiary-container, #fbd7fc) 70%, var(--surface, #fff));
  color: var(--on-tertiary-container, #29132d);
}

.service-controls,
.steam-connect,
.spotify-connect,
.faceit-block,
.code-provider-block {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 170px;
}

.service-controls {
  position: relative;
  min-height: 44px;
  align-content: center;
}

.service-copy,
.service-title-row,
.service-status,
.service-account,
.service-controls,
.steam-connect,
.spotify-connect,
.faceit-block,
.code-provider-block {
  transition:
    opacity 180ms var(--integration-standard),
    min-width 220ms var(--integration-standard),
    background 180ms var(--integration-standard),
    color 180ms var(--integration-standard);
}

.service-swap-enter-active,
.service-swap-leave-active {
  transition:
    opacity 140ms var(--integration-standard),
    filter 140ms var(--integration-standard);
  will-change: opacity, filter;
}

.service-swap-enter-from,
.service-swap-leave-to {
  opacity: 0;
  filter: blur(3px);
}

.service-data-enter-active,
.service-data-leave-active {
  transition:
    opacity 120ms var(--integration-standard),
    filter 120ms var(--integration-standard);
  will-change: filter, opacity;
}

.service-data-enter-from,
.service-data-leave-to {
  opacity: 0;
  filter: blur(2px);
}

.steam-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.steam-login,
.spotify-login,
.service-action {
  min-height: 44px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 14px;
  font: inherit;
  font-size: 13px;
  font-weight: 900;
  transition:
    transform 240ms var(--integration-motion),
    background 180ms var(--integration-standard),
    border-color 180ms var(--integration-standard),
    color 180ms var(--integration-standard),
    box-shadow 180ms var(--integration-standard);
}

.steam-login::after,
.spotify-login::after,
.service-action::after,
.modal-auth-button::after,
.integration-modal-close::after,
.integration-modal-back::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: currentColor;
  opacity: 0;
  pointer-events: none;
  transition: opacity 180ms var(--integration-standard);
}

.steam-login > *,
.spotify-login > *,
.service-action > *,
.modal-auth-button > *,
.integration-modal-close > *,
.integration-modal-back > * {
  position: relative;
  z-index: 1;
}

.steam-login {
  border-color: transparent;
  background: #171a21;
  color: #fff;
  cursor: pointer;
}

.spotify-login {
  border-color: transparent;
  background: #1db954;
  color: #06140b;
  cursor: pointer;
}

.service-action {
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
  cursor: default;
}

.service-action.primary {
  border-color: transparent;
  background: var(--primary, #345EA8);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 10px 22px color-mix(in srgb, var(--primary, #345EA8) 20%, transparent);
}

.service-action.complete {
  border-color: color-mix(in srgb, var(--success, #188A55) 28%, var(--outline, #d4dbe8));
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
  cursor: default;
}

.service-action.danger {
  border-color: color-mix(in srgb, var(--error, #B3323A) 24%, var(--outline, #d4dbe8));
  background: color-mix(in srgb, var(--error-container, #FFE5E7) 62%, white);
  color: var(--error, #B3323A);
  cursor: pointer;
}

.steam-login:disabled,
.spotify-login:disabled,
.service-action:disabled:not(.complete) {
  cursor: wait;
  opacity: 0.72;
}

.faceit-summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.spotify-summary,
.code-provider-summary {
  display: grid;
  gap: 10px;
  justify-items: end;
  min-width: 280px;
}

.spotify-summary > div:first-child,
.code-provider-summary > div:first-child {
  display: grid;
  justify-items: end;
  gap: 3px;
  padding: 11px 13px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface-container-high, var(--surface-low, #F2F4F8)) 78%, var(--surface, #fff));
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 52%, transparent);
}

.spotify-summary strong,
.code-provider-summary strong {
  color: var(--text-1, #10182b);
  font-size: 13px;
  font-weight: 950;
  overflow-wrap: anywhere;
}

.spotify-summary span,
.code-provider-summary span {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.provider-field {
  display: grid;
  width: 100%;
  gap: 6px;
}

.provider-field span {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.provider-field input {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 18px;
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
  font: inherit;
  outline: none;
  padding: 0 12px;
  transition:
    border-color 180ms var(--integration-standard),
    box-shadow 180ms var(--integration-standard),
    background 180ms var(--integration-standard);
}

.provider-field input:focus {
  border-color: var(--primary, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 15%, transparent);
}

.integration-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 18px;
  background:
    radial-gradient(circle at 50% 16%, color-mix(in srgb, var(--primary, #345EA8) 20%, transparent), transparent 34%),
    color-mix(in srgb, #05070c 58%, transparent);
  backdrop-filter: blur(14px) saturate(128%);
}

.integration-modal {
  position: relative;
  width: min(100%, 460px);
  display: grid;
  gap: 18px;
  overflow: hidden;
  padding: 30px;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 64%, transparent);
  border-radius: var(--integration-radius-strong);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 34%, transparent), transparent 40%),
    color-mix(in srgb, var(--surface, #fff) 97%, transparent);
  box-shadow:
    0 28px 82px color-mix(in srgb, #05070c 36%, transparent),
    inset 0 1px 0 color-mix(in srgb, white 70%, transparent);
}

.integration-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  isolation: isolate;
  overflow: hidden;
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
  cursor: pointer;
  font: inherit;
  font-size: 20px;
}

.integration-modal-head {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 10px 28px 0;
  text-align: center;
}

.integration-modal-icon {
  width: 64px;
  height: 64px;
  display: inline-grid;
  place-items: center;
  border-radius: 22px;
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 84%, var(--surface, #fff));
  color: var(--on-primary-container, #163E86);
  font-size: 31px;
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 58%, transparent);
}

.integration-modal-head h2,
.integration-modal-head p {
  margin: 0;
}

.integration-modal-head h2 {
  color: var(--text-1, #10182b);
  font-size: 30px;
  line-height: 1.1;
  letter-spacing: -0.01em;
  font-weight: 950;
}

.integration-modal-head p {
  color: var(--text-2, #475778);
  font-size: 18px;
  line-height: 1.35;
}

.integration-modal-actions,
.integration-modal-form {
  display: grid;
  gap: 12px;
}

.modal-auth-button {
  min-height: 60px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 20px;
  padding: 0 18px;
  font: inherit;
  font-size: 16px;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 240ms var(--integration-motion),
    background 180ms var(--integration-standard),
    border-color 180ms var(--integration-standard),
    box-shadow 180ms var(--integration-standard);
}

.modal-auth-button.primary {
  background: var(--primary, #345EA8);
  color: var(--on-primary, #fff);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--primary, #345EA8) 22%, transparent);
}

.modal-auth-button.secondary {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 16%, var(--outline, rgba(82, 103, 138, 0.18)));
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 72%, var(--surface, #fff));
  color: var(--on-primary-container, #163E86);
}

.modal-auth-button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.modal-field input {
  min-height: 58px;
  border-radius: 18px;
  font-size: 18px;
}

.modal-hint {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 800;
  text-align: center;
}

.integration-modal-back {
  justify-self: center;
  min-height: 38px;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-2, #475778);
  font: inherit;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.integration-modal-enter-active,
.integration-modal-leave-active {
  transition: opacity 220ms var(--integration-standard);
}

.integration-modal-enter-active .integration-modal,
.integration-modal-leave-active .integration-modal {
  transition:
    transform 300ms var(--integration-motion),
    opacity 220ms var(--integration-standard);
}

.integration-modal-enter-from,
.integration-modal-leave-to {
  opacity: 0;
}

.integration-modal-enter-from .integration-modal,
.integration-modal-leave-to .integration-modal {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}

.faceit-summary span,
.service-hint {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 72%, transparent);
  background: color-mix(in srgb, var(--surface-container-high, var(--surface-low, #F2F4F8)) 78%, var(--surface, #fff));
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.service-hint {
  max-width: 240px;
  height: auto;
  min-height: 36px;
  padding: 8px 10px;
  border-radius: 14px;
  line-height: 1.25;
  text-align: right;
}

.integration-notice {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 14px;
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 60%, var(--surface, #fff));
  color: var(--text-2, #475778);
  font-size: 13px;
  font-weight: 800;
}

.integration-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid rgba(255,255,255,0.38);
  border-top-color: #fff;
  border-radius: 50%;
  animation: integration-spin 0.78s linear infinite;
}

.integration-spinner.dark {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 24%, transparent);
  border-top-color: var(--primary, #345EA8);
}

.steam-login:focus-visible,
.spotify-login:focus-visible,
.service-action:focus-visible,
.integration-modal-close:focus-visible,
.modal-auth-button:focus-visible,
.integration-modal-back:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--primary, #345EA8) 32%, transparent);
  outline-offset: 2px;
}

.integrations-summary {
  min-height: 138px;
  border-radius: var(--md-sys-shape-corner-extra-large-increased, var(--integration-radius-strong));
  background:
    radial-gradient(circle at 0% 10%, color-mix(in srgb, var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12))) 86%, transparent) 0 30%, transparent 56%),
    linear-gradient(135deg, var(--md-sys-color-surface-container-low, var(--surface, #fff)), color-mix(in srgb, var(--md-sys-color-tertiary-container, #fbd7fc) 28%, var(--md-sys-color-surface-container-low, var(--surface-low, #F2F4F8))));
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--md-sys-color-surface-bright, white) 70%, transparent);
}

.summary-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
  background: var(--md-sys-color-primary, var(--primary, #345EA8));
}

.summary-copy h2 {
  font: var(--md-sys-typescale-headline-large-weight, 950) clamp(30px, 3vw, 44px) / 1.03 var(--md-sys-typescale-headline-large-font, inherit);
  letter-spacing: 0;
}

.summary-copy p {
  display: none;
}

.summary-pill {
  min-height: 46px;
  border-radius: var(--md-sys-shape-corner-full, 999px);
  background: color-mix(in srgb, var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8)) 82%, transparent);
}

.integration-notice {
  position: absolute;
  top: 148px;
  right: 12px;
  z-index: 5;
  width: min(calc(100% - 24px), 330px);
  min-height: 48px;
  margin: 0;
  opacity: 0;
  transform: translateY(-4px) scale(0.99);
  pointer-events: none;
  transition:
    opacity 220ms var(--integration-standard),
    transform 300ms var(--integration-motion);
}

.integration-notice.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.service-list {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
}

.service-card {
  grid-column: span 6;
  min-height: 228px;
  grid-template-columns: 1fr;
  align-items: stretch;
  gap: 18px;
  border-radius: var(--md-sys-shape-corner-extra-large, var(--integration-radius));
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12))) 18%, transparent), transparent 58%),
    var(--md-sys-color-surface-container, var(--surface-low, #F2F4F8));
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--md-sys-color-surface-bright, white) 66%, transparent);
}

.service-card.widget_steam,
.service-card.widget_spotify {
  grid-column: span 6;
}

.service-card.code_gitea,
.service-card.widget_lastfm {
  grid-column: span 6;
}

.service-card::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0;
  transform: translateX(-100%);
  background:
    linear-gradient(90deg, transparent, color-mix(in srgb, var(--md-sys-color-surface-bright, white) 46%, transparent), transparent);
  pointer-events: none;
}

.integrations-shell.is-loading .service-card::after {
  opacity: 1;
  animation: integration-shimmer 1.35s var(--integration-standard) infinite;
}

.service-main {
  align-items: flex-start;
}

.service-icon {
  width: 58px;
  height: 58px;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
}

.service-title-row {
  align-items: flex-start;
}

.service-copy h3 {
  font: var(--md-sys-typescale-title-large-weight, 920) var(--md-sys-typescale-title-large-size, 22px) / var(--md-sys-typescale-title-large-line-height, 28px) var(--md-sys-typescale-title-large-font, inherit);
}

.service-copy p {
  display: none;
}

.service-status {
  min-height: 32px;
  border-radius: var(--md-sys-shape-corner-full, 999px);
}

.service-controls,
.steam-connect,
.spotify-connect,
.faceit-block,
.code-provider-block {
  justify-items: stretch;
  min-width: 0;
}

.steam-actions {
  justify-content: stretch;
}

.steam-actions > * {
  flex: 1 1 150px;
}

.steam-login,
.spotify-login,
.service-action {
  width: 100%;
  min-height: 48px;
  border-radius: var(--md-sys-shape-corner-full, 999px);
}

.spotify-summary,
.code-provider-summary {
  justify-items: stretch;
  min-width: 0;
}

.spotify-summary > div:first-child,
.code-provider-summary > div:first-child {
  justify-items: start;
  min-height: 56px;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
}

.faceit-summary {
  justify-content: stretch;
}

.faceit-summary span,
.service-hint {
  flex: 1 1 140px;
  justify-content: center;
  min-height: 44px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  text-align: center;
}

@keyframes integration-shimmer {
  to { transform: translateX(100%); }
}

@media (hover: hover) {
  .service-card:hover {
    transform: translateY(-4px) scale(1.006);
    border-color: color-mix(in srgb, var(--primary, #345EA8) 28%, var(--outline, #d4dbe8));
    box-shadow:
      inset 0 1px 0 color-mix(in srgb, white 72%, transparent);
  }

  .service-card:hover::before {
    opacity: 0.035;
  }

  .service-action.primary:hover:not(:disabled),
  .spotify-login:hover:not(:disabled),
  .steam-login:hover:not(:disabled),
  .modal-auth-button:hover:not(:disabled) {
    transform: translateY(-1px);
  }

  .service-action:hover:not(:disabled)::after,
  .spotify-login:hover:not(:disabled)::after,
  .steam-login:hover:not(:disabled)::after,
  .modal-auth-button:hover:not(:disabled)::after,
  .integration-modal-close:hover::after,
  .integration-modal-back:hover::after {
    opacity: var(--integration-state-layer);
  }
}

@keyframes integration-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 860px) {
  .integrations-shell {
    max-width: 760px;
  }

  .integrations-summary,
  .service-card {
    align-items: stretch;
    grid-template-columns: 1fr;
  }

  .integrations-summary {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-stats {
    justify-content: flex-start;
  }

  .service-controls,
  .steam-connect,
  .spotify-connect,
  .faceit-block,
  .code-provider-block,
  .spotify-summary,
  .code-provider-summary {
    justify-items: stretch;
    min-width: 0;
  }

  .steam-actions,
  .faceit-summary {
    justify-content: flex-start;
  }

  .service-action,
  .spotify-login,
  .steam-login {
    width: 100%;
  }

  .spotify-summary > div:first-child,
  .code-provider-summary > div:first-child {
    justify-items: start;
  }

  .service-hint {
    max-width: none;
    text-align: left;
  }

  .integration-modal {
    padding: 24px 18px;
    border-radius: 24px;
  }

  .integration-modal-head {
    padding-inline: 24px;
  }

  .integration-modal-head h2 {
    font-size: 26px;
  }

  .integration-modal-head p {
    font-size: 16px;
  }
}

@media (max-width: 520px) {
  .integrations-summary,
  .service-card {
    border-radius: 16px;
    padding: 14px;
  }

  .summary-copy {
    align-items: flex-start;
  }

  .summary-icon {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    font-size: 23px;
  }

  .summary-pill {
    flex: 1 1 auto;
    justify-content: center;
  }

  .service-main {
    align-items: flex-start;
  }

  .service-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
  }

  .service-copy h3 {
    font-size: 16px;
  }
}

.integrations-summary,
.service-card,
.integration-notice {
  border-color: transparent;
  box-shadow: none;
}

.integrations-summary {
  min-height: 84px;
  padding: 14px 18px;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12))) 36%, transparent), transparent 68%),
    var(--md-sys-color-surface-container, var(--surface-low, #F2F4F8));
}

.integrations-summary::after {
  display: none;
}

.summary-copy {
  gap: 12px;
}

.summary-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  background: var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12)));
  color: var(--md-sys-color-on-primary-container, var(--on-primary-container, #163E86));
  font-size: 22px;
  box-shadow: none;
}

.summary-copy h2 {
  color: var(--md-sys-color-on-surface, var(--text-1, #10182b));
  font: var(--md-sys-typescale-headline-small-weight, 900) var(--md-sys-typescale-headline-small-size, 24px) / var(--md-sys-typescale-headline-small-line-height, 32px) var(--md-sys-typescale-headline-small-font, inherit);
  letter-spacing: 0;
}

.summary-stats {
  gap: 8px;
}

.summary-pill,
.summary-pill.strong {
  min-height: 36px;
  border: 0;
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  font-size: 12px;
  box-shadow: none;
}

.summary-pill strong {
  font-size: 16px;
}

.service-list {
  gap: 10px;
}

.service-card {
  min-height: 136px;
  gap: 12px;
  padding: 16px 18px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container-low, var(--surface-low, #F2F4F8));
  box-shadow: none;
}

.service-card.connected {
  border-color: transparent;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--success-container, #E1F6EA) 20%, transparent), transparent 62%),
    var(--md-sys-color-surface-container-low, var(--surface-low, #F2F4F8));
}

.service-card.available {
  border-color: transparent;
}

.service-main {
  gap: 12px;
}

.service-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  font-size: 21px;
  box-shadow: none;
}

.faceit-logo {
  width: 20px;
  height: 20px;
}

.gitea-logo {
  width: 22px;
  height: 22px;
}

.service-title-row {
  gap: 7px;
}

.service-copy h3 {
  color: var(--md-sys-color-on-surface, var(--text-1, #10182b));
  font: var(--md-sys-typescale-title-large-weight, 850) 20px / 25px var(--md-sys-typescale-title-large-font, inherit);
}

.service-account {
  display: block;
  margin-top: 2px;
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  font: var(--md-sys-typescale-label-large-weight, 700) 13px / 18px var(--md-sys-typescale-label-large-font, inherit);
  overflow-wrap: anywhere;
}

.service-status {
  min-height: 26px;
  padding: 0 9px;
  border: 0;
  font-size: 11px;
  box-shadow: none;
}

.service-controls,
.steam-connect,
.spotify-connect,
.faceit-block,
.code-provider-block {
  gap: 8px;
}

.steam-login,
.spotify-login,
.service-action {
  min-height: 40px;
  padding: 0 12px;
  border: 0;
  font-size: 12px;
  box-shadow: none;
}

.service-action.primary {
  background: var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12)));
  color: var(--md-sys-color-on-primary-container, var(--on-primary-container, #163E86));
  box-shadow: none;
}

.service-action.danger {
  background: var(--md-sys-color-error-container, #FFE5E7);
  color: var(--md-sys-color-on-error-container, var(--error, #B3323A));
}

.spotify-summary,
.code-provider-summary {
  gap: 0;
}

.faceit-summary {
  gap: 6px;
}

.faceit-summary span,
.service-hint {
  min-height: 34px;
  border: 0;
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8));
  font-size: 12px;
  box-shadow: none;
}

.integration-notice {
  top: 94px;
  right: 12px;
  width: min(calc(100% - 24px), 330px);
  min-height: 40px;
}

@media (hover: hover) {
  .service-card:hover {
    transform: translateY(-1px);
    border-color: transparent;
    background: color-mix(in srgb, var(--md-sys-color-primary-container, var(--primary-container, rgba(52,94,168,0.12))) 10%, var(--md-sys-color-surface-container-low, var(--surface-low, #F2F4F8)));
    box-shadow: none;
  }

  .service-card:hover::before {
    opacity: 0.045;
  }
}

@media (max-width: 860px) {
  .integrations-summary {
    min-height: 0;
    flex-direction: row;
    align-items: center;
  }

  .service-card {
    grid-column: 1 / -1;
    min-height: 0;
  }
}

@media (max-width: 520px) {
  .integrations-summary,
  .service-card {
    border-radius: var(--md-sys-shape-corner-large, 16px);
    padding: 14px;
  }

  .summary-icon,
  .service-icon {
    width: 40px;
    height: 40px;
  }
}

.integrations-summary {
  min-height: 72px;
  padding: 12px 16px;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container, var(--surface-low, #F2F4F8));
}

.summary-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  font-size: 20px;
}

.summary-copy h2 {
  font: var(--md-sys-typescale-title-large-weight, 850) var(--md-sys-typescale-title-large-size, 22px) / var(--md-sys-typescale-title-large-line-height, 28px) var(--md-sys-typescale-title-large-font, inherit);
}

.summary-pill,
.summary-pill.strong {
  min-height: 34px;
  padding: 0 12px;
  background: var(--md-sys-color-surface-container-high, color-mix(in srgb, var(--surface-low, #F2F4F8) 86%, white));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
}

.service-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2px;
  padding: 8px;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container-low, var(--surface-low, #F2F4F8));
}

.service-card,
.service-card.connected,
.service-card.available,
.service-card.widget_steam,
.service-card.widget_spotify,
.service-card.code_gitea,
.service-card.widget_lastfm {
  grid-column: auto;
}

.service-card {
  min-height: 76px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 10px 12px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--service-accent, var(--md-sys-color-primary, #345EA8)) 8%, transparent), transparent 34%),
    transparent;
  color: var(--service-accent, var(--md-sys-color-primary, #345EA8));
}

.service-card.connected {
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--success, #188A55) 9%, transparent), transparent 34%),
    transparent;
}

.service-card::after {
  border-radius: inherit;
}

.service-main {
  align-items: center;
  gap: 12px;
}

.service-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  font-size: 19px;
  background: color-mix(in srgb, var(--service-accent, var(--md-sys-color-primary, #345EA8)) 16%, var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8)));
  color: color-mix(in srgb, var(--service-accent, var(--md-sys-color-primary, #345EA8)) 82%, var(--md-sys-color-on-surface, var(--text-1, #10182b)));
}

.service-card.connected .service-icon {
  background: color-mix(in srgb, var(--success, #188A55) 18%, var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8)));
  color: var(--success, #188A55);
}

.service-card.widget_steam { --service-accent: #8fb7ff; }
.service-card.widget_faceit { --service-accent: #d9793b; }
.service-card.widget_spotify { --service-accent: #38a86b; }
.service-card.code_github { --service-accent: #a4adbc; }
.service-card.code_gitlab { --service-accent: #d87945; }
.service-card.code_gitea { --service-accent: #79a84a; }
.service-card.widget_lastfm { --service-accent: #7ea7da; }

.service-card.widget_steam:not(.connected) .service-icon {
  background: color-mix(in srgb, #8fb7ff 22%, var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8)));
  color: #d8e6ff;
}

.service-card::before {
  background: var(--service-accent, currentColor);
}

.service-copy {
  display: grid;
  gap: 1px;
}

.service-title-row {
  align-items: center;
}

.service-copy h3 {
  font: var(--md-sys-typescale-title-medium-weight, 850) var(--md-sys-typescale-title-medium-size, 16px) / var(--md-sys-typescale-title-medium-line-height, 24px) var(--md-sys-typescale-title-medium-font, inherit);
}

.service-account {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  font: var(--md-sys-typescale-label-medium-weight, 650) var(--md-sys-typescale-label-medium-size, 12px) / var(--md-sys-typescale-label-medium-line-height, 16px) var(--md-sys-typescale-label-medium-font, inherit);
}

.service-status,
.service-status.connected,
.service-status.available,
.service-status.derived {
  min-height: 24px;
  padding: 0 8px;
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  font-size: 11px;
  min-width: 112px;
  justify-content: center;
}

.service-status.connected {
  background: color-mix(in srgb, var(--success, #188A55) 14%, var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8)));
  color: var(--success, #188A55);
}

.service-controls,
.steam-connect,
.spotify-connect,
.faceit-block,
.code-provider-block {
  min-width: 150px;
  min-height: 36px;
  justify-items: end;
  align-content: center;
}

.spotify-summary,
.code-provider-summary {
  display: block;
}

.steam-actions {
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.steam-actions > * {
  flex: 0 0 auto;
}

.steam-login,
.spotify-login,
.service-action,
.service-action.primary,
.service-action.danger,
.service-action.complete {
  width: auto;
  min-width: 136px;
  min-height: 36px;
  padding: 0 14px;
  background: var(--md-sys-color-secondary-container, color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 76%, var(--surface, #fff)));
  color: var(--md-sys-color-on-secondary-container, var(--on-primary-container, #163E86));
  box-shadow: none;
}

.service-action.danger {
  min-width: 120px;
  background: var(--md-sys-color-error-container, #FFE5E7);
  color: var(--md-sys-color-on-error-container, var(--error, #B3323A));
}

.spotify-login:disabled,
.service-action:disabled:not(.complete) {
  cursor: not-allowed;
  opacity: 0.62;
}

.faceit-summary {
  justify-content: flex-end;
}

.faceit-summary span,
.service-hint {
  min-height: 32px;
  padding: 0 10px;
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #F2F4F8));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  text-align: start;
}

@media (hover: hover) {
  .service-card:hover {
    transform: none;
    background:
      linear-gradient(90deg, color-mix(in srgb, var(--service-accent, var(--md-sys-color-primary, #345EA8)) 14%, transparent), transparent 38%),
      var(--md-sys-color-surface-container, var(--surface-low, #F2F4F8));
  }

  .service-card:hover::before {
    opacity: 0.035;
  }
}

@media (max-width: 860px) {
  .service-card {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .service-controls,
  .steam-connect,
  .spotify-connect,
  .faceit-block,
  .code-provider-block {
    min-width: 0;
    justify-items: stretch;
  }

  .steam-actions {
    flex-wrap: wrap;
  }

  .steam-login,
  .spotify-login,
  .service-action,
  .service-action.primary,
  .service-action.danger,
  .service-action.complete {
    width: 100%;
  }

  .integration-notice {
    right: 8px;
    width: calc(100% - 16px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .integrations-shell *,
  .integrations-shell *::before,
  .integrations-shell *::after {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
  }
}
</style>
