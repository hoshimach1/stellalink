<template>
  <div v-if="pending" class="pub-loading">
    <div class="pub-spinner" />
  </div>

  <div v-else-if="!profile" class="pub-notfound">
    <img src="/images/logos/logo.png" alt="" class="pub-nf-logo">
    <h2>Профиль не найден</h2>
    <p>Пользователь <strong>{{ $route.params.slug }}</strong> не существует или ещё не опубликовал профиль.</p>
    <NuxtLink to="/" class="pub-home-btn">На главную</NuxtLink>
  </div>

  <div v-else class="pub-page">
    <!-- Header -->
    <div class="pub-header">
      <div class="pub-avatar">{{ initial }}</div>
      <div class="pub-info">
        <div class="pub-name">{{ profile.display_name }}</div>
        <div v-if="profile.bio" class="pub-bio">{{ profile.bio }}</div>
        <div v-if="profile.tags.length" class="pub-tags">
          <span v-for="tag in profile.tags" :key="tag" class="pub-tag">{{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- Blocks -->
    <div class="pub-blocks">
      <template v-for="block in visibleBlocks" :key="block.id">

        <!-- Links -->
        <div v-if="block.block_type === 'links'" class="pub-block">
          <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
            <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
            <a
              v-for="link in group.links"
              :key="link.url"
              :href="link.url"
              target="_blank"
              rel="noopener"
              class="pub-link"
            >
              <i v-if="link.icon" :class="`ri-${link.icon}-fill`" />
              <span>{{ link.label }}</span>
              <i class="ri-arrow-right-up-line pub-link-arrow" />
            </a>
          </div>
        </div>

        <!-- Text -->
        <div v-else-if="block.block_type === 'text'" class="pub-block pub-text">
          {{ (block.config.content as string) }}
        </div>

        <!-- Steam -->
        <div v-else-if="block.block_type === 'widget_steam'" class="pub-block pub-widget">
          <div class="pub-widget-header">
            <span class="pub-widget-icon">🎮</span>
            <span class="pub-widget-title">Steam</span>
          </div>
          <div class="pub-widget-val">{{ (block.config.steam_id as string) || '—' }}</div>
        </div>

        <!-- Last.fm -->
        <div v-else-if="block.block_type === 'widget_lastfm'" class="pub-block pub-widget">
          <div class="pub-widget-header">
            <span class="pub-widget-icon">🎵</span>
            <span class="pub-widget-title">Last.fm</span>
          </div>
          <div class="pub-widget-val">{{ (block.config.username as string) || '—' }}</div>
        </div>

        <!-- GitHub -->
        <div v-else-if="block.block_type === 'widget_github'" class="pub-block pub-widget">
          <div class="pub-widget-header">
            <span class="pub-widget-icon">🐙</span>
            <span class="pub-widget-title">GitHub</span>
          </div>
          <div class="pub-widget-val">{{ (block.config.username as string) || '—' }}</div>
        </div>

        <!-- PC Config -->
        <div v-else-if="block.block_type === 'pc_config'" class="pub-block pub-pc">
          <div class="pub-widget-header">
            <span class="pub-widget-icon">💻</span>
            <span class="pub-widget-title">{{ (block.config.title as string) || 'PC Config' }}</span>
          </div>
          <div v-for="c in (block.config.components as Component[])" :key="c.category" class="pub-pc-row">
            <span class="pub-pc-cat">{{ c.category }}</span>
            <span class="pub-pc-val">{{ c.name }}</span>
          </div>
        </div>

      </template>
    </div>

    <!-- Footer -->
    <div class="pub-footer">
      <NuxtLink to="/" class="pub-footer-link">
        <img src="/images/logos/logo.png" alt="" class="pub-footer-logo">
        Сделано на Stellalink
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Block } from '~/stores/profile'

interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }

definePageMeta({ layout: 'landing' })

const route = useRoute()
const config = useRuntimeConfig()
const slug = route.params.slug as string

useHead({ title: `${slug} — Stellalink` })

