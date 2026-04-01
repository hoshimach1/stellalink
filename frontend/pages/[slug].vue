<template>
  <div v-if="pending" class="pub-loading"><div class="pub-spinner" /></div>

  <div v-else-if="!profile" class="pub-notfound">
    <img src="/images/logos/logo.png" alt="" class="pub-nf-logo">
    <h2>Профиль не найден</h2>
    <p>Пользователь <strong>{{ $route.params.slug }}</strong> не существует или ещё не опубликовал профиль.</p>
    <NuxtLink to="/" class="pub-home-btn">На главную</NuxtLink>
  </div>

  <div
    v-else
    class="pub-page"
    :data-theme="theme"
    :style="accentVars"
  >
    <!-- Background effects -->
    <div class="pub-bg-effects">
      <div class="pub-glow" />
      <div class="pub-bg-orb pub-bg-orb-1" />
      <div class="pub-bg-orb pub-bg-orb-2" />
      <div class="pub-bg-orb pub-bg-orb-3" />
      <div class="pub-bg-orb pub-bg-orb-4" />
    </div>

    <!-- ═══════════ MATERIAL 3 THEME ═══════════ -->
    <v-card
      v-if="theme === 'material3'"
      class="pub-card pub-card-m3"
      :color="profile.accent_color ? undefined : '#0c0a1a'"
      variant="tonal"
      :rounded="'xl'"
      elevation="8"
    >
      <!-- Header -->
      <v-card-text class="pub-header">
        <v-sheet
          class="pub-avatar"
          :color="profile.accent_color || '#D0BCFF'"
          rounded="circle"
          elevation="4"
        >
          <img v-if="profile.avatar_url" :src="avatarSrc ?? undefined" class="pub-avatar-img" alt="avatar">
          <span v-else>{{ initial }}</span>
        </v-sheet>
        <h1 class="pub-name">{{ profile.display_name }}</h1>
        <p v-if="profile.bio" class="pub-bio">{{ profile.bio }}</p>
        <div v-if="profile.tags.length" class="pub-tags">
          <v-chip
            v-for="tag in profile.tags"
            :key="tag"
            size="small"
            variant="tonal"
            :color="profile.accent_color || '#D0BCFF'"
            label
          >{{ tag }}</v-chip>
        </div>
      </v-card-text>

      <v-divider />

      <!-- Blocks -->
      <div class="pub-blocks">
        <template v-for="(block, idx) in visibleBlocks" :key="block.id">
          <!-- Links -->
          <div v-if="block.block_type === 'links'" class="pub-block-links">
            <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
              <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
              <v-card
                v-for="link in group.links"
                :key="link.url"
                :href="normalizeUrl(link.url)"
                target="_blank"
                rel="noopener"
                class="pub-link"
                variant="tonal"
                :rounded="idx % 2 === 0 ? 'lg-sm-lg-sm' : 'sm-lg-sm-lg'"
                hover
              >
                <v-card-text class="pub-link-inner d-flex align-center ga-3 pa-3">
                  <v-sheet
                    class="pub-link-icon-wrap"
                    :color="profile.accent_color || '#D0BCFF'"
                    rounded="lg"
                    width="34"
                    height="34"
                  >
                    <i v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                    <i v-else class="ri-link pub-link-icon" />
                  </v-sheet>
                  <span class="pub-link-label flex-grow-1">{{ link.label || link.url }}</span>
                  <i class="ri-arrow-right-up-line pub-link-arrow" />
                </v-card-text>
              </v-card>
            </div>
          </div>

          <!-- Other blocks wrapped in v-card -->
          <v-card
            v-else
            class="pub-block"
            variant="tonal"
            :rounded="idx % 2 === 0 ? 'xl-lg-xl-lg' : 'lg-xl-lg-xl'"
          >
            <v-card-text>
              <!-- Text -->
              <div v-if="block.block_type === 'text'" class="pub-text">
                {{ (block.config.content as string) }}
              </div>

              <!-- Steam -->
              <template v-else-if="block.block_type === 'widget_steam'">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <v-sheet class="pub-w-ico-bg" color="rgba(25,144,212,0.15)" rounded="lg" width="40" height="40">
                      <span style="color:#66c0f4">🎮</span>
                    </v-sheet>
                    <div>
                      <div class="pub-w-name">Steam</div>
                      <div class="pub-w-id">{{ block.config.steam_id || '—' }}</div>
                    </div>
                  </div>
                  <v-chip size="small" color="success" variant="tonal">● Online</v-chip>
                </div>
                <template v-if="block.config.show_recent_games && block.config.steam_id">
                  <v-divider class="my-3" />
                  <div class="pub-sub-label">Недавно в игре</div>
                  <div v-for="g in mock.steamGames(block.config.steam_id as string)" :key="g.name" class="pub-steam-row">
                    <span class="pub-steam-name">{{ g.name }}</span>
                    <span class="pub-steam-h">{{ g.hours.toLocaleString('ru') }} ч</span>
                  </div>
                </template>
              </template>

              <!-- Last.fm -->
              <template v-else-if="block.block_type === 'widget_lastfm'">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <v-sheet class="pub-w-ico-bg" color="rgba(200,0,0,0.15)" rounded="lg" width="40" height="40">
                      <span style="color:#e5343a">🎵</span>
                    </v-sheet>
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
                  <v-divider class="my-3" />
                  <div class="pub-np-row">
                    <div class="pub-np-disc">♫</div>
                    <div>
                      <div class="pub-np-label">Сейчас слушает</div>
                      <div class="pub-np-track">{{ mock.lastfmTrack(block.config.username as string).track }}</div>
                      <div class="pub-np-artist">{{ mock.lastfmTrack(block.config.username as string).artist }}</div>
                    </div>
                  </div>
                </template>
              </template>

              <!-- GitHub -->
              <template v-else-if="block.block_type === 'widget_github'">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <v-sheet class="pub-w-ico-bg" color="rgba(255,255,255,0.06)" rounded="lg" width="40" height="40">
                      <span style="color:#ececef">🐙</span>
                    </v-sheet>
                    <div>
                      <div class="pub-w-name">GitHub</div>
                      <div class="pub-w-id">@{{ block.config.username || '—' }}</div>
                    </div>
                  </div>
                  <v-chip v-if="block.config.username" size="small" variant="tonal" :color="profile.accent_color || '#D0BCFF'">
                    {{ mock.ghStats(block.config.username as string).repos }} репо
                  </v-chip>
                </div>
                <template v-if="block.config.username">
                  <v-divider class="my-3" />
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
                      <v-chip v-for="r in mock.ghRepos(block.config.username as string)" :key="r" variant="tonal" size="small" :color="profile.accent_color || '#D0BCFF'" prepend-icon="mdi-source-repository">
                        {{ block.config.username }}/{{ r }}
                      </v-chip>
                    </div>
                  </template>
                </template>
              </template>

              <!-- PC Config -->
              <template v-else-if="block.block_type === 'pc_config'">
                <div class="pub-wh" style="margin-bottom:0">
                  <div class="pub-wh-left">
                    <v-sheet class="pub-w-ico-bg" color="var(--t-accent12)" rounded="lg" width="40" height="40">
                      <span style="color:var(--t-accent)">💻</span>
                    </v-sheet>
                    <div class="pub-w-name">{{ (block.config.title as string) || 'PC Config' }}</div>
                  </div>
                </div>
                <template v-if="(block.config.components as Component[]).length">
                  <v-divider class="mt-3 mb-3" />
                  <div class="pub-pc-list">
                    <div v-for="c in (block.config.components as Component[])" :key="c.category" class="pub-pc-row">
                      <span class="pub-pc-cat">{{ c.category }}</span>
                      <span class="pub-pc-val">{{ c.name }}</span>
                    </div>
                  </div>
                </template>
              </template>

              <!-- Faceit -->
              <template v-else-if="block.block_type === 'widget_faceit'">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <v-sheet class="pub-w-ico-bg" color="rgba(255,90,0,0.15)" rounded="lg" width="40" height="40">
                      <span style="color:#ff8c42">⚡</span>
                    </v-sheet>
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
                  <v-divider class="my-3" />
                  <div class="pub-faceit-stats">
                    <v-sheet v-for="s in faceitStatsList(block)" :key="s.label" class="pub-faceit-stat" rounded="lg" color="rgba(255,255,255,0.04)">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </v-sheet>
                  </div>
                </template>
              </template>
            </v-card-text>
          </v-card>
        </template>
      </div>

      <!-- Footer -->
      <v-divider />
      <div class="pub-footer">
        <NuxtLink to="/" class="pub-footer-link">
          <img src="/images/logos/logo.png" alt="" class="pub-footer-logo">
          Сделано на Stellalink
        </NuxtLink>
      </div>
    </v-card>

    <!-- ═══════════ LIQUID GLASS THEME ═══════════ -->
    <ClientOnly v-else-if="theme === 'glass'">
      <div class="pub-card pub-card-glass">
        <div class="pub-card-glass-scroll">
        <!-- Header -->
        <div class="pub-glass-header">
          <div class="pub-header-glass-row">
            <div class="pub-avatar-glass-wrap">
              <div class="pub-avatar pub-avatar-glass">
                <img v-if="profile.avatar_url" :src="avatarSrc ?? undefined" class="pub-avatar-img" alt="avatar">
                <span v-else>{{ initial }}</span>
              </div>
              <span class="pub-avatar-online" />
            </div>
            <div class="pub-header-glass-info">
              <h1 class="pub-name">{{ profile.display_name }}</h1>
              <p v-if="profile.bio" class="pub-bio">{{ profile.bio }}</p>
              <div v-if="profile.tags.length" class="pub-tags pub-tags-glass">
                <span v-for="tag in profile.tags" :key="tag" class="pub-glass-tag">
                  <span class="pub-tag-text">{{ tag }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Blocks -->
        <div class="pub-blocks">
          <template v-for="block in visibleBlocks" :key="block.id">
            <!-- Links — each link is a glass pane -->
            <div v-if="block.block_type === 'links'" class="pub-block-links">
              <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
                <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
                <div
                  v-for="link in group.links"
                  :key="link.url"
                  class="pub-glass-link-wrap"
                >
                  <a
                    :href="normalizeUrl(link.url)"
                    target="_blank"
                    rel="noopener"
                    class="pub-link pub-link-glass"
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
            </div>

            <!-- Other blocks in glass panes -->
            <div
              v-else
              class="pub-glass-block"
            >
              <!-- Text -->
              <div v-if="block.block_type === 'text'" class="pub-text">
                {{ (block.config.content as string) }}
              </div>

              <!-- Steam -->
              <template v-else-if="block.block_type === 'widget_steam'">
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
              </template>

              <!-- Last.fm -->
              <template v-else-if="block.block_type === 'widget_lastfm'">
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
              </template>

              <!-- GitHub -->
              <template v-else-if="block.block_type === 'widget_github'">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <div class="pub-w-ico-bg" style="background:rgba(255,255,255,0.06);color:#ececef">🐙</div>
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
              </template>

              <!-- PC Config -->
              <template v-else-if="block.block_type === 'pc_config'">
                <div class="pub-wh" style="margin-bottom:0">
                  <div class="pub-wh-left">
                    <div class="pub-w-ico-bg" style="background:var(--t-accent12);color:var(--t-accent)">💻</div>
                    <div class="pub-w-name">{{ (block.config.title as string) || 'PC Config' }}</div>
                  </div>
                </div>
                <template v-if="(block.config.components as Component[]).length">
                  <div class="pub-divider" />
                  <div class="pub-pc-list">
                    <div v-for="c in (block.config.components as Component[])" :key="c.category" class="pub-pc-row">
                      <span class="pub-pc-cat">{{ c.category }}</span>
                      <span class="pub-pc-val">{{ c.name }}</span>
                    </div>
                  </div>
                </template>
              </template>

              <!-- Faceit -->
              <template v-else-if="block.block_type === 'widget_faceit'">
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
                    <div v-for="s in faceitStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                </template>
              </template>
            </div>
          </template>
        </div>

        <!-- Footer — sticky bottom inside scroll -->
        <div class="pub-footer pub-footer-glass">
          <NuxtLink to="/" class="pub-footer-link">
            <img src="/images/logos/logo.png" alt="" class="pub-footer-logo">
            Сделано на Stellalink
          </NuxtLink>
        </div>

        </div><!-- /pub-card-glass-scroll -->
      </div>

      <template #fallback>
        <div class="pub-card">
          <div class="pub-header">
            <div class="pub-avatar">
              <img v-if="profile.avatar_url" :src="avatarSrc ?? undefined" class="pub-avatar-img" alt="avatar">
              <span v-else>{{ initial }}</span>
            </div>
            <h1 class="pub-name">{{ profile.display_name }}</h1>
          </div>
          <div class="pub-footer">
            <span class="pub-loading-text">Загрузка эффектов...</span>
          </div>
        </div>
      </template>
    </ClientOnly>

    <!-- ═══════════ FLUENT THEME ═══════════ -->
    <ClientOnly v-else-if="theme === 'fluent'">
      <div class="pub-card pub-card-fluent">
        <!-- Header -->
        <fluent-card class="pub-fluent-section pub-fluent-header-card">
          <div class="pub-header">
            <div class="pub-avatar">
              <img v-if="profile.avatar_url" :src="avatarSrc ?? undefined" class="pub-avatar-img" alt="avatar">
              <span v-else>{{ initial }}</span>
            </div>
            <h1 class="pub-name">{{ profile.display_name }}</h1>
            <p v-if="profile.bio" class="pub-bio">{{ profile.bio }}</p>
            <div v-if="profile.tags.length" class="pub-tags">
              <fluent-badge v-for="tag in profile.tags" :key="tag" appearance="accent" class="pub-fluent-tag">{{ tag }}</fluent-badge>
            </div>
          </div>
        </fluent-card>

        <!-- Blocks -->
        <div class="pub-blocks">
          <template v-for="block in visibleBlocks" :key="block.id">
            <!-- Links -->
            <div v-if="block.block_type === 'links'" class="pub-block-links">
              <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
                <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
                <fluent-card
                  v-for="link in group.links"
                  :key="link.url"
                  class="pub-fluent-link-card"
                >
                  <a
                    :href="normalizeUrl(link.url)"
                    target="_blank"
                    rel="noopener"
                    class="pub-link pub-link-fluent"
                  >
                    <span class="pub-link-icon-wrap">
                      <i v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                      <i v-else class="ri-link pub-link-icon" />
                    </span>
                    <span class="pub-link-label">{{ link.label || link.url }}</span>
                    <i class="ri-arrow-right-up-line pub-link-arrow" />
                  </a>
                </fluent-card>
              </div>
            </div>

            <!-- Other blocks in fluent-card -->
            <fluent-card v-else class="pub-fluent-block">
              <!-- Text -->
              <div v-if="block.block_type === 'text'" class="pub-block-inner pub-text">
                {{ (block.config.content as string) }}
              </div>

              <!-- Steam -->
              <div v-else-if="block.block_type === 'widget_steam'" class="pub-block-inner">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <div class="pub-w-ico-bg" style="background:rgba(25,144,212,0.15);color:#66c0f4">🎮</div>
                    <div>
                      <div class="pub-w-name">Steam</div>
                      <div class="pub-w-id">{{ block.config.steam_id || '—' }}</div>
                    </div>
                  </div>
                  <fluent-badge appearance="accent" class="pub-fluent-badge-online">Online</fluent-badge>
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
              <div v-else-if="block.block_type === 'widget_lastfm'" class="pub-block-inner">
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
              <div v-else-if="block.block_type === 'widget_github'" class="pub-block-inner">
                <div class="pub-wh">
                  <div class="pub-wh-left">
                    <div class="pub-w-ico-bg" style="background:rgba(255,255,255,0.06);color:#ececef">🐙</div>
                    <div>
                      <div class="pub-w-name">GitHub</div>
                      <div class="pub-w-id">@{{ block.config.username || '—' }}</div>
                    </div>
                  </div>
                  <fluent-badge v-if="block.config.username" appearance="neutral">
                    {{ mock.ghStats(block.config.username as string).repos }} репо
                  </fluent-badge>
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
              <div v-else-if="block.block_type === 'pc_config'" class="pub-block-inner">
                <div class="pub-wh" style="margin-bottom:0">
                  <div class="pub-wh-left">
                    <div class="pub-w-ico-bg" style="background:var(--t-accent12);color:var(--t-accent)">💻</div>
                    <div class="pub-w-name">{{ (block.config.title as string) || 'PC Config' }}</div>
                  </div>
                </div>
                <template v-if="(block.config.components as Component[]).length">
                  <div class="pub-divider" />
                  <div class="pub-pc-list">
                    <div v-for="c in (block.config.components as Component[])" :key="c.category" class="pub-pc-row">
                      <span class="pub-pc-cat">{{ c.category }}</span>
                      <span class="pub-pc-val">{{ c.name }}</span>
                    </div>
                  </div>
                </template>
              </div>

              <!-- Faceit -->
              <div v-else-if="block.block_type === 'widget_faceit'" class="pub-block-inner">
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
                    <div v-for="s in faceitStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                </template>
              </div>
            </fluent-card>
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

      <template #fallback>
        <div class="pub-card">
          <div class="pub-header">
            <div class="pub-avatar">
              <img v-if="profile.avatar_url" :src="avatarSrc ?? undefined" class="pub-avatar-img" alt="avatar">
              <span v-else>{{ initial }}</span>
            </div>
            <h1 class="pub-name">{{ profile.display_name }}</h1>
          </div>
        </div>
      </template>
    </ClientOnly>
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
  theme_preset: string | null
  accent_color: string | null
} | null>(`${config.public.apiBase}/u/${slug}`, {
  default: () => null,
  onResponseError() { return null },
})

