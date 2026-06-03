<template>
  <div class="integrations-shell">
    <section class="integrations-summary" aria-label="Сводка сервисов">
      <div class="summary-copy">
        <h2>Сервисы</h2>
        <p>Подключения, которые могут автоматически наполнять публичный профиль.</p>
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

    <div v-if="loading" class="integration-notice">
      <span class="integration-spinner dark" />
      Загружаем подключения...
    </div>

    <section class="service-list" aria-label="Сервисы">
      <article
        v-for="service in serviceCards"
        :key="service.type"
        class="service-card"
        :class="{ connected: service.connected, available: service.canConnect }"
      >
        <div class="service-main">
          <span class="service-icon">
            <FaceitLogo v-if="service.type === 'widget_faceit'" class="faceit-logo" />
            <GiteaLogo v-else-if="service.type === 'code_gitea'" class="gitea-logo" />
            <i v-else :class="service.icon" />
          </span>

          <div class="service-copy">
            <div class="service-title-row">
              <h3>{{ service.label }}</h3>
              <span class="service-status" :class="{ connected: service.connected, available: service.canConnect }">
                <i :class="service.statusIcon" />
                {{ service.statusLabel }}
              </span>
            </div>
            <p>{{ service.description }}</p>
          </div>
        </div>

        <div class="service-controls">
          <div v-if="service.type === 'widget_steam'" class="steam-connect">
            <button v-if="!steamAccount" class="steam-login" type="button" :disabled="steamOauthBusy" @click="startSteamLogin">
              <span v-if="steamOauthBusy" class="integration-spinner" />
              <i v-else class="ri-steam-fill" />
              <span>Войти через Steam</span>
            </button>

            <div v-if="steamAccount" class="steam-actions">
              <button class="service-action primary" type="button" :disabled="steamBusy" @click="syncSteamConnection">
                <span v-if="steamBusy" class="integration-spinner" />
                <template v-else>
                  <i class="ri-refresh-line" />
                  <span>Синхронизировать</span>
                </template>
              </button>
              <button class="service-action danger" type="button" :disabled="steamBusy" @click="disconnectSteamConnection">
                <i class="ri-link-unlink-m" />
                <span>Отключить</span>
              </button>
            </div>
          </div>

          <div v-else-if="service.type === 'widget_faceit'" class="faceit-block">
            <div v-if="faceitAccount" class="faceit-summary">
              <span>Уровень {{ faceitSkillLevel || '—' }}</span>
              <span>{{ faceitElo ? `${faceitElo} ELO` : 'ELO не получен' }}</span>
            </div>
            <span v-else class="service-hint">Найдется после Steam, если ключ FACEIT настроен.</span>
          </div>

          <div v-else-if="service.provider" class="code-provider-block">
            <div v-if="codeProviderAccount(service.provider)" class="code-provider-summary">
              <div>
                <strong>{{ codeProviderUsername(service.provider) }}</strong>
                <span>{{ codeProviderBaseUrl(service.provider) }}</span>
              </div>
              <div class="steam-actions">
                <button class="service-action primary" type="button" :disabled="codeBusy === `${service.provider}:sync`" @click="syncCodeProvider(service.provider)">
                  <span v-if="codeBusy === `${service.provider}:sync`" class="integration-spinner" />
                  <template v-else>
                    <i class="ri-refresh-line" />
                    <span>Синхронизировать</span>
                  </template>
                </button>
                <button class="service-action danger" type="button" :disabled="codeBusy === `${service.provider}:disconnect`" @click="disconnectCodeProvider(service.provider)">
                  <i class="ri-link-unlink-m" />
                  <span>Отключить</span>
                </button>
              </div>
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
                <i class="ri-link-m" />
                <span>Подключить</span>
              </template>
            </button>
          </div>

          <button
            v-else
            class="service-action"
            :class="{ primary: service.canConnect, complete: service.connected }"
            type="button"
            :disabled="!service.canConnect || connectingType === service.type"
            @click="connectService(service.type)"
          >
            <span v-if="connectingType === service.type" class="integration-spinner" />
            <i v-else :class="service.actionIcon" />
            <span>{{ service.actionLabel }}</span>
          </button>
        </div>
      </article>
    </section>

    <Teleport to="body">
      <Transition name="integration-modal">
        <div v-if="codeProviderModal.provider && activeCodeProvider" class="integration-modal-overlay" @click.self="closeCodeProviderModal">
          <section class="integration-modal" role="dialog" aria-modal="true" :aria-labelledby="`code-provider-title-${activeCodeProvider.provider}`">
            <button class="integration-modal-close" type="button" aria-label="Закрыть" @click="closeCodeProviderModal">
              <i class="ri-close-line" />
            </button>

            <div class="integration-modal-head">
              <span class="integration-modal-icon">
                <GiteaLogo v-if="activeCodeProvider.provider === 'gitea'" class="gitea-logo" />
                <i v-else :class="activeCodeProvider.icon" />
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
                  <i :class="activeCodeProvider.provider === 'gitea' ? 'ri-login-circle-line' : activeCodeProvider.icon" />
                </template>
              </button>

              <button class="modal-auth-button secondary" type="button" @click="showCodeProviderTokenServer(activeCodeProvider.provider)">
                <i class="ri-key-2-line" />
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
                <i class="ri-external-link-line" />
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
                  <i class="ri-link-m" />
                  <span>Привязать</span>
                </template>
              </button>
            </div>

            <button v-if="codeProviderModal.step !== 'choice'" class="integration-modal-back" type="button" @click="codeProviderModal.step = 'choice'">
              <i class="ri-arrow-left-line" />
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
type IntegrationType = 'widget_steam' | 'widget_lastfm' | 'widget_faceit'
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
    code_provider_token_auth_enabled: boolean
  }
}

