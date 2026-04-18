<template>
  <div class="hero">
    <div class="hero-glow" />
    <div class="hero-glow2" />
    <div class="hero-inner">
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
      <div class="url-strip">
        <md-outlined-card class="url-pill">stellalink.app/<strong>username</strong></md-outlined-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ openAuth: [] }>()
const scrollToDemo = () => document.querySelector('.demo-wrap')?.scrollIntoView({ behavior: 'smooth' })
</script>
