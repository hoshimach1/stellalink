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
          class="pt-add-grid"
          :group="{ name: 'blocks', pull: 'clone', put: false }"
          :sort="false"
          ghost-class="pt-ghost-add"
        >
          <div
            v-for="bt in blockTypes"
            :key="bt.type"
            class="pt-add-btn"
            :data-type="bt.type"
            @click="addBlock(bt.type)"
          >
            <span class="pt-add-icon">{{ bt.icon }}</span>
            <span>{{ bt.label }}</span>
          </div>
        </VueDraggable>

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
    <div class="pt-canvas" @click.self="deselectAll">
      <div class="pt-profile-card">

        <!-- Header -->
        <div class="pt-ph" :class="{ editing: editingHeader }" @click="!editingHeader && (editingHeader = true)">
          <div class="pt-ph-avatar">{{ initial }}</div>
          <div class="pt-ph-info">
            <template v-if="editingHeader">
              <input ref="nameInput" v-model="editName" class="pt-inline-input pt-inline-name" placeholder="Имя / Никнейм" @keydown.enter="saveHeader" @keydown.esc="cancelHeader">
              <input v-model="editSlug" class="pt-inline-input pt-inline-slug" placeholder="username" @keydown.enter="saveHeader" @keydown.esc="cancelHeader">
              <textarea v-model="editBio" class="pt-inline-input" placeholder="Bio..." rows="2" />
              <input v-model="editTagsRaw" class="pt-inline-input pt-inline-tags" placeholder="теги через запятую">
              <div class="pt-inline-actions">
                <button class="pt-save-btn" @click.stop="saveHeader">Сохранить</button>
                <button class="pt-cancel-btn" @click.stop="cancelHeader">Отмена</button>
              </div>
            </template>
            <template v-else>
              <div class="pt-ph-name">{{ profile.profile!.display_name || 'Нажми чтобы редактировать' }}</div>
              <div class="pt-ph-slug">stellalink.app/{{ profile.profile!.slug }}</div>
              <div v-if="profile.profile!.bio" class="pt-ph-bio">{{ profile.profile!.bio }}</div>
              <div v-if="profile.profile!.tags.length" class="pt-ph-tags">
                <span v-for="tag in profile.profile!.tags" :key="tag" class="pt-tag">{{ tag }}</span>
              </div>
              <div class="pt-edit-hint"><i class="ri-edit-line" /> Редактировать</div>
            </template>
          </div>
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
              <template v-if="block.block_type === 'links'">
                <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pt-links-group">
                  <div v-if="group.title" class="pt-group-label">{{ group.title }}</div>
                  <div v-for="link in group.links" :key="link.url" class="pt-link-row">
                    <i v-if="link.icon" :class="`ri-${link.icon}-fill`" />
                    {{ link.label || link.url || '(пусто)' }}
                  </div>
                  <div v-if="!group.links.length" class="pt-block-empty">Нет ссылок</div>
                </div>
              </template>
              <template v-else-if="block.block_type === 'text'">
                <div class="pt-text-content">{{ (block.config.content as string) || '(пусто)' }}</div>
              </template>
              <template v-else>
                <div class="pt-widget-row">
                  <span>{{ blockIcon(block.block_type) }}</span>
                  <span class="pt-widget-name">{{ blockLabel(block.block_type) }}</span>
                  <span class="pt-widget-val">{{ widgetVal(block) }}</span>
                </div>
              </template>
            </div>
            <div class="pt-block-overlay" @click="selectBlock(block.id)">
              <i class="ri-edit-line" /> Редактировать
            </div>
            <div v-if="!block.is_visible" class="pt-hidden-badge">скрыт</div>
          </div>

          <template #footer>
            <div v-if="!localBlocks.length" class="pt-drop-zone">
              <i class="ri-drag-drop-line" />
              <span>Перетащи блок сюда или нажми «+» в сайдбаре</span>
            </div>
          </template>
        </VueDraggable>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { VueDraggable } from 'vue-draggable-plus'
import { useProfileStore, type Block } from '~/stores/profile'

interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }

const profile = useProfileStore()

const blockTypes = ref([
  { type: 'links',         icon: '🔗', label: 'Ссылки' },
  { type: 'text',          icon: '📝', label: 'Текст' },
  { type: 'widget_steam',  icon: '🎮', label: 'Steam' },
  { type: 'widget_lastfm', icon: '🎵', label: 'Last.fm' },
  { type: 'widget_github', icon: '🐙', label: 'GitHub' },
  { type: 'pc_config',     icon: '💻', label: 'ПК конфиг' },
])
const defaultConfigs: Record<string, Record<string, unknown>> = {
  links:          { groups: [{ title: '', links: [] }] },
  text:           { content: '', format: 'markdown' },
  widget_steam:   { steam_id: '', show_recent_games: true },
  widget_lastfm:  { username: '', show_now_playing: true },
  widget_github:  { username: '', show_contributions: true, show_pinned_repos: true },
  pc_config:      { title: 'My Rig', components: [] },
}

