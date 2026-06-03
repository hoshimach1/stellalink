<template>
  <div class="block-form">
    <template v-if="type === 'links'">
      <section v-for="(group, groupIndex) in linkGroups()" :key="groupIndex" class="bf-section">
        <div class="bf-section-head">
          <div>
            <strong>Группа {{ groupIndex + 1 }}</strong>
            <span>Заголовок можно оставить пустым.</span>
          </div>
          <button class="bf-icon danger" type="button" title="Удалить группу" @click="removeLinkGroup(groupIndex)">
            <i class="ri-delete-bin-line" />
          </button>
        </div>

        <label class="bf-field">
          <span>Заголовок группы</span>
          <input v-model="group.title" type="text" placeholder="Соцсети">
        </label>

        <div class="bf-stack">
          <article v-for="(link, linkIndex) in group.links" :key="linkIndex" class="bf-link">
            <div class="bf-link-head">
              <strong>Ссылка {{ linkIndex + 1 }}</strong>
              <button class="bf-icon danger" type="button" title="Удалить ссылку" @click="group.links.splice(linkIndex, 1)">
                <i class="ri-close-line" />
              </button>
            </div>

            <div class="bf-grid">
              <label class="bf-field">
                <span>Название</span>
                <input v-model="link.label" type="text" placeholder="Telegram">
              </label>
              <label class="bf-field">
                <span>URL</span>
                <input v-model="link.url" type="url" placeholder="https://t.me/username">
              </label>
            </div>

            <label class="bf-field">
              <span>Иконка</span>
              <div class="bf-icons">
                <button
                  v-for="icon in POPULAR_ICONS"
                  :key="icon"
                  class="bf-icon-choice"
                  :class="{ active: link.icon === icon }"
                  type="button"
                  :title="icon"
                  @click="link.icon = link.icon === icon ? '' : icon"
                >
                  <i :class="`ri-${icon}-fill`" />
                </button>
              </div>
              <div class="bf-inline">
                <span v-if="link.icon" class="bf-icon-preview"><i :class="`ri-${link.icon}-fill`" /></span>
                <input v-model="link.icon" type="text" placeholder="github, vk, telegram">
              </div>
            </label>
          </article>
        </div>

        <button class="bf-secondary" type="button" @click="addLink(groupIndex)">
          <i class="ri-add-line" />
          <span>Добавить ссылку</span>
        </button>
      </section>

      <button class="bf-secondary wide" type="button" @click="addLinkGroup">
        <i class="ri-folder-add-line" />
        <span>Добавить группу</span>
      </button>
    </template>

    <template v-else-if="type === 'text'">
      <label class="bf-field">
        <span>Текст блока</span>
        <textarea v-model="config.content" rows="8" placeholder="Коротко о себе, проекте, правилах или расписании." />
      </label>
    </template>

    <template v-else-if="type === 'widget_steam'">
      <div class="bf-readonly">
        <span>Аккаунт Steam</span>
        <strong>{{ steamDisplayName() }}</strong>
        <small>{{ steamSubLabel() }}</small>
      </div>
      <label class="bf-check">
        <input v-model="config.show_recent_games" type="checkbox">
        <span>Последние игры и часы</span>
      </label>
      <label class="bf-check">
        <input v-model="config.show_profile_stats" type="checkbox">
        <span>Статистика профиля Steam: уровень, значки, XP</span>
      </label>
      <label class="bf-check">
        <input v-model="config.show_inventory_highlight" type="checkbox">
        <span>Самый дорогой предмет инвентаря, если источник цен доступен</span>
      </label>
      <div class="bf-note">
        Обычный Steam Web API не отдаёт рыночные цены предметов. Если цены недоступны, блок покажет честное предупреждение вместо выдуманной оценки.
      </div>
    </template>

    <template v-else-if="type === 'widget_lastfm'">
      <label class="bf-field">
        <span>Ник Last.fm</span>
        <input v-model="config.username" type="text" placeholder="username">
      </label>
      <label class="bf-check">
        <input v-model="config.show_now_playing" type="checkbox">
        <span>Показывать текущий трек</span>
      </label>
    </template>

    <template v-else-if="type === 'widget_github'">
      <div class="bf-readonly">
        <span>Git-профиль</span>
        <strong>{{ gitDisplayName() }}</strong>
        <small>{{ gitSubLabel() }}</small>
      </div>
      <label class="bf-check">
        <input v-model="config.show_contributions" type="checkbox">
        <span>Показывать активность</span>
      </label>
      <div v-if="config.show_contributions" class="bf-field">
        <span>Период активности</span>
        <div class="bf-segments bf-segments-activity" role="group" aria-label="Период активности Git">
          <button
            v-for="days in CONTRIBUTION_DAY_OPTIONS"
            :key="days"
            class="bf-segment"
            :class="{ active: contributionDays() === days }"
            type="button"
            @click="config.contributions_days = days"
          >
            {{ days }} дн.
          </button>
        </div>
      </div>
      <label class="bf-check">
        <input v-model="config.show_repository_stats" type="checkbox">
        <span>Показывать статистику репозиториев</span>
      </label>
      <label class="bf-check">
        <input v-model="config.show_pinned_repos" type="checkbox">
        <span>Показывать закрепленные репозитории</span>
      </label>
      <label class="bf-check">
        <input v-model="config.include_private_repositories" type="checkbox">
        <span>Учитывать приватные репозитории в публичном блоке</span>
      </label>
      <div class="bf-note">
        По умолчанию публичный профиль не раскрывает приватные репозитории даже при подключенном token с доступом к ним.
      </div>
    </template>

    <template v-else-if="type === 'widget_faceit'">
      <div class="bf-readonly">
        <span>Аккаунт FACEIT</span>
        <strong>{{ faceitDisplayName() }}</strong>
        <small>{{ faceitSubLabel() }}</small>
      </div>
      <div class="bf-field">
        <span>Игра</span>
        <div class="bf-segments" role="group" aria-label="Игра FACEIT">
          <button class="bf-segment" :class="{ active: !config.game || config.game === 'cs2' }" type="button" @click="config.game = 'cs2'">
            CS2
          </button>
          <button class="bf-segment" :class="{ active: config.game === 'csgo' }" type="button" @click="config.game = 'csgo'">
            CS:GO
          </button>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'pc_config'">
      <label class="bf-field">
        <span>Название конфига</span>
        <input v-model="config.title" type="text" placeholder="Основной сетап">
      </label>

      <section class="bf-section">
        <div class="bf-section-head">
          <div>
            <strong>Компоненты</strong>
            <span>CPU, GPU, RAM, монитор и другие части сетапа.</span>
          </div>
        </div>

        <div class="bf-stack">
          <div v-for="(component, index) in pcComponents()" :key="index" class="bf-grid bf-component">
            <label class="bf-field">
              <span>Категория</span>
              <input v-model="component.category" type="text" placeholder="CPU">
            </label>
            <label class="bf-field">
              <span>Значение</span>
              <div class="bf-inline">
                <input v-model="component.name" type="text" placeholder="AMD Ryzen 5 7500F">
                <button class="bf-icon danger" type="button" title="Удалить компонент" @click="pcComponents().splice(index, 1)">
                  <i class="ri-close-line" />
                </button>
              </div>
            </label>
          </div>
        </div>

        <button class="bf-secondary" type="button" @click="addComponent">
          <i class="ri-add-line" />
          <span>Добавить компонент</span>
        </button>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