const pageTitle = computed(() => {
  const name = profile.value?.display_name
  return name ? `${name} — Stellalink` : `${slug} — Stellalink`
})
useHead({ title: pageTitle })

const theme = computed(() => profile.value?.theme_preset || 'material3')
const initial = computed(() => profile.value?.display_name?.[0]?.toUpperCase() ?? '?')
const visibleBlocks = computed(() => profile.value?.blocks.filter(b => b.is_visible) ?? [])
const avatarSrc = computed(() =>
  profile.value?.avatar_url
    ? resolveAvatarUrl(profile.value.avatar_url, config.public.apiBase as string)
    : null
)

const accentVars = computed(() => {
  const c = profile.value?.accent_color
  if (!c) return ''
  return `--t-accent:${c};--t-accent20:${c}20;--t-accent30:${c}30;--t-accent12:${c}1e`
})

// Liquid Glass — SVG displacement filter applied once after mount
type DisplacementUtils = {
  getDisplacementFilter(opts: { height: number; width: number; radius: number; depth: number; strength: number; chromaticAberration: number }): string
}

let glassApplied = false

function applyLiquidGlass() {
  if (typeof window === 'undefined') return
  if (theme.value !== 'glass') return

  const utils = (window as unknown as { DisplacementUtils?: DisplacementUtils }).DisplacementUtils
  if (!utils) {
    setTimeout(applyLiquidGlass, 80)
    return
  }

  const elements = document.querySelectorAll<HTMLElement>('.pub-glass-block, .pub-glass-link-wrap, .pub-glass-header, .pub-footer-glass')
  elements.forEach(el => {
    const rect = el.getBoundingClientRect()
    if (rect.width < 10 || rect.height < 10) return

    const isHeader = el.classList.contains('pub-glass-header')
    const isFooter = el.classList.contains('pub-footer-glass')
    const radius = (isHeader || isFooter) ? 28 : el.classList.contains('pub-glass-block') ? 20 : 16

    const filterUrl = utils.getDisplacementFilter({
      height: Math.ceil(rect.height),
      width: Math.ceil(rect.width),
      radius,
      depth: 14,
      strength: 70,
      chromaticAberration: 3,
    })

    const bf = `blur(1px) url('${filterUrl}') blur(8px) brightness(1.10) saturate(2.2)`
    el.style.backdropFilter = bf
    ;(el.style as CSSStyleDeclaration & { webkitBackdropFilter: string }).webkitBackdropFilter = bf
  })

  glassApplied = true
}

