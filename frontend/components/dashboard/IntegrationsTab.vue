<template>
  <div class="integrations-shell">
    <section class="integrations-hero">
      <div class="hero-copy">
        <p class="hero-kicker">Подключения</p>
        <h2>Интеграции публичного профиля</h2>
        <p>
          Здесь вы можете посмотреть ваши интеграции с сервисами
        </p>
      </div>

      <div class="hero-meter" aria-label="Подключенные сервисы">
        <strong>{{ connectedCount }}</strong>
        <span>из {{ serviceCards.length }} интеграций активны</span>
      </div>
    </section>

    <div v-if="connectNotice" class="integration-notice" :class="connectNoticeTone">
      {{ connectNotice }}
    </div>

    <div v-if="loading" class="integration-notice">
      Загружаем подключения...
    </div>

    <section class="service-grid" aria-label="Сервисы">
      <article
        v-for="service in serviceCards"
        :key="service.type"
        class="service-card"
        :class="{ connected: service.connected, available: service.canConnect }"
      >
        <div class="service-head">
          <span class="service-icon">
            <FaceitLogo v-if="service.type === 'widget_faceit'" class="faceit-logo" />
            <i v-else :class="service.icon" />
          </span>
          <span class="service-status" :class="{ connected: service.connected, available: service.canConnect }">
            <i :class="service.statusIcon" />
            {{ service.statusLabel }}
          </span>
        </div>

        <div class="service-copy">
          <h3>{{ service.label }}</h3>
          <p>{{ service.description }}</p>
        </div>

        <form v-if="service.type === 'widget_steam'" class="steam-connect" @submit.prevent="saveSteamConnection">
          <label class="steam-field">
            <span>SteamID64 или ссылка на профиль</span>
            <input v-model="steamInput" type="text" placeholder="76561198... или https://steamcommunity.com/id/name">
          </label>
          <div class="steam-actions">
            <button class="service-action primary" type="submit" :disabled="steamBusy || !steamInput.trim()">
              <span v-if="steamBusy" class="integration-spinner" />
              <i v-else class="ri-link-m" />
              <span>{{ steamAccount ? 'Обновить привязку' : 'Привязать Steam' }}</span>
            </button>
            <button v-if="steamAccount" class="service-action" type="button" :disabled="steamBusy" @click="syncSteamConnection">
              <i class="ri-refresh-line" />
              <span>Синхронизировать</span>
            </button>
            <button v-if="steamAccount" class="service-action danger" type="button" :disabled="steamBusy" @click="disconnectSteamConnection">
              <i class="ri-link-unlink-m" />
              <span>Отключить</span>
            </button>
          </div>
        </form>

        <div v-else-if="service.type === 'widget_faceit' && faceitAccount" class="faceit-summary">
          <span>Уровень {{ faceitSkillLevel || '—' }}</span>
          <span>{{ faceitElo ? `${faceitElo} ELO` : 'ELO не получен' }}</span>
        </div>

        <button
          v-if="service.type !== 'widget_steam' && service.type !== 'widget_faceit'"
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
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { BLOCK_LIBRARY, createDefaultBlockConfig } from '~/utils/dashboard-studio'
import { useProfileStore, type Block } from '~/stores/profile'
import { useAuthStore } from '~/stores/auth'
import { extractAuthError } from '~/utils/auth-feedback'

const profile = useProfileStore()
const auth = useAuthStore()
const config = useRuntimeConfig()

type IntegrationType = 'widget_steam' | 'widget_lastfm' | 'widget_github' | 'widget_faceit'
type NoticeTone = 'success' | 'error'
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
  }
}

const integrationTypes = new Set<IntegrationType>(['widget_steam', 'widget_lastfm', 'widget_github', 'widget_faceit'])
const integrationOrder: IntegrationType[] = ['widget_steam', 'widget_faceit', 'widget_github', 'widget_lastfm']
const connectableTypes = new Set<IntegrationType>(['widget_lastfm', 'widget_github'])
const integrations = ref<IntegrationsResponse | null>(null)
const loading = ref(false)
const steamBusy = ref(false)
const steamInput = ref('')
const connectingType = ref<IntegrationType | null>(null)
const connectNotice = ref('')
const connectNoticeTone = ref<NoticeTone>('success')

