<template>
  <div v-if="pending" class="pub-loading"><div class="pub-spinner" /></div>

  <div v-else-if="!profile" class="pub-notfound">
    <img src="/images/logos/logo.png" alt="" class="pub-nf-logo">
    <h2>Профиль не найден</h2>
    <p>Пользователь <strong>{{ $route.params.slug }}</strong> не существует или ещё не опубликовал профиль.</p>
    <NuxtLink to="/" class="pub-home-btn">На главную</NuxtLink>
  </div>

  <div v-else class="pub-page">
    <div class="pub-glow" />

    <!-- Header -->
    <div class="pub-header">
      <div class="pub-avatar">
        <img v-if="profile.avatar_url" :src="profile.avatar_url" class="pub-avatar-img" alt="avatar">
        <span v-else>{{ initial }}</span>
      </div>
      <h1 class="pub-name">{{ profile.display_name }}</h1>
      <p v-if="profile.bio" class="pub-bio">{{ profile.bio }}</p>
      <div v-if="profile.tags.length" class="pub-tags">
        <span v-for="tag in profile.tags" :key="tag" class="pub-tag">{{ tag }}</span>
      </div>
    </div>

    <!-- Blocks -->
    <div class="pub-blocks">
      <template v-for="block in visibleBlocks" :key="block.id">

        <!-- Links -->
        <div v-if="block.block_type === 'links'" class="pub-block-links">
          <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
            <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
            <a
              v-for="link in group.links"
              :key="link.url"
              :href="link.url"
              target="_blank"
              rel="noopener"
              class="pub-link"
            >
              <span class="pub-link-icon-wrap">
                <i v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                <i v-else class="ri-link pub-link-icon" />
              </span>
              <span class="pub-link-label">{{ link.label || link.url }}</span>
              <i class="ri-arrow-right-up-line pub-link-arrow" />
            </a>
          </div>
        </div>

        <!-- Text -->
        <div v-else-if="block.block_type === 'text'" class="pub-block pub-text">
          {{ (block.config.content as string) }}
        </div>

        <!-- Steam -->
        <div v-else-if="block.block_type === 'widget_steam'" class="pub-block">
          <div class="pub-wh">
            <div class="pub-wh-left">
              <div class="pub-w-ico-bg" style="background:rgba(25,144,212,0.15);color:#66c0f4">🎮</div>
              <div>
                <div class="pub-w-name">Steam</div>
                <div class="pub-w-id">{{ block.config.steam_id || '—' }}</div>
              </div>
            </div>
            <span class="pub-badge-green">● Online</span>
          </div>
          <template v-if="block.config.show_recent_games && block.config.steam_id">
            <div class="pub-divider" />
            <div class="pub-sub-label">Недавно в игре</div>
            <div v-for="g in mock.steamGames(block.config.steam_id as string)" :key="g.name" class="pub-steam-row">
              <span class="pub-steam-name">{{ g.name }}</span>
              <span class="pub-steam-h">{{ g.hours.toLocaleString('ru') }} ч</span>
            </div>
          </template>
        </div>

        <!-- Last.fm -->
        <div v-else-if="block.block_type === 'widget_lastfm'" class="pub-block">
          <div class="pub-wh">
            <div class="pub-wh-left">
              <div class="pub-w-ico-bg" style="background:rgba(200,0,0,0.15);color:#e5343a">🎵</div>
              <div>
                <div class="pub-w-name">Last.fm</div>
                <div class="pub-w-id">@{{ block.config.username || '—' }}</div>
              </div>
            </div>
            <div v-if="block.config.show_now_playing && block.config.username" class="pub-np-bars">
              <span v-for="i in 5" :key="i" class="pub-np-bar" :style="`animation-delay:${(i-1)*0.18}s`" />
            </div>
          </div>
          <template v-if="block.config.show_now_playing && block.config.username">
            <div class="pub-divider" />
            <div class="pub-np-row">
              <div class="pub-np-disc">♫</div>
              <div>
                <div class="pub-np-label">Сейчас слушает</div>
                <div class="pub-np-track">{{ mock.lastfmTrack(block.config.username as string).track }}</div>
                <div class="pub-np-artist">{{ mock.lastfmTrack(block.config.username as string).artist }}</div>
              </div>
            </div>
          </template>
        </div>

        <!-- GitHub -->
        <div v-else-if="block.block_type === 'widget_github'" class="pub-block">
          <div class="pub-wh">
            <div class="pub-wh-left">
              <div class="pub-w-ico-bg" style="background:rgba(255,255,255,0.06);color:#eeeef8">🐙</div>
              <div>
                <div class="pub-w-name">GitHub</div>
                <div class="pub-w-id">@{{ block.config.username || '—' }}</div>
              </div>
            </div>
            <span v-if="block.config.username" class="pub-gh-repos-badge">
              {{ mock.ghStats(block.config.username as string).repos }} репо
            </span>
          </div>
          <template v-if="block.config.username">
            <div class="pub-divider" />
            <div class="pub-gh-grid-wrap">
              <div class="pub-gh-grid">
                <div
                  v-for="(level, i) in mock.ghHeatmap(block.config.username as string)"
                  :key="i"
                  class="pub-gh-cell"
                  :class="`pub-gh-l${level}`"
                />
              </div>
            </div>
            <div class="pub-gh-count">
              {{ mock.ghStats(block.config.username as string).contributions.toLocaleString('ru') }} contributions за последний год
            </div>
            <template v-if="block.config.show_pinned_repos">
              <div class="pub-sub-label" style="margin-top:12px">Закреплённые репозитории</div>
              <div class="pub-gh-repos">
                <div v-for="r in mock.ghRepos(block.config.username as string)" :key="r" class="pub-gh-repo">
                  <i class="ri-git-repository-line" />
                  <span>{{ block.config.username }}/{{ r }}</span>
                </div>
              </div>
            </template>
          </template>
        </div>

        <!-- PC Config -->
        <div v-else-if="block.block_type === 'pc_config'" class="pub-block">
          <div class="pub-wh" style="margin-bottom:0">
            <div class="pub-wh-left">
              <div class="pub-w-ico-bg" style="background:rgba(61,142,255,0.12);color:#90beff">💻</div>
              <div class="pub-w-name">{{ (block.config.title as string) || 'PC Config' }}</div>
            </div>
          </div>
          <template v-if="(block.config.components as Component[]).length">
            <div class="pub-divider" style="margin-top:12px" />
            <div class="pub-pc-list">
              <div v-for="c in (block.config.components as Component[])" :key="c.category" class="pub-pc-row">
                <span class="pub-pc-cat">{{ c.category }}</span>
                <span class="pub-pc-val">{{ c.name }}</span>
              </div>
            </div>
          </template>
        </div>

        <!-- Faceit -->
        <div v-else-if="block.block_type === 'widget_faceit'" class="pub-block">
          <div class="pub-wh">
            <div class="pub-wh-left">
              <div class="pub-w-ico-bg" style="background:rgba(255,90,0,0.15);color:#ff8c42">⚡</div>
              <div>
                <div class="pub-w-name">FACEIT · CS2</div>
                <div class="pub-w-id">{{ block.config.nickname || '—' }}</div>
              </div>
            </div>
            <div
              v-if="block.config.nickname"
              class="pub-faceit-lvl"
              :style="`background:${mock.faceitLevelColor(mock.faceitData(block.config.nickname as string).level)}`"
            >{{ mock.faceitData(block.config.nickname as string).level }}</div>
          </div>
          <template v-if="block.config.nickname">
            <div class="pub-divider" />
            <div class="pub-faceit-stats">
              <div class="pub-faceit-stat">
                <div class="pub-fstat-v">{{ mock.faceitData(block.config.nickname as string).elo }}</div>
                <div class="pub-fstat-l">ELO</div>
              </div>
              <div class="pub-faceit-stat">
                <div class="pub-fstat-v">{{ mock.faceitData(block.config.nickname as string).kd }}</div>
                <div class="pub-fstat-l">K/D</div>
              </div>
              <div class="pub-faceit-stat">
                <div class="pub-fstat-v">{{ mock.faceitData(block.config.nickname as string).winRate }}%</div>
                <div class="pub-fstat-l">Win Rate</div>
              </div>
              <div class="pub-faceit-stat">
                <div class="pub-fstat-v">{{ mock.faceitData(block.config.nickname as string).matches }}</div>
                <div class="pub-fstat-l">Матчи</div>
              </div>
            </div>
          </template>
        </div>

      </template>
    </div>

    <!-- Footer -->
    <div class="pub-footer">
      <NuxtLink to="/" class="pub-footer-link">
        <img src="/images/logos/logo.png" alt="" class="pub-footer-logo">
        Сделано на Stellalink
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Block } from '~/stores/profile'

interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }

definePageMeta({ layout: 'landing' })

const route = useRoute()
const config = useRuntimeConfig()
const slug = route.params.slug as string

const mock = useProfileMockData()

const { data: profile, pending } = await useFetch<{
  id: string
  slug: string
  status: string
  display_name: string
  bio: string | null
  tags: string[]
  blocks: Block[]
  avatar_url: string | null
} | null>(`${config.public.apiBase}/u/${slug}`, {
  default: () => null,
  onResponseError() { return null },
})

const pageTitle = computed(() => {
  const name = profile.value?.display_name
  return name ? `${name} — Stellalink` : `${slug} — Stellalink`
})
useHead({ title: pageTitle })

const initial = computed(() => profile.value?.display_name?.[0]?.toUpperCase() ?? '?')
const visibleBlocks = computed(() => profile.value?.blocks.filter(b => b.is_visible) ?? [])
</script>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css');
</style>

<style scoped>
/* ── Loading / 404 ──────────────────────────────────────────────────────────── */
.pub-loading {
  min-height: 100vh; background: #090910;
  display: flex; align-items: center; justify-content: center;
}
.pub-spinner {
  width: 36px; height: 36px; border-radius: 50%;
  border: 3px solid rgba(61,142,255,0.2); border-top-color: #3D8EFF;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pub-notfound {
  min-height: 100vh; background: #090910; color: #eeeef8;
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 24px; gap: 12px;
}
.pub-nf-logo { width: 56px; opacity: 0.5; mix-blend-mode: screen; }
.pub-notfound h2 { font-size: 24px; font-weight: 800; }
.pub-notfound p { color: #6a6a90; font-size: 15px; }
.pub-home-btn {
  margin-top: 8px; padding: 10px 24px;
  background: rgba(61,142,255,0.12); border: 1px solid rgba(61,142,255,0.24);
  border-radius: 10px; color: #90beff; text-decoration: none; font-size: 14px;
}

/* ── Page ───────────────────────────────────────────────────────────────────── */
.pub-page {
  min-height: 100vh; background: #090910; color: #eeeef8;
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center;
  padding: 56px 16px 48px; position: relative; overflow-x: hidden;
}
.pub-glow {
  position: fixed; top: 0; left: 50%; transform: translateX(-50%);
  width: 700px; height: 320px; pointer-events: none;
  background: radial-gradient(ellipse 60% 80% at 50% 0%, rgba(61,142,255,0.09), transparent);
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
.pub-header {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; width: 100%; max-width: 520px; margin-bottom: 32px; gap: 10px;
}
.pub-avatar {
  width: 88px; height: 88px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 34px; font-weight: 800; color: #fff; overflow: hidden;
  box-shadow: 0 0 0 3px rgba(61,142,255,0.20), 0 8px 32px rgba(61,142,255,0.20);
  margin-bottom: 4px;
}
.pub-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.pub-name { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; margin: 0; }
.pub-bio { font-size: 14px; color: #8888aa; line-height: 1.5; margin: 0; max-width: 360px; }
.pub-tags { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }
.pub-tag {
  background: rgba(61,142,255,0.10); color: #90beff;
  border: 1px solid rgba(61,142,255,0.18); border-radius: 100px;
  padding: 3px 12px; font-size: 12px; font-weight: 500;
}

/* ── Blocks container ───────────────────────────────────────────────────────── */
.pub-blocks {
  width: 100%; max-width: 520px;
  display: flex; flex-direction: column; gap: 10px;
}

/* ── Base card ──────────────────────────────────────────────────────────────── */
.pub-block {
  background: rgba(255,255,255,0.025); border: 1px solid rgba(61,142,255,0.10);
  border-radius: 16px; padding: 16px 18px;
  backdrop-filter: blur(4px);
}

/* ── Links block ────────────────────────────────────────────────────────────── */
.pub-block-links { display: flex; flex-direction: column; gap: 8px; }
.pub-links-group { display: flex; flex-direction: column; gap: 6px; }
.pub-group-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.4px; color: #4a4a68; padding: 0 4px;
}
.pub-link {
  display: flex; align-items: center; gap: 12px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px; padding: 13px 16px;
  text-decoration: none; color: #eeeef8; font-size: 14px; font-weight: 500;
  transition: background 0.18s, border-color 0.18s, transform 0.15s;
}
.pub-link:hover {
  background: rgba(61,142,255,0.08); border-color: rgba(61,142,255,0.22);
  transform: translateY(-1px);
}
.pub-link-icon-wrap {
  width: 34px; height: 34px; border-radius: 8px; flex-shrink: 0;
  background: rgba(61,142,255,0.10); border: 1px solid rgba(61,142,255,0.15);
  display: flex; align-items: center; justify-content: center; font-size: 16px; color: #90beff;
}
.pub-link-label { flex: 1; }
.pub-link-arrow { color: #3a3a58; font-size: 16px; transition: color 0.18s; }
.pub-link:hover .pub-link-arrow { color: #90beff; }

/* ── Text block ─────────────────────────────────────────────────────────────── */
.pub-text {
  font-size: 14px; color: #aaaacc; white-space: pre-wrap; line-height: 1.7;
  border-left: 2px solid rgba(61,142,255,0.20);
}

/* ── Widget shared ──────────────────────────────────────────────────────────── */
.pub-wh { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.pub-wh-left { display: flex; align-items: center; gap: 12px; }
.pub-w-ico-bg {
  width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.pub-w-name { font-size: 14px; font-weight: 700; line-height: 1.2; }
.pub-w-id { font-size: 12px; color: #6a6a90; margin-top: 1px; }
.pub-divider { height: 1px; background: rgba(61,142,255,0.07); margin: 12px 0; }
.pub-sub-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #4a4a68; margin-bottom: 8px; }

.pub-badge-green {
  font-size: 11px; font-weight: 600; color: #4ade80;
  background: rgba(74,222,128,0.10); border: 1px solid rgba(74,222,128,0.20);
  border-radius: 100px; padding: 2px 9px;
}

/* ── Steam ──────────────────────────────────────────────────────────────────── */
.pub-steam-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid rgba(61,142,255,0.05); font-size: 13px;
}
.pub-steam-row:last-child { border-bottom: none; }
.pub-steam-name { color: #ccccdd; }
.pub-steam-h { color: #6a6a90; font-size: 12px; }

/* ── Last.fm now playing ────────────────────────────────────────────────────── */
.pub-np-bars { display: flex; align-items: flex-end; gap: 3px; height: 18px; }
.pub-np-bar {
  width: 3px; height: 18px; background: #e5343a; border-radius: 2px;
  animation: npBounce 1.1s ease-in-out infinite;
  transform-origin: bottom;
}
@keyframes npBounce {
  0%, 100% { transform: scaleY(0.25); }
  50% { transform: scaleY(1); }
}
.pub-np-row { display: flex; align-items: center; gap: 12px; }
.pub-np-disc {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  background: rgba(200,0,0,0.15); border: 1px solid rgba(200,0,0,0.20);
  display: flex; align-items: center; justify-content: center; font-size: 18px;
  animation: npSpin 6s linear infinite;
}
@keyframes npSpin { to { transform: rotate(360deg); } }
.pub-np-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #e5343a; margin-bottom: 2px; }
.pub-np-track { font-size: 14px; font-weight: 700; line-height: 1.2; }
.pub-np-artist { font-size: 12px; color: #8888aa; margin-top: 2px; }

/* ── GitHub heatmap ─────────────────────────────────────────────────────────── */
.pub-gh-repos-badge {
  font-size: 11px; font-weight: 600; color: #90beff;
  background: rgba(61,142,255,0.10); border: 1px solid rgba(61,142,255,0.18);
  border-radius: 100px; padding: 2px 9px;
}
.pub-gh-grid-wrap { overflow-x: auto; padding-bottom: 2px; }
.pub-gh-grid {
  display: grid;
  grid-template-rows: repeat(7, 8px);
  grid-auto-flow: column;
  grid-auto-columns: 8px;
  gap: 3px;
  min-width: max-content;
}
.pub-gh-cell { border-radius: 2px; }
.pub-gh-l0 { background: rgba(255,255,255,0.05); }
.pub-gh-l1 { background: rgba(61,142,255,0.22); }
.pub-gh-l2 { background: rgba(61,142,255,0.45); }
.pub-gh-l3 { background: rgba(61,142,255,0.68); }
.pub-gh-l4 { background: #3D8EFF; }
.pub-gh-count { font-size: 11px; color: #6a6a90; margin-top: 6px; }
.pub-gh-repos { display: flex; flex-direction: column; gap: 6px; }
.pub-gh-repo {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #90beff;
  background: rgba(61,142,255,0.06); border: 1px solid rgba(61,142,255,0.12);
  border-radius: 7px; padding: 6px 10px;
}

/* ── PC Config ──────────────────────────────────────────────────────────────── */
.pub-pc-list { display: flex; flex-direction: column; }
.pub-pc-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid rgba(61,142,255,0.06); font-size: 13px;
}
.pub-pc-row:last-child { border-bottom: none; }
.pub-pc-cat { color: #6a6a90; min-width: 60px; }
.pub-pc-val { font-weight: 500; text-align: right; color: #ccccdd; }

/* ── Faceit ─────────────────────────────────────────────────────────────────── */
.pub-faceit-lvl {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 900; color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.pub-faceit-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
}
.pub-faceit-stat {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 10px 8px; text-align: center;
}
.pub-fstat-v { font-size: 16px; font-weight: 800; line-height: 1; }
.pub-fstat-l { font-size: 10px; color: #6a6a90; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Footer ─────────────────────────────────────────────────────────────────── */
.pub-footer {
  margin-top: 40px; padding-top: 24px;
  border-top: 1px solid rgba(61,142,255,0.06);
  width: 100%; max-width: 520px;
  display: flex; justify-content: center;
}
.pub-footer-link {
  display: flex; align-items: center; gap: 7px;
  color: #3a3a58; text-decoration: none; font-size: 12px; transition: color 0.2s;
}
.pub-footer-link:hover { color: #6a6a90; }
.pub-footer-logo { width: 18px; opacity: 0.4; mix-blend-mode: screen; }
</style>
