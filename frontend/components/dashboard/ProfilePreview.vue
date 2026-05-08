<template>
  <div class="preview">
    <header class="preview-header">
      <div class="preview-avatar">{{ initial }}</div>
      <div class="preview-copy">
        <strong>{{ profile.display_name || 'Имя не указано' }}</strong>
        <span v-if="profile.bio">{{ profile.bio }}</span>
        <div v-if="profile.tags.length" class="preview-tags">
          <span v-for="tag in profile.tags" :key="tag">{{ tag }}</span>
        </div>
      </div>
    </header>

    <div class="preview-blocks">
      <template v-for="block in visibleBlocks" :key="block.id">
        <section v-if="block.block_type === 'links'" class="preview-block">
          <div v-for="(group, index) in asGroups(block.config)" :key="`${group.title}-${index}`" class="preview-links">
            <p v-if="group.title" class="preview-title">{{ group.title }}</p>
            <a v-for="link in group.links" :key="`${link.label}-${link.url}`" :href="link.url" target="_blank" rel="noopener noreferrer">
              <i v-if="link.icon" :class="`ri-${link.icon}-fill`" />
              <span>{{ link.label || link.url }}</span>
            </a>
          </div>
        </section>

        <section v-else-if="block.block_type === 'text'" class="preview-block preview-text">
          {{ (block.config.content as string) || '' }}
        </section>

        <section v-else-if="block.block_type === 'widget_steam'" class="preview-block">
          <p class="preview-title">Steam</p>
          <strong>{{ (block.config.steam_id as string) || 'ID не указан' }}</strong>
        </section>

        <section v-else-if="block.block_type === 'widget_lastfm'" class="preview-block">
          <p class="preview-title">Last.fm</p>
          <strong>{{ (block.config.username as string) || 'Ник не указан' }}</strong>
        </section>

        <section v-else-if="block.block_type === 'widget_github'" class="preview-block">
          <p class="preview-title">GitHub</p>
          <strong>{{ (block.config.username as string) || 'Ник не указан' }}</strong>
        </section>

        <section v-else-if="block.block_type === 'pc_config'" class="preview-block">
          <p class="preview-title">{{ (block.config.title as string) || 'Конфиг ПК' }}</p>
          <div v-for="component in asComponents(block.config)" :key="`${component.category}-${component.name}`" class="preview-row">
            <span>{{ component.category }}</span>
            <strong>{{ component.name }}</strong>
          </div>
        </section>
      </template>

      <div v-if="!visibleBlocks.length" class="preview-empty">Добавьте блоки в редакторе</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Profile } from '~/stores/profile'

interface Link {
  label: string
  url: string
  icon?: string
}

interface Group {
  title: string
  links: Link[]
}

interface ComponentItem {
  category: string
  name: string
}

const props = defineProps<{ profile: Profile }>()

const initial = computed(() => props.profile.display_name?.[0]?.toUpperCase() ?? '?')
const visibleBlocks = computed(() => props.profile.blocks.filter(block => block.is_visible))

function asGroups(config: Record<string, unknown>): Group[] {
  return Array.isArray(config.groups) ? config.groups as Group[] : []
}

function asComponents(config: Record<string, unknown>): ComponentItem[] {
  return Array.isArray(config.components) ? config.components as ComponentItem[] : []
}
</script>

<style scoped>
.preview {
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: #11151d;
  color: #f8fafc;
  font-family: Onest, "Segoe UI", sans-serif;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.preview-avatar {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: linear-gradient(135deg, #345EA8, #F59E0B);
  color: #fff;
  font-size: 20px;
  font-weight: 900;
}

.preview-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.preview-copy strong {
  font-size: 16px;
}

.preview-copy span,
.preview-title,
.preview-empty {
  color: rgba(248,250,252,0.68);
  font-size: 12px;
}

.preview-tags,
.preview-links,
.preview-blocks {
  display: grid;
  gap: 8px;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.preview-tags span {
  padding: 3px 8px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 999px;
  background: rgba(255,255,255,0.07);
  color: rgba(248,250,252,0.78);
  font-size: 11px;
}

.preview-blocks {
  padding: 12px;
}

.preview-block {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.06);
}

.preview-title {
  margin: 0;
  font-weight: 900;
}

.preview-links a {
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.07);
  color: #f8fafc;
  text-decoration: none;
  font-size: 13px;
}

.preview-text {
  color: rgba(248,250,252,0.82);
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 6px;
  font-size: 12px;
}

.preview-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.preview-row span {
  color: rgba(248,250,252,0.62);
}

.preview-empty {
  padding: 18px;
  text-align: center;
}
</style>
