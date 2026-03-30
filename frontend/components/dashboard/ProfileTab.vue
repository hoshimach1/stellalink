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
          <div class="pt-theme-grid">
            <button
              v-for="t in THEMES"
              :key="t.id"
              class="pt-theme-card"
              :class="{ active: (profile.profile!.theme_preset || 'material3') === t.id }"
              @click="setTheme(t.id)"
            >
              <div class="pt-theme-preview" :style="t.preview" />
              <span class="pt-theme-name">{{ t.label }}</span>
            </button>
          </div>

          <div class="pt-section-label" style="margin-top:16px">Акцентный цвет</div>
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

    <div class="pt-canvas" @click.self="deselectAll">
      <div class="pt-profile-card">

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
  { id: 'material3', label: 'Dark',     preview: 'background: linear-gradient(135deg,#0d0d1c 50%,#1a2540); border: 1.5px solid rgba(61,142,255,0.3)' },
  { id: 'midnight', label: 'Midnight',  preview: 'background: linear-gradient(135deg,#000000 50%,#0d0018); border: 1.5px solid rgba(139,92,246,0.3)' },
  { id: 'aurora',   label: 'Aurora',    preview: 'background: linear-gradient(135deg,#06110d 50%,#0a1f18); border: 1.5px solid rgba(52,211,153,0.3)' },
  { id: 'sunset',   label: 'Sunset',    preview: 'background: linear-gradient(135deg,#110808 50%,#1f1008); border: 1.5px solid rgba(249,115,22,0.3)' },
  { id: 'light',    label: 'Light',     preview: 'background: linear-gradient(135deg,#f4f6fb 50%,#e8edf8); border: 1.5px solid rgba(37,99,235,0.25)' },
]

const ACCENT_COLORS = [
  { label: 'Blue',   value: '#3D8EFF' },
  { label: 'Purple', value: '#8B5CF6' },
  { label: 'Pink',   value: '#EC4899' },
  { label: 'Red',    value: '#EF4444' },
  { label: 'Orange', value: '#F97316' },
  { label: 'Yellow', value: '#EAB308' },
  { label: 'Green',  value: '#22C55E' },
  { label: 'Teal',   value: '#14B8A6' },
]

const currentAccent = computed(() => profile.profile?.accent_color || '#3D8EFF')

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
  border-right: 1px solid rgba(61,142,255,0.08);
  display: flex; flex-direction: column;
  overflow: hidden;
  background: rgba(13,13,28,0.6);
}

