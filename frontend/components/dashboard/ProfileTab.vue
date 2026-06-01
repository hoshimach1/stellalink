<template>
  <CropAvatarModal
    :file="avatarCropFile"
    :saving="avatarUploading"
    @save="onAvatarCropSave"
    @cancel="avatarCropFile = null"
  />

  <div v-if="profile.profile" class="studio-shell">
    <section class="studio-preview-pane" aria-label="Живое превью профиля">
      <article class="public-card" :class="previewCardClasses" :data-color-mode="currentColorMode" :style="profileAccentStyle">
        <header class="public-header">
          <div class="avatar-wrap">
            <div class="public-avatar">
              <img v-if="avatarDisplaySrc" :src="avatarDisplaySrc" alt="" class="avatar-img">
              <span v-else>{{ profileInitial }}</span>
            </div>
            <label class="avatar-upload" :class="{ loading: avatarUploading }" title="Загрузить аватар">
              <span v-if="avatarUploading" class="studio-spinner dark" />
              <i v-else class="ri-camera-line" />
              <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden @change="onAvatarFileChange">
            </label>
          </div>

          <div class="public-copy">
            <h2>{{ profile.profile.display_name || 'Без имени' }}</h2>
            <span>{{ publicUrlLabel }}</span>
            <p v-if="profile.profile.bio" class="bio">{{ profile.profile.bio }}</p>
            <p v-else class="bio muted">Био пока не заполнено.</p>
            <div v-if="profile.profile.tags.length" class="tag-row">
              <span v-for="tag in profile.profile.tags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </header>

        <ClientOnly>
          <VueDraggable
            v-model="draggableBlocks"
            class="public-blocks"
            handle=".drag-handle"
            :animation="220"
            ghost-class="block-ghost"
            @end="onDragEnd"
          >
            <article
              v-for="block in draggableBlocks"
              :key="block.id"
              class="public-block"
              :class="{ hidden: !block.is_visible, editing: editingBlockId === block.id }"
              @click="openBlockEditor(block)"
            >
              <div class="block-toolbar">
                <div class="block-title">
                  <span class="drag-handle" title="Перетащить" @click.stop>
                    <i class="ri-draggable" />
                  </span>
                  <span class="block-icon">
                    <FaceitLogo v-if="block.block_type === 'widget_faceit'" class="faceit-logo" />
                    <i v-else :class="displayBlockIcon(block)" />
                  </span>
                  <div>
                    <strong>{{ displayBlockLabel(block) }}</strong>
                    <small>{{ block.is_visible ? displayBlockDescription(block) : 'Скрыт на публичной странице' }}</small>
                  </div>
                </div>
                <div class="block-actions">
                  <button class="tiny-action" :class="{ active: block.is_visible }" type="button" title="Видимость" @click.stop="toggleVisible(block)">
                    <i :class="block.is_visible ? 'ri-eye-line' : 'ri-eye-off-line'" />
                  </button>
                  <button class="tiny-action danger" type="button" title="Удалить" @click.stop="deleteBlock(block.id)">
                    <i class="ri-delete-bin-line" />
                  </button>
                </div>
              </div>

              <div class="block-preview">
                <template v-if="block.block_type === 'links'">
                  <div v-for="(group, index) in asGroups(previewConfig(block))" :key="`${group.title}-${index}`" class="links-group">
                    <p v-if="group.title" class="group-title">{{ group.title }}</p>
                    <a v-for="link in group.links" :key="`${link.label}-${link.url}`" class="link-row" :href="link.url || '#'" target="_blank" rel="noopener noreferrer" @click.prevent>
                      <i :class="link.icon ? `ri-${link.icon}-fill` : 'ri-link'" />
                      <span>{{ link.label || link.url || 'Новая ссылка' }}</span>
                    </a>
                  </div>
                  <p v-if="!asGroups(previewConfig(block)).some(group => group.links.length)" class="empty-line">Добавьте первую ссылку.</p>
                </template>

                <template v-else-if="block.block_type === 'text'">
                  <p class="text-preview">{{ (previewConfig(block).content as string) || 'Текст блока появится здесь.' }}</p>
                </template>

                <template v-else-if="block.block_type === 'widget_steam'">
                  <div class="widget-head">
                    <div>
                      <p>Steam</p>
                      <span>{{ steamDisplayName(previewConfig(block)) }}</span>
                    </div>
                    <span class="soft-badge">Игры</span>
                  </div>
                  <div v-if="previewConfig(block).show_recent_games && steamGamesList(previewConfig(block)).length" class="widget-list">
                    <div v-for="game in steamGamesList(previewConfig(block))" :key="`${game.appid || game.name}`">
                      <span class="widget-game-copy">
                        <span>{{ game.name }}</span>
                        <small v-if="steamGameMeta(game)">{{ steamGameMeta(game) }}</small>
                      </span>
                      <strong>{{ steamTotalHours(game) }} ч</strong>
                    </div>
                  </div>
                  <p v-else-if="previewConfig(block).show_recent_games" class="empty-line">
                    Последние игры появятся после синхронизации Steam.
                  </p>
                  <div v-if="previewConfig(block).show_profile_stats && steamStatsList(previewConfig(block)).length" class="stat-grid">
                    <div v-for="stat in steamStatsList(previewConfig(block))" :key="stat.label">
                      <strong>{{ stat.value }}</strong><span>{{ stat.label }}</span>
                    </div>
                  </div>
                  <p v-if="previewConfig(block).show_inventory_highlight && inventoryStatus(previewConfig(block))" class="empty-line">
                    {{ inventoryStatus(previewConfig(block))?.title }}: {{ inventoryStatus(previewConfig(block))?.reason }}
                  </p>
                </template>

                <template v-else-if="block.block_type === 'widget_lastfm'">
                  <div class="widget-head">
                    <div>
                      <p>Last.fm</p>
                      <span>@{{ (previewConfig(block).username as string) || 'username' }}</span>
                    </div>
                    <div v-if="previewConfig(block).show_now_playing && previewConfig(block).username" class="sound-bars" aria-hidden="true">
                      <span v-for="bar in 4" :key="bar" :style="{ animationDelay: `${(bar - 1) * 0.12}s` }" />
                    </div>
                  </div>
                  <p v-if="previewConfig(block).username" class="now-playing">
                    {{ mock.lastfmTrack(previewConfig(block).username as string).track }}
                    <span>{{ mock.lastfmTrack(previewConfig(block).username as string).artist }}</span>
                  </p>
                </template>

                <template v-else-if="block.block_type === 'widget_github'">
                  <div class="widget-head">
                    <div>
                      <p>{{ gitProviderLabel(previewConfig(block)) }}</p>
                      <span>{{ gitAccountCaption(previewConfig(block)) }}</span>
                    </div>
                    <span v-if="gitRepositoryTotal(previewConfig(block)) !== null" class="soft-badge">
                      {{ gitRepositoryTotal(previewConfig(block)) }} repo
                    </span>
                  </div>
                  <div v-if="previewConfig(block).show_repository_stats && gitRepositoryStatsList(previewConfig(block)).length" class="stat-grid">
                    <div v-for="stat in gitRepositoryStatsList(previewConfig(block))" :key="stat.label">
                      <strong>{{ stat.value }}</strong><span>{{ stat.label }}</span>
                    </div>
                  </div>
                  <p v-if="previewConfig(block).show_contributions && gitActivitySummary(previewConfig(block))" class="empty-line">
                    {{ gitActivitySummary(previewConfig(block)) }}
                  </p>
                  <div v-if="gitUsername(previewConfig(block)) && previewConfig(block).show_pinned_repos" class="repo-row">
                    <span v-for="repo in gitPinnedRepositories(previewConfig(block))" :key="repo.id || repo.full_name">{{ repo.name }}</span>
                  </div>
                </template>

                <template v-else-if="block.block_type === 'widget_faceit'">
                  <div class="widget-head">
                    <div>
                      <p>FACEIT</p>
                      <span>{{ faceitDisplayName(previewConfig(block)) }}</span>
                    </div>
                    <FaceitSkillLevel
                      v-if="faceitPreviewData(previewConfig(block))"
                      class="faceit-level"
                      :level="faceitPreviewData(previewConfig(block))?.level || 0"
                      :accent-color="faceitAccentColor"
                    />
                  </div>
                  <div v-if="faceitPreviewData(previewConfig(block))" class="stat-grid">
                    <div><strong>{{ faceitPreviewData(previewConfig(block))?.elo }}</strong><span>ELO</span></div>
                    <div><strong>{{ faceitPreviewData(previewConfig(block))?.kd }}</strong><span>K/D</span></div>
                    <div><strong>{{ faceitPreviewData(previewConfig(block))?.winRate }}</strong><span>Win rate</span></div>
                  </div>
                  <p v-else class="empty-line">FACEIT подтянется автоматически, если профиль найден по Steam.</p>
                </template>

                <template v-else-if="block.block_type === 'pc_config'">
                  <div class="widget-head">
                    <div>
                      <p>{{ (previewConfig(block).title as string) || 'Конфиг ПК' }}</p>
                      <span>{{ asComponents(previewConfig(block)).length }} компонентов</span>
                    </div>
                  </div>
                  <div class="widget-list">
                    <div v-for="component in asComponents(previewConfig(block))" :key="`${component.category}-${component.name}`">
                      <span>{{ component.category || 'Категория' }}</span>
                      <strong>{{ component.name || 'Компонент' }}</strong>
                    </div>
                    <p v-if="!asComponents(previewConfig(block)).length" class="empty-line">Добавьте компоненты сетапа.</p>
                  </div>
                </template>
              </div>
            </article>
          </VueDraggable>
        </ClientOnly>

        <button v-if="!blocks.length" class="empty-add" type="button" @click="panel = 'blocks'">
          <i class="ri-add-circle-line" />
          <span>Добавить первый блок</span>
        </button>
      </article>
    </section>

    <aside class="studio-inspector" aria-label="Инспектор профиля">
      <div class="studio-preview-bar">
        <div class="studio-status" aria-label="Сводка профиля">
          <span class="status-pill" :class="{ published: profile.isPublished }">
            <i :class="profile.isPublished ? 'ri-broadcast-line' : 'ri-draft-line'" />
            {{ profile.isPublished ? 'Опубликован' : 'Черновик' }}
          </span>
          <span class="count-pill" title="Видимые блоки">
            <i class="ri-stack-line" />
            {{ visibleBlocksCount }} / {{ blocks.length }}
          </span>
          <span class="url-pill">{{ publicUrlLabel }}</span>
        </div>

        <div class="studio-quick-actions">
          <button class="icon-action publish-action" type="button" :title="profile.isPublished ? 'Снять с публикации' : 'Опубликовать'" @click="toggleStatus">
            <i :class="profile.isPublished ? 'ri-eye-off-line' : 'ri-rocket-line'" />
            <span>{{ profile.isPublished ? 'Снять' : 'Опубликовать' }}</span>
          </button>
          <a class="icon-action" :href="publicPath" target="_blank" rel="noopener noreferrer" title="Открыть профиль">
            <i class="ri-external-link-line" />
            <span>Открыть</span>
          </a>
          <button class="icon-action" type="button" title="Скопировать ссылку" @click="copyLink">
            <i class="ri-file-copy-line" />
            <span>Копировать</span>
          </button>
        </div>
      </div>

      <div class="inspector-tabs">
        <button class="inspector-tab" :class="{ active: panel === 'profile' && !editingBlockId }" type="button" @click="openPanel('profile')">
          <i class="ri-user-settings-line" />
          <span>Профиль</span>
        </button>
        <button class="inspector-tab" :class="{ active: panel === 'blocks' || Boolean(editingBlockId) }" type="button" @click="openPanel('blocks')">
          <i class="ri-layout-grid-line" />
          <span>Блоки</span>
        </button>
      </div>

      <div class="inspector-body">
        <Transition name="inspector-pane" mode="out-in">
          <section v-if="panel === 'profile' && !editingBlockId" key="profile" class="inspector-section">
            <div class="section-head compact">
              <span class="section-icon"><i class="ri-user-smile-line" /></span>
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
                <span><i :class="currentColorMode === 'dark' ? 'ri-moon-clear-line' : 'ri-sun-line'" /></span>
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
                  <i class="ri-add-line" />
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
                  <span><i :class="isMaterial3Wide ? 'ri-layout-column-line' : 'ri-smartphone-line'" /></span>
                </span>
              </button>
            </div>
          </section>

          <section v-else-if="panel === 'blocks' && !editingBlockId" key="blocks" class="inspector-section">
            <div class="section-head compact">
              <span class="section-icon"><i class="ri-stack-line" /></span>
              <div>
                <h3>Блоки</h3>
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
                  <button
                    v-for="block in draggableBlocks"
                    :key="block.id"
                    class="mini-block"
                    :class="{ hidden: !block.is_visible }"
                    type="button"
                    @click="openBlockEditor(block)"
                  >
                    <span class="mini-handle" title="Перетащить" @click.stop><i class="ri-draggable" /></span>
                    <span class="mini-icon">
                      <FaceitLogo v-if="block.block_type === 'widget_faceit'" class="faceit-logo" />
                      <i v-else :class="displayBlockIcon(block)" />
                    </span>
                    <span class="mini-label">{{ displayBlockLabel(block) }}</span>
                    <span class="mini-actions">
                      <button class="tiny-action" :class="{ active: block.is_visible }" type="button" title="Видимость" @click.stop="toggleVisible(block)">
                        <i :class="block.is_visible ? 'ri-eye-line' : 'ri-eye-off-line'" />
                      </button>
                      <button class="tiny-action danger" type="button" title="Удалить" @click.stop="deleteBlock(block.id)">
                        <i class="ri-delete-bin-line" />
                      </button>
                    </span>
                  </button>
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
                  <i v-else :class="item.icon" />
                </span>
                <span>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.description }}</small>
                </span>
              </button>
            </div>
          </section>

          <section v-else-if="activeBlock" :key="`edit-${activeBlock.id}`" class="inspector-section">
            <div class="section-head">
              <button class="back-btn" type="button" title="Назад" @click="closeBlockEditor">
                <i class="ri-arrow-left-line" />
              </button>
              <span class="section-icon">
                <FaceitLogo v-if="activeBlock.block_type === 'widget_faceit'" class="faceit-logo" />
                <i v-else :class="displayBlockIcon(activeBlock)" />
              </span>
              <div>
                <h3>{{ displayBlockLabel(activeBlock) }}</h3>
                <p>{{ displayBlockDescription(activeBlock) }}</p>
              </div>
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
            <i class="ri-close-line" />
          </button>

          <div class="git-provider-head">
            <span class="git-provider-head-icon"><i class="ri-git-branch-line" /></span>
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
              <span><i :class="provider.icon" /></span>
              <strong>{{ provider.label }}</strong>
              <small>{{ provider.description }}</small>
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRequestURL } from '#app'
import { VueDraggable } from 'vue-draggable-plus'
import { resolveAvatarUrl } from '~/composables/useAvatarUrl'
import { useAuthStore } from '~/stores/auth'
import { useProfileStore, type Block } from '~/stores/profile'
import { extractAuthError } from '~/utils/auth-feedback'
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

