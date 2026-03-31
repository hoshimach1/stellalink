<template>
  <div class="pt-wrap">

    <!-- ── Sidebar ── -->
    <div class="pt-sidebar">

      <!-- Block list view -->
      <template v-if="!selectedBlockId">

        <div class="pt-status-row">
          <button class="pt-toggle" :class="{ active: profile.isPublished }" @click="toggleStatus">
            <span class="pt-toggle-dot" />
            {{ profile.isPublished ? 'Опубликован' : 'Черновик' }}
          </button>
          <a v-if="profile.isPublished" :href="`/${profile.profile!.slug}`" target="_blank" class="pt-view-btn">
            <i class="ri-external-link-line" />
          </a>
        </div>

        <!-- Sidebar tabs -->
        <div class="pt-sidebar-tabs">
          <button class="pt-stab" :class="{ active: sidebarTab === 'blocks' }" @click="sidebarTab = 'blocks'">
            <i class="ri-layout-grid-line" /> Блоки
          </button>
          <button class="pt-stab" :class="{ active: sidebarTab === 'design' }" @click="sidebarTab = 'design'">
            <i class="ri-palette-line" /> Оформление
          </button>
        </div>

        <!-- Blocks tab -->
        <template v-if="sidebarTab === 'blocks'">
          <div class="pt-section-label">Блоки</div>
          <VueDraggable
            v-model="localBlocks"
            class="pt-block-list"
            :animation="180"
            handle=".pt-drag-handle"
            ghost-class="pt-ghost"
            @end="saveOrder"
          >
            <div
              v-for="block in localBlocks"
              :key="block.id"
              class="pt-block-item"
              @click="selectBlock(block.id)"
            >
              <i class="ri-drag-move-line pt-drag-handle" />
              <span class="pt-block-icon">{{ blockIcon(block.block_type) }}</span>
              <span class="pt-block-label">{{ blockLabel(block.block_type) }}</span>
              <div class="pt-block-actions">
                <button class="pt-vis-btn" :class="{ active: block.is_visible }" @click.stop="toggleVisible(block)" />
                <button class="pt-del-btn" @click.stop="deleteBlock(block.id)">
                  <i class="ri-delete-bin-line" />
                </button>
              </div>
            </div>
          </VueDraggable>
          <p v-if="!localBlocks.length" class="pt-empty">Перетащи блок из панели ниже или нажми «+»</p>

          <div class="pt-section-label" style="margin-top:14px">Добавить</div>
          <VueDraggable
            v-model="blockTypes"
            class="pt-add-list"
            :group="{ name: 'blocks', pull: 'clone', put: false }"
            :sort="false"
            ghost-class="pt-ghost-add"
          >
            <div
              v-for="bt in blockTypes"
              :key="bt.type"
              class="pt-add-item"
              :data-type="bt.type"
              @click="addBlock(bt.type)"
            >
              <span class="pt-add-ico">{{ bt.icon }}</span>
              <span class="pt-add-label">{{ bt.label }}</span>
              <i class="ri-add-line pt-add-plus" />
            </div>
          </VueDraggable>
        </template>

        <!-- Design tab -->
        <template v-else-if="sidebarTab === 'design'">
          <div class="pt-section-label">Тема</div>
          <div class="pt-theme-list">
            <button
              v-for="t in THEMES"
              :key="t.id"
              class="pt-theme-row"
              :class="{ active: currentTheme === t.id }"
              @click="setTheme(t.id)"
            >
              <div class="pt-theme-swatch" :class="`pt-swatch-${t.id}`">
                <div v-if="t.id === 'glass'" class="pt-swatch-glass-orbs">
                  <span class="pt-swatch-orb pt-swatch-orb-1" />
                  <span class="pt-swatch-orb pt-swatch-orb-2" />
                </div>
                <div v-if="t.id === 'glass'" class="pt-swatch-glass-pane" />
                <div v-if="t.id === 'material3'" class="pt-swatch-m3-shapes">
                  <span class="pt-swatch-m3-s1" :style="`background:${currentAccent}`" />
                  <span class="pt-swatch-m3-s2" :style="`background:${currentAccent}`" />
                </div>
                <span v-if="t.id === 'fluent'" class="pt-theme-dot" :style="`background:${t.previewDot}`" />
              </div>
              <div class="pt-theme-info">
                <span class="pt-theme-name">{{ t.label }}</span>
                <span class="pt-theme-sub">{{ t.sub }}</span>
              </div>
              <i v-if="currentTheme === t.id" class="ri-check-line pt-theme-check" />
            </button>
          </div>

          <!-- Material 3 palettes -->
          <template v-if="currentTheme === 'material3'">
            <div class="pt-section-label" style="margin-top:14px">Палитра</div>
            <div class="pt-palette-list">
              <button
                v-for="p in M3_PALETTES"
                :key="p.name"
                class="pt-palette-row"
                :class="{ active: currentAccent === p.accent }"
                @click="setAccent(p.accent)"
              >
                <div class="pt-palette-chips">
                  <span v-for="(c, i) in p.colors" :key="i" class="pt-palette-chip" :style="`background:${c}`" />
                </div>
                <span class="pt-palette-name">{{ p.name }}</span>
                <i v-if="currentAccent === p.accent" class="ri-check-line pt-palette-check" />
              </button>
            </div>
          </template>

          <div class="pt-section-label" style="margin-top:14px">
            {{ currentTheme === 'material3' ? 'Seed color' : 'Accent' }}
          </div>
          <div class="pt-accent-grid">
            <button
              v-for="c in ACCENT_COLORS"
              :key="c.value"
              class="pt-accent-dot"
              :class="{ active: currentAccent === c.value }"
              :style="`background: ${c.value}`"
              :title="c.label"
              @click="setAccent(c.value)"
            />
            <label class="pt-accent-dot pt-accent-custom" title="Свой цвет">
              <i class="ri-add-line" />
              <input type="color" :value="currentAccent" style="display:none" @input="setAccent(($event.target as HTMLInputElement).value)">
            </label>
          </div>
          <div class="pt-accent-preview">
            <span class="pt-accent-swatch" :style="`background:${currentAccent}`" />
            <span class="pt-accent-hex">{{ currentAccent }}</span>
          </div>
        </template>

      </template>

      <!-- Block editor view -->
      <template v-else-if="activeBlock">
        <div class="pt-editor-header">
          <button class="pt-back-btn" @click="selectedBlockId = null">
            <i class="ri-arrow-left-line" />
          </button>
          <span class="pt-editor-title">{{ blockIcon(activeBlock.block_type) }} {{ blockLabel(activeBlock.block_type) }}</span>
        </div>

        <div class="pt-editor-body">
          <DashboardBlockForm :type="activeBlock.block_type" :config="activeBlockConfig" />
        </div>

        <div class="pt-editor-footer">
          <button class="pt-ep-cancel" @click="selectedBlockId = null">Отмена</button>
          <button class="pt-ep-save" @click="saveBlock">Сохранить</button>
        </div>
      </template>

    </div>

    <!-- ── Canvas ── -->
    <CropAvatarModal
      :file="avatarCropFile"
      :saving="avatarUploading"
      @save="onAvatarCropSave"
      @cancel="avatarCropFile = null"
    />

    <div class="pt-canvas" :style="canvasBgStyle" @click.self="deselectAll">
      <div class="pt-profile-card" :data-theme="currentTheme" :style="canvasThemeStyle">

        <!-- Header -->
        <div class="pt-ph" :class="{ editing: editingHeader }">
          <div class="pt-ph-glow" />

          <template v-if="editingHeader">
            <div class="pt-ph-edit-wrap">
            <!-- Avatar with upload in edit mode -->
            <div class="pt-ph-avatar-wrap-center">
              <div class="pt-ph-avatar pt-ph-avatar-center">
                <img v-if="avatarDisplaySrc" :src="avatarDisplaySrc" class="pt-ph-avatar-img" alt="avatar">
                <span v-else>{{ initial }}</span>
              </div>
              <label class="pt-ph-avatar-cam" title="Изменить фото">
                <span v-if="avatarUploading" class="pt-avt-spin" />
                <i v-else class="ri-camera-line" />
                <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" style="display:none" @change="onAvatarFileChange">
              </label>
            </div>
            <div class="pt-inline-fields">
              <div class="pt-if-group">
                <label class="pt-if-label">Имя / Никнейм</label>
                <input ref="nameInput" v-model="editName" class="pt-inline-input pt-inline-name" placeholder="Иван Иванов" @keydown.enter="saveHeader" @keydown.esc="cancelHeader">
              </div>
              <div class="pt-if-group">
                <label class="pt-if-label">Адрес страницы</label>
                <div class="pt-slug-row">
                  <span class="pt-slug-prefix">stellalink.app/</span>
                  <input v-model="editSlug" class="pt-inline-input pt-inline-slug-bare" placeholder="username" @keydown.enter="saveHeader" @keydown.esc="cancelHeader">
                </div>
              </div>
              <div class="pt-if-group">
                <label class="pt-if-label">Биография</label>
                <textarea v-model="editBio" class="pt-inline-input" placeholder="Расскажи о себе..." rows="2" />
              </div>
              <div class="pt-if-group">
                <label class="pt-if-label">Теги <span class="pt-if-hint">через запятую</span></label>
                <input v-model="editTagsRaw" class="pt-inline-input" placeholder="developer, gaming, music">
              </div>
              <div class="pt-inline-actions">
                <button class="pt-cancel-btn" @click.stop="cancelHeader">Отмена</button>
                <button class="pt-save-btn" @click.stop="saveHeader">Сохранить</button>
              </div>
            </div>
            </div>
          </template>

          <template v-else>
            <div class="pt-ph-center">
              <!-- Avatar with camera badge (always visible, not dependent on editingHeader) -->
              <div class="pt-ph-avatar-wrap-center">
                <div class="pt-ph-avatar pt-ph-avatar-center">
                  <img v-if="avatarDisplaySrc" :src="avatarDisplaySrc" class="pt-ph-avatar-img" alt="avatar">
                  <span v-else>{{ initial }}</span>
                </div>
                <label class="pt-ph-avatar-cam" title="Изменить фото" @click.stop>
                  <span v-if="avatarUploading" class="pt-avt-spin" />
                  <i v-else class="ri-camera-line" />
                  <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" style="display:none" @change="onAvatarFileChange">
                </label>
              </div>
              <div class="pt-ph-name" @click="editingHeader = true">{{ profile.profile!.display_name || '—' }}</div>
              <div class="pt-ph-slug" @click="editingHeader = true">stellalink.app/{{ profile.profile!.slug }}</div>
              <div v-if="profile.profile!.bio" class="pt-ph-bio" @click="editingHeader = true">{{ profile.profile!.bio }}</div>
              <div v-if="profile.profile!.tags.length" class="pt-ph-tags" @click="editingHeader = true">
                <span v-for="tag in profile.profile!.tags" :key="tag" class="pt-tag">{{ tag }}</span>
              </div>
              <div class="pt-edit-chip" @click="editingHeader = true"><i class="ri-edit-line" /> Редактировать профиль</div>
            </div>
          </template>
        </div>

        <!-- Blocks -->
        <VueDraggable
          v-model="localBlocks"
          class="pt-blocks"
          :animation="200"
          :group="{ name: 'blocks', pull: false, put: true }"
          handle=".pt-block-drag"
          ghost-class="pt-ghost-block"
          @add="onDropFromSidebar"
          @end="saveOrder"
        >
          <div
            v-for="block in localBlocks"
            :key="block.id"
            class="pt-block-preview"
            :class="{ selected: selectedBlockId === block.id, hidden: !block.is_visible }"
          >
            <i class="ri-drag-move-2-line pt-block-drag" />
            <div class="pt-block-inner" @click="selectBlock(block.id)">

              <!-- Links -->
              <template v-if="block.block_type === 'links'">
                <div v-for="group in (blockCfg(block).groups as Group[])" :key="group.title" class="pt-links-group">
                  <div v-if="group.title" class="pt-group-label">{{ group.title }}</div>
                  <div v-for="link in group.links" :key="link.url" class="pt-link-row">
                    <i v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pt-link-icon" />
                    <i v-else class="ri-link pt-link-icon" />
                    {{ link.label || link.url || '(пусто)' }}
                  </div>
                  <div v-if="!group.links.length" class="pt-block-empty">Нет ссылок</div>
                </div>
              </template>

              <!-- Text -->
              <template v-else-if="block.block_type === 'text'">
                <div class="pt-text-content">{{ (blockCfg(block).content as string) || '(пусто)' }}</div>
              </template>

              <!-- Steam -->
              <template v-else-if="block.block_type === 'widget_steam'">
                <div class="pt-w-header">
                  <div class="pt-w-hl">
                    <span class="pt-w-ico">🎮</span>
                    <div>
                      <div class="pt-w-name">Steam</div>
                      <div class="pt-w-id">{{ (blockCfg(block).steam_id as string) || 'не настроен' }}</div>
                    </div>
                  </div>
                  <span class="pt-badge-green">● Online</span>
                </div>
                <template v-if="blockCfg(block).show_recent_games && blockCfg(block).steam_id">
                  <div class="pt-w-divider" />
                  <div v-for="g in mock.steamGames(blockCfg(block).steam_id as string)" :key="g.name" class="pt-steam-row">
                    <span>{{ g.name }}</span><span class="pt-steam-h">{{ g.hours.toLocaleString('ru') }} ч</span>
                  </div>
                </template>
              </template>

              <!-- Last.fm -->
              <template v-else-if="block.block_type === 'widget_lastfm'">
                <div class="pt-w-header">
                  <div class="pt-w-hl">
                    <span class="pt-w-ico">🎵</span>
                    <div>
                      <div class="pt-w-name">Last.fm</div>
                      <div class="pt-w-id">@{{ (blockCfg(block).username as string) || 'не настроен' }}</div>
                    </div>
                  </div>
                  <div v-if="blockCfg(block).show_now_playing && blockCfg(block).username" class="pt-np-bars">
                    <span v-for="i in 4" :key="i" class="pt-np-bar" :style="`animation-delay:${(i-1)*0.18}s`" />
                  </div>
                </div>
                <template v-if="blockCfg(block).show_now_playing && blockCfg(block).username">
                  <div class="pt-w-divider" />
                  <div class="pt-np-row">
                    <span class="pt-np-label">Сейчас:</span>
                    <span class="pt-np-track">{{ mock.lastfmTrack(blockCfg(block).username as string).track }}</span>
                    <span class="pt-np-artist">— {{ mock.lastfmTrack(blockCfg(block).username as string).artist }}</span>
                  </div>
                </template>
              </template>

              <!-- GitHub -->
              <template v-else-if="block.block_type === 'widget_github'">
                <div class="pt-w-header">
                  <div class="pt-w-hl">
                    <span class="pt-w-ico">🐙</span>
                    <div>
                      <div class="pt-w-name">GitHub</div>
                      <div class="pt-w-id">@{{ (blockCfg(block).username as string) || 'не настроен' }}</div>
                    </div>
                  </div>
                  <span v-if="blockCfg(block).username" class="pt-gh-badge">
                    {{ mock.ghStats(blockCfg(block).username as string).repos }} репо
                  </span>
                </div>
                <template v-if="blockCfg(block).username">
                  <div class="pt-w-divider" />
                  <div class="pt-gh-mini">
                    <div
                      v-for="(level, i) in mock.ghHeatmap(blockCfg(block).username as string).slice(0, 182)"
                      :key="i"
                      class="pt-gh-cell"
                      :class="`pt-gh-l${level}`"
                    />
                  </div>
                  <div class="pt-gh-count">{{ mock.ghStats(blockCfg(block).username as string).contributions.toLocaleString('ru') }} contributions</div>
                </template>
              </template>

              <!-- PC Config -->
              <template v-else-if="block.block_type === 'pc_config'">
                <div class="pt-w-header" style="margin-bottom:0">
                  <div class="pt-w-hl">
                    <span class="pt-w-ico">💻</span>
                    <div class="pt-w-name">{{ (blockCfg(block).title as string) || 'PC Config' }}</div>
                  </div>
                </div>
                <template v-if="(blockCfg(block).components as Component[]).length">
                  <div class="pt-w-divider" />
                  <div v-for="c in (blockCfg(block).components as Component[]).slice(0, 4)" :key="c.category" class="pt-pc-row">
                    <span class="pt-pc-cat">{{ c.category }}</span>
                    <span class="pt-pc-val">{{ c.name }}</span>
                  </div>
                </template>
              </template>

              <!-- Faceit -->
              <template v-else-if="block.block_type === 'widget_faceit'">
                <div class="pt-w-header">
                  <div class="pt-w-hl">
                    <span class="pt-w-ico">⚡</span>
                    <div>
                      <div class="pt-w-name">FACEIT · CS2</div>
                      <div class="pt-w-id">{{ (blockCfg(block).nickname as string) || 'не настроен' }}</div>
                    </div>
                  </div>
                  <div
                    v-if="blockCfg(block).nickname"
                    class="pt-faceit-lvl"
                    :style="`background:${mock.faceitLevelColor(mock.faceitData(blockCfg(block).nickname as string).level)}`"
                  >{{ mock.faceitData(blockCfg(block).nickname as string).level }}</div>
                </div>
                <template v-if="blockCfg(block).nickname">
                  <div class="pt-w-divider" />
                  <div class="pt-faceit-stats">
                    <div class="pt-fstat">
                      <span class="pt-fstat-v">{{ mock.faceitData(blockCfg(block).nickname as string).elo }}</span>
                      <span class="pt-fstat-l">ELO</span>
                    </div>
                    <div class="pt-fstat">
                      <span class="pt-fstat-v">{{ mock.faceitData(blockCfg(block).nickname as string).kd }}</span>
                      <span class="pt-fstat-l">K/D</span>
                    </div>
                    <div class="pt-fstat">
                      <span class="pt-fstat-v">{{ mock.faceitData(blockCfg(block).nickname as string).winRate }}%</span>
                      <span class="pt-fstat-l">Win</span>
                    </div>
                  </div>
                </template>
              </template>

            </div>
            <div class="pt-block-overlay" @click="selectBlock(block.id)">
              <i class="ri-edit-line" /> Редактировать
            </div>
            <div v-if="!block.is_visible" class="pt-hidden-badge">скрыт</div>
          </div>

          <template #footer>
            <div v-if="!localBlocks.length" class="pt-drop-zone">
              <div class="pt-dz-icons">
                <span v-for="bt in blockTypes.slice(0,5)" :key="bt.type" class="pt-dz-ico">{{ bt.icon }}</span>
              </div>
              <div class="pt-dz-title">Добавь первый блок</div>
              <div class="pt-dz-hint">Нажми «+» в боковой панели или перетащи блок сюда</div>
            </div>
          </template>
        </VueDraggable>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch, nextTick } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useProfileStore, type Block } from '~/stores/profile'
