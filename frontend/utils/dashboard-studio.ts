export type DashboardThemeId = 'material3' | 'glass' | 'fluent'

export type BlockCatalogItem = {
  type: string
  icon: string
  label: string
  description: string
}

export type ThemeCatalogItem = {
  id: DashboardThemeId
  label: string
  sub: string
}

export const BLOCK_LIBRARY: BlockCatalogItem[] = [
  {
    type: 'links',
    icon: 'ri-links-line',
    label: 'Ссылки',
    description: 'Telegram, GitHub, портфолио, магазин или любой важный переход.',
  },
  {
    type: 'text',
    icon: 'ri-quill-pen-line',
    label: 'Текст',
    description: 'Короткое вступление, заметка, правила или мини-FAQ.',
  },
  {
    type: 'widget_steam',
    icon: 'ri-steam-fill',
    label: 'Steam',
    description: 'Последние игры, часы, уровень Steam и статус инвентаря.',
  },
  {
    type: 'widget_lastfm',
    icon: 'ri-disc-line',
    label: 'Last.fm',
    description: 'Музыка и трек, который сейчас играет.',
  },
  {
    type: 'widget_spotify',
    icon: 'ri-spotify-fill',
    label: 'Spotify',
    description: 'Текущий трек, последние прослушивания и музыкальные топы Spotify.',
  },
  {
    type: 'widget_github',
    icon: 'ri-github-fill',
    label: 'Git',
    description: 'Профиль, статистика и закрепленные репозитории GitHub, GitLab или Gitea.',
  },
  {
    type: 'widget_faceit',
    icon: 'ri-trophy-line',
    label: 'FACEIT',
    description: 'Ник, уровень, ELO и краткая игровая статистика.',
  },
  {
    type: 'pc_config',
    icon: 'ri-computer-line',
    label: 'Конфиг ПК',
    description: 'Железо, рабочий сетап или любимая машина.',
  },
]

export const THEME_LIBRARY: ThemeCatalogItem[] = [
  { id: 'material3', label: 'M3 Expressive', sub: 'Чистые поверхности, живой акцент и мягкое движение.' },
  { id: 'glass', label: 'Liquid Glass', sub: 'Полупрозрачные панели и глубина для медиа-профиля.' },
  { id: 'fluent', label: 'Fluent', sub: 'Спокойный контраст, строгий ритм и плотные списки.' },
]

export const ACCENT_COLORS = [
  { label: 'Indigo', value: '#345EA8' },
  { label: 'Sky', value: '#3D8EFF' },
  { label: 'Teal', value: '#14B8A6' },
  { label: 'Green', value: '#22C55E' },
  { label: 'Amber', value: '#F59E0B' },
  { label: 'Orange', value: '#F97316' },
  { label: 'Pink', value: '#EC4899' },
  { label: 'Rose', value: '#F43F5E' },
] as const

export const M3_PALETTES = [
  { name: 'Stellalink Blue', accent: '#345EA8', colors: ['#DCE7FF', '#B5C7FF', '#6A8BDE', '#345EA8', '#163166'] },
  { name: 'Ocean', accent: '#3D8EFF', colors: ['#D9ECFF', '#A0C4FF', '#3D8EFF', '#1565C0', '#0D3B72'] },
  { name: 'Mint', accent: '#14B8A6', colors: ['#D4FFF8', '#99F6E4', '#14B8A6', '#0D9488', '#134E4A'] },
  { name: 'Sunset', accent: '#F97316', colors: ['#FFE5D2', '#FDBA74', '#F97316', '#C2410C', '#7C2D12'] },
  { name: 'Rose', accent: '#F43F5E', colors: ['#FFD6DC', '#FDA4AF', '#F43F5E', '#BE123C', '#881337'] },
] as const

const DEFAULT_CONFIGS: Record<string, Record<string, unknown>> = {
  links: { groups: [{ title: '', links: [] }] },
  text: { content: '', format: 'markdown' },
  widget_steam: {
    use_connected_account: true,
    show_recent_games: true,
    show_profile_stats: true,
    show_inventory_highlight: true,
  },
  widget_lastfm: { username: '', show_now_playing: true },
  widget_spotify: {
    use_connected_account: true,
    show_now_playing: true,
    show_recent_tracks: true,
    show_top_tracks: true,
    show_top_artists: true,
    show_stats: true,
  },
  widget_github: {
    provider: 'github',
    use_connected_account: true,
    show_contributions: true,
    contributions_days: 30,
    show_repository_stats: true,
    show_pinned_repos: true,
    include_private_repositories: false,
  },
  widget_faceit: { game: 'cs2' },
  pc_config: { title: 'My Rig', components: [] },
}

export function blockLabel(type: string): string {
  return BLOCK_LIBRARY.find(item => item.type === type)?.label ?? type
}

export function blockIcon(type: string): string {
  return BLOCK_LIBRARY.find(item => item.type === type)?.icon ?? 'ri-shapes-line'
}

export function blockDescription(type: string): string {
  return BLOCK_LIBRARY.find(item => item.type === type)?.description ?? 'Настройте блок под свой профиль.'
}

export function createDefaultBlockConfig(type: string): Record<string, unknown> {
  return JSON.parse(JSON.stringify(DEFAULT_CONFIGS[type] ?? {}))
}