interface SteamGame {
  appid?: number
  name: string
  playtime_2weeks?: number
  playtime_forever?: number
  playtime_recent_minutes?: number
  playtime_total_minutes?: number
  recent_hours?: number
  total_hours?: number
  last_played_at?: string | null
  hours?: number
}

interface GitRepository {
  id?: string
  name: string
  full_name?: string
  url?: string
  description?: string
  language?: string
  stars?: number
  forks?: number
  updated_at?: string | null
}

type NoticeTone = 'success' | 'info' | 'error'
type Panel = 'profile' | 'blocks'
type ThemeColorMode = 'light' | 'dark'
type Material3Layout = 'compact' | 'wide'
type GitProvider = 'github' | 'gitlab' | 'gitea'

interface ProfileThemeTokens {
  colorMode?: ThemeColorMode
  material3Layout?: Material3Layout
  [key: string]: unknown
}

const profile = useProfileStore()
const auth = useAuthStore()
const config = useRuntimeConfig()
const mock = useProfileMockData()
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

const panel = ref<Panel>('profile')
const editingBlockId = ref<string | null>(null)
const gitProviderModalOpen = ref(false)
const gitBlockAdding = ref(false)

const avatarTimestamp = ref(Date.now())
const avatarCropFile = ref<File | null>(null)
const avatarUploading = ref(false)
const avatarDisplaySrc = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarTimestamp.value),
)