onMounted(() => nextTick(() => setTimeout(applyLiquidGlass, 200)))
watch(theme, () => { glassApplied = false; nextTick(() => setTimeout(applyLiquidGlass, 200)) })

function normalizeUrl(url: string | undefined): string {
  if (!url) return '#'
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

function faceitStatsList(block: Block) {
  const data = mock.faceitData(block.config.nickname as string)
  return [
    { value: data.elo, label: 'ELO' },
    { value: data.kd, label: 'K/D' },
    { value: `${data.winRate}%`, label: 'Win Rate' },
    { value: data.matches, label: 'Матчи' },
  ]
}
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
  border: 3px solid rgba(255,255,255,0.12); border-top-color: #d4d4d8;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pub-notfound {
  min-height: 100vh; background: #09090b; color: #ececef;
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 24px; gap: 12px;
}
.pub-nf-logo { width: 56px; opacity: 0.5; mix-blend-mode: screen; }
.pub-notfound h2 { font-size: 24px; font-weight: 800; }
.pub-notfound p { color: #71717a; font-size: 15px; }
.pub-home-btn {
  margin-top: 8px; padding: 10px 24px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px; color: #a1a1aa; text-decoration: none; font-size: 14px;
}
.pub-loading-text { color: #71717a; font-size: 13px; }

/* ── Theme tokens ────────────────────────────────────────────────────────────── */
.pub-page {
  --t-accent:   #D0BCFF;
  --t-accent20: rgba(208,188,255,0.20);
  --t-accent30: rgba(208,188,255,0.30);
  --t-accent12: rgba(208,188,255,0.12);
  --t-bg:       #0c0a1a;
  --t-surface:  rgba(208,188,255,0.06);
  --t-card-bg:  rgba(208,188,255,0.03);
  --t-card-border: rgba(208,188,255,0.10);
  --t-text:     #e9e0f8;
  --t-muted:    #cac4d0;
  --t-dim:      #938f99;
  --t-border:   rgba(208,188,255,0.14);
  --t-glow:     rgba(208,188,255,0.14);
  --t-tag-bg:   rgba(208,188,255,0.10);
  --t-tag-c:    #D0BCFF;
  --t-radius:   28px;
  --t-radius-sm: 16px;
  --t-blur:     none;
  --t-card-shadow: 0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(208,188,255,0.06);
  --t-block-shadow: none;
}

/* Glass tokens */
[data-theme="glass"] {
  --t-accent:   #a8d8ff;
  --t-accent20: rgba(168,216,255,0.20);
  --t-accent30: rgba(168,216,255,0.30);
  --t-accent12: rgba(168,216,255,0.12);
  --t-bg:       #000000;
  --t-surface:  rgba(255,255,255,0.06);
  --t-card-bg:  rgba(255,255,255,0.05);
  --t-card-border: rgba(255,255,255,0.15);
  --t-text:     #f0eeff;
  --t-muted:    rgba(240,238,255,0.65);
  --t-dim:      rgba(240,238,255,0.35);
  --t-border:   rgba(255,255,255,0.12);
  --t-glow:     rgba(130,80,255,0.35);
  --t-tag-bg:   rgba(168,216,255,0.10);
  --t-tag-c:    #c8e8ff;
  --t-radius:   24px;
  --t-radius-sm: 16px;
  --t-blur:     blur(40px) saturate(220%);
  --t-card-shadow: 0 32px 80px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.15);
  --t-block-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

/* Fluent 2 tokens */
[data-theme="fluent"] {
  --t-accent:   #60cdff;
  --t-accent20: rgba(96,205,255,0.20);
  --t-accent30: rgba(96,205,255,0.30);
  --t-accent12: rgba(96,205,255,0.12);
  --t-bg:       #202020;
  --t-surface:  rgba(255,255,255,0.07);
  --t-card-bg:  rgba(255,255,255,0.055);
  --t-card-border: rgba(255,255,255,0.09);
  --t-text:     #f8f8f8;
  --t-muted:    rgba(255,255,255,0.70);
  --t-dim:      rgba(255,255,255,0.42);
  --t-border:   rgba(255,255,255,0.09);
  --t-glow:     rgba(96,205,255,0.08);
  --t-tag-bg:   rgba(96,205,255,0.12);
  --t-tag-c:    #74d8ff;
  --t-radius:   8px;
  --t-radius-sm: 6px;
  --t-blur:     blur(60px) saturate(160%);
  --t-card-shadow: 0 8px 32px rgba(0,0,0,0.5);
  --t-block-shadow: none;
}
/* Fluent 2 — Acrylic background noise layer */
[data-theme="fluent"] .pub-bg-effects {
  background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(255,255,255,0.04), transparent);
}
[data-theme="fluent"] .pub-glow {
  background: radial-gradient(ellipse 60% 80% at 50% 0%, rgba(96,205,255,0.06), transparent);
}

/* ── Page ───────────────────────────────────────────────────────────────────── */
.pub-page {
  min-height: 100vh; background: var(--t-bg); color: var(--t-text);
  font-family: 'Onest', sans-serif;
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-start;
  padding: 24px 16px 48px; position: relative; overflow-x: clip;
}

/* ── Background effects ────────────────────────────────────────────────────── */
.pub-bg-effects {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
}
.pub-glow {
  display: none;
}
.pub-bg-orb {
  position: absolute; border-radius: 50%; filter: blur(30px); opacity: 0;
}
[data-theme="glass"] .pub-bg-orb { opacity: 1; }
[data-theme="glass"] .pub-bg-orb-1 {
  width: 480px; height: 480px; top: -15%; left: -5%;
  background: radial-gradient(circle, rgba(110,60,230,0.35) 0%, rgba(80,40,180,0.18) 55%, transparent 75%);
  animation: orbFloat1 12s ease-in-out infinite;
}
[data-theme="glass"] .pub-bg-orb-2 {
  width: 420px; height: 420px; top: 25%; right: -5%;
  background: radial-gradient(circle, rgba(40,130,220,0.30) 0%, rgba(20,90,180,0.15) 55%, transparent 75%);
  animation: orbFloat2 15s ease-in-out infinite;
}
[data-theme="glass"] .pub-bg-orb-3 {
  width: 380px; height: 380px; bottom: 0%; left: 10%;
  background: radial-gradient(circle, rgba(160,40,210,0.28) 0%, rgba(120,30,170,0.14) 55%, transparent 75%);
  animation: orbFloat3 18s ease-in-out infinite;
}
[data-theme="glass"] .pub-bg-orb-4 {
  width: 300px; height: 300px; top: 35%; left: 50%; transform: translateX(-50%);
  background: radial-gradient(circle, rgba(200,100,50,0.16) 0%, rgba(160,70,30,0.08) 55%, transparent 75%);
  animation: orbFloat1 20s ease-in-out infinite reverse;
}
@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 40px); }
}
@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-20px, -30px); }
}
@keyframes orbFloat3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(25px, -20px); }
}

