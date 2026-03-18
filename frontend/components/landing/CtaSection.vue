<template>
  <div class="cta-section">
    <div class="cta-card reveal">
      <img src="/images/logos/logo.png" alt="" class="cta-logo">
      <h2 class="cta-title">Займи своё имя</h2>
      <p class="cta-sub">Бесплатно. Профиль готов за 2 минуты. Подключи сервисы — и он живёт сам.</p>
      <div class="cta-row">
        <div class="input-wrap">
          <div class="input-prefix">stellalink.app/</div>
          <input v-model="slug" class="input-slug" type="text" placeholder="username" @keydown.enter="submit">
        </div>
        <button class="btn-primary" @click="submit">Создать →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ openAuth: [slug: string] }>()
const slug = ref('')
const submit = () => emit('openAuth', slug.value)
</script>