const headerSaving = ref(false)
const blockSaving = ref(false)
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
const profileAccentStyle = computed<Record<string, string>>(() => {
  const fallbackAccent = currentTheme.value === 'glass' ? '#a8d8ff' : '#60cdff'
  return { '--profile-accent': currentTheme.value === 'material3' ? currentAccent.value : fallbackAccent }
})
const previewCardClasses = computed(() => [
  `theme-${currentTheme.value}`,
  { 'layout-wide': isMaterial3Wide.value },
])
const faceitAccentColor = computed(() => currentTheme.value === 'material3' ? currentAccent.value : null)
const publicPath = computed(() => profile.profile ? `/${profile.profile.slug}` : '/')
const publicUrl = computed(() => new URL(publicPath.value, requestOrigin).toString())
const publicUrlLabel = computed(() => profile.profile ? `${requestHost}/${profile.profile.slug}` : requestHost)
const profileInitial = computed(() =>
  profile.profile?.display_name?.trim().charAt(0).toUpperCase()
    || auth.user?.email?.trim().charAt(0).toUpperCase()
    || '?',
)

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

function confirmBlockSwitch() {
  if (!editingBlockId.value || !blockHasChanges()) return true
  return window.confirm('Есть несохраненные изменения в блоке. Закрыть редактор?')
}

