<template>
  <div class="dash">
    <!-- Header -->
    <header class="dash-header">
      <NuxtLink to="/" class="dash-brand">
        <img src="/images/logos/logo.png" alt="" class="dash-logo">
        <span>Stellalink</span>
      </NuxtLink>
      <div class="dash-header-right">
        <a
          v-if="profile.hasProfile && profile.isPublished"
          :href="`http://144.31.66.170:3000/p/${profile.profile!.slug}`"
          target="_blank"
          class="dash-view-btn"
        >
          <i class="ri-external-link-line" /> Смотреть профиль
        </a>
        <span class="dash-email">{{ auth.user?.email }}</span>
        <button class="dash-logout" @click="logout">
          <i class="ri-logout-box-r-line" />
        </button>
      </div>
    </header>

    <!-- Body -->
    <div class="dash-body">

      <!-- Setup: no profile yet -->
      <div v-if="!profile.hasProfile" class="setup-wrap">
        <div class="setup-card">
          <img src="/images/logos/logo.png" class="setup-logo" alt="">
          <h2>Создай свой профиль</h2>
          <p>Выбери адрес — это будет твоя ссылка</p>

          <form class="setup-form" @submit.prevent="createProfile">
            <div class="setup-url">
              <span class="setup-prefix">stellalink.app/</span>
              <input
                v-model="setupSlug"
                type="text"
                placeholder="username"
                pattern="[a-z0-9_-]+"
                minlength="2"
                maxlength="50"
                required
                autocomplete="off"
              >
            </div>
            <div class="dash-field">
              <label>Имя / Никнейм</label>
              <input v-model="setupName" type="text" placeholder="Иван Иванов" required maxlength="100">
            </div>
            <div class="dash-field">
              <label>Bio <span class="dash-optional">необязательно</span></label>
              <textarea v-model="setupBio" placeholder="Пару слов о себе..." rows="2" />
            </div>
            <div v-if="setupError" class="dash-error">{{ setupError }}</div>
            <button type="submit" class="dash-btn-primary" :disabled="setupLoading">
              <span v-if="setupLoading" class="dash-spinner" />
              <span v-else>Создать профиль →</span>
            </button>
          </form>
        </div>
      </div>

      <!-- Dashboard: profile exists -->
      <div v-else class="dash-layout">

        <!-- Left: editor -->
        <div class="dash-editor">

          <!-- Profile header card -->
          <div class="dash-card">
            <div class="dash-card-header">
              <span class="dash-card-title">Шапка профиля</span>
              <div class="dash-status-toggle">
                <span class="dash-status-label">{{ profile.isPublished ? 'Опубликован' : 'Черновик' }}</span>
                <button
                  class="dash-toggle"
                  :class="{ active: profile.isPublished }"
                  @click="toggleStatus"
                />
              </div>
            </div>

            <div class="dash-card-body">
              <div class="dash-field">
                <label>Адрес профиля</label>
                <div class="dash-slug-wrap">
                  <span class="dash-slug-prefix">stellalink.app/</span>
                  <input v-model="editSlug" type="text" @blur="saveHeader">
                </div>
              </div>
              <div class="dash-field">
                <label>Имя / Никнейм</label>
                <input v-model="editName" type="text" @blur="saveHeader">
              </div>
              <div class="dash-field">
                <label>Bio</label>
                <textarea v-model="editBio" rows="2" @blur="saveHeader" />
              </div>
              <div class="dash-field">
                <label>Теги <span class="dash-optional">через запятую</span></label>
                <input v-model="editTagsRaw" type="text" placeholder="геймер, разработчик, стример" @blur="saveHeader">
              </div>
              <div v-if="headerError" class="dash-error">{{ headerError }}</div>
            </div>
          </div>

          <!-- Blocks -->
          <div class="dash-card">
            <div class="dash-card-header">
              <span class="dash-card-title">Блоки</span>
            </div>
            <div class="dash-card-body">

              <!-- Block list -->
              <div v-if="profile.profile!.blocks.length" class="block-list">
                <div
                  v-for="block in profile.profile!.blocks"
                  :key="block.id"
                  class="block-item"
                >
                  <div class="block-item-left">
                    <i class="ri-drag-move-line block-drag" />
                    <span class="block-icon">{{ blockIcon(block.block_type) }}</span>
                    <span class="block-label">{{ blockLabel(block.block_type) }}</span>
                  </div>
                  <div class="block-item-right">
                    <button
                      class="block-toggle"
                      :class="{ active: block.is_visible }"
                      @click="toggleBlock(block)"
                    />
                    <button class="block-edit-btn" @click="editBlock(block)">
                      <i class="ri-edit-line" />
                    </button>
                    <button class="block-del-btn" @click="deleteBlock(block.id)">
                      <i class="ri-delete-bin-line" />
                    </button>
                  </div>
                </div>
              </div>

              <p v-else class="dash-empty">Нет блоков. Добавь первый!</p>

              <!-- Add block -->
              <div class="add-block-grid">
                <button
                  v-for="bt in blockTypes"
                  :key="bt.type"
                  class="add-block-btn"
                  @click="addBlock(bt.type)"
                >
                  <span>{{ bt.icon }}</span>
                  <span>{{ bt.label }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: preview -->
        <div class="dash-preview-col">
          <div class="dash-preview-label">Предпросмотр</div>
          <div class="dash-preview-wrap">
            <DashboardProfilePreview :profile="profile.profile!" />
          </div>
        </div>

      </div>
    </div>

    <!-- Block editor modal -->
    <DashboardBlockEditor
      v-if="editingBlock"
      :block="editingBlock"
      @save="saveBlock"
      @close="editingBlock = null"
    />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useProfileStore, type Block } from '~/stores/profile'

