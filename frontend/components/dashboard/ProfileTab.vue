<template>
  <ClientOnly>
    <CropAvatarModal
      :file="avatarCropFile"
      :saving="avatarUploading"
      @save="onAvatarCropSave"
      @cancel="avatarCropFile = null"
    />
  </ClientOnly>

  <div v-if="profile.profile" class="studio-shell">
    <section class="studio-preview-pane" aria-label="Живое превью профиля">
      <Suspense>
        <PublicProfilePage
          :profile-override="editorPreviewProfile"
          :avatar-src-override="avatarDisplaySrc"
          :active-block-id="editingBlockId"
          embedded
          editable
          @edit-block="openBlockEditor"
        />
      </Suspense>

    </section>

    <aside ref="inspectorEl" class="studio-inspector" aria-label="Инспектор профиля">
      <div class="studio-preview-bar">
        <div class="studio-status" aria-label="Сводка профиля">
          <span class="status-pill" :class="{ published: profile.isPublished }">
            <i aria-hidden="true" :class="profile.isPublished ? 'ri-broadcast-line' : 'ri-draft-line'" />
            {{ profile.isPublished ? 'Опубликован' : 'Черновик' }}
          </span>
          <span class="count-pill" title="Видимые блоки">
            <i aria-hidden="true" class="ri-stack-line" />
            {{ visibleBlocksCount }} / {{ blocks.length }}
          </span>
          <span class="url-pill">{{ publicUrlLabel }}</span>
        </div>

        <div class="studio-quick-actions">
          <button class="icon-action publish-action" type="button" :title="profile.isPublished ? 'Снять с публикации' : 'Опубликовать'" @click="toggleStatus">
            <i aria-hidden="true" :class="profile.isPublished ? 'ri-eye-off-line' : 'ri-rocket-line'" />
            <span>{{ profile.isPublished ? 'Снять' : 'Опубликовать' }}</span>
          </button>
          <a class="icon-action" :href="publicPath" target="_blank" rel="noopener noreferrer" title="Открыть профиль">
            <i aria-hidden="true" class="ri-external-link-line" />
            <span>Открыть</span>
          </a>
          <button class="icon-action" type="button" title="Скопировать ссылку" @click="copyLink">
            <i aria-hidden="true" class="ri-file-copy-line" />
            <span>Копировать</span>
          </button>
        </div>
      </div>

      <div class="inspector-tabs">
        <button class="inspector-tab" :class="{ active: panel === 'profile' && !editingBlockId }" type="button" @click="openPanel('profile')">
          <i aria-hidden="true" class="ri-user-settings-line" />
          <span>Профиль</span>
        </button>
        <button class="inspector-tab" :class="{ active: panel === 'blocks' || Boolean(editingBlockId) }" type="button" @click="openPanel('blocks')">
          <i aria-hidden="true" class="ri-layout-grid-line" />
          <span>Блоки</span>
        </button>
      </div>

      <div v-if="blocks.length" class="block-rail" aria-label="Быстрый выбор блоков">
        <button
          v-for="block in draggableBlocks"
          :key="`rail-${block.id}`"
          class="block-rail-item"
          :class="{ active: editingBlockId === block.id, hidden: !block.is_visible }"
          type="button"
          :title="displayBlockLabel(block)"
          :aria-label="`Открыть блок ${displayBlockLabel(block)}`"
          @click="openBlockEditor(block)"
        >
          <FaceitLogo v-if="block.block_type === 'widget_faceit'" class="faceit-logo" />
          <i v-else aria-hidden="true" :class="displayBlockIcon(block)" />
        </button>
      </div>

      <div class="inspector-body">
        <Transition name="inspector-pane" mode="out-in">
          <section v-if="panel === 'profile' && !editingBlockId" key="profile" class="inspector-section">
            <div class="section-head compact">
              <span class="section-icon"><i aria-hidden="true" class="ri-user-smile-line" /></span>
              <div>
                <h3>Профиль</h3>
              </div>
            </div>

            <div class="form-grid">
              <label class="studio-field">
                <span>Имя или ник</span>
                <input v-model="editName" type="text" placeholder="Alex K." autocomplete="off">
              </label>

              <label class="studio-field">
                <span>Адрес страницы</span>
                <div class="slug-input">
                  <span>{{ requestHost }}/</span>
                  <input v-model="editSlug" type="text" placeholder="username" autocomplete="off">
                </div>
              </label>

              <label class="studio-field wide">
                <span>Био</span>
                <textarea v-model="editBio" rows="4" placeholder="Коротко о себе" />
              </label>

              <label class="studio-field wide">
                <span>Теги</span>
                <input v-model="editTagsRaw" type="text" placeholder="design, games, music">
              </label>
            </div>

            <div class="form-actions">
              <button class="ghost-btn" type="button" :disabled="!profileHasChanges" @click="initProfileForm">Сбросить</button>
              <button class="filled-btn" type="button" :disabled="headerSaving || !profileHasChanges" @click="saveProfile">
                <span v-if="headerSaving" class="studio-spinner" />
                <span v-else>Сохранить</span>
              </button>
            </div>

            <div class="divider" />

            <div class="section-subhead">
              <strong>Тема</strong>
            </div>
            <div class="theme-grid">
              <button
                v-for="theme in THEME_LIBRARY"
                :key="theme.id"
                class="theme-option"
                :class="{ active: currentTheme === theme.id }"
                type="button"
                @click="setTheme(theme.id)"
              >
                <span class="theme-swatch" :class="`theme-${theme.id}`" :style="theme.id === 'material3' ? { '--profile-accent': currentAccent } : undefined" />
                <span>
                  <strong>{{ theme.label }}</strong>
                  <small>{{ theme.sub }}</small>
                </span>
              </button>
            </div>

            <div class="section-subhead">
              <strong>Тон темы</strong>
            </div>
            <button
              class="switch-setting"
              type="button"
              role="switch"
              :aria-checked="currentColorMode === 'dark'"
              @click="setColorMode(currentColorMode === 'dark' ? 'light' : 'dark')"
            >
              <span class="switch-setting-copy">
                <strong>{{ currentColorMode === 'dark' ? 'Темная' : 'Светлая' }}</strong>
                <small>{{ currentColorMode === 'dark' ? 'Глубокие поверхности и мягкий контраст.' : 'Чистые поверхности и спокойный контраст.' }}</small>
              </span>
              <span class="custom-switch" :class="{ active: currentColorMode === 'dark' }" aria-hidden="true">
                <span><i aria-hidden="true" :class="currentColorMode === 'dark' ? 'ri-moon-clear-line' : 'ri-sun-line'" /></span>
              </span>
            </button>

            <div v-if="currentTheme === 'material3'" class="material3-theme-controls">
              <div class="section-subhead">
                <strong>Акцент Material 3</strong>
              </div>
              <div class="accent-row">
                <button
                  v-for="color in ACCENT_COLORS"
                  :key="color.value"
                  class="accent-dot"
                  :class="{ active: currentAccent === color.value }"
                  :style="{ background: color.value }"
                  :title="color.label"
                  type="button"
                  @click="setAccent(color.value)"
                />
                <label class="accent-dot custom" title="Свой цвет">
                  <i aria-hidden="true" class="ri-add-line" />
                  <input type="color" :value="currentAccent" hidden @input="setAccent(($event.target as HTMLInputElement).value)">
                </label>
              </div>

              <div class="section-subhead">
                <strong>Формат Material 3</strong>
              </div>
              <button
                class="switch-setting"
                type="button"
                role="switch"
                :aria-checked="isMaterial3Wide"
                @click="setMaterial3Wide(!isMaterial3Wide)"
              >
                <span class="switch-setting-copy">
                  <strong>{{ isMaterial3Wide ? 'Широкий' : 'Компактный' }}</strong>
                  <small>{{ isMaterial3Wide ? 'Профиль раскрывается в две колонки.' : 'Классический вертикальный профиль.' }}</small>
                </span>
                <span class="custom-switch wide-switch" :class="{ active: isMaterial3Wide }" aria-hidden="true">
                  <span><i aria-hidden="true" :class="isMaterial3Wide ? 'ri-layout-column-line' : 'ri-smartphone-line'" /></span>
                </span>
              </button>
            </div>
          </section>

          <section v-else-if="panel === 'blocks' && !editingBlockId" key="blocks" class="inspector-section">
            <div class="section-head compact block-manager-head">
              <span class="section-icon"><i aria-hidden="true" class="ri-stack-line" /></span>
              <div>
                <h3>Блоки</h3>
                <p>{{ visibleBlocksCount }} из {{ blocks.length }} видны</p>
              </div>
            </div>

            <div v-if="blocks.length" class="mini-block-list">
              <ClientOnly>
                <VueDraggable
                  v-model="draggableBlocks"
                  class="mini-drag"
                  handle=".mini-handle"
                  :animation="220"
                  ghost-class="mini-ghost"
                  @end="onDragEnd"
                >
                  <article
                    v-for="block in draggableBlocks"
                    :key="block.id"
                    class="mini-block"
                    :class="{ hidden: !block.is_visible }"
                    role="button"
                    tabindex="0"
                    @click="openBlockEditor(block)"
                    @keydown.enter.self.prevent="openBlockEditor(block)"
                    @keydown.space.self.prevent="openBlockEditor(block)"
                  >
                    <button
                      class="mini-handle"
                      type="button"
                      aria-roledescription="draggable"
                      :aria-label="dragHandleLabel(block)"
                      title="Перетащить"
                      @click.stop
                      @keydown.up.prevent.stop="moveBlockByKeyboard(block, -1)"
                      @keydown.down.prevent.stop="moveBlockByKeyboard(block, 1)"
                      @keydown.enter.prevent.stop="openBlockEditor(block)"
                      @keydown.space.prevent.stop="openBlockEditor(block)"
                    >
                      <i aria-hidden="true" class="ri-draggable" />
                    </button>
                    <span class="mini-icon">
                      <FaceitLogo v-if="block.block_type === 'widget_faceit'" class="faceit-logo" />
                      <i aria-hidden="true" v-else :class="displayBlockIcon(block)" />
                    </span>
                    <span class="mini-copy">
                      <span class="mini-label">{{ displayBlockLabel(block) }}</span>
                      <span class="mini-meta" :class="{ hidden: !block.is_visible }">
                        {{ block.is_visible ? 'Виден' : 'Скрыт' }}
                      </span>
                    </span>
                    <span class="mini-actions">
                      <button class="tiny-action" :class="{ active: block.is_visible }" type="button" :title="visibilityToggleLabel(block)" :aria-label="visibilityToggleLabel(block)" :aria-pressed="block.is_visible" :disabled="visibilitySavingBlockId === block.id" @click.stop="toggleVisible(block)">
                        <i aria-hidden="true" :class="block.is_visible ? 'ri-eye-line' : 'ri-eye-off-line'" />
                      </button>
                      <button class="tiny-action danger" type="button" :aria-label="deleteBlockLabel(block)" title="Удалить" :disabled="deletingBlockId === block.id" @click.stop="deleteBlock(block.id)">
                        <i aria-hidden="true" class="ri-delete-bin-line" />
                      </button>
                    </span>
                  </article>
                </VueDraggable>
              </ClientOnly>
            </div>

            <p v-else class="muted-panel">Профиль пока пуст.</p>

            <div class="section-subhead">
              <strong>Добавить</strong>
            </div>
            <div class="library-grid">
              <button v-for="item in BLOCK_LIBRARY" :key="item.type" class="library-item" type="button" @click="addBlock(item.type)">
                <span class="library-item-icon">
                  <FaceitLogo v-if="item.type === 'widget_faceit'" class="faceit-logo" />
                  <i aria-hidden="true" v-else :class="item.icon" />
                </span>
                <span>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.description }}</small>
                </span>
              </button>
            </div>
          </section>

          <section v-else-if="activeBlock" :key="`edit-${activeBlock.id}`" class="inspector-section">
            <div class="selected-block-head">
              <div class="section-head">
                <button class="back-btn" type="button" title="Назад" @click="closeBlockEditor">
                  <i aria-hidden="true" class="ri-arrow-left-line" />
                </button>
                <span class="section-icon">
                  <FaceitLogo v-if="activeBlock.block_type === 'widget_faceit'" class="faceit-logo" />
                  <i aria-hidden="true" v-else :class="displayBlockIcon(activeBlock)" />
                </span>
                <div>
                  <h3>{{ displayBlockLabel(activeBlock) }}</h3>
                  <p>{{ displayBlockDescription(activeBlock) }}</p>
                </div>
              </div>
              <span class="block-status-pill" :class="{ hidden: !activeBlock.is_visible }">
                <i aria-hidden="true" :class="activeBlock.is_visible ? 'ri-eye-line' : 'ri-eye-off-line'" />
                {{ activeBlock.is_visible ? 'Виден' : 'Скрыт' }}
              </span>
            </div>

            <div class="selected-block-actions">
              <button
                class="block-action-card"
                type="button"
                :aria-pressed="activeBlock.is_visible"
                :disabled="visibilitySavingBlockId === activeBlock.id || blockSaving"
                @click="toggleVisible(activeBlock)"
              >
                <span class="block-action-icon">
                  <i aria-hidden="true" :class="activeBlock.is_visible ? 'ri-eye-off-line' : 'ri-eye-line'" />
                </span>
                <span>
                  <strong>{{ activeBlock.is_visible ? 'Скрыть блок' : 'Показать блок' }}</strong>
                  <small>{{ activeBlock.is_visible ? 'Убрать из публичного профиля' : 'Вернуть в публичный профиль' }}</small>
                </span>
              </button>

              <button
                class="block-action-card danger"
                type="button"
                :disabled="deletingBlockId === activeBlock.id || blockSaving"
                @click="deleteActiveBlock"
              >
                <span class="block-action-icon">
                  <i aria-hidden="true" class="ri-delete-bin-line" />
                </span>
                <span>
                  <strong>Удалить блок</strong>
                  <small>Удаление после подтверждения</small>
                </span>
              </button>
            </div>

            <DashboardBlockForm :type="activeBlock.block_type" :config="blockDraft" />

            <div class="form-actions sticky">
              <button class="ghost-btn" type="button" @click="closeBlockEditor">Отмена</button>
              <button class="filled-btn" type="button" :disabled="blockSaving" @click="saveBlock">
                <span v-if="blockSaving" class="studio-spinner" />
                <span v-else>Сохранить блок</span>
              </button>
            </div>
          </section>
        </Transition>
      </div>
    </aside>
  </div>

  <Teleport to="body">
    <Transition name="git-provider-modal">
      <div v-if="gitProviderModalOpen" class="git-provider-overlay" @click.self="closeGitProviderModal">
        <section class="git-provider-modal" role="dialog" aria-modal="true" aria-labelledby="git-provider-title">
          <button class="git-provider-close" type="button" aria-label="Закрыть" @click="closeGitProviderModal">
            <i aria-hidden="true" class="ri-close-line" />
          </button>

          <div class="git-provider-head">
            <span class="git-provider-head-icon"><i aria-hidden="true" class="ri-git-branch-line" /></span>
            <h2 id="git-provider-title">Git</h2>
            <p>Выберите интеграцию для блока профиля.</p>
          </div>

          <div class="git-provider-grid">
            <button
              v-for="provider in GIT_PROVIDER_CHOICES"
              :key="provider.value"
              class="git-provider-choice"
              type="button"
              :disabled="gitBlockAdding"
              @click="createGitBlock(provider.value)"
            >
              <span><i aria-hidden="true" :class="provider.icon" /></span>
              <strong>{{ provider.label }}</strong>
              <small>{{ provider.description }}</small>
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>

  <Teleport to="body">
    <Transition name="git-provider-modal">
      <div v-if="confirmDialog" class="git-provider-overlay" @click.self="resolveConfirm(false)">
        <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
          <div class="confirm-dialog-icon" :class="{ danger: confirmDialog.tone === 'danger' }">
            <i aria-hidden="true" :class="confirmDialog.icon" />
          </div>
          <div class="confirm-dialog-copy">
            <h2 id="confirm-dialog-title">{{ confirmDialog.title }}</h2>
            <p>{{ confirmDialog.message }}</p>
          </div>
          <div class="confirm-dialog-actions">
            <button class="ghost-btn" type="button" @click="resolveConfirm(false)">
              {{ confirmDialog.cancelText }}
            </button>
            <button class="filled-btn" :class="{ danger: confirmDialog.tone === 'danger' }" type="button" @click="resolveConfirm(true)">
              {{ confirmDialog.confirmText }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRequestURL } from '#app'
