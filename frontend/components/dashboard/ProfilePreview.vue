<template>
  <div class="preview">
    <!-- Header -->
    <div class="prev-header">
      <div class="prev-avatar">{{ initial }}</div>
      <div>
        <div class="prev-name">{{ profile.display_name || 'Имя не указано' }}</div>
        <div class="prev-bio">{{ profile.bio || '' }}</div>
        <div v-if="profile.tags.length" class="prev-tags">
          <span v-for="tag in profile.tags" :key="tag" class="prev-tag">{{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- Blocks -->
    <div class="prev-blocks">
      <template v-for="block in visibleBlocks" :key="block.id">
        <!-- Links -->
        <div v-if="block.block_type === 'links'" class="prev-block">
          <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="prev-links-group">
            <div v-if="group.title" class="prev-group-title">{{ group.title }}</div>
            <a
              v-for="link in group.links"
              :key="link.url"
              :href="link.url"
              target="_blank"
              class="prev-link"
            >
              <i v-if="link.icon" :class="`ri-${link.icon}-fill`" />
              {{ link.label }}
            </a>
          </div>
        </div>

        <!-- Text -->
        <div v-else-if="block.block_type === 'text'" class="prev-block prev-text">
          {{ (block.config.content as string) || '' }}
        </div>

        <!-- Steam -->
        <div v-else-if="block.block_type === 'widget_steam'" class="prev-block prev-widget">
          <div class="prev-widget-title">🎮 Steam</div>
          <div class="prev-widget-val">{{ (block.config.steam_id as string) || 'ID не указан' }}</div>
        </div>

        <!-- Last.fm -->
        <div v-else-if="block.block_type === 'widget_lastfm'" class="prev-block prev-widget">
          <div class="prev-widget-title">🎵 Last.fm</div>
          <div class="prev-widget-val">{{ (block.config.username as string) || 'Имя не указано' }}</div>
        </div>

        <!-- GitHub -->
        <div v-else-if="block.block_type === 'widget_github'" class="prev-block prev-widget">
          <div class="prev-widget-title">🐙 GitHub</div>
          <div class="prev-widget-val">{{ (block.config.username as string) || 'Имя не указано' }}</div>
        </div>

        <!-- PC Config -->
        <div v-else-if="block.block_type === 'pc_config'" class="prev-block prev-pc">
          <div class="prev-widget-title">💻 {{ (block.config.title as string) || 'PC Config' }}</div>
          <div v-for="c in (block.config.components as Component[])" :key="c.category" class="prev-pc-row">
            <span class="prev-pc-cat">{{ c.category }}</span>
            <span>{{ c.name }}</span>
          </div>
        </div>
      </template>

      <div v-if="!visibleBlocks.length" class="prev-empty">
        Добавь блоки в редакторе
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Profile, Block } from '~/stores/profile'

interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }

const props = defineProps<{ profile: Profile }>()

const initial = computed(() =>
  props.profile.display_name?.[0]?.toUpperCase() ?? '?'
)
const visibleBlocks = computed(() =>
  props.profile.blocks.filter(b => b.is_visible)
)
</script>

<style scoped>
.preview {
  font-family: 'Onest', sans-serif;
  color: #eeeef8;
}

.prev-header {
  display: flex; align-items: center; gap: 14px;
  padding: 20px;
  border-bottom: 1px solid rgba(61,142,255,0.07);
  background: linear-gradient(160deg, rgba(61,142,255,0.06) 0%, transparent 60%);
}
.prev-avatar {
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800; color: #fff;
}
.prev-name { font-size: 15px; font-weight: 700; margin-bottom: 2px; }
.prev-bio { font-size: 12px; color: #6a6a90; margin-bottom: 6px; }
.prev-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.prev-tag {
  background: rgba(61,142,255,0.10); color: #90beff;
  border: 1px solid rgba(61,142,255,0.16); border-radius: 100px;
  padding: 1px 8px; font-size: 10px; font-weight: 500;
}

.prev-blocks { padding: 12px; display: flex; flex-direction: column; gap: 8px; }

.prev-block {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(61,142,255,0.08);
  border-radius: 10px; padding: 12px;
}

.prev-links-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.prev-links-group:last-child { margin-bottom: 0; }
.prev-group-title { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6a6a90; margin-bottom: 4px; }
.prev-link {
  display: flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.10);
  border-radius: 8px; padding: 8px 12px;
  text-decoration: none; color: #eeeef8; font-size: 13px;
  transition: background 0.2s;
}
.prev-link:hover { background: rgba(61,142,255,0.08); }

.prev-text { font-size: 13px; color: #aaaacc; white-space: pre-wrap; }

.prev-widget { }
.prev-widget-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6a6a90; margin-bottom: 6px; }
.prev-widget-val { font-size: 14px; font-weight: 600; }

.prev-pc-row { display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; border-bottom: 1px solid rgba(61,142,255,0.06); }
.prev-pc-cat { color: #6a6a90; }

.prev-empty { text-align: center; padding: 24px; color: #3a3a58; font-size: 13px; }
</style>