definePageMeta({ layout: 'default' })
useHead({ title: 'Dashboard — Stellalink' })

const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()

if (!auth.isAuthenticated) {
  await navigateTo('/')
}

await profile.fetch()

// ── Setup form ────────────────────────────────────────────────────────────────
const setupSlug = ref('')
const setupName = ref('')
const setupBio = ref('')
const setupError = ref('')
const setupLoading = ref(false)

async function createProfile() {
  setupError.value = ''
  setupLoading.value = true
  try {
    await profile.create({
      slug: setupSlug.value,
      display_name: setupName.value,
      bio: setupBio.value || undefined,
    })
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string } }
    setupError.value = err.data?.detail ?? 'Ошибка создания профиля'
  } finally {
    setupLoading.value = false
  }
}

// ── Header editor ─────────────────────────────────────────────────────────────
const editSlug = ref('')
const editName = ref('')
const editBio = ref('')
const editTagsRaw = ref('')
const headerError = ref('')

watch(() => profile.profile, (p) => {
  if (p) {
    editSlug.value = p.slug
    editName.value = p.display_name
    editBio.value = p.bio ?? ''
    editTagsRaw.value = p.tags.join(', ')
  }
}, { immediate: true })

async function saveHeader() {
  if (!profile.profile) return
  headerError.value = ''
  const tags = editTagsRaw.value.split(',').map(t => t.trim()).filter(Boolean)
  try {
    await profile.update({
      slug: editSlug.value || undefined,
      display_name: editName.value || undefined,
      bio: editBio.value || undefined,
      tags,
    })
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string } }
    headerError.value = err.data?.detail ?? 'Ошибка сохранения'
  }
}

async function toggleStatus() {
  const next = profile.isPublished ? 'draft' : 'published'
  await profile.update({ status: next })
}

// ── Blocks ────────────────────────────────────────────────────────────────────
const blockTypes = [
  { type: 'links', icon: '🔗', label: 'Ссылки' },
  { type: 'text', icon: '📝', label: 'Текст' },
  { type: 'widget_steam', icon: '🎮', label: 'Steam' },
  { type: 'widget_lastfm', icon: '🎵', label: 'Last.fm' },
  { type: 'widget_github', icon: '🐙', label: 'GitHub' },
  { type: 'pc_config', icon: '💻', label: 'ПК конфиг' },
]

function blockLabel(type: string) {
  return blockTypes.find(b => b.type === type)?.label ?? type
}
function blockIcon(type: string) {
  return blockTypes.find(b => b.type === type)?.icon ?? '📦'
}

const defaultConfigs: Record<string, Record<string, unknown>> = {
  links: { groups: [{ title: 'Ссылки', links: [] }] },
  text: { content: '', format: 'markdown' },
  widget_steam: { steam_id: '', show_recent_games: true },
  widget_lastfm: { username: '', show_now_playing: true },
  widget_github: { username: '', show_contributions: true, show_pinned_repos: true },
  pc_config: { title: 'My Rig', components: [] },
}