/* ── Card wrapper (shared) ────────────────────────────────────────────────── */
.pub-card {
  width: 100%; max-width: 380px;
  position: relative; z-index: 1;
  max-height: calc(92vh - 48px);
  display: flex; flex-direction: column;
  transition: border-radius 0.4s ease, background 0.4s ease, box-shadow 0.4s ease;
}

/* ── Material 3 Card (Vuetify) ────────────────────────────────────────────── */
.pub-card-m3 {
  background: linear-gradient(180deg, var(--t-accent12) 0%, rgba(208,188,255,0.01) 100%) !important;
  border: 1px solid var(--t-card-border) !important;
  box-shadow: var(--t-card-shadow) !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.pub-card-m3 :deep(.v-card__text) {
  padding: 0;
}
.pub-card-m3 :deep(.v-card__underlay) {
  display: none;
}

/* ── Glass Card ───────────────────────────────────────────────────────────── */
.pub-card-glass-scroll {
  width: 100%;
  max-height: calc(92vh - 48px);
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  display: flex;
  flex-direction: column;
}
.pub-card-glass-scroll::-webkit-scrollbar { width: 3px; }
.pub-card-glass-scroll::-webkit-scrollbar-track { background: transparent; }
.pub-card-glass-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
.pub-card-glass {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.20);
  border-top: 1px solid rgba(255,255,255,0.38);
  border-radius: 28px;
  box-shadow:
    0 12px 60px rgba(0,0,0,0.60),
    0 1px 0 rgba(255,255,255,0.40) inset,
    0 -1px 0 rgba(0,0,0,0.30) inset,
    0 0 0 0.5px rgba(255,255,255,0.08) inset;
  overflow: clip;
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  /* height handled by pub-card-glass-scroll child */
  max-height: none;
}
.pub-glass-header {
  display: block;
  width: 100%;
  padding: 0;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border-bottom: 1px solid rgba(255,255,255,0.14);
}
.pub-glass-header::after {
  content: '';
  position: absolute;
  top: 0; left: 10%; right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.70) 30%, rgba(255,255,255,0.80) 50%, rgba(255,255,255,0.70) 70%, transparent);
  pointer-events: none;
}
.pub-glass-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 100px;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.20);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25), 0 1px 4px rgba(0,0,0,0.20);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
}
.pub-tag-text {
  font-size: 12px; font-weight: 500; color: var(--t-tag-c);
}
.pub-glass-block {
  display: block;
  width: 100%;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.22);
  box-shadow:
    0 4px 20px rgba(0,0,0,0.28),
    inset 0 1px 0 rgba(255,255,255,0.40),
    inset 0 -1px 0 rgba(0,0,0,0.15);
}
.pub-glass-link-wrap {
  display: block;
  width: 100%;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.20);
  box-shadow:
    0 2px 12px rgba(0,0,0,0.22),
    inset 0 1px 0 rgba(255,255,255,0.36),
    inset 0 -1px 0 rgba(0,0,0,0.12);
}