const integrationTypes = new Set<IntegrationType>(['widget_steam', 'widget_lastfm', 'widget_faceit'])
const integrationOrder: IntegrationType[] = ['widget_steam', 'widget_faceit', 'widget_lastfm']
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
const faceitSkillLevel = computed(() => faceitAccount.value?.metadata?.skill_level ?? faceitAccount.value?.metadata?.skill_level_label ?? null)
const faceitElo = computed(() => faceitAccount.value?.metadata?.faceit_elo ?? null)
const blockConnectedTypes = computed(() => new Set(profile.profile?.blocks.map(block => block.block_type) ?? []))
const connectedTypes = computed(() => {
  const set = new Set<string>()
  if (blockConnectedTypes.value.has('widget_lastfm')) set.add('widget_lastfm')
  if (steamAccount.value) set.add('widget_steam')
  if (faceitAccount.value) set.add('widget_faceit')
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
        ? `${faceitAccount.value.display_name || 'FACEIT'} найден по Steam: уровень, ELO и статистика доступны для блока.`
        : apiReady?.faceit_api_key_set
          ? 'После привязки Steam попробуем найти FACEIT-профиль по SteamID64.'
          : 'Для автоподтягивания FACEIT администратору нужен FACEIT Data API key.'
      const descriptions: Partial<Record<IntegrationType, string>> = {
        widget_steam: steamDescription,
        widget_faceit: faceitDescription,
        widget_lastfm: 'Подключите Last.fm, чтобы показывать текущий трек и музыкальную активность.',
      }
      return {
        ...item,
        actionIcon: connected ? 'ri-checkbox-circle-line' : 'ri-plug-line',
        actionLabel: connected ? 'Подключено' : 'Подключиться',
        canConnect: connectableTypes.has(type) && !connected,
        connected,
        description: descriptions[type] ?? item.description,
        statusIcon: connected ? 'ri-checkbox-circle-line' : type === 'widget_faceit' ? 'ri-link-m' : 'ri-add-circle-line',
        statusLabel: connected ? (type === 'widget_faceit' ? 'Через Steam' : 'Подключён') : type === 'widget_faceit' ? 'Автопоиск' : 'Доступно',
      }
    })
  const codeCards = codeProviderDefinitions.map((item) => {
    const connected = Boolean(codeProviderAccount(item.provider))
    return {
      ...item,
      actionIcon: connected ? 'ri-checkbox-circle-line' : 'ri-key-2-line',
      actionLabel: connected ? 'Подключено' : 'Подключиться',
      canConnect: !connected,
      connected,
      statusIcon: connected ? 'ri-checkbox-circle-line' : 'ri-key-2-line',
      statusLabel: connected ? 'Подключён' : 'Token / OAuth',
    }
  })
  const byType = new Map([...baseCards, ...codeCards].map(card => [card.type, card]))
  return ['widget_steam', 'widget_faceit', 'code_github', 'code_gitlab', 'code_gitea', 'widget_lastfm']
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
  const existing = profile.profile?.blocks.find((block: Block) => block.block_type === 'widget_github')
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