async function addBlock(type: string) {
  await profile.createBlock(type, defaultConfigs[type] ?? {})
}

async function toggleBlock(block: Block) {
  await profile.updateBlock(block.id, { is_visible: !block.is_visible })
}

async function deleteBlock(id: string) {
  if (!confirm('Удалить блок?')) return
  await profile.deleteBlock(id)
}

const editingBlock = ref<Block | null>(null)
function editBlock(block: Block) {
  editingBlock.value = { ...block, config: { ...block.config } }
}
async function saveBlock(data: { config: Record<string, unknown> }) {
  if (!editingBlock.value) return
  await profile.updateBlock(editingBlock.value.id, { config: data.config })
  editingBlock.value = null
}

async function logout() {
  auth.logout()
  await router.push('/')
}
</script>

<style scoped>
.dash {
  min-height: 100vh;
  background: #090910;
  color: #eeeef8;
  font-family: 'Onest', sans-serif;
}

/* Header */
.dash-header {
  display: flex; align-items: center;
  padding: 0 28px; height: 58px;
  background: rgba(13,13,28,0.95);
  border-bottom: 1px solid rgba(61,142,255,0.10);
  position: sticky; top: 0; z-index: 50;
}
.dash-brand {
  display: flex; align-items: center; gap: 9px;
  text-decoration: none; color: #eeeef8;
  font-weight: 800; font-size: 16px;
}
.dash-logo { width: 26px; height: 26px; object-fit: contain; mix-blend-mode: screen; }
.dash-header-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.dash-email { font-size: 13px; color: #6a6a90; }
.dash-view-btn {
  display: flex; align-items: center; gap: 6px;
  background: rgba(61,142,255,0.10); border: 1px solid rgba(61,142,255,0.22);
  border-radius: 8px; padding: 6px 14px;
  font-size: 13px; color: #90beff; text-decoration: none;
  transition: background 0.2s;
}
.dash-view-btn:hover { background: rgba(61,142,255,0.18); }
.dash-logout {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.12);
  border-radius: 8px; width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  color: #6a6a90; cursor: pointer; font-size: 16px;
  transition: background 0.2s, color 0.2s;
}
.dash-logout:hover { background: rgba(255,80,80,0.10); color: #ff7070; }

/* Body */
.dash-body { padding: 32px 28px; max-width: 1200px; margin: 0 auto; }

/* Setup */
.setup-wrap { display: flex; justify-content: center; padding: 60px 0; }
.setup-card {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.14);
  border-radius: 20px; padding: 40px 36px; width: 100%; max-width: 440px;
  text-align: center;
}
.setup-logo { width: 52px; height: 52px; object-fit: contain; mix-blend-mode: screen; margin: 0 auto 16px; display: block; }
.setup-card h2 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 6px; }
.setup-card p { color: #6a6a90; font-size: 14px; margin-bottom: 28px; }
.setup-form { text-align: left; display: flex; flex-direction: column; gap: 16px; }
.setup-url {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 10px; overflow: hidden;
}
.setup-prefix {
  padding: 11px 0 11px 14px; font-size: 14px; color: #6a6a90;
  white-space: nowrap;
}
.setup-url input {
  flex: 1; background: none; border: none; outline: none;
  padding: 11px 14px 11px 0; color: #eeeef8; font-size: 14px; font-family: 'Onest', sans-serif;
}

/* Layout */
.dash-layout { display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start; }
@media (max-width: 900px) { .dash-layout { grid-template-columns: 1fr; } }

/* Cards */
.dash-card {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 16px; overflow: hidden; margin-bottom: 16px;
}
.dash-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid rgba(61,142,255,0.07);
}
.dash-card-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #6a6a90; }
.dash-card-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