import { VueDraggable } from 'vue-draggable-plus'
import { resolveAvatarUrl } from '~/composables/useAvatarUrl'
import { useAuthStore } from '~/stores/auth'
import { useProfileStore, type Block } from '~/stores/profile'
import { extractAuthError } from '~/utils/auth-feedback'
import PublicProfilePage from '~/pages/[slug].vue'
import {
  ACCENT_COLORS,
  BLOCK_LIBRARY,
  THEME_LIBRARY,
  blockDescription,
  blockIcon,
  blockLabel,
  createDefaultBlockConfig,
  type DashboardThemeId,
} from '~/utils/dashboard-studio'

type NoticeTone = 'success' | 'info' | 'error'
type ConfirmTone = 'default' | 'danger'
type Panel = 'profile' | 'blocks'
type ThemeColorMode = 'light' | 'dark'
type Material3Layout = 'compact' | 'wide'
type GitProvider = 'github' | 'gitlab' | 'gitea'

interface ConfirmDialogState {
  title: string
  message: string
  confirmText: string
  cancelText: string
  icon: string
  tone: ConfirmTone
  resolve: (confirmed: boolean) => void
}

interface ProfileThemeTokens {
  colorMode?: ThemeColorMode
  material3Layout?: Material3Layout
  [key: string]: unknown
}

const profile = useProfileStore()
const auth = useAuthStore()
const config = useRuntimeConfig()
const request = useRequestURL()
const requestHost = request.host
const requestOrigin = request.origin
const { pushToast } = useAppToast()

const GIT_PROVIDER_CHOICES: Array<{
  value: GitProvider
  label: string
  icon: string
  description: string
}> = [
  {
    value: 'github',
    label: 'GitHub',
    icon: 'ri-github-fill',
    description: 'Pinned repositories и статистика GitHub.',
  },
  {
    value: 'gitlab',
    label: 'GitLab',
    icon: 'ri-gitlab-fill',
    description: 'Проекты, звезды и активность GitLab.',
  },
  {
    value: 'gitea',
    label: 'Gitea',
    icon: 'ri-git-repository-line',
    description: 'Репозитории и активность Gitea.',
  },
]
const DUPLICATE_WARN_BLOCK_TYPES = new Set(['widget_steam', 'widget_faceit', 'widget_spotify', 'widget_lastfm', 'widget_github'])
const LIVE_PREVIEW_CONFIG_KEYS = [
  'steam_profile',
  'steam_recent_games',
  'steam_profile_stats',
  'steam_inventory_highlight',
  'faceit_profile',
  'spotify_profile',
  'spotify_playback',
  'spotify_recent_tracks',
  'spotify_top_tracks',
  'spotify_top_artists',
  'spotify_stats',
  'git_profile',
  'git_repository_stats',
  'git_pinned_repositories',
  'git_contributions',
]

const panel = ref<Panel>('profile')
const inspectorEl = ref<HTMLElement | null>(null)
const editingBlockId = ref<string | null>(null)
const gitProviderModalOpen = ref(false)
const gitBlockAdding = ref(false)
const confirmDialog = ref<ConfirmDialogState | null>(null)

const avatarTimestamp = ref(Date.now())
const avatarCropFile = ref<File | null>(null)
const avatarUploading = ref(false)
const avatarDisplaySrc = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarTimestamp.value),
)