/* ── Fluent 2 / Windows 11 Card ──────────────────────────────────────────── */
.pub-card-fluent {
  background: rgba(24,24,24,0.75);
  backdrop-filter: blur(60px) saturate(160%);
  -webkit-backdrop-filter: blur(60px) saturate(160%);
  border: 1px solid rgba(255,255,255,0.09);
  border-top: 1px solid rgba(255,255,255,0.14);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,0,0,0.2);
  overflow: clip;
}
.pub-fluent-section {
  --card-fill-color: transparent;
}
.pub-card-fluent :deep(fluent-card) {
  --fill-color: rgba(255,255,255,0.055);
  background: rgba(255,255,255,0.055);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 6px;
  color: inherit;
  padding: 0;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.pub-card-fluent :deep(fluent-card):hover {
  --fill-color: rgba(255,255,255,0.09);
  background: rgba(255,255,255,0.09);
  border-color: var(--t-accent12);
  box-shadow: 0 0 0 1px var(--t-accent12);
}
.pub-fluent-header-card {
  border-radius: 0 !important;
  border: none !important;
  border-bottom: 1px solid rgba(255,255,255,0.07) !important;
  flex-shrink: 0;
}
.pub-fluent-tag {
  font-size: 12px;
  font-family: 'Onest', sans-serif;
}
.pub-fluent-link-card {
  margin-bottom: 5px;
}
.pub-fluent-block {
  margin-bottom: 6px;
}
.pub-block-inner {
  padding: 14px 16px;
}
.pub-fluent-badge-online {
  font-size: 11px;
}
/* Fluent 2 accent top bar */
.pub-card-fluent::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--t-accent), transparent 80%);
  z-index: 2;
  border-radius: 8px 8px 0 0;
  pointer-events: none;
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
.pub-header {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; width: 100%; padding: 22px 20px 14px; gap: 6px;
  position: relative; z-index: 1;
  flex-shrink: 0;
}
[data-theme="glass"] .pub-header {
  padding: 14px 20px 10px; gap: 4px;
}
[data-theme="glass"] .pub-avatar {
  width: 52px; height: 52px; font-size: 20px;
}
.pub-header-glass-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14px;
  padding: 14px 16px 12px;
  width: 100%;
}
.pub-avatar-glass-wrap {
  position: relative;
  flex-shrink: 0;
}
.pub-avatar-glass {
  width: 54px !important;
  height: 54px !important;
  font-size: 22px !important;
}
.pub-avatar-online {
  position: absolute;
  bottom: 1px; right: 1px;
  width: 11px; height: 11px;
  border-radius: 50%;
  background: #4ade80;
  border: 2px solid rgba(10,7,30,0.9);
}
.pub-header-glass-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
  flex: 1;
  text-align: left;
}
.pub-header-glass-info .pub-name {
  font-size: 16px;
  font-weight: 700;
  text-align: left;
  margin: 0;
  line-height: 1.2;
}
.pub-header-glass-info .pub-bio {
  font-size: 12px;
  text-align: left;
  margin: 0;
  color: var(--t-muted);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.pub-tags-glass {
  justify-content: flex-start !important;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 2px;
}
.pub-avatar {
  width: 68px; height: 68px; border-radius: 50%; flex-shrink: 0;
  background: var(--t-accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: 800; color: #fff; overflow: hidden;
  box-shadow: 0 0 0 3px var(--t-accent20), 0 6px 24px var(--t-accent20);
  margin-bottom: 2px;
}
[data-theme="glass"] .pub-avatar {
  box-shadow: 0 0 0 3px rgba(255,255,255,0.15), 0 8px 40px rgba(0,0,0,0.3), 0 0 24px var(--t-accent20);
}
.pub-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.pub-name { font-size: 20px; font-weight: 800; letter-spacing: -0.3px; margin: 0; }
.pub-bio { font-size: 14px; color: var(--t-muted); line-height: 1.5; margin: 0; max-width: 360px; }
.pub-tags { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }
.pub-tag {
  background: var(--t-tag-bg); color: var(--t-tag-c);
  border: 1px solid var(--t-accent12); border-radius: 100px;
  padding: 3px 12px; font-size: 12px; font-weight: 500;
}

/* ── Blocks container ───────────────────────────────────────────────────────── */
.pub-blocks {
  width: 100%;
  display: flex; flex-direction: column; gap: 8px;
  padding: 10px 14px 14px;
  position: relative; z-index: 1;
  flex: 1;
}
.pub-blocks::-webkit-scrollbar { width: 3px; }
.pub-blocks::-webkit-scrollbar-track { background: transparent; }
.pub-blocks::-webkit-scrollbar-thumb { background: var(--t-border); border-radius: 2px; }

/* ── Links block ────────────────────────────────────────────────────────────── */
.pub-block-links { display: flex; flex-direction: column; gap: 8px; }
.pub-links-group { display: flex; flex-direction: column; gap: 6px; }
.pub-group-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.4px; color: var(--t-dim); padding: 0 4px;
}
.pub-link {
  display: flex; align-items: center; gap: 12px;
  text-decoration: none; color: var(--t-text); font-size: 14px; font-weight: 500;
  transition: background 0.18s, border-color 0.18s, transform 0.15s, box-shadow 0.18s;
  position: relative; overflow: hidden;
}
.pub-link-inner {
  display: flex; align-items: center;
}
/* Glass link styling */
.pub-link-glass {
  padding: 13px 16px; width: 100%;
}
/* Fluent link styling */
.pub-link-fluent {
  padding: 13px 16px; width: 100%;
}
.pub-link:hover {
  transform: translateY(-1px);
}

.pub-link-icon-wrap {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  background: var(--t-accent12); border: 1px solid var(--t-border);
  display: flex; align-items: center; justify-content: center; font-size: 16px; color: var(--t-accent);
}
/* M3 icon wrap uses v-sheet so override */
.pub-card-m3 .pub-link-icon-wrap {
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #fff;
  background: transparent !important;
}
[data-theme="glass"] .pub-link-icon-wrap {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.08);
}
.pub-link-label { flex: 1; }
.pub-link-arrow { color: var(--t-dim); font-size: 16px; transition: color 0.18s; }
.pub-link:hover .pub-link-arrow { color: var(--t-tag-c); }

