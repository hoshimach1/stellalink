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

        <button
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
import { computed, ref } from 'vue'
import { BLOCK_LIBRARY, createDefaultBlockConfig } from '~/utils/dashboard-studio'
import { useProfileStore } from '~/stores/profile'
import { extractAuthError } from '~/utils/auth-feedback'

const profile = useProfileStore()

type IntegrationType = 'widget_steam' | 'widget_lastfm' | 'widget_github' | 'widget_faceit'
type NoticeTone = 'success' | 'error'

const integrationTypes = new Set<IntegrationType>(['widget_steam', 'widget_lastfm', 'widget_github', 'widget_faceit'])
const integrationOrder: IntegrationType[] = ['widget_steam', 'widget_faceit', 'widget_github', 'widget_lastfm']
const connectableTypes = new Set<IntegrationType>(['widget_lastfm', 'widget_github'])
const connectedTypes = computed(() => new Set(profile.profile?.blocks.map(block => block.block_type) ?? []))
const connectingType = ref<IntegrationType | null>(null)
const connectNotice = ref('')
const connectNoticeTone = ref<NoticeTone>('success')
const showcaseIntegrations: Partial<Record<IntegrationType, {
  actionIcon: string
  actionLabel: string
  connected?: boolean
  description: string
  statusIcon: string
  statusLabel: string
}>> = {
  widget_steam: {
    actionIcon: 'ri-checkbox-circle-line',
    actionLabel: 'Подключено',
    connected: true,
    description: 'Steam привязан к аккаунту: профиль, статус и недавние игры готовы к показу.',
    statusIcon: 'ri-checkbox-circle-line',
    statusLabel: 'Подключён',
  },
  widget_faceit: {
    actionIcon: 'ri-link-m',
    actionLabel: 'Через Steam',
    connected: true,
    description: 'FACEIT настроен через Steam: CS2, уровень и ELO подтягиваются из игровой связки.',
    statusIcon: 'ri-link-m',
    statusLabel: 'Через Steam',
  },
  widget_lastfm: {
    actionIcon: 'ri-plug-line',
    actionLabel: 'Подключиться',
    description: 'Подключите Last.fm, чтобы показывать текущий трек и музыкальную активность.',
    statusIcon: 'ri-add-circle-line',
    statusLabel: 'Доступно',
  },
  widget_github: {
    actionIcon: 'ri-plug-line',
    actionLabel: 'Подключиться',
    description: 'Подключите GitHub, чтобы вывести активность и закреплённые репозитории.',
    statusIcon: 'ri-add-circle-line',
    statusLabel: 'Доступно',
  },
}
const serviceCards = computed(() =>
  BLOCK_LIBRARY
    .filter(item => integrationTypes.has(item.type as IntegrationType))
    .sort((a, b) => integrationOrder.indexOf(a.type as IntegrationType) - integrationOrder.indexOf(b.type as IntegrationType))
    .map((item) => {
      const type = item.type as IntegrationType
      const showcase = showcaseIntegrations[type]
      const connected = Boolean(showcase?.connected || connectedTypes.value.has(type))
      return {
        ...item,
        ...showcase,
        actionIcon: connected ? (showcase?.actionIcon ?? 'ri-checkbox-circle-line') : (showcase?.actionIcon ?? 'ri-plug-line'),
        actionLabel: connected ? (showcase?.connected ? showcase.actionLabel : 'Подключено') : (showcase?.actionLabel ?? 'Подключиться'),
        canConnect: connectableTypes.has(type) && !connected,
        connected,
        description: showcase?.description ?? item.description,
        statusIcon: connected ? (showcase?.statusIcon ?? 'ri-checkbox-circle-line') : (showcase?.statusIcon ?? 'ri-add-circle-line'),
        statusLabel: connected ? (showcase?.statusLabel === 'Доступно' ? 'Подключён' : showcase?.statusLabel ?? 'Подключён') : (showcase?.statusLabel ?? 'Доступно'),
      }
    }),
)
const connectedCount = computed(() => serviceCards.value.filter(service => service.connected).length)

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