const headerSaving = ref(false)
const blockSaving = ref(false)
const visibilitySavingBlockId = ref<string | null>(null)
const deletingBlockId = ref<string | null>(null)
const editName = ref('')
const editSlug = ref('')
const editBio = ref('')
const editTagsRaw = ref('')
const blockDraft = reactive<Record<string, unknown>>({})

const blocks = computed(() => profile.profile?.blocks ?? [])
const visibleBlocksCount = computed(() => blocks.value.filter(block => block.is_visible).length)
const draggableBlocks = ref<Block[]>([])

watch(blocks, (value) => {
  draggableBlocks.value = [...value]
  if (editingBlockId.value && !value.some(block => block.id === editingBlockId.value)) {
    editingBlockId.value = null
  }
}, { immediate: true })

watch(() => auth.user?.avatar_url, () => {
  avatarTimestamp.value = Date.now()
})

const activeBlock = computed(() =>
  editingBlockId.value ? blocks.value.find(block => block.id === editingBlockId.value) ?? null : null,
)

const currentTheme = computed<DashboardThemeId>(() => {
  const preset = profile.profile?.theme_preset
  return preset === 'glass' || preset === 'fluent' ? preset : 'material3'
})
const currentAccent = computed(() => profile.profile?.accent_color || '#345EA8')
const themeTokens = computed<ProfileThemeTokens>(() => {
  const tokens = profile.profile?.theme_tokens
  return tokens && typeof tokens === 'object' ? tokens as ProfileThemeTokens : {}
})
const currentColorMode = computed<ThemeColorMode>(() => {
  const mode = themeTokens.value.colorMode
  if (mode === 'light' || mode === 'dark') return mode
  return currentTheme.value === 'material3' ? 'light' : 'dark'
})
const isMaterial3Wide = computed(() =>
  currentTheme.value === 'material3' && themeTokens.value.material3Layout === 'wide',
)
const publicPath = computed(() => profile.profile ? `/${profile.profile.slug}` : '/')
const publicUrl = computed(() => new URL(publicPath.value, requestOrigin).toString())
const publicUrlLabel = computed(() => profile.profile ? `${requestHost}/${profile.profile.slug}` : requestHost)
const editorPreviewProfile = computed(() => {
  if (!profile.profile) return null
  const liveBlocks = draggableBlocks.value.map(block => ({
    ...block,
    config: editingBlockId.value === block.id ? cloneConfig(previewConfig(block)) : cloneConfig(block.config),
  }))
  return {
    ...profile.profile,
    display_name: editName.value.trim() || profile.profile.display_name,
    bio: editBio.value.trim() || null,
    tags: parseTags(),
    blocks: liveBlocks,
  }
})
const profileHasChanges = computed(() => {
  if (!profile.profile) return false
  return editName.value !== profile.profile.display_name
    || normalizeSlug(editSlug.value) !== profile.profile.slug
    || editBio.value !== (profile.profile.bio ?? '')
    || JSON.stringify(parseTags()) !== JSON.stringify(profile.profile.tags)
})

if (profile.profile) initProfileForm()

function cloneConfig<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function clearObject(target: Record<string, unknown>) {
  Object.keys(target).forEach(key => delete target[key])
}

function setNotice(message: string, tone: NoticeTone = 'info') {
  pushToast(message, tone)
}

function normalizeSlug(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9_-]/g, '').slice(0, 50)
}

function parseTags() {
  return editTagsRaw.value.split(',').map(tag => tag.trim()).filter(Boolean)
}

function initProfileForm() {
  if (!profile.profile) return
  editName.value = profile.profile.display_name
  editSlug.value = profile.profile.slug
  editBio.value = profile.profile.bio ?? ''
  editTagsRaw.value = profile.profile.tags.join(', ')
}

function blockHasChanges() {
  if (!activeBlock.value) return false
  return JSON.stringify(blockDraft) !== JSON.stringify(activeBlock.value.config)
}

function requestConfirm(options: {
  title: string
  message: string
  confirmText: string
  cancelText?: string
  icon?: string
  tone?: ConfirmTone
}): Promise<boolean> {
  return new Promise((resolve) => {
    confirmDialog.value = {
      title: options.title,
      message: options.message,
      confirmText: options.confirmText,
      cancelText: options.cancelText ?? 'Отмена',
      icon: options.icon ?? 'ri-question-line',
      tone: options.tone ?? 'default',
      resolve,
    }
  })
}

function resolveConfirm(confirmed: boolean) {
  const dialog = confirmDialog.value
  if (!dialog) return
  confirmDialog.value = null
  dialog.resolve(confirmed)
}

async function confirmBlockSwitch() {
  if (!editingBlockId.value || !blockHasChanges()) return true
  return requestConfirm({
    title: 'Закрыть редактор блока?',
    message: 'Есть несохраненные изменения. Если закрыть редактор, они будут потеряны.',
    confirmText: 'Закрыть',
    icon: 'ri-error-warning-line',
  })
}

async function openPanel(next: Panel) {
  if (!await confirmBlockSwitch()) return
  editingBlockId.value = null
  panel.value = next
  if (next === 'profile') initProfileForm()
}