interface Link {
  label: string
  url: string
  icon: string
}

interface Group {
  title: string
  links: Link[]
}

interface Component {
  category: string
  name: string
}

const props = defineProps<{ type: string; config: Record<string, unknown> }>()

const type = props.type
const config = props.config

const POPULAR_ICONS = [
  'telegram',
  'vk',
  'github',
  'twitter-x',
  'instagram',
  'youtube',
  'discord',
  'twitch',
  'tiktok',
  'linkedin',
  'spotify',
  'steam',
  'reddit',
  'behance',
  'dribbble',
]

const GIT_PROVIDER_LABELS: Record<string, string> = {
  github: 'GitHub',
  gitlab: 'GitLab',
  gitea: 'Gitea',
}
const CONTRIBUTION_DAY_OPTIONS = [7, 14, 30, 90]

function linkGroups(): Group[] {
  if (!Array.isArray(config.groups)) {
    config.groups = [{ title: '', links: [] }]
  }
  return config.groups as Group[]
}

function addLinkGroup() {
  linkGroups().push({ title: '', links: [] })
}

function removeLinkGroup(index: number) {
  linkGroups().splice(index, 1)
  if (!linkGroups().length) addLinkGroup()
}

function addLink(index: number) {
  const group = linkGroups()[index]
  if (!group) return
  if (!Array.isArray(group.links)) group.links = []
  group.links.push({ label: '', url: '', icon: '' })
}