/* ── Text block ─────────────────────────────────────────────────────────────── */
.pub-text {
  font-size: 14px; color: var(--t-muted); white-space: pre-wrap; line-height: 1.7;
  border-left: 2px solid var(--t-accent30);
  padding-left: 14px;
}

/* ── Widget shared ──────────────────────────────────────────────────────────── */
.pub-wh { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.pub-wh-left { display: flex; align-items: center; gap: 12px; }
.pub-w-ico-bg {
  width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 20px;
}
/* v-sheet ico override */
:deep(.v-sheet.pub-w-ico-bg) {
  display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.pub-w-name { font-size: 14px; font-weight: 700; line-height: 1.2; }
.pub-w-id { font-size: 12px; color: var(--t-muted); margin-top: 1px; }
.pub-divider { height: 1px; background: var(--t-border); margin: 12px 0; }
[data-theme="glass"] .pub-divider {
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
}
.pub-sub-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: var(--t-dim); margin-bottom: 8px; }

.pub-badge-green {
  font-size: 11px; font-weight: 600; color: #4ade80;
  background: rgba(74,222,128,0.10); border: 1px solid rgba(74,222,128,0.20);
  border-radius: 100px; padding: 2px 9px;
}

/* ── Steam ──────────────────────────────────────────────────────────────────── */
.pub-steam-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid var(--t-border); font-size: 13px;
}
.pub-steam-row:last-child { border-bottom: none; }
.pub-steam-name { color: var(--t-text); }
.pub-steam-h { color: var(--t-muted); font-size: 12px; }

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
.pub-np-artist { font-size: 12px; color: var(--t-muted); margin-top: 2px; }