function openPanel(next: Panel) {
  if (!confirmBlockSwitch()) return
  editingBlockId.value = null
  panel.value = next
  if (next === 'profile') initProfileForm()
}

function openBlockEditor(block: Block) {
  if (editingBlockId.value === block.id) return
  if (!confirmBlockSwitch()) return
  clearObject(blockDraft)
  Object.assign(blockDraft, cloneConfig(block.config))
  editingBlockId.value = block.id
  panel.value = 'blocks'
}

function closeBlockEditor() {
  if (!confirmBlockSwitch()) return
  editingBlockId.value = null
}

function previewConfig(block: Block) {
  return editingBlockId.value === block.id ? blockDraft : block.config
}

function asGroups(value: Record<string, unknown>): Group[] {
  return Array.isArray(value.groups) ? value.groups as Group[] : []
}

function asComponents(value: Record<string, unknown>): ComponentItem[] {
  return Array.isArray(value.components) ? value.components as ComponentItem[] : []
}

function steamGamesList(value: Record<string, unknown>): SteamGame[] {
  const liveGames = Array.isArray(value.steam_recent_games) ? value.steam_recent_games as SteamGame[] : []
  return liveGames
}

function steamDisplayName(value: Record<string, unknown>): string {
  const steamProfile = value.steam_profile as Record<string, unknown> | undefined
  return String(value.steam_display_name || steamProfile?.personaname || 'Steam не привязан')
}