function pcComponents(): Component[] {
  if (!Array.isArray(config.components)) {
    config.components = []
  }
  return config.components as Component[]
}

function addComponent() {
  pcComponents().push({ category: '', name: '' })
}

function steamDisplayName(): string {
  const profile = config.steam_profile as Record<string, unknown> | undefined
  return String(config.steam_display_name || profile?.personaname || 'Steam не привязан')
}

function steamSubLabel(): string {
  return config.steam_id
    ? 'Подключен через официальный вход Steam'
    : 'Подключите Steam в разделе интеграций'
}

function faceitDisplayName(): string {
  const profile = config.faceit_profile as Record<string, unknown> | undefined
  return String(config.faceit_display_name || config.nickname || profile?.nickname || 'FACEIT не найден')
}

function faceitSubLabel(): string {
  const profile = config.faceit_profile as Record<string, unknown> | undefined
  const elo = profile?.faceit_elo ? `${profile.faceit_elo} ELO` : ''
  const level = profile?.skill_level ? `уровень ${profile.skill_level}` : ''
  return [level, elo].filter(Boolean).join(' · ') || 'FACEIT подтягивается автоматически через Steam'
}

function gitProvider(): string {
  const provider = String(config.provider || config.git_provider || 'github')
  return ['github', 'gitlab', 'gitea'].includes(provider) ? provider : 'github'
}

function gitDisplayName(): string {
  const profile = config.git_profile as Record<string, unknown> | undefined
  return String(config.git_display_name || config.github_display_name || profile?.display_name || profile?.username || config.username || 'Git-профиль не привязан')
}

function contributionDays(): number {
  const days = Number(config.contributions_days || 30)
  return CONTRIBUTION_DAY_OPTIONS.includes(days) ? days : 30
}

function gitSubLabel(): string {
  const provider = String(config.git_provider_label || GIT_PROVIDER_LABELS[gitProvider()] || 'Git')
  const stats = config.git_repository_stats as Record<string, unknown> | undefined
  const total = stats?.total_repositories
  return total !== undefined && total !== null
    ? `${provider} · ${total} репозиториев`
    : `Подключите ${provider} в разделе интеграций`
}
</script>

<style scoped>
.block-form {
  display: grid;
  gap: 12px;
}

.bf-section,
.bf-link {
  display: grid;
  gap: 12px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-soft, #f2f4f8) 68%, transparent);
}

.bf-section {
  padding: 12px;
}

.bf-link {
  padding: 12px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 88%, transparent);
}