/* Fields */
.dash-field { display: flex; flex-direction: column; gap: 6px; }
.dash-field label { font-size: 12px; font-weight: 600; color: #6a6a90; }
.dash-optional { font-weight: 400; color: #3a3a58; }
.dash-field input,
.dash-field textarea {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 9px 12px; color: #eeeef8;
  font-size: 14px; font-family: 'Onest', sans-serif; outline: none;
  transition: border-color 0.2s;
  resize: none;
}
.dash-field input:focus,
.dash-field textarea:focus { border-color: rgba(61,142,255,0.40); }
.dash-field input::placeholder,
.dash-field textarea::placeholder { color: #3a3a58; }

.dash-slug-wrap { display: flex; align-items: center; background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14); border-radius: 8px; overflow: hidden; }
.dash-slug-prefix { padding: 9px 0 9px 12px; font-size: 13px; color: #6a6a90; white-space: nowrap; }
.dash-slug-wrap input { flex: 1; background: none; border: none; outline: none; padding: 9px 12px 9px 0; color: #eeeef8; font-size: 14px; font-family: 'Onest', sans-serif; }

/* Status toggle */
.dash-status-toggle { display: flex; align-items: center; gap: 10px; }
.dash-status-label { font-size: 12px; color: #6a6a90; }
.dash-toggle {
  width: 38px; height: 22px; border-radius: 11px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(61,142,255,0.16);
  position: relative; cursor: pointer; transition: background 0.2s;
}
.dash-toggle::after {
  content: ''; position: absolute; top: 3px; left: 3px;
  width: 14px; height: 14px; border-radius: 50%;
  background: #6a6a90; transition: transform 0.2s, background 0.2s;
}
.dash-toggle.active { background: rgba(61,142,255,0.30); border-color: rgba(61,142,255,0.50); }
.dash-toggle.active::after { transform: translateX(16px); background: #3D8EFF; }

/* Blocks */
.block-list { display: flex; flex-direction: column; gap: 6px; }
.block-item {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(61,142,255,0.08);
  border-radius: 10px; padding: 10px 14px;
}
.block-item-left { display: flex; align-items: center; gap: 10px; }
.block-drag { color: #3a3a58; font-size: 18px; cursor: grab; }
.block-icon { font-size: 18px; }
.block-label { font-size: 14px; font-weight: 500; }
.block-item-right { display: flex; align-items: center; gap: 6px; }
.block-toggle {
  width: 32px; height: 18px; border-radius: 9px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(61,142,255,0.14);
  position: relative; cursor: pointer; transition: background 0.2s;
}
.block-toggle::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 12px; height: 12px; border-radius: 50%; background: #3a3a58;
  transition: transform 0.2s, background 0.2s;
}
.block-toggle.active { background: rgba(61,142,255,0.25); }
.block-toggle.active::after { transform: translateX(14px); background: #3D8EFF; }
.block-edit-btn, .block-del-btn {
  width: 30px; height: 30px; border-radius: 7px; border: 1px solid transparent;
  background: rgba(255,255,255,0.04); display: flex; align-items: center; justify-content: center;
  color: #6a6a90; cursor: pointer; font-size: 15px; transition: all 0.2s;
}
.block-edit-btn:hover { background: rgba(61,142,255,0.12); color: #90beff; border-color: rgba(61,142,255,0.2); }
.block-del-btn:hover { background: rgba(255,80,80,0.10); color: #ff7070; border-color: rgba(255,80,80,0.2); }

/* Add block */
.add-block-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; }
.add-block-btn {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(61,142,255,0.10);
  border-radius: 10px; padding: 12px 8px;
  font-size: 12px; font-weight: 500; color: #6a6a90;
  cursor: pointer; transition: all 0.2s; font-family: 'Onest', sans-serif;
}
.add-block-btn span:first-child { font-size: 22px; }
.add-block-btn:hover { background: rgba(61,142,255,0.08); border-color: rgba(61,142,255,0.22); color: #eeeef8; }

/* Misc */
.dash-empty { color: #3a3a58; font-size: 14px; text-align: center; padding: 16px 0; }
.dash-error {
  background: rgba(255,80,80,0.10); border: 1px solid rgba(255,80,80,0.22);
  border-radius: 8px; padding: 9px 12px; color: #ff7070; font-size: 13px;
}
.dash-btn-primary {
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  color: #fff; border: none; border-radius: 10px; padding: 12px;
  font-size: 15px; font-weight: 700; font-family: 'Onest', sans-serif;
  cursor: pointer; transition: opacity 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.dash-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.dash-spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Preview column */
.dash-preview-col { position: sticky; top: 78px; }
.dash-preview-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #3a3a58; margin-bottom: 12px; }
.dash-preview-wrap {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 16px; overflow: hidden; max-height: calc(100vh - 120px); overflow-y: auto;
}
</style>