function blockLabel(type: string) { return blockTypes.value.find(b => b.type === type)?.label ?? type }
function blockIcon(type: string)  { return blockTypes.value.find(b => b.type === type)?.icon  ?? '📦' }
function widgetVal(block: Block) {
  const c = block.config
  if (block.block_type === 'widget_steam')  return (c.steam_id  as string) || '—'
  if (block.block_type === 'widget_lastfm') return (c.username  as string) || '—'
  if (block.block_type === 'widget_github') return (c.username  as string) || '—'
  if (block.block_type === 'pc_config')     return (c.title     as string) || '—'
  return ''
}

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
  // Remove spurious placeholder vue-draggable inserted
  localBlocks.value = localBlocks.value.filter(b => b.id)
  const block = await profile.createBlock(type, defaultConfigs[type] ?? {})
  localBlocks.value.push(block)
  selectedBlockId.value = block.id
}

async function addBlock(type: string) {
  const block = await profile.createBlock(type, defaultConfigs[type] ?? {})
  localBlocks.value.push(block)
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
    bio: editBio.value || undefined,
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
  width: 230px; flex-shrink: 0;
  border-right: 1px solid rgba(61,142,255,0.08);
  display: flex; flex-direction: column;
  overflow: hidden;
}

/* Block list mode */
.pt-sidebar > template:first-child,
.pt-sidebar > .pt-status-row,
.pt-sidebar > .pt-section-label,
.pt-sidebar > .pt-block-list,
.pt-sidebar > .pt-empty,
.pt-sidebar > .pt-add-grid {
  padding: 0 12px;
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

.pt-section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #3a3a58; padding: 6px 12px 4px;
}

.pt-block-list { display: flex; flex-direction: column; gap: 3px; padding: 0 8px; overflow-y: auto; flex: 1; }
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

.pt-add-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 6px 8px 12px; }
.pt-add-btn {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(61,142,255,0.08);
  border-radius: 8px; padding: 8px 4px; font-size: 10px; color: #6a6a90;
  cursor: grab; font-family: 'Onest', sans-serif; transition: all 0.2s; user-select: none;
}
.pt-add-icon { font-size: 18px; }
.pt-add-btn:hover { background: rgba(61,142,255,0.08); border-color: rgba(61,142,255,0.22); color: #eeeef8; }
.pt-add-btn:active { cursor: grabbing; }

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
.pt-canvas { flex: 1; overflow-y: auto; padding: 24px; display: flex; justify-content: center; }
.pt-profile-card {
  width: 100%; max-width: 440px; height: fit-content;
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 18px; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

/* Header */
.pt-ph {
  padding: 20px; border-bottom: 1px solid rgba(61,142,255,0.07);
  background: linear-gradient(160deg, rgba(61,142,255,0.06) 0%, transparent 60%);
  cursor: pointer; position: relative;
}
.pt-ph.editing { cursor: default; }
.pt-ph:not(.editing):hover .pt-edit-hint { opacity: 1; }
.pt-ph-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 800; color: #fff; margin-bottom: 12px;
}
.pt-ph-info { display: flex; flex-direction: column; gap: 7px; }
.pt-ph-name { font-size: 17px; font-weight: 800; }
.pt-ph-slug { font-size: 12px; color: #3a3a58; }
.pt-ph-bio  { font-size: 13px; color: #6a6a90; }
.pt-ph-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.pt-tag {
  background: rgba(61,142,255,0.10); color: #90beff;
  border: 1px solid rgba(61,142,255,0.16); border-radius: 100px;
  padding: 2px 9px; font-size: 11px; font-weight: 500;
}
.pt-edit-hint {
  position: absolute; top: 12px; right: 12px; opacity: 0; transition: opacity 0.2s;
  font-size: 11px; color: #6a6a90; display: flex; align-items: center; gap: 4px;
  background: rgba(13,13,28,0.9); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 6px; padding: 3px 8px; pointer-events: none;
}

.pt-inline-input {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(61,142,255,0.25);
  border-radius: 7px; padding: 7px 10px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; width: 100%; resize: none;
}
.pt-inline-name { font-size: 15px; font-weight: 700; }
.pt-inline-slug { font-size: 12px; color: #90beff; }
.pt-inline-actions { display: flex; gap: 8px; }
.pt-save-btn {
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF); border: none;
  border-radius: 7px; padding: 6px 16px; color: #fff;
  font-size: 12px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}
.pt-cancel-btn {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 7px; padding: 6px 12px; color: #6a6a90;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
}

/* Canvas blocks */
.pt-blocks { padding: 10px; display: flex; flex-direction: column; gap: 7px; min-height: 60px; }
.pt-drop-zone {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 32px 16px; color: #3a3a58;
  border: 1.5px dashed rgba(61,142,255,0.14); border-radius: 12px;
  font-size: 13px; text-align: center;
}
.pt-drop-zone i { font-size: 28px; }

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

.pt-links-group { margin-bottom: 6px; }
.pt-links-group:last-child { margin-bottom: 0; }
.pt-group-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6a6a90; margin-bottom: 4px; }
.pt-link-row { font-size: 13px; color: #aaaacc; padding: 3px 0; display: flex; align-items: center; gap: 6px; }
.pt-block-empty { font-size: 12px; color: #3a3a58; font-style: italic; }
.pt-text-content { font-size: 13px; color: #aaaacc; white-space: pre-wrap; }
.pt-widget-row { display: flex; align-items: center; gap: 9px; font-size: 13px; }
.pt-widget-name { font-weight: 600; }
.pt-widget-val { color: #6a6a90; margin-left: auto; }

.pt-ghost { opacity: 0.4; background: rgba(61,142,255,0.08) !important; border-radius: 8px; }
.pt-ghost-block { opacity: 0.35; }
.pt-ghost-add { opacity: 0.5; }
</style>