.bf-section-head,
.bf-link-head,
.bf-inline {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bf-section-head,
.bf-link-head {
  justify-content: space-between;
}

.bf-section-head strong,
.bf-link-head strong {
  display: block;
  color: var(--dash-text-1, #10182b);
  font-size: 14px;
  font-weight: 900;
}

.bf-section-head span {
  display: block;
  margin-top: 2px;
  color: var(--dash-text-3, #66789c);
  font-size: 12px;
  line-height: 1.4;
}

.bf-stack {
  display: grid;
  gap: 10px;
}

.bf-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.bf-field {
  display: grid;
  gap: 6px;
}

.bf-field > span {
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
}

.bf-field input,
.bf-field textarea {
  width: 100%;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  outline: none;
  transition: border-color 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.bf-field input {
  min-height: 42px;
  padding: 0 12px;
}

.bf-field textarea {
  min-height: 124px;
  padding: 10px 12px;
  resize: vertical;
}

.bf-field input:focus,
.bf-field textarea:focus {
  border-color: var(--dash-accent, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 16%, transparent);
}

.bf-icons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bf-icon,
.bf-icon-choice,
.bf-secondary,
.bf-segment {
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-2, #475778);
  font: inherit;
  cursor: pointer;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    color 180ms cubic-bezier(0.2, 0, 0, 1);
}

.bf-icon,
.bf-icon-choice {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 8px;
  font-size: 18px;
}

.bf-icon-preview {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-accent, #345EA8) 12%, transparent);
  color: var(--dash-accent, #345EA8);
  font-size: 18px;
}

.bf-icon-choice.active,
.bf-segment.active {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 38%, var(--dash-outline, #d4dbe8));
  background: color-mix(in srgb, var(--dash-accent, #345EA8) 12%, var(--dash-surface-strong, #fff));
  color: var(--dash-accent, #345EA8);
}

.bf-secondary {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 900;
}

.bf-secondary.wide {
  width: 100%;
}

.bf-check {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font-size: 14px;
}

.bf-check input {
  width: 18px;
  height: 18px;
  accent-color: var(--dash-accent, #345EA8);
}

.bf-note {
  padding: 10px 12px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  line-height: 1.45;
}

.bf-readonly {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
}

.bf-readonly span {
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.bf-readonly strong {
  color: var(--dash-text-1, #10182b);
  font-size: 15px;
  font-weight: 950;
  overflow-wrap: anywhere;
}

.bf-readonly small {
  color: var(--dash-text-3, #66789c);
  font-size: 12px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.bf-segments {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.bf-segments-activity {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.bf-segment {
  min-height: 42px;
  border-radius: 999px;
  font-weight: 900;
}

.bf-component .bf-inline {
  align-items: stretch;
}

.bf-inline input {
  min-width: 0;
}

.danger:hover {
  border-color: color-mix(in srgb, var(--dash-red, #B3323A) 34%, var(--dash-outline, #d4dbe8));
  background: var(--dash-red-soft, #FFE5E7);
  color: var(--dash-red, #B3323A);
}

@media (hover: hover) {
  .bf-icon:hover,
  .bf-icon-choice:hover,
  .bf-secondary:hover,
  .bf-segment:hover {
    transform: translateY(-1px);
  }
}

@media (max-width: 640px) {
  .bf-grid {
    grid-template-columns: 1fr;
  }

  .bf-segments-activity {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .bf-inline {
    align-items: stretch;
  }
}

/* Material 3 Expressive form surfaces */
.block-form {
  --bf-ease: cubic-bezier(0.2, 0, 0, 1);
  --bf-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  gap: 14px;
}

.bf-section,
.bf-link,
.bf-note,
.bf-readonly {
  border-radius: 22px;
}

.bf-section {
  padding: 14px;
  background: color-mix(in srgb, var(--dash-surface-soft, #f2f4f8) 76%, transparent);
}

.bf-link {
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 94%, transparent);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--dash-text-1, #10182b) 5%, transparent);
}

.bf-section-head strong,
.bf-link-head strong {
  font-weight: 950;
}

.bf-field input,
.bf-field textarea {
  border-radius: 18px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 94%, transparent);
}

.bf-field input {
  min-height: 48px;
}

.bf-field textarea {
  min-height: 132px;
}

.bf-icon,
.bf-icon-choice,
.bf-secondary,
.bf-segment,
.bf-check {
  transition:
    transform 240ms var(--bf-spring),
    background 180ms var(--bf-ease),
    border-color 180ms var(--bf-ease),
    color 180ms var(--bf-ease),
    box-shadow 180ms var(--bf-ease);
}

.bf-icon,
.bf-icon-choice,
.bf-icon-preview {
  border-radius: 14px;
}

.bf-icon,
.bf-icon-choice {
  width: 44px;
  height: 44px;
}

.bf-secondary,
.bf-segment {
  min-height: 48px;
}

.bf-secondary {
  background: color-mix(in srgb, var(--dash-accent-soft, rgba(52,94,168,0.12)) 68%, var(--dash-surface-strong, #fff));
  color: var(--dash-accent-strong, #163E86);
}

.bf-check {
  min-height: 56px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 94%, transparent);
}

.bf-check input {
  width: 20px;
  height: 20px;
}

.bf-segment.active,
.bf-icon-choice.active {
  box-shadow: 0 8px 18px color-mix(in srgb, var(--dash-accent, #345EA8) 12%, transparent);
}

@media (hover: hover) {
  .bf-check:hover,
  .bf-link:hover {
    border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 26%, var(--dash-outline, #d4dbe8));
  }
}
</style>