import { useAuthStore } from '~/stores/auth'

interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }

const profile = useProfileStore()
const auth = useAuthStore()
const config = useRuntimeConfig()
const mock = useProfileMockData()

// ── Avatar upload from profile canvas ────────────────────────────────────────
const avatarTimestamp = ref(Date.now())
const avatarCropFile = ref<File | null>(null)
const avatarUploading = ref(false)
const avatarDisplaySrc = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarTimestamp.value)
)

function onAvatarFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  ;(e.target as HTMLInputElement).value = ''
  avatarCropFile.value = file
}

async function onAvatarCropSave(blob: Blob) {
  avatarCropFile.value = null
  avatarUploading.value = true
  try {
    await auth.uploadAvatar(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    avatarTimestamp.value = Date.now()
  } finally {
    avatarUploading.value = false
  }
}

// ── Design / Themes ──────────────────────────────────────────────────────────
const sidebarTab = ref<'blocks' | 'design'>('blocks')

const THEMES = [
  {
    id: 'material3',
    label: 'Material 3',
    sub: 'Expressive',
    preview: 'background: linear-gradient(135deg,#13102a 0%,#1a1535 60%,#211e40 100%)',
    previewDot: '#D0BCFF',
  },
  {
    id: 'glass',
    label: 'Liquid Glass',
    sub: 'Apple-like',
    preview: 'background: linear-gradient(135deg,rgba(14,12,30,0.9) 0%,rgba(30,28,60,0.85) 100%); backdrop-filter: blur(8px)',
    previewDot: '#a8d8ff',
  },
  {
    id: 'fluent',
    label: 'Fluent',
    sub: 'Microsoft',
    preview: 'background: linear-gradient(135deg,#1c1c1c 0%,#242424 100%)',
    previewDot: '#60cdff',
  },
]

const ACCENT_COLORS = [
  { label: 'Violet',  value: '#D0BCFF' },
  { label: 'Blue',    value: '#3D8EFF' },
  { label: 'Teal',    value: '#14B8A6' },
  { label: 'Green',   value: '#22C55E' },
  { label: 'Amber',   value: '#F59E0B' },
  { label: 'Orange',  value: '#F97316' },
  { label: 'Pink',    value: '#EC4899' },
  { label: 'Rose',    value: '#F43F5E' },
]

const M3_PALETTES = [
  { name: 'Violet Dream',  accent: '#D0BCFF', colors: ['#D0BCFF', '#9A82DB', '#6750A4', '#381E72', '#1C1135'] },
  { name: 'Ocean Blue',    accent: '#3D8EFF', colors: ['#A0C4FF', '#3D8EFF', '#1565C0', '#0D3B72', '#091E3A'] },
  { name: 'Sakura',        accent: '#EC4899', colors: ['#FBB6CE', '#EC4899', '#BE185D', '#831843', '#3B0720'] },
  { name: 'Emerald',       accent: '#22C55E', colors: ['#86EFAC', '#22C55E', '#15803D', '#14532D', '#052E16'] },
  { name: 'Sunset',        accent: '#F97316', colors: ['#FED7AA', '#F97316', '#C2410C', '#7C2D12', '#3B1106'] },
  { name: 'Teal Surf',     accent: '#14B8A6', colors: ['#99F6E4', '#14B8A6', '#0D9488', '#134E4A', '#042F2E'] },
  { name: 'Golden',        accent: '#F59E0B', colors: ['#FDE68A', '#F59E0B', '#B45309', '#78350F', '#3D1C04'] },
  { name: 'Rose Quartz',   accent: '#F43F5E', colors: ['#FDA4AF', '#F43F5E', '#BE123C', '#881337', '#4C0519'] },
]

const currentAccent = computed(() => profile.profile?.accent_color || '#D0BCFF')
const currentTheme  = computed(() => profile.profile?.theme_preset || 'material3')

// ── Canvas theme CSS variables ────────────────────────────────────────────────
function hexToRgba(hex: string, op: number): string {
  const c = hex.replace('#', '')
  const r = parseInt(c.slice(0, 2), 16) || 61
  const g = parseInt(c.slice(2, 4), 16) || 142
  const b = parseInt(c.slice(4, 6), 16) || 255
  return `rgba(${r},${g},${b},${op})`
}

const canvasThemeStyle = computed((): Record<string, string> => {
  const preset  = currentTheme.value
  const accent  = currentAccent.value
  const a04 = hexToRgba(accent, 0.04)
  const a08 = hexToRgba(accent, 0.08)
  const a12 = hexToRgba(accent, 0.12)
  const a20 = hexToRgba(accent, 0.20)
  const a28 = hexToRgba(accent, 0.28)

  if (preset === 'glass') {
    return {
      '--th-card':    'rgba(255,255,255,0.04)',
      '--th-block':   'rgba(255,255,255,0.04)',
      '--th-hborder': 'rgba(255,255,255,0.08)',
      '--th-text':    '#f0eeff',
      '--th-sub':     'rgba(240,238,255,0.60)',
      '--th-dim':     'rgba(240,238,255,0.32)',
      '--th-accent':  accent,
      '--th-a04': a04, '--th-a08': a08, '--th-a12': a12, '--th-a20': a20, '--th-a28': a28,
      '--th-radius':  '24px',
      '--th-radius-sm': '16px',
      '--th-blur':    'blur(40px) saturate(180%)',
      '--th-shadow':  '0 32px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)',
      '--th-glow':    hexToRgba(accent, 0.18),
      '--th-block-border': 'rgba(255,255,255,0.10)',
      '--th-block-blur': 'blur(20px) saturate(160%)',
      '--th-block-shadow': '0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.06)',
    }
  }
  if (preset === 'fluent') {
    return {
      '--th-card':    'rgba(28,28,28,0.88)',
      '--th-block':   'rgba(255,255,255,0.04)',
      '--th-hborder': 'rgba(255,255,255,0.07)',
      '--th-text':    '#ffffff',
      '--th-sub':     'rgba(255,255,255,0.65)',
      '--th-dim':     'rgba(255,255,255,0.38)',
      '--th-accent':  accent,
      '--th-a04': a04, '--th-a08': a08, '--th-a12': a12, '--th-a20': a20, '--th-a28': a28,
      '--th-radius':  '8px',
      '--th-radius-sm': '6px',
      '--th-blur':    'blur(32px) saturate(140%)',
      '--th-shadow':  '0 16px 48px rgba(0,0,0,0.45)',
      '--th-glow':    hexToRgba(accent, 0.12),
      '--th-block-border': 'rgba(255,255,255,0.07)',
      '--th-block-blur': 'none',
      '--th-block-shadow': 'none',
    }
  }
  // material3 (default)
  return {
    '--th-card':    hexToRgba(accent, 0.03),
    '--th-block':   hexToRgba(accent, 0.05),
    '--th-hborder': a12,
    '--th-text':    '#e9e0f8',
    '--th-sub':     '#cac4d0',
    '--th-dim':     '#938f99',
    '--th-accent':  accent,
    '--th-a04': a04, '--th-a08': a08, '--th-a12': a12, '--th-a20': a20, '--th-a28': a28,
    '--th-radius':  '28px',
    '--th-radius-sm': '16px',
    '--th-blur':    '',
    '--th-shadow':  `0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px ${a08}`,
    '--th-glow':    hexToRgba(accent, 0.22),
    '--th-block-border': a12,
    '--th-block-blur': 'none',
    '--th-block-shadow': 'none',
  }
})

const canvasBgStyle = computed((): Record<string, string> => {
  const preset = currentTheme.value
  const accent = currentAccent.value
  if (preset === 'glass') {
    return { background: 'radial-gradient(ellipse 60% 40% at 30% 20%, rgba(120,80,255,0.12), transparent), radial-gradient(ellipse 50% 35% at 70% 60%, rgba(60,160,255,0.10), transparent), #050510' }
  }
  if (preset === 'fluent') {
    return { background: '#1a1a1a' }
  }
  return { background: `radial-gradient(ellipse 60% 30% at 50% 0%, ${hexToRgba(accent, 0.07)}, transparent), #0c0a1a` }
})

async function setTheme(id: string) {
  await profile.update({ theme_preset: id })
}

async function setAccent(color: string) {
  await profile.update({ accent_color: color })
}

const blockTypes = ref([
  { type: 'links',          icon: '🔗', label: 'Ссылки' },
  { type: 'text',           icon: '📝', label: 'Текст' },
  { type: 'widget_steam',   icon: '🎮', label: 'Steam' },
  { type: 'widget_lastfm',  icon: '🎵', label: 'Last.fm' },
  { type: 'widget_github',  icon: '🐙', label: 'GitHub' },
  { type: 'widget_faceit',  icon: '⚡', label: 'FACEIT' },
  { type: 'pc_config',      icon: '💻', label: 'ПК конфиг' },
])
const defaultConfigs: Record<string, Record<string, unknown>> = {
  links:           { groups: [{ title: '', links: [] }] },
  text:            { content: '', format: 'markdown' },
  widget_steam:    { steam_id: '', show_recent_games: true },
  widget_lastfm:   { username: '', show_now_playing: true },
  widget_github:   { username: '', show_contributions: true, show_pinned_repos: true },
  widget_faceit:   { nickname: '', game: 'cs2' },
  pc_config:       { title: 'My Rig', components: [] },
}

function blockLabel(type: string) { return blockTypes.value.find(b => b.type === type)?.label ?? type }
function blockIcon(type: string)  { return blockTypes.value.find(b => b.type === type)?.icon  ?? '📦' }

// ── Local blocks ──────────────────────────────────────────────────────────────
const localBlocks = ref<Block[]>([])
watch(() => profile.profile?.blocks, (b: Block[] | undefined) => { if (b) localBlocks.value = [...b] }, { immediate: true })

async function saveOrder() {
  const ids = localBlocks.value.map(b => b.id)
  await profile.reorder(ids)
}

async function onDropFromSidebar(evt: { item: HTMLElement }) {
  const type = evt.item.dataset.type
  if (!type) return
  // Restore from store first (VueDraggable inserted a raw blockType object into localBlocks)
  if (profile.profile) localBlocks.value = [...profile.profile.blocks]
  const block = await profile.createBlock(type, defaultConfigs[type] ?? {})
  if (profile.profile) localBlocks.value = [...profile.profile.blocks]
  selectedBlockId.value = block.id
}

async function addBlock(type: string) {
  const block = await profile.createBlock(type, defaultConfigs[type] ?? {})
  if (profile.profile) localBlocks.value = [...profile.profile.blocks]
  selectedBlockId.value = block.id
}

// ── Header ────────────────────────────────────────────────────────────────────
const editingHeader = ref(false)
const editName = ref(''), editSlug = ref(''), editBio = ref(''), editTagsRaw = ref('')
const nameInput = ref<HTMLInputElement | null>(null)
const initial = computed(() => profile.profile?.display_name?.[0]?.toUpperCase() ?? '?')

watch(editingHeader, val => {
  if (val && profile.profile) {
    editName.value    = profile.profile.display_name
    editSlug.value    = profile.profile.slug
    editBio.value     = profile.profile.bio ?? ''
    editTagsRaw.value = profile.profile.tags.join(', ')
    nextTick(() => nameInput.value?.focus())
  }
})

async function saveHeader() {
  await profile.update({
    slug: editSlug.value || undefined,
    display_name: editName.value || undefined,
    bio: editBio.value,
    tags: editTagsRaw.value.split(',').map(t => t.trim()).filter(Boolean),
  })
  editingHeader.value = false
}
function cancelHeader() { editingHeader.value = false }
async function toggleStatus() {
  await profile.update({ status: profile.isPublished ? 'draft' : 'published' })
}

// ── Block selection ───────────────────────────────────────────────────────────
const selectedBlockId   = ref<string | null>(null)
const activeBlock       = computed(() => localBlocks.value.find(b => b.id === selectedBlockId.value) ?? null)
const activeBlockConfig = reactive<Record<string, unknown>>({})

watch(activeBlock, block => {
  Object.keys(activeBlockConfig).forEach(k => delete activeBlockConfig[k])
  if (block) Object.assign(activeBlockConfig, JSON.parse(JSON.stringify(block.config)))
})

function blockCfg(block: Block): Record<string, unknown> {
  return selectedBlockId.value === block.id ? activeBlockConfig : block.config
}

function selectBlock(id: string) {
  selectedBlockId.value = id
  editingHeader.value = false
}
function deselectAll() {
  selectedBlockId.value = null
  editingHeader.value = false
}

async function toggleVisible(block: Block) {
  await profile.updateBlock(block.id, { is_visible: !block.is_visible })
}
async function deleteBlock(id: string) {
  if (!confirm('Удалить блок?')) return
  if (selectedBlockId.value === id) selectedBlockId.value = null
  await profile.deleteBlock(id)
}
async function saveBlock() {
  if (!selectedBlockId.value) return
  await profile.updateBlock(selectedBlockId.value, { config: JSON.parse(JSON.stringify(activeBlockConfig)) })
  selectedBlockId.value = null
}
</script>

<style scoped>
.pt-wrap { display: flex; height: calc(100vh - 58px); overflow: hidden; }

/* ── Sidebar ── */
.pt-sidebar {
  width: 220px; flex-shrink: 0;
  border-right: 1px solid rgba(255,255,255,0.08);
  display: flex; flex-direction: column;
  overflow: hidden;
  background: rgba(15,15,18,0.6);
}

.pt-status-row { display: flex; align-items: center; gap: 8px; padding: 14px 12px 8px; }
.pt-toggle {
  flex: 1; display: flex; align-items: center; gap: 7px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 8px; padding: 7px 10px;
  font-size: 12px; font-weight: 600; color: #71717a;
  cursor: pointer; font-family: 'Onest', sans-serif; transition: all 0.2s;
}
.pt-toggle.active { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.28); color: #a1a1aa; }
.pt-toggle-dot { width: 7px; height: 7px; border-radius: 50%; background: #3f3f46; flex-shrink: 0; transition: background 0.2s; }
.pt-toggle.active .pt-toggle-dot { background: #fafafa; }
.pt-view-btn {
  width: 32px; height: 32px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18);
  border-radius: 8px; color: #a1a1aa; text-decoration: none; font-size: 16px;
}

/* ── Sidebar tabs ── */
.pt-sidebar-tabs {
  display: flex; gap: 4px; padding: 6px 8px 0;
}
.pt-stab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 5px;
  padding: 7px 4px; border-radius: 8px; border: 1px solid transparent;
  font-size: 11px; font-weight: 600; color: #52525b;
  background: none; cursor: pointer; font-family: 'Onest', sans-serif;
  transition: all 0.15s;
}
.pt-stab:hover { color: #a1a1aa; background: rgba(255,255,255,0.03); }
.pt-stab.active {
  color: #a1a1aa; background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.18);
}

.pt-section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.2px; color: #52525b; padding: 8px 12px 4px;
}

/* ── Design tab ── */
.pt-theme-list {
  display: flex; flex-direction: column; gap: 4px; padding: 4px 8px;
}
.pt-theme-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 10px;
  border: 1px solid transparent; background: none;
  cursor: pointer; font-family: 'Onest', sans-serif; transition: all 0.15s;
  text-align: left;
}
.pt-theme-row:hover { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.06); }
.pt-theme-row.active { background: rgba(208,188,255,0.07); border-color: rgba(208,188,255,0.20); }
.pt-theme-swatch {
  width: 40px; height: 32px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,0.08);
}
.pt-theme-dot { width: 10px; height: 10px; border-radius: 50%; }
.pt-theme-info { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.pt-theme-name { font-size: 12px; font-weight: 700; color: #d4d4d8; }
.pt-theme-sub { font-size: 10px; color: #5a5a78; }
.pt-theme-row.active .pt-theme-name { color: #D0BCFF; }
.pt-theme-row.active .pt-theme-sub { color: #7c6fa0; }
.pt-theme-check { font-size: 14px; color: #D0BCFF; flex-shrink: 0; }

.pt-accent-grid {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 10px;
}
.pt-accent-dot {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid transparent; cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: rgba(255,255,255,0.7);
}
.pt-accent-dot:hover { transform: scale(1.15); }
.pt-accent-dot.active { border-color: #fff; box-shadow: 0 0 0 3px rgba(255,255,255,0.2); transform: scale(1.1); }
.pt-accent-custom {
  background: rgba(255,255,255,0.06); border: 1.5px dashed rgba(255,255,255,0.2) !important;
  cursor: pointer;
}
.pt-accent-preview {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 10px 12px;
}
.pt-accent-swatch { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.pt-accent-hex { font-size: 11px; color: #71717a; font-family: monospace; }

/* ── Theme swatch previews ── */
.pt-swatch-glass {
  background: linear-gradient(135deg, #0e0c1e 0%, #1a1840 100%);
  position: relative; overflow: hidden;
}
.pt-swatch-glass-orbs {
  position: absolute; inset: 0; pointer-events: none;
}
.pt-swatch-orb {
  position: absolute; border-radius: 50%; filter: blur(6px);
}
.pt-swatch-orb-1 {
  width: 18px; height: 18px; top: 3px; left: 4px;
  background: rgba(120,80,255,0.5);
}
.pt-swatch-orb-2 {
  width: 14px; height: 14px; bottom: 4px; right: 5px;
  background: rgba(60,160,255,0.45);
}
.pt-swatch-glass-pane {
  position: absolute; bottom: 5px; left: 50%; transform: translateX(-50%);
  width: 24px; height: 10px; border-radius: 4px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  backdrop-filter: blur(4px);
}
.pt-swatch-material3 {
  background: linear-gradient(135deg, #13102a 0%, #1a1535 60%, #211e40 100%);
  position: relative; overflow: hidden;
}
.pt-swatch-m3-shapes {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 3px;
}
.pt-swatch-m3-s1 {
  width: 14px; height: 14px; border-radius: 8px 3px 8px 3px;
  opacity: 0.5;
}
.pt-swatch-m3-s2 {
  width: 10px; height: 10px; border-radius: 3px 6px 3px 6px;
  opacity: 0.35;
}
.pt-swatch-fluent {
  background: linear-gradient(135deg, #1c1c1c 0%, #242424 100%);
}

/* ── Palette list ── */
.pt-palette-list {
  display: flex; flex-direction: column; gap: 3px; padding: 4px 8px;
  max-height: 180px; overflow-y: auto;
}
.pt-palette-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 8px;
  border: 1px solid transparent; background: none;
  cursor: pointer; font-family: 'Onest', sans-serif; transition: all 0.15s;
  text-align: left;
}
.pt-palette-row:hover { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.06); }
.pt-palette-row.active { background: rgba(208,188,255,0.07); border-color: rgba(208,188,255,0.18); }
.pt-palette-chips {
  display: flex; gap: 2px; flex-shrink: 0;
}
.pt-palette-chip {
  width: 12px; height: 18px; border-radius: 3px;
  transition: transform 0.15s;
}
.pt-palette-chip:first-child { border-radius: 5px 3px 3px 5px; }
.pt-palette-chip:last-child { border-radius: 3px 5px 5px 3px; }
.pt-palette-row:hover .pt-palette-chip { transform: scaleY(1.1); }
.pt-palette-name { flex: 1; font-size: 11px; font-weight: 600; color: #a1a1aa; }
.pt-palette-row.active .pt-palette-name { color: #D0BCFF; }
.pt-palette-check { font-size: 12px; color: #D0BCFF; flex-shrink: 0; }

.pt-block-list { display: flex; flex-direction: column; gap: 2px; padding: 0 8px; overflow-y: auto; max-height: 220px; }
.pt-block-item {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 6px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; transition: all 0.15s;
}
.pt-block-item:hover { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.10); }
.pt-drag-handle { color: #3f3f46; font-size: 15px; cursor: grab; flex-shrink: 0; }
.pt-drag-handle:active { cursor: grabbing; }
.pt-block-icon { font-size: 14px; }
.pt-block-label { font-size: 13px; flex: 1; color: #a1a1aa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pt-block-actions { display: flex; align-items: center; gap: 3px; opacity: 0; transition: opacity 0.15s; }
.pt-block-item:hover .pt-block-actions { opacity: 1; }

.pt-vis-btn {
  width: 22px; height: 13px; border-radius: 7px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14);
  position: relative; cursor: pointer; transition: background 0.2s; flex-shrink: 0;
}
.pt-vis-btn::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 9px; height: 9px; border-radius: 50%; background: #3f3f46; transition: transform 0.2s, background 0.2s;
}
.pt-vis-btn.active { background: rgba(255,255,255,0.25); }
.pt-vis-btn.active::after { transform: translateX(9px); background: #fafafa; }

.pt-del-btn {
  background: none; border: none; color: #3f3f46; cursor: pointer;
  font-size: 13px; display: flex; align-items: center; padding: 2px; transition: color 0.2s;
}
.pt-del-btn:hover { color: #ff7070; }
.pt-empty { font-size: 11px; color: #3f3f46; padding: 8px 12px; }

.pt-add-list { display: flex; flex-direction: column; gap: 2px; padding: 4px 8px 12px; overflow-y: auto; flex: 1; }
.pt-add-item {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px; border-radius: 8px;
  border: 1px solid transparent;
  font-size: 13px; color: #a1a1aa;
  cursor: grab; font-family: 'Onest', sans-serif; transition: all 0.15s; user-select: none;
}
.pt-add-ico { font-size: 17px; flex-shrink: 0; }
.pt-add-label { flex: 1; font-weight: 500; }
.pt-add-plus { font-size: 16px; color: #3f3f46; opacity: 0; transition: opacity 0.15s; }
.pt-add-item:hover {
  background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.16);
  color: #ececef;
}
.pt-add-item:hover .pt-add-plus { opacity: 1; color: #a1a1aa; }
.pt-add-item:active { cursor: grabbing; }

/* Block editor mode */
.pt-editor-header {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 12px 10px; border-bottom: 1px solid rgba(255,255,255,0.08); flex-shrink: 0;
}
.pt-back-btn {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 7px; width: 30px; height: 30px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #71717a; cursor: pointer; font-size: 16px; transition: all 0.2s;
}
.pt-back-btn:hover { color: #ececef; background: rgba(255,255,255,0.08); }
.pt-editor-title { font-size: 13px; font-weight: 700; }

.pt-editor-body { flex: 1; overflow-y: auto; padding: 14px 12px; }

.pt-editor-footer {
  display: flex; gap: 8px; padding: 12px;
  border-top: 1px solid rgba(255,255,255,0.08); flex-shrink: 0;
}
.pt-ep-cancel {
  flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 8px; padding: 9px; color: #71717a;
  font-size: 13px; font-family: 'Onest', sans-serif; cursor: pointer;
}
.pt-ep-save {
  flex: 2; background: #fafafa; border: none;
  border-radius: 8px; padding: 9px; color: #09090b;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}

/* ── Canvas ── */
.pt-canvas {
  flex: 1; overflow-y: auto; padding: 24px;
  display: flex; justify-content: center; align-items: flex-start;
  background: radial-gradient(ellipse 60% 30% at 50% 0%, rgba(255,255,255,0.04), transparent);
}
.pt-profile-card {
  width: 100%; max-width: 420px; height: fit-content;
  background: var(--th-card, #0f0f12);
  border: 1px solid var(--th-a12, rgba(255,255,255,0.12));
  border-radius: var(--th-radius, 20px); overflow: hidden;
  box-shadow: var(--th-shadow, 0 24px 64px rgba(0,0,0,0.5));
  backdrop-filter: var(--th-blur, none);
  -webkit-backdrop-filter: var(--th-blur, none);
  transition: border-radius 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
  position: relative;
}

/* Header */
.pt-ph {
  position: relative; overflow: hidden;
  border-bottom: 1px solid var(--th-hborder, rgba(255,255,255,0.08));
}
.pt-ph-glow {
  position: absolute; top: -40px; left: 50%; transform: translateX(-50%);
  width: 200px; height: 120px; pointer-events: none;
  background: radial-gradient(ellipse, var(--th-glow, rgba(255,255,255,0.18)), transparent 70%);
}
.pt-ph-center {
  display: flex; flex-direction: column; align-items: center;
  padding: 28px 20px 20px; text-align: center; cursor: pointer;
  position: relative;
}
.pt-ph-center:hover .pt-edit-chip { opacity: 1; }

.pt-ph-avatar {
  width: 68px; height: 68px; border-radius: 50%;
  background: var(--th-accent, #d4d4d8);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: #fff;
  overflow: hidden; flex-shrink: 0;
  box-shadow: 0 0 0 3px var(--th-a20, rgba(255,255,255,0.22)), 0 6px 20px var(--th-a20, rgba(255,255,255,0.20));
}
.pt-ph-avatar-center { margin-bottom: 14px; }
.pt-ph-avatar-img { width: 100%; height: 100%; object-fit: cover; }

.pt-ph-name { font-size: 18px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 2px; color: var(--th-text, #ececef); }
.pt-ph-slug { font-size: 12px; color: var(--th-dim, #3f3f46); margin-bottom: 6px; }
.pt-ph-bio  { font-size: 13px; color: var(--th-sub, #a1a1aa); margin-bottom: 8px; max-width: 280px; line-height: 1.4; }
.pt-ph-tags { display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; }
.pt-tag {
  background: var(--th-a08, rgba(255,255,255,0.10)); color: var(--th-accent, #a1a1aa);
  border: 1px solid var(--th-a12, rgba(255,255,255,0.16)); border-radius: 100px;
  padding: 2px 10px; font-size: 11px; font-weight: 500;
}
.pt-edit-chip {
  margin-top: 12px; display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; color: #71717a;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12);
  border-radius: 100px; padding: 4px 12px;
  opacity: 0; transition: opacity 0.2s;
}

/* Edit mode wrapper */
.pt-ph-edit-wrap {
  display: flex; flex-direction: column; align-items: center;
  padding: 20px 0 0;
}

/* Inline edit form */
.pt-inline-fields {
  display: flex; flex-direction: column; gap: 8px; padding: 16px 16px 14px;
}
.pt-slug-row {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.25);
  border-radius: 7px; overflow: hidden;
}
.pt-slug-prefix { padding: 7px 0 7px 10px; font-size: 12px; color: #3f3f46; white-space: nowrap; }
.pt-slug-prefix + .pt-inline-slug-bare { border: none; background: none; padding-left: 2px; }
.pt-inline-slug-bare {
  flex: 1; background: none; border: none; outline: none;
  padding: 7px 10px; color: #a1a1aa; font-size: 12px; font-family: 'Onest', sans-serif;
}
.pt-inline-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.22);
  border-radius: 7px; padding: 7px 10px; color: #ececef;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; width: 100%; resize: none;
  transition: border-color 0.2s;
}
.pt-inline-input:focus { border-color: rgba(255,255,255,0.45); }
.pt-inline-name { font-size: 15px; font-weight: 700; }
.pt-inline-actions { display: flex; gap: 8px; justify-content: flex-end; }
.pt-save-btn {
  background: #fafafa; border: none;
  border-radius: 7px; padding: 7px 18px; color: #09090b;
  font-size: 12px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}
.pt-cancel-btn {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.14);
  border-radius: 7px; padding: 7px 14px; color: #71717a;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
}

/* Canvas blocks */
.pt-blocks { padding: 10px; display: flex; flex-direction: column; gap: 7px; min-height: 60px; }
.pt-drop-zone {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 36px 20px;
  border: 1.5px dashed rgba(255,255,255,0.12); border-radius: 14px;
  text-align: center;
}
.pt-dz-icons { display: flex; gap: 8px; font-size: 22px; opacity: 0.5; }
.pt-dz-ico { filter: grayscale(0.3); }
.pt-dz-title { font-size: 14px; font-weight: 700; color: #52525b; }
.pt-dz-hint { font-size: 12px; color: #3f3f46; max-width: 220px; line-height: 1.5; }

.pt-block-preview {
  position: relative; border-radius: var(--th-radius-sm, calc(var(--th-radius, 20px) * 0.4)); overflow: hidden;
  border: 1px solid var(--th-block-border, var(--th-a08, rgba(255,255,255,0.08)));
  background: var(--th-block, rgba(255,255,255,0.025));
  backdrop-filter: var(--th-block-blur, none);
  -webkit-backdrop-filter: var(--th-block-blur, none);
  box-shadow: var(--th-block-shadow, none);
  display: flex; align-items: stretch; transition: border-color 0.2s, border-radius 0.3s, background 0.3s;
}
.pt-block-preview:hover { border-color: var(--th-a28, rgba(255,255,255,0.28)); }
.pt-block-preview.selected { border-color: var(--th-accent, #d4d4d8); box-shadow: 0 0 0 2px var(--th-a12, rgba(255,255,255,0.10)); }
.pt-block-preview.hidden { opacity: 0.4; }

.pt-block-drag {
  flex-shrink: 0; width: 22px; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  color: #3f3f46; cursor: grab;
  background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.06);
  transition: color 0.2s, background 0.2s;
}
.pt-block-drag:hover { color: #71717a; background: rgba(255,255,255,0.05); }
.pt-block-drag:active { cursor: grabbing; }

.pt-block-inner { flex: 1; padding: 11px 13px; cursor: pointer; }
.pt-block-overlay {
  position: absolute; inset: 0; left: 22px;
  background: var(--th-a08, rgba(255,255,255,0.07));
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: var(--th-accent, #a1a1aa); gap: 6px;
  opacity: 0; transition: opacity 0.18s; cursor: pointer;
}
.pt-block-preview:hover .pt-block-overlay { opacity: 1; }
.pt-block-preview.selected .pt-block-overlay { opacity: 0; }
.pt-hidden-badge {
  position: absolute; top: 5px; right: 6px;
  background: rgba(255,255,255,0.07); border-radius: 4px;
  padding: 1px 6px; font-size: 10px; color: #71717a; pointer-events: none;
}

/* ── Block inner: links ── */
.pt-links-group { margin-bottom: 6px; }
.pt-links-group:last-child { margin-bottom: 0; }
.pt-group-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #71717a; margin-bottom: 4px; }
.pt-link-row { font-size: 13px; color: #a1a1aa; padding: 3px 0; display: flex; align-items: center; gap: 6px; }
.pt-link-icon { font-size: 14px; color: #a1a1aa; flex-shrink: 0; }
.pt-block-empty { font-size: 12px; color: #3f3f46; font-style: italic; }
.pt-text-content { font-size: 13px; color: #a1a1aa; white-space: pre-wrap; }

/* ── Block inner: widget shared ── */
.pt-w-header { display: flex; align-items: center; justify-content: space-between; }
.pt-w-hl { display: flex; align-items: center; gap: 8px; }
.pt-w-ico { font-size: 20px; }
.pt-w-name { font-size: 13px; font-weight: 700; line-height: 1.2; }
.pt-w-id { font-size: 11px; color: #71717a; }
.pt-w-divider { height: 1px; background: rgba(255,255,255,0.07); margin: 8px 0; }
.pt-badge-green {
  font-size: 10px; font-weight: 600; color: #4ade80;
  background: rgba(74,222,128,0.10); border: 1px solid rgba(74,222,128,0.18);
  border-radius: 100px; padding: 2px 7px;
}

/* ── Block inner: Steam ── */
.pt-steam-row {
  display: flex; justify-content: space-between; font-size: 12px;
  padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05); color: #a1a1aa;
}
.pt-steam-row:last-child { border-bottom: none; }
.pt-steam-h { color: #71717a; }

/* ── Block inner: Last.fm ── */
.pt-np-bars { display: flex; align-items: flex-end; gap: 2px; height: 14px; }
.pt-np-bar {
  width: 3px; height: 14px; background: #e5343a; border-radius: 1px;
  animation: npBounce 1.1s ease-in-out infinite; transform-origin: bottom;
}
@keyframes npBounce { 0%, 100% { transform: scaleY(0.25); } 50% { transform: scaleY(1); } }
.pt-np-row { display: flex; align-items: center; gap: 5px; font-size: 12px; flex-wrap: wrap; }
.pt-np-label { color: #e5343a; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; }
.pt-np-track { font-weight: 600; color: #ececef; }
.pt-np-artist { color: #71717a; }

/* ── Block inner: GitHub ── */
.pt-gh-badge {
  font-size: 10px; font-weight: 600; color: #a1a1aa;
  background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18);
  border-radius: 100px; padding: 2px 7px;
}
.pt-gh-mini {
  display: grid;
  grid-template-rows: repeat(7, 5px);
  grid-auto-flow: column;
  grid-auto-columns: 5px;
  gap: 2px;
  overflow: hidden;
}
.pt-gh-cell { border-radius: 1px; }
.pt-gh-l0 { background: rgba(255,255,255,0.05); }
.pt-gh-l1 { background: rgba(255,255,255,0.22); }
.pt-gh-l2 { background: rgba(255,255,255,0.45); }
.pt-gh-l3 { background: rgba(255,255,255,0.68); }
.pt-gh-l4 { background: var(--th-accent, #d4d4d8); }
.pt-gh-count { font-size: 11px; color: #71717a; margin-top: 5px; }

/* ── Block inner: PC Config ── */
.pt-pc-row {
  display: flex; justify-content: space-between; font-size: 12px;
  padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.pt-pc-row:last-child { border-bottom: none; }
.pt-pc-cat { color: #71717a; }
.pt-pc-val { color: #d4d4d8; text-align: right; max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Block inner: Faceit ── */
.pt-faceit-lvl {
  width: 26px; height: 26px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 900; color: #fff;
}
.pt-faceit-stats { display: flex; gap: 12px; }
.pt-fstat { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.pt-fstat-v { font-size: 14px; font-weight: 800; }
.pt-fstat-l { font-size: 9px; color: #71717a; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Avatar wrapper in canvas ── */
.pt-ph-avatar-wrap-center {
  position: relative; display: inline-block; margin-bottom: 14px;
}
.pt-ph-avatar-center { margin-bottom: 0; }
.pt-ph-avatar-cam {
  position: absolute; bottom: -2px; right: -2px;
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(13,13,28,0.92); border: 1.5px solid rgba(255,255,255,0.35);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #a1a1aa; cursor: pointer;
  transition: background 0.2s;
}
.pt-ph-avatar-cam:hover { background: rgba(255,255,255,0.18); }
.pt-avt-spin {
  width: 11px; height: 11px; border-radius: 50%;
  border: 2px solid rgba(144,190,255,0.25); border-top-color: #a1a1aa;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Inline form labels ── */
.pt-if-group { display: flex; flex-direction: column; gap: 4px; }
.pt-if-label { font-size: 11px; font-weight: 600; color: #52525b; text-transform: uppercase; letter-spacing: 0.6px; }
.pt-if-hint { font-weight: 400; text-transform: none; letter-spacing: 0; color: #3f3f46; font-size: 10px; }

/* ── Theme-specific canvas block styles ── */
/* Material 3 — alternating expressive corners */
[data-theme="material3"] .pt-block-preview:nth-child(odd) {
  border-radius: 20px 8px 20px 8px;
}
[data-theme="material3"] .pt-block-preview:nth-child(even) {
  border-radius: 8px 20px 8px 20px;
}

/* Glass — frosted block appearance */
[data-theme="glass"] .pt-block-preview::after {
  content: '';
  position: absolute; inset: 0; pointer-events: none; border-radius: inherit;
  background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 50%);
}
[data-theme="glass"] .pt-w-divider {
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
}

.pt-ghost { opacity: 0.4; background: rgba(255,255,255,0.08) !important; border-radius: 8px; }
.pt-ghost-block { opacity: 0.35; }
.pt-ghost-add { opacity: 0.5; }
</style>