async function openBlockEditor(block: Block) {
  if (editingBlockId.value === block.id) return
  if (!await confirmBlockSwitch()) return
  clearObject(blockDraft)
  Object.assign(blockDraft, cloneConfig(block.config))
  editingBlockId.value = block.id
  panel.value = 'blocks'
  await nextTick()
  inspectorEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function closeBlockEditor() {
  if (!await confirmBlockSwitch()) return
  editingBlockId.value = null
}

function previewConfig(block: Block) {
  if (editingBlockId.value !== block.id) return block.config
  const merged = { ...blockDraft }
  for (const key of LIVE_PREVIEW_CONFIG_KEYS) {
    if (key in block.config) merged[key] = block.config[key]
  }
  return merged
}

function gitProviderLabel(value: Record<string, unknown>): string {
  const provider = String(value.git_provider || value.provider || 'github')
  return String(value.git_provider_label || ({ github: 'GitHub', gitlab: 'GitLab', gitea: 'Gitea' } as Record<string, string>)[provider] || 'Git')
}

function gitProviderIcon(value: Record<string, unknown>): string {
  const provider = String(value.git_provider || value.provider || 'github')
  return ({ github: 'ri-github-fill', gitlab: 'ri-gitlab-fill', gitea: 'ri-git-repository-line' } as Record<string, string>)[provider] || 'ri-git-repository-line'
}

function gitProviderChoiceLabel(provider: GitProvider): string {
  return GIT_PROVIDER_CHOICES.find(item => item.value === provider)?.label ?? 'Git'
}

function blockGitProvider(block: Block): GitProvider {
  const provider = String(block.config.provider || block.config.git_provider || 'github')
  return ['github', 'gitlab', 'gitea'].includes(provider) ? provider as GitProvider : 'github'
}

function displayBlockLabel(block: Block): string {
  return block.block_type === 'widget_github' ? gitProviderLabel(block.config) : blockLabel(block.block_type)
}

function displayBlockIcon(block: Block): string {
  return block.block_type === 'widget_github' ? gitProviderIcon(block.config) : blockIcon(block.block_type)
}

function displayBlockDescription(block: Block): string {
  if (block.block_type === 'widget_github') {
    return `${gitProviderLabel(block.config)}: профиль, статистика и репозитории.`
  }
  return blockDescription(block.block_type)
}

function dragHandleLabel(block: Block): string {
  return `Переместить блок ${displayBlockLabel(block)}`
}

function visibilityToggleLabel(block: Block): string {
  return block.is_visible ? 'Скрыть блок' : 'Показать блок'
}

function deleteBlockLabel(block: Block): string {
  return `Удалить блок ${displayBlockLabel(block)}`
}

async function saveProfile() {
  if (!profile.profile) return
  headerSaving.value = true
  try {
    await profile.update({
      display_name: editName.value.trim() || profile.profile.display_name,
      slug: normalizeSlug(editSlug.value) || profile.profile.slug,
      bio: editBio.value.trim() || null,
      tags: parseTags(),
    })
    initProfileForm()
    setNotice('Профиль обновлен.', 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось сохранить профиль.'), 'error')
  } finally {
    headerSaving.value = false
  }
}

async function saveBlock() {
  if (!activeBlock.value) return
  blockSaving.value = true
  try {
    await profile.updateBlock(activeBlock.value.id, { config: cloneConfig(blockDraft) })
    editingBlockId.value = null
    setNotice('Блок сохранен.', 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось сохранить блок.'), 'error')
  } finally {
    blockSaving.value = false
  }
}

async function addBlock(type: string) {
  if (type === 'widget_github') {
    gitProviderModalOpen.value = true
    return
  }

  if (DUPLICATE_WARN_BLOCK_TYPES.has(type) && profile.profile?.blocks.some(block => block.block_type === type)) {
    const confirmed = await requestConfirm({
      title: 'Добавить второй блок?',
      message: `В профиле уже есть блок "${blockLabel(type)}". Повтор может выглядеть как дубль на публичной странице.`,
      confirmText: 'Добавить',
      icon: 'ri-file-copy-line',
    })
    if (!confirmed) return
  }

  try {
    const block = await profile.createBlock(type, createDefaultBlockConfig(type))
    clearObject(blockDraft)
    Object.assign(blockDraft, cloneConfig(block.config))
    editingBlockId.value = block.id
    panel.value = 'blocks'
    setNotice(`Блок "${blockLabel(type)}" добавлен.`, 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось добавить блок.'), 'error')
  }
}

function closeGitProviderModal() {
  if (gitBlockAdding.value) return
  gitProviderModalOpen.value = false
}

async function createGitBlock(provider: GitProvider) {
  if (profile.profile?.blocks.some(block => block.block_type === 'widget_github' && blockGitProvider(block) === provider)) {
    const confirmed = await requestConfirm({
      title: 'Добавить второй Git-блок?',
      message: `В профиле уже есть блок "${gitProviderChoiceLabel(provider)}". Повтор может выглядеть как дубль на публичной странице.`,
      confirmText: 'Добавить',
      icon: 'ri-file-copy-line',
    })
    if (!confirmed) {
      gitProviderModalOpen.value = false
      return
    }
  }

  gitBlockAdding.value = true
  try {
    const blockConfig = {
      ...createDefaultBlockConfig('widget_github'),
      provider,
    }
    const block = await profile.createBlock('widget_github', blockConfig)
    clearObject(blockDraft)
    Object.assign(blockDraft, cloneConfig(block.config))
    editingBlockId.value = block.id
    panel.value = 'blocks'
    gitProviderModalOpen.value = false
    setNotice(`Блок "${gitProviderChoiceLabel(provider)}" добавлен.`, 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось добавить Git-блок.'), 'error')
  } finally {
    gitBlockAdding.value = false
  }
}

async function deleteBlock(id: string) {
  const target = blocks.value.find(block => block.id === id)
  const confirmed = await requestConfirm({
    title: 'Удалить блок?',
    message: target
      ? `Блок "${displayBlockLabel(target)}" пропадет из редактора и публичного профиля. Это действие нельзя отменить.`
      : 'Блок пропадет из редактора и публичного профиля. Это действие нельзя отменить.',
    confirmText: 'Удалить',
    icon: 'ri-delete-bin-line',
    tone: 'danger',
  })
  if (!confirmed) return
  const wasEditing = editingBlockId.value === id
  deletingBlockId.value = id
  try {
    await profile.deleteBlock(id)
    if (wasEditing) {
      editingBlockId.value = null
      clearObject(blockDraft)
    }
    setNotice('Блок удален.', 'info')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось удалить блок.'), 'error')
  } finally {
    if (deletingBlockId.value === id) deletingBlockId.value = null
  }
}

async function deleteActiveBlock() {
  if (!activeBlock.value) return
  await deleteBlock(activeBlock.value.id)
}

async function toggleVisible(block: Block) {
  const nextVisible = !block.is_visible
  visibilitySavingBlockId.value = block.id
  try {
    await profile.updateBlock(block.id, { is_visible: nextVisible })
    setNotice(nextVisible ? 'Блок показан.' : 'Блок скрыт.', 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить видимость.'), 'error')
  } finally {
    if (visibilitySavingBlockId.value === block.id) visibilitySavingBlockId.value = null
  }
}

async function onDragEnd() {
  const ids = draggableBlocks.value.map(block => block.id)
  try {
    await profile.reorder(ids)
  } catch (error) {
    draggableBlocks.value = [...blocks.value]
    setNotice(extractAuthError(error, 'Не удалось изменить порядок.'), 'error')
  }
}

async function moveBlockByKeyboard(block: Block, delta: number) {
  const currentIndex = draggableBlocks.value.findIndex(item => item.id === block.id)
  if (currentIndex === -1) return
  const nextIndex = currentIndex + delta
  if (nextIndex < 0 || nextIndex >= draggableBlocks.value.length) return

  const nextBlocks = [...draggableBlocks.value]
  const [moved] = nextBlocks.splice(currentIndex, 1)
  nextBlocks.splice(nextIndex, 0, moved)
  draggableBlocks.value = nextBlocks

  try {
    await profile.reorder(nextBlocks.map(item => item.id))
  } catch (error) {
    draggableBlocks.value = [...blocks.value]
    setNotice(extractAuthError(error, 'Не удалось изменить порядок.'), 'error')
  }
}

async function toggleStatus() {
  const willPublish = !profile.isPublished
  try {
    await profile.update({ status: willPublish ? 'published' : 'draft' })
    setNotice(willPublish ? 'Профиль опубликован.' : 'Профиль переведен в черновик.', 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить статус.'), 'error')
  }
}

async function setTheme(id: DashboardThemeId) {
  try {
    await profile.update({ theme_preset: id })
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить тему.'), 'error')
  }
}

function mergeThemeTokens(patch: Partial<ProfileThemeTokens>): ProfileThemeTokens {
  return { ...themeTokens.value, ...patch }
}

async function setColorMode(mode: ThemeColorMode) {
  try {
    await profile.update({ theme_tokens: mergeThemeTokens({ colorMode: mode }) })
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить тон темы.'), 'error')
  }
}

async function setMaterial3Wide(enabled: boolean) {
  if (currentTheme.value !== 'material3') return
  try {
    await profile.update({ theme_tokens: mergeThemeTokens({ material3Layout: enabled ? 'wide' : 'compact' }) })
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить формат профиля.'), 'error')
  }
}

async function setAccent(color: string) {
  if (currentTheme.value !== 'material3') return
  try {
    await profile.update({ accent_color: color })
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить акцент.'), 'error')
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(publicUrl.value)
    setNotice('Ссылка скопирована.', 'success')
  } catch {
    setNotice('Не удалось скопировать ссылку.', 'error')
  }
}

function onAvatarFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  avatarCropFile.value = file
}

async function onAvatarCropSave(blob: Blob) {
  avatarCropFile.value = null
  avatarUploading.value = true
  try {
    await auth.uploadAvatar(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    avatarTimestamp.value = Date.now()
    setNotice('Аватар обновлен.', 'success')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось обновить аватар.'), 'error')
  } finally {
    avatarUploading.value = false
  }
}

</script>

<style scoped>
.studio-shell {
  display: grid;
  width: 100%;
  min-width: 0;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
  gap: 18px;
  align-items: start;
  position: relative;
}

.studio-shell,
.studio-shell * {
  box-sizing: border-box;
}

.studio-preview-pane,
.studio-inspector {
  min-width: 0;
}

.studio-preview-pane {
  display: grid;
  gap: 12px;
}

.studio-preview-bar,
.studio-inspector {
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--surface, #fff) 88%, transparent);
  box-shadow: var(--shadow-soft, 0 16px 42px rgba(48, 63, 92, 0.11));
}

.studio-preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
}

.studio-status,
.studio-quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.status-pill,
.url-pill,
.soft-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.status-pill {
  background: var(--warning-container, #FFF0CF);
  color: var(--warning, #9B6200);
}

.status-pill.published {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.url-pill {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
}

.icon-action,
.tiny-action,
.inspector-tab,
.filled-btn,
.ghost-btn,
.theme-option,
.accent-dot,
.library-item,
.mini-block,
.empty-add,
.back-btn,
.avatar-upload {
  position: relative;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  background: var(--surface, #fff);
  color: var(--text-2, #475778);
  font: inherit;
  cursor: pointer;
  overflow: hidden;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    color 180ms cubic-bezier(0.2, 0, 0, 1),
    box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.icon-action {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  text-decoration: none;
  font-size: 17px;
}

.public-card {
  --card-bg: #171A22;
  --card-text: #F8FAFC;
  --card-muted: rgba(248, 250, 252, 0.68);
  --card-panel: rgba(255, 255, 255, 0.07);
  --card-line: rgba(255, 255, 255, 0.12);
  display: grid;
  gap: 12px;
  padding: 18px;
  background:
    linear-gradient(160deg, rgba(255,255,255,0.12), transparent 38%),
    var(--card-bg);
  color: var(--card-text);
}

.public-card.theme-material3 {
  --card-bg: linear-gradient(145deg, color-mix(in srgb, var(--profile-accent) 24%, #111827), #11151E 62%, #171A22);
}

.public-card.theme-material3 .public-avatar {
  width: 82px;
  height: 82px;
  border-radius: 28px 28px 22px 28px;
  font-size: 30px;
}

.public-card.theme-glass {
  --card-bg: linear-gradient(145deg, rgba(25, 31, 42, 0.86), rgba(13, 18, 28, 0.94));
  --card-panel: rgba(255, 255, 255, 0.1);
}

.public-card.theme-fluent {
  --card-bg: linear-gradient(145deg, #15171D, #0F1117);
  --card-panel: rgba(255, 255, 255, 0.055);
}

.public-card[data-color-mode="light"] {
  --card-bg: #fffbff;
  --card-text: #1d1b20;
  --card-muted: #5f5a66;
  --card-panel: color-mix(in srgb, var(--profile-accent, #345EA8) 9%, #ffffff);
  --card-line: rgba(73, 69, 79, 0.16);
}

.public-card.theme-material3[data-color-mode="light"] {
  --card-bg: linear-gradient(145deg, color-mix(in srgb, var(--profile-accent) 18%, #fffbff), #ffffff 64%, #f7f2fa);
}

.public-card.theme-glass[data-color-mode="light"] {
  --card-bg: linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(236, 244, 255, 0.9));
  --card-panel: rgba(255, 255, 255, 0.7);
}

.public-card.theme-fluent[data-color-mode="light"] {
  --card-bg: linear-gradient(145deg, #fafafa, #f3f6fb);
  --card-panel: rgba(255, 255, 255, 0.76);
}

.public-card[data-color-mode="light"] .bio {
  color: #49454f;
}

.public-card[data-color-mode="light"] .preview-note {
  color: #625b71;
}

.public-card[data-color-mode="light"] .tag-row span,
.public-card[data-color-mode="light"] .repo-row span,
.public-card[data-color-mode="light"] .tiny-action {
  color: #49454f;
}

.public-card.theme-material3.layout-wide {
  width: min(100%, 980px);
  grid-template-columns: minmax(220px, 300px) minmax(0, 1fr);
  align-items: start;
}

.public-card.theme-material3.layout-wide .public-header {
  position: sticky;
  top: 0;
  flex-direction: column;
  padding: 14px;
  border: 1px solid var(--card-line);
  border-radius: 22px;
  background: var(--card-panel);
}

.public-card.theme-material3.layout-wide .public-copy h2 {
  font-size: clamp(32px, 3.6vw, 52px);
}

.public-card.theme-material3.layout-wide .bio {
  max-width: 100%;
}

.public-card.theme-material3.layout-wide .public-blocks {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: start;
}

.public-card.theme-material3.layout-wide .public-block:first-child {
  grid-column: 1 / -1;
}

.public-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 8px 4px 12px;
}

.avatar-wrap {
  position: relative;
  flex: 0 0 auto;
}

.public-avatar {
  width: 96px;
  height: 96px;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--card-line);
  border-radius: 8px;
  background: linear-gradient(135deg, var(--profile-accent), #F59E0B);
  color: #fff;
  font-size: 38px;
  font-weight: 900;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-upload {
  position: absolute;
  right: -8px;
  bottom: -8px;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: color-mix(in srgb, var(--profile-accent) 86%, #fff);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.28);
}

.public-copy {
  min-width: 0;
}

.eyebrow,
.group-title,
.widget-head p,
.section-subhead,
.muted-panel {
  margin: 0;
}

.eyebrow {
  color: var(--card-muted);
  font-size: 12px;
  font-weight: 900;
}

.public-copy h2 {
  margin: 4px 0 0;
  font-size: 44px;
  line-height: 1;
  font-weight: 900;
}

.public-copy > span {
  display: block;
  margin-top: 6px;
  color: var(--card-muted);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.bio {
  max-width: 720px;
  margin: 12px 0 0;
  color: rgba(248, 250, 252, 0.84);
  font-size: 15px;
  line-height: 1.55;
}

.bio.muted,
.empty-line,
.muted-panel {
  color: var(--card-muted);
}

.tag-row,
.repo-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.tag-row span,
.repo-row span {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  border: 1px solid var(--card-line);
  border-radius: 999px;
  background: var(--card-panel);
  color: rgba(248, 250, 252, 0.82);
  font-size: 12px;
  font-weight: 800;
}

.public-card.theme-material3 .tag-row span {
  min-height: 30px;
  padding: 0 12px;
  border-color: rgba(73, 69, 79, 0.10);
  background: color-mix(in srgb, var(--profile-accent) 18%, #ffffff);
  color: color-mix(in srgb, var(--profile-accent) 64%, #1d1b20);
}

.preview-note {
  margin: -4px 4px 0;
  color: var(--card-muted);
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
}

.public-blocks {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.public-block {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--card-line);
  border-radius: 8px;
  background: var(--card-panel);
  cursor: pointer;
  transition: transform 220ms cubic-bezier(0.2, 0, 0, 1), border-color 220ms cubic-bezier(0.2, 0, 0, 1), opacity 220ms cubic-bezier(0.2, 0, 0, 1);
}

.public-block.hidden {
  opacity: 0.56;
}

.public-block.editing {
  border-color: color-mix(in srgb, var(--profile-accent) 70%, white);
}

.block-toolbar {
  min-width: 0;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border-bottom: 1px solid var(--card-line);
}

.block-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.block-title > div {
  min-width: 0;
}

.drag-handle,
.mini-handle {
  appearance: none;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--card-muted);
  cursor: grab;
  font: inherit;
}

.drag-handle,
.mini-handle {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  outline: none;
}

.drag-handle:focus-visible,
.mini-handle:focus-visible {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--profile-accent, var(--primary, #345EA8)) 28%, transparent);
  color: var(--card-text);
}

.mini-block:focus-visible {
  outline: none;
  border-color: color-mix(in srgb, var(--primary, #345EA8) 44%, var(--outline, rgba(82, 103, 138, 0.18)));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary, #345EA8) 18%, transparent);
}

.block-icon,
.section-icon,
.mini-icon {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: color-mix(in srgb, var(--profile-accent, var(--primary, #345EA8)) 16%, transparent);
  color: color-mix(in srgb, var(--profile-accent, var(--primary, #345EA8)) 74%, #fff);
  font-size: 18px;
}

.faceit-logo {
  width: 18px;
  height: 18px;
  display: block;
}

.block-title strong,
.block-title small {
  display: block;
}

.block-title strong {
  color: var(--card-text);
  font-size: 14px;
}

.block-title small {
  color: var(--card-muted);
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
  white-space: normal;
}

.block-actions {
  display: inline-flex;
  gap: 6px;
}

.tiny-action {
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  color: rgba(248,250,252,0.72);
  border-color: var(--card-line);
}

.tiny-action.active {
  color: #fff;
  background: color-mix(in srgb, var(--profile-accent) 42%, rgba(255,255,255,0.08));
}

.tiny-action.danger:hover {
  color: #fff;
  background: rgba(190, 56, 68, 0.58);
}

.block-preview {
  min-width: 0;
  display: grid;
  gap: 10px;
  padding: 12px;
}

.links-group {
  display: grid;
  gap: 7px;
}

.group-title {
  color: var(--card-muted);
  font-size: 11px;
  font-weight: 900;
}

.link-row {
  min-width: 0;
  min-height: 42px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  border: 1px solid var(--card-line);
  border-radius: 8px;
  background: rgba(255,255,255,0.06);
  color: var(--card-text);
  text-decoration: none;
  font-size: 14px;
}

.link-row span,
.widget-list span,
.widget-list strong,
.repo-row span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.text-preview,
.now-playing,
.empty-line {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.widget-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.widget-head p {
  color: var(--card-text);
  font-size: 15px;
  font-weight: 900;
}

.widget-head span,
.now-playing span {
  color: var(--card-muted);
  font-size: 12px;
}

.soft-badge {
  background: rgba(255,255,255,0.08);
  color: rgba(248,250,252,0.82);
  border: 1px solid var(--card-line);
}

.widget-list {
  display: grid;
  gap: 6px;
}

.widget-list > div {
  min-width: 0;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--card-line);
  color: rgba(248,250,252,0.82);
  font-size: 13px;
}

.widget-list > div:last-child {
  border-bottom: 0;
}

.widget-game-copy {
  display: grid;
  gap: 2px;
}

.widget-game-copy small {
  color: var(--card-muted);
  font-size: 11px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.sound-bars {
  display: inline-flex;
  align-items: end;
  gap: 3px;
  height: 24px;
}

.sound-bars span {
  width: 4px;
  height: 9px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--profile-accent) 84%, white);
  animation: sound-bars 0.9s ease-in-out infinite alternate;
}

.heatmap {
  display: grid;
  grid-template-columns: repeat(14, minmax(0, 1fr));
  gap: 4px;
}

.heatmap span {
  aspect-ratio: 1;
  border-radius: 3px;
  background: rgba(255,255,255,0.08);
}

.heatmap .level-1 { background: color-mix(in srgb, var(--profile-accent) 24%, rgba(255,255,255,0.08)); }
.heatmap .level-2 { background: color-mix(in srgb, var(--profile-accent) 42%, rgba(255,255,255,0.08)); }
.heatmap .level-3 { background: color-mix(in srgb, var(--profile-accent) 62%, rgba(255,255,255,0.08)); }
.heatmap .level-4 { background: color-mix(in srgb, var(--profile-accent) 86%, rgba(255,255,255,0.08)); }

.faceit-level {
  width: 42px;
  height: 42px;
  display: block;
  flex: 0 0 auto;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-grid div {
  display: grid;
  gap: 2px;
  padding: 10px;
  border: 1px solid var(--card-line);
  border-radius: 8px;
  background: rgba(255,255,255,0.06);
}

.stat-grid strong {
  font-size: 18px;
}

.stat-grid span {
  color: var(--card-muted);
  font-size: 11px;
}

.empty-add {
  min-height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--profile-accent) 16%, rgba(255,255,255,0.08));
  color: #fff;
  border-color: var(--card-line);
  font-weight: 900;
}

.studio-inspector {
  position: sticky;
  top: 122px;
  overflow: clip;
}

.inspector-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  padding: 8px;
  border-bottom: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 60%, transparent);
}

.inspector-tab {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 999px;
  font-weight: 900;
}

.inspector-tab.active {
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  border-color: transparent;
}

.inspector-section {
  display: grid;
  gap: 16px;
  padding: 16px;
}

.section-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.section-head h3,
.section-head p {
  margin: 0;
}

.section-head h3 {
  color: var(--text-1, #10182b);
  font-size: 20px;
  line-height: 1.15;
}

.section-head p {
  margin-top: 3px;
  color: var(--text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.back-btn {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 50%;
  font-size: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.studio-field {
  display: grid;
  gap: 6px;
}

.studio-field.wide {
  grid-column: 1 / -1;
}

.studio-field > span {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.studio-field input,
.studio-field textarea,
.slug-input {
  width: 100%;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
  font: inherit;
  outline: none;
  transition: border-color 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.studio-field input,
.slug-input {
  min-height: 44px;
}

.studio-field input,
.studio-field textarea {
  padding: 0 12px;
}

.studio-field textarea {
  min-height: 96px;
  padding-top: 10px;
  resize: vertical;
}

.slug-input {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 12px;
}

.slug-input span {
  flex: 0 0 auto;
  color: var(--text-3, #66789c);
  font-size: 12px;
  font-weight: 800;
}

.slug-input input {
  min-width: 0;
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
}

.studio-field input:focus,
.studio-field textarea:focus,
.slug-input:focus-within {
  border-color: var(--primary, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 16%, transparent);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.form-actions.sticky {
  position: sticky;
  bottom: 0;
  padding-top: 8px;
  background: linear-gradient(180deg, transparent, var(--surface, #fff) 24%);
}

.filled-btn,
.ghost-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 900;
}

.filled-btn {
  background: var(--primary, #345EA8);
  color: #fff;
  border-color: transparent;
}

.ghost-btn {
  background: var(--surface, #fff);
}

.filled-btn:disabled,
.ghost-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.divider {
  height: 1px;
  background: var(--outline, rgba(82, 103, 138, 0.18));
}

.section-subhead {
  color: var(--text-1, #10182b);
  font-size: 13px;
}

.theme-grid {
  display: grid;
  gap: 8px;
}

.theme-option {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  min-height: 70px;
  padding: 8px;
  border-radius: 8px;
  text-align: left;
}

.theme-option.active {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 44%, var(--outline, #d4dbe8));
  background: var(--primary-container, rgba(52,94,168,0.12));
}

.theme-swatch {
  width: 58px;
  height: 48px;
  border-radius: 8px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  background: linear-gradient(135deg, var(--profile-accent), #111827);
}

.theme-swatch.theme-glass {
  background: linear-gradient(135deg, rgba(255,255,255,0.55), rgba(36, 52, 82, 0.82));
}

.theme-swatch.theme-fluent {
  background: linear-gradient(135deg, #252B35, #111318);
}

.theme-option strong,
.theme-option small {
  display: block;
}

.theme-option strong {
  color: var(--text-1, #10182b);
  font-size: 14px;
}

.theme-option small {
  margin-top: 2px;
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.accent-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.accent-dot {
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
}

.accent-dot.active {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 18%, transparent);
}

.accent-dot.custom {
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
}

.material3-theme-controls {
  display: grid;
  gap: 10px;
}

.switch-setting {
  width: 100%;
  min-height: 68px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 18px;
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 260ms var(--m3-spring, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1),
    box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.switch-setting-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.switch-setting-copy strong,
.switch-setting-copy small {
  overflow-wrap: anywhere;
}

.switch-setting-copy strong {
  font-size: 14px;
  font-weight: 950;
}

.switch-setting-copy small {
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.custom-switch {
  width: 64px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  padding: 3px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 999px;
  background: var(--surface-low, #F2F4F8);
  transition:
    background 220ms cubic-bezier(0.2, 0, 0, 1),
    border-color 220ms cubic-bezier(0.2, 0, 0, 1);
}

.custom-switch span {
  width: 30px;
  height: 30px;
  display: inline-grid;
  place-items: center;
  border-radius: 999px;
  background: var(--surface, #fff);
  color: var(--text-2, #475778);
  box-shadow: 0 3px 9px color-mix(in srgb, var(--text-1, #10182b) 12%, transparent);
  transform: translateX(0);
  transition:
    transform 280ms var(--m3-spring, cubic-bezier(0.2, 0, 0, 1)),
    color 180ms cubic-bezier(0.2, 0, 0, 1);
}

.custom-switch.active {
  border-color: transparent;
  background: var(--primary, #345EA8);
}

.custom-switch.active span {
  color: var(--on-primary-container, #163E86);
  transform: translateX(28px);
}

.wide-switch.active {
  background: linear-gradient(135deg, var(--primary, #345EA8), color-mix(in srgb, var(--primary, #345EA8) 54%, #F59E0B));
}

.mini-block-list,
.mini-drag,
.library-grid {
  display: grid;
  gap: 8px;
}

.mini-block {
  width: 100%;
  min-height: 52px;
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  gap: 9px;
  align-items: center;
  padding: 8px;
  border-radius: 8px;
  text-align: left;
}

.mini-block.hidden {
  opacity: 0.58;
}

.mini-handle {
  color: var(--text-3, #66789c);
}

.mini-label {
  overflow: hidden;
  color: var(--text-1, #10182b);
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.mini-meta {
  color: var(--primary, #345EA8);
  font-size: 11px;
  font-weight: 900;
  line-height: 1.2;
}

.mini-meta.hidden {
  color: var(--text-3, #66789c);
}

.mini-actions {
  display: inline-flex;
  gap: 5px;
}

.library-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.library-item {
  min-height: 116px;
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  text-align: left;
}

.library-item-icon {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  border-radius: 8px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 18px;
}

.library-item strong,
.library-item small {
  display: block;
}

.library-item strong {
  color: var(--text-1, #10182b);
  font-size: 14px;
}

.library-item small {
  margin-top: 3px;
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.muted-panel {
  padding: 14px;
  border-radius: 8px;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
  font-size: 13px;
}

.studio-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid rgba(255,255,255,0.38);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.78s linear infinite;
}

.studio-spinner.dark {
  border-color: rgba(255,255,255,0.34);
  border-top-color: #fff;
}

.git-provider-overlay {
  position: fixed;
  inset: 0;
  z-index: 210;
  display: grid;
  place-items: center;
  padding: 18px;
  background: color-mix(in srgb, #05070c 54%, transparent);
  backdrop-filter: blur(12px);
}

.git-provider-modal {
  position: relative;
  width: min(100%, 520px);
  display: grid;
  gap: 18px;
  padding: 26px;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 64%, transparent);
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface, #fff) 96%, transparent);
  box-shadow: 0 24px 70px color-mix(in srgb, #05070c 32%, transparent);
}

.confirm-dialog {
  width: min(100%, 440px);
  display: grid;
  gap: 16px;
  padding: 24px;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 64%, transparent);
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface, #fff) 96%, transparent);
  box-shadow: 0 24px 70px color-mix(in srgb, #05070c 32%, transparent);
}

.confirm-dialog-icon {
  width: 52px;
  height: 52px;
  display: inline-grid;
  place-items: center;
  border-radius: 20px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 26px;
}

.confirm-dialog-icon.danger {
  background: color-mix(in srgb, #dc2626 14%, var(--surface-low, #F2F4F8));
  color: #b91c1c;
}

.confirm-dialog-copy {
  display: grid;
  gap: 6px;
}

.confirm-dialog-copy h2,
.confirm-dialog-copy p {
  margin: 0;
}

.confirm-dialog-copy h2 {
  color: var(--text-1, #10182b);
  font-size: 24px;
  line-height: 1.12;
}

.confirm-dialog-copy p {
  color: var(--text-2, #475778);
  font-size: 14px;
  line-height: 1.45;
}

.confirm-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.filled-btn.danger {
  background: #dc2626;
  color: #fff;
}

.git-provider-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: var(--surface-low, #F2F4F8);
  color: var(--text-2, #475778);
  cursor: pointer;
  font: inherit;
  font-size: 20px;
}

.git-provider-head {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 8px 28px 0;
  text-align: center;
}

.git-provider-head-icon {
  width: 54px;
  height: 54px;
  display: inline-grid;
  place-items: center;
  border-radius: 20px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 28px;
}

.git-provider-head h2,
.git-provider-head p {
  margin: 0;
}

.git-provider-head h2 {
  color: var(--text-1, #10182b);
  font-size: 28px;
  line-height: 1.1;
}

.git-provider-head p {
  color: var(--text-2, #475778);
  font-size: 14px;
  line-height: 1.35;
}

.git-provider-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.git-provider-choice {
  min-width: 0;
  min-height: 132px;
  display: grid;
  align-content: start;
  justify-items: start;
  gap: 8px;
  padding: 13px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 18px;
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.git-provider-choice span {
  width: 40px;
  height: 40px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 22px;
}

.git-provider-choice strong,
.git-provider-choice small {
  overflow-wrap: anywhere;
}

.git-provider-choice strong {
  font-size: 14px;
  font-weight: 950;
}

.git-provider-choice small {
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.git-provider-choice:disabled {
  cursor: wait;
  opacity: 0.68;
}

.git-provider-modal-enter-active,
.git-provider-modal-leave-active {
  transition: opacity 200ms cubic-bezier(0.2, 0, 0, 1);
}

.git-provider-modal-enter-active .git-provider-modal,
.git-provider-modal-leave-active .git-provider-modal {
  transition:
    transform 220ms cubic-bezier(0.2, 0, 0, 1),
    opacity 220ms cubic-bezier(0.2, 0, 0, 1);
}

.git-provider-modal-enter-from,
.git-provider-modal-leave-to {
  opacity: 0;
}

.git-provider-modal-enter-from .git-provider-modal,
.git-provider-modal-leave-to .git-provider-modal {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}

@media (max-width: 640px) {
  .confirm-dialog {
    padding: 22px 18px;
    border-radius: 24px;
  }

  .confirm-dialog-actions {
    align-items: stretch;
    flex-direction: column-reverse;
  }

  .git-provider-modal {
    padding: 24px 18px;
    border-radius: 24px;
  }

  .git-provider-grid {
    grid-template-columns: 1fr;
  }

  .git-provider-choice {
    min-height: 96px;
  }
}

.block-ghost,
.mini-ghost {
  opacity: 0.5;
}

.inspector-pane-enter-active,
.inspector-pane-leave-active {
  transition: opacity 220ms cubic-bezier(0.2, 0, 0, 1), transform 220ms cubic-bezier(0.2, 0, 0, 1);
}

.inspector-pane-enter-from,
.inspector-pane-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (hover: hover) {
  .icon-action:hover,
  .tiny-action:hover,
  .inspector-tab:hover,
  .filled-btn:hover:not(:disabled),
  .ghost-btn:hover:not(:disabled),
  .theme-option:hover,
  .accent-dot:hover,
  .library-item:hover,
  .mini-block:hover,
  .empty-add:hover,
  .back-btn:hover,
  .avatar-upload:hover,
  .switch-setting:hover {
    transform: translateY(-1px);
  }

  .public-block:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--profile-accent) 42%, var(--card-line));
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes sound-bars {
  from { height: 8px; }
  to { height: 22px; }
}

@media (max-width: 1120px) {
  .studio-shell {
    grid-template-columns: 1fr;
  }

  .studio-inspector {
    position: static;
    order: -1;
  }
}

@media (max-width: 680px) {
  .studio-preview-bar,
  .public-header,
  .block-toolbar,
  .form-actions {
    align-items: stretch;
  }

  .studio-preview-bar,
  .public-header {
    flex-direction: column;
  }

  .studio-status,
  .studio-quick-actions,
  .form-actions {
    flex-wrap: wrap;
  }

  .url-pill {
    max-width: 100%;
  }

  .public-avatar {
    width: 84px;
    height: 84px;
    font-size: 32px;
  }

  .public-card.theme-material3 .public-avatar {
    width: 68px;
    height: 68px;
    border-radius: 24px 24px 18px 24px;
    font-size: 25px;
  }

  .public-copy h2 {
    font-size: 34px;
  }

  .block-toolbar {
    flex-direction: column;
  }

  .block-actions,
  .studio-quick-actions {
    width: 100%;
  }

  .studio-quick-actions .icon-action {
    flex: 1;
  }

  .block-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
  }

  .block-actions .tiny-action {
    width: auto;
    min-width: 0;
  }

  .form-grid,
  .library-grid {
    grid-template-columns: 1fr;
  }

  .mini-block {
    grid-template-columns: auto auto minmax(0, 1fr);
  }

  .mini-actions {
    grid-column: 1 / -1;
    width: 100%;
  }

  .mini-actions .tiny-action {
    flex: 1;
  }
}

.studio-shell {
  grid-template-columns: minmax(0, 1fr) minmax(340px, 392px);
  gap: 14px;
}

.studio-preview-pane {
  min-height: calc(100vh - 146px);
  align-items: start;
  justify-items: center;
  padding: 18px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface, #fff) 58%, transparent), transparent 260px),
    color-mix(in srgb, var(--surface-low, #F2F4F8) 78%, transparent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62);
}

.public-card {
  width: min(100%, 760px);
  justify-self: center;
  box-shadow: var(--shadow-soft, 0 16px 42px rgba(48, 63, 92, 0.11));
}

.studio-inspector {
  top: 92px;
  max-height: calc(100vh - 110px);
  overflow: auto;
  background: color-mix(in srgb, var(--surface, #fff) 94%, transparent);
}

.studio-preview-bar {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 0;
  border-bottom: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 0;
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 54%, transparent);
  box-shadow: none;
}

.studio-status {
  display: grid;
  gap: 8px;
}

.url-pill {
  max-width: 100%;
}

.studio-quick-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.studio-quick-actions .icon-action {
  width: 100%;
  border-radius: 8px;
}

.inspector-tabs {
  background: color-mix(in srgb, var(--surface, #fff) 88%, transparent);
}

.inspector-tab.active {
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 88%, white);
}

@media (max-width: 1120px) {
  .studio-shell {
    grid-template-columns: 1fr;
  }

  .studio-preview-pane {
    min-height: auto;
  }

  .studio-inspector {
    order: 0;
    width: 100%;
    max-width: 100%;
    max-height: none;
  }
}

@media (max-width: 680px) {
  .studio-shell,
  .studio-preview-pane,
  .studio-inspector,
  .public-card {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }

  .studio-preview-pane {
    padding: 0;
    border: 0;
    background: transparent;
    box-shadow: none;
  }

  .public-card {
    padding: 16px;
    overflow: hidden;
  }

  .studio-status,
  .studio-quick-actions {
    width: 100%;
  }

  .studio-preview-bar {
    align-items: stretch;
    overflow: hidden;
  }

  .inspector-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .inspector-tab {
    min-width: 0;
  }

  .slug-input {
    display: grid;
    gap: 4px;
    min-height: 58px;
    padding: 8px 12px;
  }

  .slug-input span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* Material 3 Expressive dashboard refresh */
.studio-shell {
  --m3-radius-sm: 14px;
  --m3-radius-md: 20px;
  --m3-radius-lg: 28px;
  --m3-radius-xl: 34px;
  --m3-ease: cubic-bezier(0.2, 0, 0, 1);
  --m3-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  grid-template-columns: minmax(520px, 1fr) minmax(340px, 392px);
  gap: clamp(12px, 1.5vw, 18px);
  align-items: stretch;
  height: calc(100dvh - 146px);
  min-height: 0;
  overflow: hidden;
}

.studio-preview-pane {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 0;
  height: 100%;
  overflow: auto;
  overscroll-behavior: contain;
  padding: clamp(10px, 1.2vw, 16px);
  border-radius: 28px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--primary, #345EA8) 6%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--surface, #fff) 86%, transparent), color-mix(in srgb, var(--surface-low, #F2F4F8) 74%, transparent));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 16px 42px color-mix(in srgb, var(--text-1, #10182b) 7%, transparent);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 11px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface, #fff) 78%, transparent);
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.studio-preview-bar {
  position: relative;
  top: auto;
  z-index: 2;
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  align-items: stretch;
  gap: 6px;
  margin: 8px 8px 0;
  padding: 6px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #fff) 82%, transparent);
  box-shadow: none;
  backdrop-filter: blur(18px) saturate(140%);
}

.studio-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.studio-preview-bar .status-pill,
.studio-preview-bar .count-pill {
  min-height: 28px;
  gap: 5px;
  padding-inline: 9px;
  font-size: 11px;
}

.studio-status .url-pill {
  flex: 1 1 100%;
}

.url-pill {
  min-width: 0;
  max-width: 100%;
  min-height: 0;
  padding: 0 3px;
  border-radius: 0;
  border: 0;
  background: transparent;
  font-size: 11px;
  line-height: 1.25;
  font-weight: 800;
  color: var(--on-primary-container, #173F86);
}

.studio-quick-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.studio-quick-actions .icon-action {
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  min-width: 38px;
  min-height: 38px;
  gap: 6px;
  padding: 0;
  border-radius: 999px;
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.studio-quick-actions .icon-action:not(.publish-action) span {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.studio-quick-actions .publish-action {
  flex: 1 1 auto;
  width: auto;
  min-width: 0;
  padding-inline: 12px;
  border-color: transparent;
  background: var(--primary, #345EA8);
  color: #fff;
  box-shadow: none;
}

.public-card {
  width: min(100%, 720px);
  gap: 12px;
  padding: clamp(14px, 1.5vw, 20px);
  border-radius: 24px;
  box-shadow:
    0 18px 46px color-mix(in srgb, var(--text-1, #10182b) 14%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.public-avatar {
  border-radius: 22px;
}

.public-block {
  border-radius: 22px;
  transition:
    transform 260ms var(--m3-spring),
    border-color 220ms var(--m3-ease),
    box-shadow 220ms var(--m3-ease),
    opacity 220ms var(--m3-ease);
}

.public-block.editing {
  border-color: color-mix(in srgb, var(--profile-accent) 72%, white);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--profile-accent) 24%, transparent);
}

.block-toolbar {
  padding: 12px;
}

.block-preview {
  padding: 12px;
}

.link-row,
.stat-grid div,
.preview-row,
.empty-add {
  border-radius: 16px;
}

.block-icon,
.section-icon,
.mini-icon,
.library-item-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
}

.tiny-action,
.back-btn,
.accent-dot {
  min-width: 44px;
  min-height: 44px;
  border-radius: 14px;
}

.studio-inspector {
  top: 92px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  border-radius: 28px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--surface, #fff) 96%, transparent), color-mix(in srgb, var(--surface-low, #F2F4F8) 70%, transparent));
  box-shadow:
    0 20px 48px color-mix(in srgb, var(--text-1, #10182b) 10%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.inspector-tabs {
  flex: 0 0 auto;
  gap: 6px;
  margin: 10px 10px 0;
  padding: 5px;
  border: 0;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 78%, transparent);
}

.inspector-tab {
  min-height: 42px;
  border-radius: 999px;
}

.inspector-tab.active {
  background: var(--surface, #fff);
  color: var(--on-primary-container, #163E86);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--text-1, #10182b) 8%, transparent);
}

.block-rail {
  flex: 0 0 auto;
  display: flex;
  gap: 7px;
  margin: 10px 10px 0;
  padding: 7px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 72%, transparent);
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface, #fff) 82%, transparent);
  scrollbar-width: thin;
}

.block-rail-item {
  position: relative;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  display: inline-grid;
  place-items: center;
  border-radius: 15px;
  color: var(--text-2, #475778);
  font-size: 18px;
  transition:
    transform 240ms var(--m3-spring),
    border-color 180ms var(--m3-ease),
    background 180ms var(--m3-ease),
    box-shadow 180ms var(--m3-ease),
    opacity 180ms var(--m3-ease);
}

.block-rail-item::after {
  content: "";
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 7px;
  height: 7px;
  border: 2px solid var(--surface, #fff);
  border-radius: 50%;
  background: #22c55e;
}

.block-rail-item.hidden {
  opacity: 0.56;
}

.block-rail-item.hidden::after {
  background: #94a3b8;
}

.block-rail-item.active {
  border-color: color-mix(in srgb, var(--primary, #345EA8) 58%, var(--outline, #d4dbe8));
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 13%, transparent);
}

.block-rail-item:hover {
  transform: translateY(-1px);
}

.inspector-section {
  gap: 14px;
  padding: 14px;
}

.inspector-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.section-head h3 {
  font-size: 18px;
  font-weight: 950;
}

.section-head.compact {
  align-items: center;
}

.block-manager-head {
  justify-content: space-between;
}

.block-manager-head p {
  margin-top: 3px;
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 800;
}

.selected-block-head {
  display: grid;
  gap: 10px;
}

.block-status-pill {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid color-mix(in srgb, var(--primary, #345EA8) 26%, var(--outline, #d4dbe8));
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 78%, transparent);
  color: var(--on-primary-container, #163E86);
  font-size: 12px;
  font-weight: 950;
}

.block-status-pill.hidden {
  border-color: var(--outline, rgba(82, 103, 138, 0.18));
  background: color-mix(in srgb, var(--surface-low, #F2F4F8) 78%, transparent);
  color: var(--text-3, #66789c);
}

.selected-block-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.block-action-card {
  min-height: 94px;
  display: grid;
  align-content: start;
  gap: 9px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface, #fff) 88%, transparent);
  color: var(--text-1, #10182b);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 240ms var(--m3-spring),
    border-color 180ms var(--m3-ease),
    background 180ms var(--m3-ease),
    box-shadow 180ms var(--m3-ease),
    opacity 180ms var(--m3-ease);
}

.block-action-card:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--primary, #345EA8) 36%, var(--outline, #d4dbe8));
  box-shadow: 0 12px 28px color-mix(in srgb, var(--text-1, #10182b) 8%, transparent);
}

.block-action-card:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.block-action-card.danger {
  border-color: color-mix(in srgb, #ef4444 26%, var(--outline, #d4dbe8));
}

.block-action-card.danger .block-action-icon {
  background: color-mix(in srgb, #ef4444 14%, var(--surface-low, #F2F4F8));
  color: #b91c1c;
}

.block-action-icon {
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 18px;
}

.block-action-card strong,
.block-action-card small {
  display: block;
  overflow-wrap: anywhere;
}

.block-action-card strong {
  font-size: 13px;
  font-weight: 950;
}

.block-action-card small {
  margin-top: 3px;
  color: var(--text-2, #475778);
  font-size: 11px;
  line-height: 1.3;
}

.studio-field input,
.studio-field textarea,
.slug-input {
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #fff) 92%, transparent);
}

.theme-option,
.library-item,
.mini-block,
.muted-panel {
  border-radius: 18px;
}

.theme-option,
.library-item,
.mini-block {
  transition:
    transform 260ms var(--m3-spring),
    border-color 180ms var(--m3-ease),
    background 180ms var(--m3-ease),
    box-shadow 180ms var(--m3-ease);
}

.theme-option.active,
.library-item:hover,
.mini-block:hover {
  box-shadow: 0 10px 26px color-mix(in srgb, var(--text-1, #10182b) 8%, transparent);
}

.theme-swatch {
  border-radius: 14px;
}

.filled-btn,
.ghost-btn {
  min-height: 44px;
}

@media (max-width: 1180px) {
  .studio-shell {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .studio-preview-pane {
    height: auto;
    overflow: visible;
  }

  .studio-inspector {
    position: static;
    order: -1;
    height: auto;
    max-height: min(72dvh, 720px);
  }
}

@media (max-width: 760px) {
  .studio-shell {
    gap: 12px;
  }

  .studio-preview-pane {
    min-height: auto;
    height: auto;
    padding: 10px;
    border: 0;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }

  .studio-preview-bar {
    grid-template-columns: 1fr;
    border-radius: 18px;
  }

  .studio-quick-actions {
    display: flex;
  }

  .studio-quick-actions .icon-action {
    justify-content: center;
    flex-basis: 44px;
    width: 44px;
    min-width: 44px;
    min-height: 44px;
  }

  .studio-quick-actions .publish-action {
    flex: 1 1 auto;
    width: auto;
    padding-inline: 10px;
  }

  .public-card {
    border-radius: 22px;
    padding: 14px;
  }

  .public-card.theme-material3.layout-wide {
    grid-template-columns: 1fr;
  }

  .public-card.theme-material3.layout-wide .public-header {
    position: relative;
  }

  .public-card.theme-material3.layout-wide .public-blocks {
    grid-template-columns: 1fr;
  }

  .studio-inspector {
    max-height: min(70dvh, 620px);
    border-radius: 22px;
  }

  .inspector-section {
    padding-inline: 14px;
  }

  .selected-block-actions {
    grid-template-columns: 1fr;
  }

  .block-rail {
    margin-inline: 8px;
  }
}

/* Compact M3E dashboard alignment */
.studio-shell {
  grid-template-columns: minmax(520px, 1fr) minmax(340px, 390px);
  gap: 14px;
}

.studio-preview-pane {
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container-low, var(--surface-low, #f2f4f8));
  box-shadow: none;
}

.studio-inspector {
  border: 0;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container-low, var(--surface-low, #f2f4f8));
  box-shadow: none;
}

.studio-preview-bar {
  min-height: 72px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  margin: 8px;
  padding: 12px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container, var(--surface-low, #f2f4f8));
  box-shadow: none;
  backdrop-filter: none;
}

.studio-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.studio-preview-bar .status-pill,
.studio-preview-bar .count-pill,
.studio-status .url-pill {
  min-height: 24px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-full, 999px);
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  padding: 0 8px;
  box-shadow: none;
  font-size: 11px;
  font-weight: 850;
  line-height: 24px;
}

.studio-preview-bar .status-pill.published {
  background: color-mix(in srgb, var(--success, #188a55) 14%, var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8)));
  color: var(--success, #188a55);
}

.studio-status .url-pill {
  flex: 1 1 100%;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.studio-quick-actions {
  justify-content: flex-end;
  gap: 8px;
}

.studio-quick-actions .icon-action,
.studio-quick-actions .publish-action {
  flex: 0 0 auto;
  width: auto;
  min-width: 38px;
  min-height: 36px;
  height: 36px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-full, 999px);
  background: var(--md-sys-color-secondary-container, color-mix(in srgb, var(--primary-container, rgba(52, 94, 168, 0.12)) 76%, var(--surface, #fff)));
  color: var(--md-sys-color-on-secondary-container, var(--on-primary-container, #163e86));
  padding: 0 12px;
  box-shadow: none;
}

.studio-quick-actions .icon-action:not(.publish-action) {
  padding: 0;
}

.studio-quick-actions .publish-action {
  min-width: 126px;
  background: var(--md-sys-color-secondary-container, color-mix(in srgb, var(--primary-container, rgba(52, 94, 168, 0.12)) 76%, var(--surface, #fff)));
  color: var(--md-sys-color-on-secondary-container, var(--on-primary-container, #163e86));
}

.inspector-tabs {
  margin: 8px;
  padding: 6px;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container, var(--surface-low, #f2f4f8));
}

.inspector-tab {
  min-height: 36px;
  border-radius: var(--md-sys-shape-corner-full, 999px);
}

.inspector-tab.active {
  background: var(--md-sys-color-secondary-container, color-mix(in srgb, var(--primary-container, rgba(52, 94, 168, 0.12)) 76%, var(--surface, #fff)));
  color: var(--md-sys-color-on-secondary-container, var(--on-primary-container, #163e86));
  box-shadow: none;
}

.block-rail {
  margin: 0 8px 8px;
  padding: 8px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container, var(--surface-low, #f2f4f8));
}

.block-rail-item {
  flex-basis: 38px;
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  background: color-mix(in srgb, var(--primary, #345ea8) 12%, var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8)));
  box-shadow: none;
}

.block-rail-item.active {
  background: color-mix(in srgb, var(--primary, #345ea8) 22%, var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8)));
  box-shadow: none;
}

.inspector-body {
  padding: 0 8px 8px;
}

.inspector-section {
  gap: 12px;
  padding: 8px;
}

.section-head.compact,
.selected-block-head {
  min-height: 60px;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--primary, #345ea8) 8%, transparent), transparent 34%),
    transparent;
  padding: 10px 12px;
}

.section-head h3,
.selected-block-head h3 {
  color: var(--md-sys-color-on-surface, var(--text-1, #10182b));
  font: var(--md-sys-typescale-title-medium-weight, 850) var(--md-sys-typescale-title-medium-size, 16px) / var(--md-sys-typescale-title-medium-line-height, 24px) var(--md-sys-typescale-title-medium-font, inherit);
}

.section-icon,
.selected-block-head .section-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--md-sys-shape-corner-large, 16px);
  background: color-mix(in srgb, var(--primary, #345ea8) 16%, var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8)));
  color: color-mix(in srgb, var(--primary, #345ea8) 82%, var(--md-sys-color-on-surface, var(--text-1, #10182b)));
  box-shadow: none;
}

.form-grid,
.theme-grid,
.mini-block-list,
.block-library,
.material3-theme-controls,
.selected-block-actions {
  padding: 8px;
  border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  background: var(--md-sys-color-surface-container, var(--surface-low, #f2f4f8));
}

.studio-field input,
.studio-field textarea,
.slug-input,
.theme-option,
.switch-setting,
.library-item,
.mini-block,
.block-action-card,
.muted-panel {
  border: 0;
  border-radius: var(--md-sys-shape-corner-large-increased, 20px);
  background: var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8));
  box-shadow: none;
}

.mini-block {
  min-height: 58px;
  grid-template-columns: auto 38px minmax(0, 1fr) auto;
  padding: 8px;
}

.mini-label {
  font-size: 13px;
}

.mini-meta,
.block-status-pill {
  min-height: 24px;
  border: 0;
  border-radius: var(--md-sys-shape-corner-full, 999px);
  background: var(--md-sys-color-surface-container-highest, var(--surface, #fff));
  color: var(--md-sys-color-on-surface-variant, var(--text-2, #475778));
  padding: 0 8px;
  font-size: 11px;
  font-weight: 850;
}

.block-status-pill:not(.hidden),
.mini-meta:not(.hidden) {
  background: color-mix(in srgb, var(--success, #188a55) 14%, var(--md-sys-color-surface-container-high, var(--surface-low, #f2f4f8)));
  color: var(--success, #188a55);
}

.selected-block-actions {
  gap: 2px;
}

.block-action-card {
  min-height: 68px;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  align-content: center;
  gap: 10px;
}

.block-action-card small {
  display: none;
}

.form-actions,
.editor-actions {
  gap: 8px;
}

.filled-btn,
.ghost-btn,
.tiny-action,
.back-btn {
  border: 0;
  border-radius: var(--md-sys-shape-corner-full, 999px);
  box-shadow: none;
}

@media (hover: hover) {
  .block-rail-item:hover,
  .mini-block:hover,
  .theme-option:hover,
  .library-item:hover,
  .block-action-card:hover:not(:disabled) {
    transform: none;
    box-shadow: none;
  }
}

@media (max-width: 1180px) {
  .studio-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .studio-shell {
    gap: 12px;
  }

  .studio-preview-pane {
    border-radius: 0;
    background: transparent;
  }

  .studio-preview-bar {
    grid-template-columns: 1fr;
    margin: 0;
  }

  .studio-quick-actions {
    justify-content: stretch;
  }

  .studio-quick-actions .publish-action {
    flex: 1 1 auto;
    min-width: 0;
  }

  .studio-inspector {
    border-radius: var(--md-sys-shape-corner-extra-large, 28px);
  }

  .mini-block {
    grid-template-columns: auto 38px minmax(0, 1fr);
  }

  .mini-actions {
    grid-column: 1 / -1;
    justify-content: stretch;
  }

  .mini-actions .tiny-action {
    flex: 1 1 0;
  }
}
</style>