async function syncSteamConnection() {
  steamBusy.value = true
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/steam/sync`, {
      method: 'POST',
    })
    applyIntegrations(data)
    await profile.fetch()
    setIntegrationNotice('Steam и FACEIT-данные синхронизированы.', 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, 'Не удалось синхронизировать Steam.'), 'error')
  } finally {
    steamBusy.value = false
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

async function syncCodeProvider(provider: CodeProvider) {
  codeBusy.value = `${provider}:sync`
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/code/${provider}/sync`, {
      method: 'POST',
    })
    applyIntegrations(data)
    await ensureGitBlock(provider)
    await profile.fetch()
    setIntegrationNotice(`${codeProviderLabel(provider)} синхронизирован.`, 'success')
  } catch (error) {
    setIntegrationNotice(extractAuthError(error, `Не удалось синхронизировать ${codeProviderLabel(provider)}.`), 'error')
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
  width: min(100%, 1060px);
  display: grid;
  gap: 12px;
  margin: 0 auto;
}

.integrations-shell,
.integrations-shell * {
  box-sizing: border-box;
}

.integrations-summary,
.service-card,
.integration-notice {
  border: 1px solid color-mix(in srgb, var(--dash-outline, #d4dbe8) 86%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 94%, transparent);
  box-shadow: 0 10px 28px color-mix(in srgb, var(--dash-text-1, #10182b) 7%, transparent);
}

.integrations-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
}

.summary-copy {
  min-width: 0;
}

.summary-copy h2,
.summary-copy p,
.service-copy h3,
.service-copy p {
  margin: 0;
}

.summary-copy h2 {
  color: var(--dash-text-1, #10182b);
  font-size: 22px;
  line-height: 1.12;
}

.summary-copy p {
  margin-top: 4px;
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.summary-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.summary-pill {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.summary-pill.strong {
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
}

.summary-pill strong {
  font-size: 18px;
  line-height: 1;
}

.service-list {
  display: grid;
  gap: 10px;
}

.service-card {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px;
  transition:
    transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    box-shadow 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.service-card.connected {
  border-color: color-mix(in srgb, var(--dash-green, #188A55) 28%, var(--dash-outline, #d4dbe8));
}

.service-card.available {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 20%, var(--dash-outline, #d4dbe8));
}

.service-main {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.service-icon {
  width: 46px;
  height: 46px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 16px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 23px;
}

.service-card.connected .service-icon {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.faceit-logo {
  width: 22px;
  height: 22px;
  display: block;
}

.gitea-logo {
  width: 26px;
  height: 26px;
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
  color: var(--dash-text-1, #10182b);
  font-size: 17px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.service-copy p {
  margin-top: 4px;
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.service-status {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 9px;
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.service-status.connected {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.service-status.available {
  background: color-mix(in srgb, var(--dash-accent, #345EA8) 12%, var(--dash-surface-soft, #F2F4F8));
  color: var(--dash-accent-strong, #163E86);
}

.service-controls,
.steam-connect,
.faceit-block,
.code-provider-block {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 170px;
}

.steam-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.steam-login,
.service-action {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 14px;
  font: inherit;
  font-size: 13px;
  font-weight: 900;
  transition:
    transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.steam-login {
  border-color: transparent;
  background: #171a21;
  color: #fff;
  cursor: pointer;
}

.service-action {
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  cursor: default;
}

.service-action.primary {
  border-color: transparent;
  background: var(--dash-accent, #345EA8);
  color: #fff;
  cursor: pointer;
}

.service-action.complete {
  border-color: color-mix(in srgb, var(--dash-green, #188A55) 28%, var(--dash-outline, #d4dbe8));
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.service-action.danger {
  border-color: color-mix(in srgb, var(--dash-red, #B3323A) 24%, var(--dash-outline, #d4dbe8));
  background: color-mix(in srgb, var(--dash-red-soft, #FFE5E7) 62%, white);
  color: var(--dash-red, #B3323A);
  cursor: pointer;
}

.steam-login:disabled,
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

.code-provider-summary {
  display: grid;
  gap: 10px;
  justify-items: end;
  min-width: 280px;
}

.code-provider-summary > div:first-child {
  display: grid;
  justify-items: end;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 16px;
  background: var(--dash-surface-soft, #F2F4F8);
}

.code-provider-summary strong {
  color: var(--dash-text-1, #10182b);
  font-size: 13px;
  font-weight: 950;
  overflow-wrap: anywhere;
}

.code-provider-summary span {
  color: var(--dash-text-2, #475778);
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
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.provider-field input {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 16px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  outline: none;
  padding: 0 12px;
  transition:
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    box-shadow 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.provider-field input:focus {
  border-color: var(--dash-accent, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 15%, transparent);
}

.integration-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 18px;
  background: color-mix(in srgb, #05070c 54%, transparent);
  backdrop-filter: blur(12px);
}

.integration-modal {
  position: relative;
  width: min(100%, 460px);
  display: grid;
  gap: 18px;
  padding: 28px;
  border: 1px solid color-mix(in srgb, var(--dash-outline, #d4dbe8) 64%, transparent);
  border-radius: 28px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 96%, transparent);
  box-shadow: 0 24px 70px color-mix(in srgb, #05070c 32%, transparent);
}

.integration-modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  width: 56px;
  height: 56px;
  display: inline-grid;
  place-items: center;
  border-radius: 20px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 29px;
}

.integration-modal-head h2,
.integration-modal-head p {
  margin: 0;
}

.integration-modal-head h2 {
  color: var(--dash-text-1, #10182b);
  font-size: 30px;
  line-height: 1.1;
  letter-spacing: 0;
}

.integration-modal-head p {
  color: var(--dash-text-2, #475778);
  font-size: 18px;
  line-height: 1.35;
}

.integration-modal-actions,
.integration-modal-form {
  display: grid;
  gap: 12px;
}

.modal-auth-button {
  min-height: 58px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 18px;
  padding: 0 18px;
  font: inherit;
  font-size: 16px;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.modal-auth-button.primary {
  border-color: var(--dash-outline, rgba(82, 103, 138, 0.18));
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
}

.modal-auth-button.secondary {
  background: var(--dash-accent, #345EA8);
  color: #fff;
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
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 800;
  text-align: center;
}

.integration-modal-back {
  justify-self: center;
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--dash-text-2, #475778);
  font: inherit;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.integration-modal-enter-active,
.integration-modal-leave-active {
  transition: opacity 200ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.integration-modal-enter-active .integration-modal,
.integration-modal-leave-active .integration-modal {
  transition:
    transform 220ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    opacity 220ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
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
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 24%, transparent);
  border-top-color: var(--dash-accent, #345EA8);
}

.steam-login:focus-visible,
.service-action:focus-visible,
.integration-modal-close:focus-visible,
.modal-auth-button:focus-visible,
.integration-modal-back:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--dash-accent, #345EA8) 32%, transparent);
  outline-offset: 2px;
}

@media (hover: hover) {
  .service-card:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 28%, var(--dash-outline, #d4dbe8));
    box-shadow: 0 14px 34px color-mix(in srgb, var(--dash-text-1, #10182b) 9%, transparent);
  }

  .service-action.primary:hover:not(:disabled),
  .steam-login:hover:not(:disabled),
  .modal-auth-button:hover:not(:disabled) {
    transform: translateY(-1px);
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
  }

  .summary-stats {
    justify-content: flex-start;
  }

  .service-controls,
  .steam-connect,
  .faceit-block,
  .code-provider-block,
  .code-provider-summary {
    justify-items: stretch;
    min-width: 0;
  }

  .steam-actions,
  .faceit-summary {
    justify-content: flex-start;
  }

  .service-action,
  .steam-login {
    width: 100%;
  }

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

  .service-main {
    align-items: flex-start;
  }

  .service-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
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
