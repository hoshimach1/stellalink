<template>
  <div class="cta-section">
    <md-filled-card class="cta-card reveal">
      <img src="/images/logos/logo.png" alt="" class="cta-logo">
      <h2 class="cta-title md-typescale-headline-large">Займи своё имя</h2>
      <p class="cta-sub md-typescale-body-large">Бесплатно. Профиль готов за 2 минуты. Подключи сервисы — и он живёт сам.</p>
      <div class="cta-row">
        <div class="input-wrap">
          <div class="input-prefix">stellalink.app/</div>
          <md-outlined-text-field class="input-slug" :value="slug" type="text" placeholder="username" @input="onSlugInput" @keydown.enter.prevent="submit" />
        </div>
        <md-filled-button class="btn-primary" @click="submit">Создать →</md-filled-button>
      </div>
    </md-filled-card>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ openAuth: [slug: string] }>()
const slug = ref('')
const submit = () => emit('openAuth', slug.value)

function onSlugInput(event: Event) {
  slug.value = (event.target as { value?: string } | null)?.value ?? ''
}
</script>