const { data: profile, pending } = await useFetch<{
  id: string
  slug: string
  status: string
  display_name: string
  bio: string | null
  tags: string[]
  blocks: Block[]
} | null>(`${config.public.apiBase}/u/${slug}`, {
  default: () => null,
  onResponseError() { return null },
})

const initial = computed(() => profile.value?.display_name?.[0]?.toUpperCase() ?? '?')
const visibleBlocks = computed(() => profile.value?.blocks.filter(b => b.is_visible) ?? [])
</script>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css');
</style>

<style scoped>
.pub-loading {
  min-height: 100vh; background: #090910;
  display: flex; align-items: center; justify-content: center;
}
.pub-spinner {
  width: 36px; height: 36px; border-radius: 50%;
  border: 3px solid rgba(61,142,255,0.2); border-top-color: #3D8EFF;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pub-notfound {
  min-height: 100vh; background: #090910; color: #eeeef8;
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 24px; gap: 12px;
}
.pub-nf-logo { width: 56px; opacity: 0.5; mix-blend-mode: screen; }
.pub-notfound h2 { font-size: 24px; font-weight: 800; }
.pub-notfound p { color: #6a6a90; font-size: 15px; }
.pub-home-btn {
  margin-top: 8px; padding: 10px 24px;
  background: rgba(61,142,255,0.12); border: 1px solid rgba(61,142,255,0.24);
  border-radius: 10px; color: #90beff; text-decoration: none; font-size: 14px;
}

.pub-page {
  min-height: 100vh; background: #090910; color: #eeeef8;
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 16px 40px;
}

.pub-header {
  display: flex; align-items: center; gap: 18px;
  width: 100%; max-width: 480px; margin-bottom: 28px;
}
.pub-avatar {
  width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: #fff;
}
.pub-name { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; margin-bottom: 4px; }
.pub-bio { font-size: 14px; color: #6a6a90; margin-bottom: 8px; }
.pub-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.pub-tag {
  background: rgba(61,142,255,0.10); color: #90beff;
  border: 1px solid rgba(61,142,255,0.18); border-radius: 100px;
  padding: 2px 10px; font-size: 11px; font-weight: 500;
}

.pub-blocks {
  width: 100%; max-width: 480px;
  display: flex; flex-direction: column; gap: 10px;
}

.pub-block {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 14px; padding: 16px;
}

.pub-links-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.pub-links-group:last-child { margin-bottom: 0; }
.pub-group-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.2px; color: #6a6a90; margin-bottom: 2px;
}
.pub-link {
  display: flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(61,142,255,0.10);
  border-radius: 10px; padding: 12px 16px;
  text-decoration: none; color: #eeeef8; font-size: 14px; font-weight: 500;
  transition: background 0.2s, border-color 0.2s, transform 0.15s;
}
.pub-link:hover { background: rgba(61,142,255,0.08); border-color: rgba(61,142,255,0.22); transform: translateY(-1px); }
.pub-link-arrow { margin-left: auto; color: #3a3a58; font-size: 16px; }

.pub-text { font-size: 14px; color: #aaaacc; white-space: pre-wrap; line-height: 1.6; }

.pub-widget-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.pub-widget-icon { font-size: 18px; }
.pub-widget-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6a6a90; }
.pub-widget-val { font-size: 15px; font-weight: 600; }

.pub-pc-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid rgba(61,142,255,0.06);
  font-size: 13px;
}
.pub-pc-row:last-child { border-bottom: none; }
.pub-pc-cat { color: #6a6a90; }
.pub-pc-val { font-weight: 500; text-align: right; }

.pub-footer {
  margin-top: 40px; padding-top: 24px;
  border-top: 1px solid rgba(61,142,255,0.06);
  width: 100%; max-width: 480px;
  display: flex; justify-content: center;
}
.pub-footer-link {
  display: flex; align-items: center; gap: 7px;
  color: #3a3a58; text-decoration: none; font-size: 12px;
  transition: color 0.2s;
}
.pub-footer-link:hover { color: #6a6a90; }
.pub-footer-logo { width: 18px; opacity: 0.4; mix-blend-mode: screen; }
</style>