function steamTotalHours(game: SteamGame): string {
  const hours = typeof game.total_hours === 'number'
    ? game.total_hours
    : typeof game.hours === 'number'
      ? game.hours
      : Math.round(((game.playtime_total_minutes || game.playtime_forever || 0) / 60) * 10) / 10
  return hours.toLocaleString('ru')
}

function steamRecentHours(game: SteamGame): string {
  const hours = typeof game.recent_hours === 'number'
    ? game.recent_hours
    : Math.round(((game.playtime_recent_minutes || game.playtime_2weeks || 0) / 60) * 10) / 10
  return hours.toLocaleString('ru')
}

function steamGameMeta(game: SteamGame): string {
  const meta: string[] = []
  if ((game.playtime_recent_minutes || game.playtime_2weeks || game.recent_hours) && steamRecentHours(game) !== '0') {
    meta.push(`${steamRecentHours(game)} ч за 2 недели`)
  }
  const lastPlayed = formatLastPlayed(game.last_played_at)
  if (lastPlayed) {
    meta.push(`последний запуск ${lastPlayed}`)
  }
  return meta.join(' · ')
}

function formatLastPlayed(value?: string | null): string {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('ru', { day: 'numeric', month: 'short' })
}

function steamStatsList(value: Record<string, unknown>) {
  const stats = value.steam_profile_stats as Record<string, unknown> | undefined
  if (!stats) return []
  return [
    { label: 'Level', value: stats.level },
    { label: 'Badges', value: stats.badge_count },
    { label: 'XP', value: stats.player_xp },
  ].filter(item => item.value !== undefined && item.value !== null && item.value !== '')
}