const steamAccount = computed(() => integrations.value?.accounts.find(account => account.provider === 'steam' && account.is_active) ?? null)
const faceitAccount = computed(() => integrations.value?.accounts.find(account => account.provider === 'faceit' && account.is_active) ?? null)
const faceitSkillLevel = computed(() => faceitAccount.value?.metadata?.skill_level ?? faceitAccount.value?.metadata?.skill_level_label ?? null)
const faceitElo = computed(() => faceitAccount.value?.metadata?.faceit_elo ?? null)
const blockConnectedTypes = computed(() => new Set(profile.profile?.blocks.map(block => block.block_type) ?? []))
const connectedTypes = computed(() => {
  const set = new Set<string>(blockConnectedTypes.value)
  if (steamAccount.value) set.add('widget_steam')
  if (faceitAccount.value) set.add('widget_faceit')
  return set
})
const serviceCards = computed(() =>
  BLOCK_LIBRARY
    .filter(item => integrationTypes.has(item.type as IntegrationType))
    .sort((a, b) => integrationOrder.indexOf(a.type as IntegrationType) - integrationOrder.indexOf(b.type as IntegrationType))
    .map((item) => {
      const type = item.type as IntegrationType
      const connected = connectedTypes.value.has(type)
      const apiReady = integrations.value?.capabilities
      const steamDescription = steamAccount.value
        ? `${steamAccount.value.display_name || steamAccount.value.provider_uid}: профиль, последние игры и Steam-статистика синхронизированы.`
        : apiReady?.steam_api_key_set
          ? 'Привяжите SteamID64 или ссылку на профиль, чтобы подтянуть Steam и FACEIT-данные.'
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
        widget_github: 'Подключите GitHub, чтобы вывести активность и закреплённые репозитории.',
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
    }),
)
const connectedCount = computed(() => serviceCards.value.filter(service => service.connected).length)

onMounted(() => {
  void loadIntegrations()
})

function applyIntegrations(data: IntegrationsResponse) {
  integrations.value = data
  if (steamAccount.value && !steamInput.value) {
    steamInput.value = steamAccount.value.provider_uid
  }
}

async function loadIntegrations() {
  loading.value = true
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/me`)
    applyIntegrations(data)
  } catch (error) {
    connectNoticeTone.value = 'error'
    connectNotice.value = extractAuthError(error, 'Не удалось загрузить подключения.')
  } finally {
    loading.value = false
  }
}

async function ensureSteamBlock(account: ConnectedAccount) {
  if (!profile.profile) return
  const existing = profile.profile?.blocks.find((block: Block) => block.block_type === 'widget_steam')
  const nextConfig = {
    ...(existing?.config ?? createDefaultBlockConfig('widget_steam')),
    steam_id: (existing?.config?.steam_id as string) || account.provider_uid,
    use_connected_account: true,
    show_recent_games: existing?.config?.show_recent_games ?? true,
    show_profile_stats: existing?.config?.show_profile_stats ?? true,
    show_inventory_highlight: existing?.config?.show_inventory_highlight ?? true,
  }

  if (existing) {
    await profile.updateBlock(existing.id, { config: nextConfig })
  } else {
    await profile.createBlock('widget_steam', nextConfig)
  }
}

async function saveSteamConnection() {
  if (!steamInput.value.trim()) return
  steamBusy.value = true
  connectNotice.value = ''
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/steam`, {
      method: 'PUT',
      body: { steam_id: steamInput.value.trim() },
    })
    applyIntegrations(data)
    if (steamAccount.value) {
      await ensureSteamBlock(steamAccount.value)
    }
    await profile.fetch()
    connectNoticeTone.value = 'success'
    connectNotice.value = faceitAccount.value
      ? 'Steam привязан, FACEIT найден автоматически.'
      : 'Steam привязан. FACEIT не найден или API-ключ FACEIT не настроен.'
  } catch (error) {
    connectNoticeTone.value = 'error'
    connectNotice.value = extractAuthError(error, 'Не удалось привязать Steam.')
  } finally {
    steamBusy.value = false
  }
}

async function syncSteamConnection() {
  steamBusy.value = true
  connectNotice.value = ''
  try {
    const data = await auth.authorizedFetch<IntegrationsResponse>(`${config.public.apiBase}/integrations/steam/sync`, {
      method: 'POST',
    })
    applyIntegrations(data)
    await profile.fetch()
    connectNoticeTone.value = 'success'
    connectNotice.value = 'Steam и FACEIT-данные синхронизированы.'
  } catch (error) {
    connectNoticeTone.value = 'error'
    connectNotice.value = extractAuthError(error, 'Не удалось синхронизировать Steam.')
  } finally {
    steamBusy.value = false
  }
}

async function disconnectSteamConnection() {
  steamBusy.value = true
  connectNotice.value = ''
  try {
    await auth.authorizedFetch(`${config.public.apiBase}/integrations/steam`, { method: 'DELETE' })
    steamInput.value = ''
    await loadIntegrations()
    await profile.fetch()
    connectNoticeTone.value = 'success'
    connectNotice.value = 'Steam отключён от аккаунта.'
  } catch (error) {
    connectNoticeTone.value = 'error'
    connectNotice.value = extractAuthError(error, 'Не удалось отключить Steam.')
  } finally {
    steamBusy.value = false
  }
}

