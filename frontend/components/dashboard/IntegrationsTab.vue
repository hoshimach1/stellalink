<template>
  <div class="integrations-shell">
    <section class="integrations-hero">
      <div class="hero-copy">
        <p class="hero-kicker">Подключения</p>
        <h2>Сервисы для публичного профиля</h2>
        <p>
          Временная страница статусов. Позже здесь появятся OAuth-подключения,
          синхронизация и управление доступами.
        </p>
      </div>

      <div class="hero-meter" aria-label="Подключенные сервисы">
        <strong>{{ connectedCount }}</strong>
        <span>из {{ serviceCards.length }} уже используются в профиле</span>
      </div>
    </section>

    <section class="service-grid" aria-label="Сервисы">
      <article
        v-for="service in serviceCards"
        :key="service.type"
        class="service-card"
        :class="{ connected: service.connected }"
      >
        <div class="service-head">
          <span class="service-icon">
            <FaceitLogo v-if="service.type === 'widget_faceit'" class="faceit-logo" />
            <i v-else :class="service.icon" />
          </span>
          <span class="service-status" :class="{ connected: service.connected }">
            <i :class="service.connected ? 'ri-checkbox-circle-line' : 'ri-time-line'" />
            {{ service.connected ? 'Есть блок' : 'Заглушка' }}
          </span>
        </div>

        <div class="service-copy">
          <h3>{{ service.label }}</h3>
          <p>{{ service.description }}</p>
        </div>

        <button class="service-action" type="button" disabled>
          <i class="ri-plug-line" />
          <span>{{ service.connected ? 'Управление скоро' : 'Подключение скоро' }}</span>
        </button>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { BLOCK_LIBRARY } from '~/utils/dashboard-studio'
import { useProfileStore } from '~/stores/profile'

const profile = useProfileStore()

const integrationTypes = new Set(['widget_steam', 'widget_lastfm', 'widget_github', 'widget_faceit'])
const connectedTypes = computed(() => new Set(profile.profile?.blocks.map(block => block.block_type) ?? []))
const serviceCards = computed(() =>
  BLOCK_LIBRARY
    .filter(item => integrationTypes.has(item.type))
    .map(item => ({
      ...item,
      connected: connectedTypes.value.has(item.type),
    })),
)
const connectedCount = computed(() => serviceCards.value.filter(service => service.connected).length)
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
  cursor: not-allowed;
  opacity: 0.72;
}

@media (hover: hover) {
  .service-card:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 32%, var(--dash-outline, #d4dbe8));
  }
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
