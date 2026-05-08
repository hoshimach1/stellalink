<template>
  <section class="hero">
    <div class="hero-glow" />
    <div class="hero-glow2" />

    <div class="hero-grid">
      <div class="hero-copy">
        <img src="/images/logos/logo.png" alt="" class="hero-logo">
        <div class="hero-badge md-typescale-body-small">
          <div class="badge-live" />
          Живые данные — прямо сейчас
        </div>

        <h1 class="md-typescale-display-large"><span class="h1-gradient">Твой профиль,<br>который дышит</span></h1>
        <p class="hero-sub md-typescale-body-large">Один линк — и все видят кто ты есть прямо сейчас. Что слушаешь, во что играешь, куда написать — всё в одном месте и всегда актуально.</p>

        <div class="hero-actions">
          <md-filled-button class="btn-primary" @click="$emit('openAuth')">Создать профиль →</md-filled-button>
          <md-outlined-button class="btn-secondary" @click="scrollToDemo">Смотреть демо</md-outlined-button>
        </div>

        <md-chip-set class="hero-signals">
          <md-suggestion-chip label="Steam Live" />
          <md-suggestion-chip label="Faceit Stats" />
          <md-suggestion-chip label="Now Playing" />
          <md-suggestion-chip label="GitHub Links" />
        </md-chip-set>
      </div>

      <md-elevated-card class="hero-panel">
        <div class="hero-panel-title md-typescale-title-large">Live-слепок профиля</div>
        <div class="hero-panel-sub md-typescale-body-medium">Как выглядит страница, когда все блоки работают в реальном времени.</div>

        <md-outlined-card class="hero-signal">
          <div class="hero-signal-head"><i class="ri-steam-fill" /> Steam</div>
          <div class="hero-signal-value">Counter-Strike 2 · онлайн</div>
        </md-outlined-card>

        <md-outlined-card class="hero-signal">
          <div class="hero-signal-head"><i class="ri-lastfm-fill" /> Музыка</div>
          <div class="hero-signal-value">Arctic Monkeys — Fluorescent Adolescent</div>
        </md-outlined-card>

        <md-outlined-card class="hero-signal">
          <div class="hero-signal-head"><FaceitLogo class="hero-faceit-logo" /> Faceit</div>
          <div class="hero-signal-value">Lvl 8 · 1847 ELO · 54% WR</div>
        </md-outlined-card>

        <md-divider />
        <md-outlined-card class="url-pill hero-url">stellalink.app/<strong>username</strong></md-outlined-card>
      </md-elevated-card>
    </div>
  </section>
</template>

<script setup lang="ts">
defineEmits<{ openAuth: [] }>()

const scrollToDemo = () => document.querySelector('.demo-wrap')?.scrollIntoView({ behavior: 'smooth' })
</script>