.pt-status-row { display: flex; align-items: center; gap: 8px; padding: 14px 12px 8px; }
.pt-toggle {
  flex: 1; display: flex; align-items: center; gap: 7px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 7px 10px;
  font-size: 12px; font-weight: 600; color: #6a6a90;
  cursor: pointer; font-family: 'Onest', sans-serif; transition: all 0.2s;
}
.pt-toggle.active { background: rgba(61,142,255,0.12); border-color: rgba(61,142,255,0.28); color: #90beff; }
.pt-toggle-dot { width: 7px; height: 7px; border-radius: 50%; background: #3a3a58; flex-shrink: 0; transition: background 0.2s; }
.pt-toggle.active .pt-toggle-dot { background: #3D8EFF; }
.pt-view-btn {
  width: 32px; height: 32px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(61,142,255,0.08); border: 1px solid rgba(61,142,255,0.18);
  border-radius: 8px; color: #90beff; text-decoration: none; font-size: 16px;
}

/* ── Sidebar tabs ── */
.pt-sidebar-tabs {
  display: flex; gap: 4px; padding: 6px 8px 0;
}
.pt-stab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 5px;
  padding: 7px 4px; border-radius: 8px; border: 1px solid transparent;
  font-size: 11px; font-weight: 600; color: #4a4a68;
  background: none; cursor: pointer; font-family: 'Onest', sans-serif;
  transition: all 0.15s;
}
.pt-stab:hover { color: #8888aa; background: rgba(255,255,255,0.03); }
.pt-stab.active {
  color: #90beff; background: rgba(61,142,255,0.08);
  border-color: rgba(61,142,255,0.18);
}

.pt-section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.2px; color: #4a4a68; padding: 8px 12px 4px;
}

/* ── Design tab ── */
.pt-theme-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
  padding: 4px 10px;
}
.pt-theme-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  background: none; border: 1px solid rgba(61,142,255,0.08);
  border-radius: 10px; padding: 8px 6px; cursor: pointer;
  transition: all 0.15s; font-family: 'Onest', sans-serif;
}
.pt-theme-card:hover { border-color: rgba(61,142,255,0.24); background: rgba(255,255,255,0.02); }
.pt-theme-card.active { border-color: #3D8EFF; box-shadow: 0 0 0 2px rgba(61,142,255,0.14); }
.pt-theme-preview {
  width: 100%; height: 38px; border-radius: 6px;
}
.pt-theme-name { font-size: 11px; font-weight: 600; color: #8888aa; }
.pt-theme-card.active .pt-theme-name { color: #90beff; }

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
.pt-accent-hex { font-size: 11px; color: #6a6a90; font-family: monospace; }

.pt-block-list { display: flex; flex-direction: column; gap: 2px; padding: 0 8px; overflow-y: auto; max-height: 220px; }
.pt-block-item {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 6px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; transition: all 0.15s;
}
.pt-block-item:hover { background: rgba(255,255,255,0.04); border-color: rgba(61,142,255,0.10); }
.pt-drag-handle { color: #3a3a58; font-size: 15px; cursor: grab; flex-shrink: 0; }
.pt-drag-handle:active { cursor: grabbing; }
.pt-block-icon { font-size: 14px; }
.pt-block-label { font-size: 13px; flex: 1; color: #aaaacc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pt-block-actions { display: flex; align-items: center; gap: 3px; opacity: 0; transition: opacity 0.15s; }
.pt-block-item:hover .pt-block-actions { opacity: 1; }

.pt-vis-btn {
  width: 22px; height: 13px; border-radius: 7px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(61,142,255,0.14);
  position: relative; cursor: pointer; transition: background 0.2s; flex-shrink: 0;
}
.pt-vis-btn::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 9px; height: 9px; border-radius: 50%; background: #3a3a58; transition: transform 0.2s, background 0.2s;
}
.pt-vis-btn.active { background: rgba(61,142,255,0.25); }
.pt-vis-btn.active::after { transform: translateX(9px); background: #3D8EFF; }

.pt-del-btn {
  background: none; border: none; color: #3a3a58; cursor: pointer;
  font-size: 13px; display: flex; align-items: center; padding: 2px; transition: color 0.2s;
}
.pt-del-btn:hover { color: #ff7070; }
.pt-empty { font-size: 11px; color: #3a3a58; padding: 8px 12px; }

.pt-add-list { display: flex; flex-direction: column; gap: 2px; padding: 4px 8px 12px; overflow-y: auto; flex: 1; }
.pt-add-item {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px; border-radius: 8px;
  border: 1px solid transparent;
  font-size: 13px; color: #8888aa;
  cursor: grab; font-family: 'Onest', sans-serif; transition: all 0.15s; user-select: none;
}
.pt-add-ico { font-size: 17px; flex-shrink: 0; }
.pt-add-label { flex: 1; font-weight: 500; }
.pt-add-plus { font-size: 16px; color: #3a3a58; opacity: 0; transition: opacity 0.15s; }
.pt-add-item:hover {
  background: rgba(61,142,255,0.07); border-color: rgba(61,142,255,0.16);
  color: #eeeef8;
}
.pt-add-item:hover .pt-add-plus { opacity: 1; color: #90beff; }
.pt-add-item:active { cursor: grabbing; }

/* Block editor mode */
.pt-editor-header {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 12px 10px; border-bottom: 1px solid rgba(61,142,255,0.08); flex-shrink: 0;
}
.pt-back-btn {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 7px; width: 30px; height: 30px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #6a6a90; cursor: pointer; font-size: 16px; transition: all 0.2s;
}
.pt-back-btn:hover { color: #eeeef8; background: rgba(255,255,255,0.08); }
.pt-editor-title { font-size: 13px; font-weight: 700; }

.pt-editor-body { flex: 1; overflow-y: auto; padding: 14px 12px; }

.pt-editor-footer {
  display: flex; gap: 8px; padding: 12px;
  border-top: 1px solid rgba(61,142,255,0.08); flex-shrink: 0;
}
.pt-ep-cancel {
  flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 9px; color: #6a6a90;
  font-size: 13px; font-family: 'Onest', sans-serif; cursor: pointer;
}
.pt-ep-save {
  flex: 2; background: linear-gradient(135deg, #2b7ef0, #3D8EFF); border: none;
  border-radius: 8px; padding: 9px; color: #fff;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}

/* ── Canvas ── */
.pt-canvas {
  flex: 1; overflow-y: auto; padding: 24px;
  display: flex; justify-content: center; align-items: flex-start;
  background: radial-gradient(ellipse 60% 30% at 50% 0%, rgba(61,142,255,0.04), transparent);
}
.pt-profile-card {
  width: 100%; max-width: 420px; height: fit-content;
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.12);
  border-radius: 20px; overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(61,142,255,0.04);
}

/* Header */
.pt-ph {
  position: relative; overflow: hidden;
  border-bottom: 1px solid rgba(61,142,255,0.08);
}
.pt-ph-glow {
  position: absolute; top: -40px; left: 50%; transform: translateX(-50%);
  width: 200px; height: 120px; pointer-events: none;
  background: radial-gradient(ellipse, rgba(61,142,255,0.18), transparent 70%);
}
.pt-ph-center {
  display: flex; flex-direction: column; align-items: center;
  padding: 28px 20px 20px; text-align: center; cursor: pointer;
  position: relative;
}
.pt-ph-center:hover .pt-edit-chip { opacity: 1; }

.pt-ph-avatar {
  width: 68px; height: 68px; border-radius: 50%;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: #fff;
  overflow: hidden; flex-shrink: 0;
  box-shadow: 0 0 0 3px rgba(61,142,255,0.22), 0 6px 20px rgba(61,142,255,0.20);
}
.pt-ph-avatar-center { margin-bottom: 14px; }
.pt-ph-avatar-img { width: 100%; height: 100%; object-fit: cover; }

.pt-ph-name { font-size: 18px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 2px; }
.pt-ph-slug { font-size: 12px; color: #3a3a58; margin-bottom: 6px; }
.pt-ph-bio  { font-size: 13px; color: #8888aa; margin-bottom: 8px; max-width: 280px; line-height: 1.4; }
.pt-ph-tags { display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; }
.pt-tag {
  background: rgba(61,142,255,0.10); color: #90beff;
  border: 1px solid rgba(61,142,255,0.16); border-radius: 100px;
  padding: 2px 10px; font-size: 11px; font-weight: 500;
}
.pt-edit-chip {
  margin-top: 12px; display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; color: #6a6a90;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.12);
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
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.25);
  border-radius: 7px; overflow: hidden;
}
.pt-slug-prefix { padding: 7px 0 7px 10px; font-size: 12px; color: #3a3a58; white-space: nowrap; }
.pt-slug-prefix + .pt-inline-slug-bare { border: none; background: none; padding-left: 2px; }
.pt-inline-slug-bare {
  flex: 1; background: none; border: none; outline: none;
  padding: 7px 10px; color: #90beff; font-size: 12px; font-family: 'Onest', sans-serif;
}
.pt-inline-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.22);
  border-radius: 7px; padding: 7px 10px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; width: 100%; resize: none;
  transition: border-color 0.2s;
}
.pt-inline-input:focus { border-color: rgba(61,142,255,0.45); }
.pt-inline-name { font-size: 15px; font-weight: 700; }
.pt-inline-actions { display: flex; gap: 8px; justify-content: flex-end; }
.pt-save-btn {
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF); border: none;
  border-radius: 7px; padding: 7px 18px; color: #fff;
  font-size: 12px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}
.pt-cancel-btn {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 7px; padding: 7px 14px; color: #6a6a90;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
}

/* Canvas blocks */
.pt-blocks { padding: 10px; display: flex; flex-direction: column; gap: 7px; min-height: 60px; }
.pt-drop-zone {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 36px 20px;
  border: 1.5px dashed rgba(61,142,255,0.12); border-radius: 14px;
  text-align: center;
}
.pt-dz-icons { display: flex; gap: 8px; font-size: 22px; opacity: 0.5; }
.pt-dz-ico { filter: grayscale(0.3); }
.pt-dz-title { font-size: 14px; font-weight: 700; color: #4a4a68; }
.pt-dz-hint { font-size: 12px; color: #3a3a58; max-width: 220px; line-height: 1.5; }

.pt-block-preview {
  position: relative; border-radius: 10px; overflow: hidden;
  border: 1px solid rgba(61,142,255,0.08);
  display: flex; align-items: stretch; transition: border-color 0.2s;
}
.pt-block-preview:hover { border-color: rgba(61,142,255,0.28); }
.pt-block-preview.selected { border-color: #3D8EFF; box-shadow: 0 0 0 2px rgba(61,142,255,0.14); }
.pt-block-preview.hidden { opacity: 0.4; }

.pt-block-drag {
  flex-shrink: 0; width: 22px; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  color: #3a3a58; cursor: grab;
  background: rgba(255,255,255,0.02); border-right: 1px solid rgba(61,142,255,0.06);
  transition: color 0.2s, background 0.2s;
}
.pt-block-drag:hover { color: #6a6a90; background: rgba(61,142,255,0.05); }
.pt-block-drag:active { cursor: grabbing; }

.pt-block-inner { flex: 1; padding: 11px 13px; cursor: pointer; }
.pt-block-overlay {
  position: absolute; inset: 0; left: 22px;
  background: rgba(61,142,255,0.07);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #90beff; gap: 6px;
  opacity: 0; transition: opacity 0.18s; cursor: pointer;
}
.pt-block-preview:hover .pt-block-overlay { opacity: 1; }
.pt-block-preview.selected .pt-block-overlay { opacity: 0; }
.pt-hidden-badge {
  position: absolute; top: 5px; right: 6px;
  background: rgba(255,255,255,0.07); border-radius: 4px;
  padding: 1px 6px; font-size: 10px; color: #6a6a90; pointer-events: none;
}

/* ── Block inner: links ── */
.pt-links-group { margin-bottom: 6px; }
.pt-links-group:last-child { margin-bottom: 0; }
.pt-group-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6a6a90; margin-bottom: 4px; }
.pt-link-row { font-size: 13px; color: #aaaacc; padding: 3px 0; display: flex; align-items: center; gap: 6px; }
.pt-link-icon { font-size: 14px; color: #90beff; flex-shrink: 0; }
.pt-block-empty { font-size: 12px; color: #3a3a58; font-style: italic; }
.pt-text-content { font-size: 13px; color: #aaaacc; white-space: pre-wrap; }

/* ── Block inner: widget shared ── */
.pt-w-header { display: flex; align-items: center; justify-content: space-between; }
.pt-w-hl { display: flex; align-items: center; gap: 8px; }
.pt-w-ico { font-size: 20px; }
.pt-w-name { font-size: 13px; font-weight: 700; line-height: 1.2; }
.pt-w-id { font-size: 11px; color: #6a6a90; }
.pt-w-divider { height: 1px; background: rgba(61,142,255,0.07); margin: 8px 0; }
.pt-badge-green {
  font-size: 10px; font-weight: 600; color: #4ade80;
  background: rgba(74,222,128,0.10); border: 1px solid rgba(74,222,128,0.18);
  border-radius: 100px; padding: 2px 7px;
}

/* ── Block inner: Steam ── */
.pt-steam-row {
  display: flex; justify-content: space-between; font-size: 12px;
  padding: 3px 0; border-bottom: 1px solid rgba(61,142,255,0.05); color: #aaaacc;
}
.pt-steam-row:last-child { border-bottom: none; }
.pt-steam-h { color: #6a6a90; }

/* ── Block inner: Last.fm ── */
.pt-np-bars { display: flex; align-items: flex-end; gap: 2px; height: 14px; }
.pt-np-bar {
  width: 3px; height: 14px; background: #e5343a; border-radius: 1px;
  animation: npBounce 1.1s ease-in-out infinite; transform-origin: bottom;
}
@keyframes npBounce { 0%, 100% { transform: scaleY(0.25); } 50% { transform: scaleY(1); } }
.pt-np-row { display: flex; align-items: center; gap: 5px; font-size: 12px; flex-wrap: wrap; }
.pt-np-label { color: #e5343a; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; }
.pt-np-track { font-weight: 600; color: #eeeef8; }
.pt-np-artist { color: #6a6a90; }

/* ── Block inner: GitHub ── */
.pt-gh-badge {
  font-size: 10px; font-weight: 600; color: #90beff;
  background: rgba(61,142,255,0.10); border: 1px solid rgba(61,142,255,0.18);
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
.pt-gh-l1 { background: rgba(61,142,255,0.22); }
.pt-gh-l2 { background: rgba(61,142,255,0.45); }
.pt-gh-l3 { background: rgba(61,142,255,0.68); }
.pt-gh-l4 { background: #3D8EFF; }
.pt-gh-count { font-size: 11px; color: #6a6a90; margin-top: 5px; }

/* ── Block inner: PC Config ── */
.pt-pc-row {
  display: flex; justify-content: space-between; font-size: 12px;
  padding: 3px 0; border-bottom: 1px solid rgba(61,142,255,0.05);
}
.pt-pc-row:last-child { border-bottom: none; }
.pt-pc-cat { color: #6a6a90; }
.pt-pc-val { color: #ccccdd; text-align: right; max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Block inner: Faceit ── */
.pt-faceit-lvl {
  width: 26px; height: 26px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 900; color: #fff;
}
.pt-faceit-stats { display: flex; gap: 12px; }
.pt-fstat { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.pt-fstat-v { font-size: 14px; font-weight: 800; }
.pt-fstat-l { font-size: 9px; color: #6a6a90; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Avatar wrapper in canvas ── */
.pt-ph-avatar-wrap-center {
  position: relative; display: inline-block; margin-bottom: 14px;
}
.pt-ph-avatar-center { margin-bottom: 0; }
.pt-ph-avatar-cam {
  position: absolute; bottom: -2px; right: -2px;
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(13,13,28,0.92); border: 1.5px solid rgba(61,142,255,0.35);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #90beff; cursor: pointer;
  transition: background 0.2s;
}
.pt-ph-avatar-cam:hover { background: rgba(61,142,255,0.18); }
.pt-avt-spin {
  width: 11px; height: 11px; border-radius: 50%;
  border: 2px solid rgba(144,190,255,0.25); border-top-color: #90beff;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Inline form labels ── */
.pt-if-group { display: flex; flex-direction: column; gap: 4px; }
.pt-if-label { font-size: 11px; font-weight: 600; color: #4a4a68; text-transform: uppercase; letter-spacing: 0.6px; }
.pt-if-hint { font-weight: 400; text-transform: none; letter-spacing: 0; color: #3a3a58; font-size: 10px; }

.pt-ghost { opacity: 0.4; background: rgba(61,142,255,0.08) !important; border-radius: 8px; }
.pt-ghost-block { opacity: 0.35; }
.pt-ghost-add { opacity: 0.5; }
</style>