async function connectService(type: IntegrationType) {
  if (!connectableTypes.has(type) || connectedTypes.value.has(type)) return
  connectingType.value = type
  connectNotice.value = ''
  try {
    await profile.createBlock(type, createDefaultBlockConfig(type))
    connectNoticeTone.value = 'success'
    connectNotice.value = type === 'widget_github'
      ? 'GitHub подключён. Блок добавлен в публичный профиль.'
      : 'Last.fm подключён. Блок добавлен в публичный профиль.'
  } catch (error) {
    connectNoticeTone.value = 'error'
    connectNotice.value = extractAuthError(error, 'Не удалось подключить интеграцию.')
  } finally {
    connectingType.value = null
  }
}
</script>

<style scoped>
.integrations-shell {
  width: min(100%, 1060px);
  display: grid;
  gap: 14px;
  margin: 0 auto;
}

.integrations-shell,
.integrations-shell * {
  box-sizing: border-box;
}

.integrations-hero,
.service-card {
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 92%, transparent);
  box-shadow: 0 10px 28px rgba(48, 63, 92, 0.08);
}

.integrations-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px;
}

.hero-copy {
  max-width: 700px;
  min-width: 0;
}

.hero-kicker,
.hero-copy h2,
.hero-copy p,
.service-copy h3,
.service-copy p {
  margin: 0;
}

.hero-kicker {
  color: var(--dash-accent-strong, #163E86);
  font-size: 12px;
  font-weight: 900;
}

.hero-copy h2 {
  margin-top: 4px;
  color: var(--dash-text-1, #10182b);
  font-size: 28px;
  line-height: 1.08;
  overflow-wrap: anywhere;
}

.hero-copy p {
  margin-top: 8px;
  color: var(--dash-text-2, #475778);
  font-size: 14px;
  line-height: 1.5;
}

.hero-meter {
  min-width: 176px;
  display: grid;
  gap: 4px;
  padding: 14px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
}

.hero-meter strong {
  font-size: 34px;
  line-height: 1;
}

.hero-meter span {
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.service-card {
  min-width: 0;
  display: grid;
  gap: 16px;
  padding: 16px;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1);
}

.service-card.connected {
  border-color: color-mix(in srgb, var(--dash-green, #188A55) 32%, var(--dash-outline, #d4dbe8));
}

.service-card.available {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 20%, var(--dash-outline, #d4dbe8));
}

.service-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.service-icon {
  width: 42px;
  height: 42px;
  display: inline-grid;
  place-items: center;
  border-radius: 8px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 22px;
}

.faceit-logo {
  width: 22px;
  height: 22px;
  display: block;
}

.service-status {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
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

.service-copy h3 {
  color: var(--dash-text-1, #10182b);
  font-size: 18px;
  overflow-wrap: anywhere;
}

.service-copy p {
  margin-top: 4px;
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.steam-connect {
  display: grid;
  gap: 10px;
}

.steam-field {
  display: grid;
  gap: 6px;
}

.steam-field span {
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.steam-field input {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  outline: none;
  padding: 0 12px;
}

.steam-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.faceit-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.faceit-summary span {
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

.service-action {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font: inherit;
  font-weight: 900;
  cursor: default;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1),
    color 180ms cubic-bezier(0.2, 0, 0, 1);
}

.service-action.primary {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 34%, var(--dash-outline, #d4dbe8));
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
  color: var(--dash-red, #B3323A);
}

.service-action:disabled:not(.complete) {
  cursor: wait;
  opacity: 0.82;
}

.integration-notice {
  min-height: 44px;
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  font-weight: 800;
}

.integration-notice.success {
  border-color: color-mix(in srgb, var(--dash-green, #188A55) 24%, var(--dash-outline, #d4dbe8));
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.integration-notice.error {
  border-color: color-mix(in srgb, var(--dash-red, #B3323A) 24%, var(--dash-outline, #d4dbe8));
  background: var(--dash-red-soft, #FFE5E7);
  color: var(--dash-red, #B3323A);
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

@media (hover: hover) {
  .service-card:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 32%, var(--dash-outline, #d4dbe8));
  }

  .service-action.primary:hover:not(:disabled) {
    transform: translateY(-1px);
    background: color-mix(in srgb, var(--dash-accent, #345EA8) 88%, #000);
  }
}

@keyframes integration-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 780px) {
  .integrations-hero {
    align-items: stretch;
    flex-direction: column;
  }

  .hero-meter {
    min-width: 0;
  }

  .service-grid {
    grid-template-columns: 1fr;
  }

  .service-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .service-status {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .integrations-hero,
  .service-card {
    padding: 16px;
  }

  .hero-copy h2 {
    font-size: 26px;
  }
}
</style>