/* ── GitHub heatmap ─────────────────────────────────────────────────────────── */
.pub-gh-repos-badge {
  font-size: 11px; font-weight: 600; color: var(--t-tag-c);
  background: var(--t-tag-bg); border: 1px solid var(--t-accent12);
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
.pub-gh-l0 { background: var(--t-surface); }
.pub-gh-l1 { background: var(--t-accent20); }
.pub-gh-l2 { background: var(--t-accent30); }
.pub-gh-l3 { background: var(--t-accent); opacity: 0.7; }
.pub-gh-l4 { background: var(--t-accent); }
[data-theme="glass"] .pub-gh-cell { border-radius: 3px; }
[data-theme="glass"] .pub-gh-l0 { background: rgba(255,255,255,0.04); }
.pub-gh-count { font-size: 11px; color: var(--t-muted); margin-top: 6px; }
.pub-gh-repos { display: flex; flex-direction: column; gap: 6px; }
.pub-gh-repo {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--t-tag-c);
  background: var(--t-tag-bg); border: 1px solid var(--t-border);
  border-radius: 6px; padding: 6px 10px;
}

/* ── PC Config ──────────────────────────────────────────────────────────────── */
.pub-pc-list { display: flex; flex-direction: column; }
.pub-pc-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--t-border); font-size: 13px;
}
.pub-pc-row:last-child { border-bottom: none; }
.pub-pc-cat { color: var(--t-dim); min-width: 60px; }
.pub-pc-val { font-weight: 500; text-align: right; color: var(--t-text); }

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
  background: var(--t-surface); border: 1px solid var(--t-border);
  border-radius: 8px; padding: 10px 8px; text-align: center;
}
.pub-fstat-v { font-size: 16px; font-weight: 800; line-height: 1; }
.pub-fstat-l { font-size: 10px; color: var(--t-dim); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Footer ─────────────────────────────────────────────────────────────────── */
.pub-footer {
  padding: 14px 16px;
  border-top: 1px solid var(--t-border);
  width: 100%;
  display: flex; justify-content: center;
  position: relative; z-index: 1;
  flex-shrink: 0;
}
[data-theme="glass"] .pub-footer {
  border-top-color: rgba(255,255,255,0.06);
}
.pub-footer-glass {
  position: sticky;
  bottom: 0;
  z-index: 10;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border-top: 1px solid rgba(255,255,255,0.08);
  border-bottom-left-radius: 28px;
  border-bottom-right-radius: 28px;
}
.pub-footer-link {
  display: flex; align-items: center; gap: 7px;
  color: var(--t-dim); text-decoration: none; font-size: 12px; transition: color 0.2s;
}
.pub-footer-link:hover { color: var(--t-muted); }
.pub-footer-logo { width: 18px; opacity: 0.4; mix-blend-mode: screen; }

/* ── Responsive ────────────────────────────────────────────────────────────── */
@media (max-width: 540px) {
  .pub-page { padding: 12px 8px 32px; }
  .pub-card { border-radius: calc(var(--t-radius) * 0.7); max-height: calc(96vh - 24px); }
  .pub-header { padding: 20px 14px 12px; }
  .pub-blocks { padding: 8px 10px 12px; }
}
</style>
