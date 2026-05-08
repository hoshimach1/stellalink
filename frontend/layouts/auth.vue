<template>
  <v-app>
    <div class="auth-root">
      <div class="auth-root-glow auth-root-glow-left" />
      <div class="auth-root-glow auth-root-glow-right" />
      <slot />
    </div>
  </v-app>
</template>

<script setup lang="ts">
useHead({
  meta: [
    { name: 'color-scheme', content: 'light dark' },
  ],
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans+Text:wght@400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wght@8..144,400;8..144,500;8..144,700&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css');
</style>

<style src="~/assets/css/auth-pages.css" />