function inventoryStatus(value: Record<string, unknown>) {
  const item = value.steam_inventory_highlight as Record<string, unknown> | undefined
  if (!item) return null
  return {
    title: String(item.title || 'Инвентарь'),
    reason: String(item.reason || 'Источник цен не настроен.'),
  }
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

function gitUsername(value: Record<string, unknown>): string {
  const profile = value.git_profile as Record<string, unknown> | undefined
  return String(value.username || profile?.username || '')
}

function gitAccountCaption(value: Record<string, unknown>): string {
  const username = gitUsername(value)
  return username ? `@${username}` : 'Интеграция не привязана'
}

function gitRepositoryStats(value: Record<string, unknown>): Record<string, unknown> {
  const stats = value.git_repository_stats as Record<string, unknown> | undefined
  return stats && typeof stats === 'object' ? stats : {}
}

function gitRepositoryTotal(value: Record<string, unknown>): number | null {
  const total = gitRepositoryStats(value).total_repositories
  return typeof total === 'number' ? total : null
}

function gitRepositoryStatsList(value: Record<string, unknown>) {
  const stats = gitRepositoryStats(value)
  return [
    { label: 'Repos', value: stats.total_repositories },
    { label: 'Stars', value: stats.stars },
    { label: 'Forks', value: stats.forks },
  ].filter(item => item.value !== undefined && item.value !== null && item.value !== '')
}

function gitPinnedRepositories(value: Record<string, unknown>): GitRepository[] {
  const repos = Array.isArray(value.git_pinned_repositories) ? value.git_pinned_repositories as GitRepository[] : []
  return repos.slice(0, 3)
}

function gitActivitySummary(value: Record<string, unknown>): string {
  const last = gitRepositoryStats(value).last_activity_at
  if (typeof last !== 'string') return ''
  const formatted = formatLastPlayed(last)
  return formatted ? `Последняя активность в репозиториях: ${formatted}` : ''
}

function faceitPreviewData(value: Record<string, unknown>) {
  const live = value.faceit_profile as Record<string, any> | undefined
  if (live) {
    return {
      level: Number(live.skill_level || live.skill_level_label || 0),
      elo: live.faceit_elo || '—',
      kd: live.stats?.kd || '—',
      winRate: live.stats?.win_rate || '—',
    }
  }
  return null
}

function faceitDisplayName(value: Record<string, unknown>): string {
  const live = value.faceit_profile as Record<string, any> | undefined
  return String(value.faceit_display_name || value.nickname || live?.nickname || 'FACEIT не найден')
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
  if (!window.confirm('Удалить этот блок?')) return
  try {
    if (editingBlockId.value === id) editingBlockId.value = null
    await profile.deleteBlock(id)
    setNotice('Блок удален.', 'info')
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось удалить блок.'), 'error')
  }
}

async function toggleVisible(block: Block) {
  try {
    await profile.updateBlock(block.id, { is_visible: !block.is_visible })
  } catch (error) {
    setNotice(extractAuthError(error, 'Не удалось изменить видимость.'), 'error')
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
.studio-inspector,
.public-card {
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 88%, transparent);
  box-shadow: var(--dash-shadow, 0 16px 42px rgba(48, 63, 92, 0.11));
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
  background: var(--dash-warn-soft, #FFF0CF);
  color: var(--dash-warn, #9B6200);
}

.status-pill.published {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.url-pill {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-2, #475778);
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
  color: var(--card-muted);
  cursor: grab;
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
  background: color-mix(in srgb, var(--profile-accent, var(--dash-accent, #345EA8)) 16%, transparent);
  color: color-mix(in srgb, var(--profile-accent, var(--dash-accent, #345EA8)) 74%, #fff);
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
  border-bottom: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  background: color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 60%, transparent);
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
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
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
  color: var(--dash-text-1, #10182b);
  font-size: 20px;
  line-height: 1.15;
}

.section-head p {
  margin-top: 3px;
  color: var(--dash-text-2, #475778);
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
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.studio-field input,
.studio-field textarea,
.slug-input {
  width: 100%;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
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
  color: var(--dash-text-3, #66789c);
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
  border-color: var(--dash-accent, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 16%, transparent);
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
  background: linear-gradient(180deg, transparent, var(--dash-surface-strong, #fff) 24%);
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
  background: var(--dash-accent, #345EA8);
  color: #fff;
  border-color: transparent;
}

.ghost-btn {
  background: var(--dash-surface-strong, #fff);
}

.filled-btn:disabled,
.ghost-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.divider {
  height: 1px;
  background: var(--dash-outline, rgba(82, 103, 138, 0.18));
}

.section-subhead {
  color: var(--dash-text-1, #10182b);
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
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 44%, var(--dash-outline, #d4dbe8));
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
}

.theme-swatch {
  width: 58px;
  height: 48px;
  border-radius: 8px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
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
  color: var(--dash-text-1, #10182b);
  font-size: 14px;
}

.theme-option small {
  margin-top: 2px;
  color: var(--dash-text-2, #475778);
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
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 18%, transparent);
}

.accent-dot.custom {
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 18px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
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
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.custom-switch {
  width: 64px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  padding: 3px;
  border: 1px solid color-mix(in srgb, var(--dash-outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
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
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-2, #475778);
  box-shadow: 0 3px 9px color-mix(in srgb, var(--dash-text-1, #10182b) 12%, transparent);
  transform: translateX(0);
  transition:
    transform 280ms var(--m3-spring, cubic-bezier(0.2, 0, 0, 1)),
    color 180ms cubic-bezier(0.2, 0, 0, 1);
}

.custom-switch.active {
  border-color: transparent;
  background: var(--dash-accent, #345EA8);
}

.custom-switch.active span {
  color: var(--dash-accent-strong, #163E86);
  transform: translateX(28px);
}

.wide-switch.active {
  background: linear-gradient(135deg, var(--dash-accent, #345EA8), color-mix(in srgb, var(--dash-accent, #345EA8) 54%, #F59E0B));
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
  color: var(--dash-text-3, #66789c);
}

.mini-label {
  overflow: hidden;
  color: var(--dash-text-1, #10182b);
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 18px;
}

.library-item strong,
.library-item small {
  display: block;
}

.library-item strong {
  color: var(--dash-text-1, #10182b);
  font-size: 14px;
}

.library-item small {
  margin-top: 3px;
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  line-height: 1.35;
}

.muted-panel {
  padding: 14px;
  border-radius: 8px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  border: 1px solid color-mix(in srgb, var(--dash-outline, #d4dbe8) 64%, transparent);
  border-radius: 28px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 96%, transparent);
  box-shadow: 0 24px 70px color-mix(in srgb, #05070c 32%, transparent);
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
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
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
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 28px;
}

.git-provider-head h2,
.git-provider-head p {
  margin: 0;
}

.git-provider-head h2 {
  color: var(--dash-text-1, #10182b);
  font-size: 28px;
  line-height: 1.1;
}

.git-provider-head p {
  color: var(--dash-text-2, #475778);
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
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 18px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
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
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
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
  color: var(--dash-text-2, #475778);
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
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--dash-surface-strong, #fff) 58%, transparent), transparent 260px),
    color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 78%, transparent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62);
}

.public-card {
  width: min(100%, 760px);
  justify-self: center;
  box-shadow: var(--dash-shadow, 0 16px 42px rgba(48, 63, 92, 0.11));
}

.studio-inspector {
  top: 92px;
  max-height: calc(100vh - 110px);
  overflow: auto;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 94%, transparent);
}

.studio-preview-bar {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 0;
  border-bottom: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 0;
  background: color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 54%, transparent);
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
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 88%, transparent);
}

.inspector-tab.active {
  background: color-mix(in srgb, var(--dash-accent-soft, rgba(52,94,168,0.12)) 88%, white);
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
    linear-gradient(135deg, color-mix(in srgb, var(--dash-accent, #345EA8) 6%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--dash-surface-strong, #fff) 86%, transparent), color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 74%, transparent));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 16px 42px color-mix(in srgb, var(--dash-text-1, #10182b) 7%, transparent);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 11px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 78%, transparent);
  color: var(--dash-text-2, #475778);
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
  border: 1px solid color-mix(in srgb, var(--dash-outline, rgba(82, 103, 138, 0.18)) 82%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 82%, transparent);
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
  color: var(--dash-accent-strong, #173F86);
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
  color: var(--dash-text-2, #475778);
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
  background: var(--dash-accent, #345EA8);
  color: #fff;
  box-shadow: none;
}

.public-card {
  width: min(100%, 720px);
  gap: 12px;
  padding: clamp(14px, 1.5vw, 20px);
  border-radius: 24px;
  box-shadow:
    0 18px 46px color-mix(in srgb, var(--dash-text-1, #10182b) 14%, transparent),
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
    linear-gradient(180deg, color-mix(in srgb, var(--dash-surface-strong, #fff) 96%, transparent), color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 70%, transparent));
  box-shadow:
    0 20px 48px color-mix(in srgb, var(--dash-text-1, #10182b) 10%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.inspector-tabs {
  flex: 0 0 auto;
  gap: 6px;
  margin: 10px 10px 0;
  padding: 5px;
  border: 0;
  border-radius: 999px;
  background: color-mix(in srgb, var(--dash-surface-soft, #F2F4F8) 78%, transparent);
}

.inspector-tab {
  min-height: 42px;
  border-radius: 999px;
}

.inspector-tab.active {
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-accent-strong, #163E86);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--dash-text-1, #10182b) 8%, transparent);
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

.studio-field input,
.studio-field textarea,
.slug-input {
  border-radius: 18px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 92%, transparent);
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
  box-shadow: 0 10px 26px color-mix(in srgb, var(--dash-text-1, #10182b) 8%, transparent);
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
}
</style>
