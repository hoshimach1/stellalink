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
    :data-mode="themeMode"
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
    <section
      v-if="theme === 'material3'"
      class="pub-card pub-card-m3"
      :class="{ 'pub-card-m3-wide': isMaterial3Wide }"
      aria-label="Публичный профиль Stellalink"
    >
      <header class="pub-m3-hero">
        <div class="pub-m3-hero-row">
          <div class="pub-m3-avatar-wrap">
            <div class="pub-avatar pub-avatar-m3">
              <img v-if="avatarSrc" :src="avatarSrc" class="pub-avatar-img" alt="">
              <span v-else>{{ initial }}</span>
            </div>
          </div>
          <div class="pub-m3-identity">
            <h1 class="pub-name">{{ profile.display_name }}</h1>
            <p v-if="profile.bio" class="pub-bio">{{ profile.bio }}</p>
          </div>
        </div>

        <div v-if="profile.tags.length" class="pub-tags pub-tags-m3">
          <span
            v-for="tag in profile.tags"
            :key="tag"
            class="pub-m3-chip"
          >{{ tag }}</span>
        </div>
      </header>

      <div class="pub-divider pub-m3-divider" />

      <div class="pub-blocks">
        <template v-for="block in visibleBlocks" :key="block.id">
          <div v-if="block.block_type === 'links'" class="pub-block-links">
            <div v-for="group in (block.config.groups as Group[])" :key="group.title" class="pub-links-group">
              <div v-if="group.title" class="pub-group-title">{{ group.title }}</div>
              <a
                v-for="link in group.links"
                :key="link.url"
                :href="normalizeUrl(link.url)"
                target="_blank"
                rel="noopener"
                class="pub-link pub-link-m3"
              >
                <span class="pub-link-icon-wrap pub-m3-link-icon">
                  <i aria-hidden="true" v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                  <i aria-hidden="true" v-else class="ri-link pub-link-icon" />
                </span>
                <span class="pub-link-label">{{ link.label || link.url }}</span>
                <span class="pub-m3-link-action" aria-hidden="true">
                  <i aria-hidden="true" class="ri-arrow-right-up-line pub-link-arrow" />
                </span>
              </a>
            </div>
          </div>

          <article
            v-else
            class="pub-block pub-block-m3"
          >
            <div v-if="block.block_type === 'text'" class="pub-text pub-text-m3">
              {{ (block.config.content as string) }}
            </div>

            <template v-else-if="block.block_type === 'widget_steam'">
              <div class="pub-wh pub-m3-widget-head">
                <div class="pub-wh-left">
                  <div class="pub-w-ico-bg pub-m3-service-icon pub-m3-steam">
                    <i aria-hidden="true" class="ri-steam-fill" />
                  </div>
                  <div>
                    <div class="pub-w-name">Steam</div>
                    <div class="pub-w-id">{{ steamDisplayName(block) }}</div>
                  </div>
                </div>
                <span v-if="steamStatusLabel(block)" class="pub-m3-status-pill" :class="steamStatusClass(block)">
                  <span class="pub-m3-status-dot" aria-hidden="true" />
                  {{ steamStatusLabel(block) }}
                </span>
              </div>
              <template v-if="block.config.show_recent_games && steamGamesList(block).length">
                <div class="pub-divider" />
                <div class="pub-sub-label">Недавно в игре</div>
                <div v-for="g in steamGamesList(block)" :key="`${g.appid || g.name}`" class="pub-steam-row">
                  <span class="pub-steam-name">
                    {{ g.name }}
                    <small v-if="steamGameMeta(g)">{{ steamGameMeta(g) }}</small>
                  </span>
                  <span class="pub-steam-h">{{ steamTotalHours(g) }} ч</span>
                </div>
              </template>
              <template v-if="block.config.show_profile_stats && steamStatsList(block).length">
                <div class="pub-divider" />
                <div class="pub-faceit-stats">
                  <div v-for="s in steamStatsList(block)" :key="s.label" class="pub-faceit-stat pub-m3-stat">
                    <div class="pub-fstat-v">{{ s.value }}</div>
                    <div class="pub-fstat-l">{{ s.label }}</div>
                  </div>
                </div>
              </template>
              <p v-if="block.config.show_inventory_highlight && inventoryStatus(block)" class="pub-sub-label">
                {{ inventoryStatus(block)?.title }}: {{ inventoryStatus(block)?.reason }}
              </p>
            </template>

            <template v-else-if="block.block_type === 'widget_lastfm'">
              <div class="pub-wh pub-m3-widget-head">
                <div class="pub-wh-left">
                  <div class="pub-w-ico-bg pub-m3-service-icon pub-m3-lastfm">
                    <i aria-hidden="true" class="ri-music-2-fill" />
                  </div>
                  <div>
                    <div class="pub-w-name">Last.fm</div>
                    <div class="pub-w-id">@{{ block.config.username || '-' }}</div>
                  </div>
                </div>
                <div v-if="block.config.show_now_playing && block.config.username" class="pub-np-bars">
                  <span v-for="i in 5" :key="i" class="pub-np-bar" :style="`animation-delay:${(i-1)*0.18}s`" />
                </div>
              </div>
              <template v-if="block.config.show_now_playing && block.config.username">
                <div class="pub-divider" />
                <div class="pub-np-row">
                  <div class="pub-np-disc"><i aria-hidden="true" class="ri-disc-fill" /></div>
                  <div>
                    <div class="pub-np-label">Сейчас слушает</div>
                    <div class="pub-np-track">{{ mock.lastfmTrack(block.config.username as string).track }}</div>
                    <div class="pub-np-artist">{{ mock.lastfmTrack(block.config.username as string).artist }}</div>
                  </div>
                </div>
              </template>
            </template>

            <template v-else-if="block.block_type === 'widget_github'">
              <div class="pub-wh pub-m3-widget-head">
                <div class="pub-wh-left">
                  <div class="pub-w-ico-bg pub-m3-service-icon pub-m3-github">
                    <i aria-hidden="true" :class="gitProviderIcon(block)" />
                  </div>
                  <div>
                    <div class="pub-w-name">{{ gitProviderLabel(block) }}</div>
                    <div class="pub-w-id">@{{ gitUsername(block) || '-' }}</div>
                  </div>
                </div>
                <span v-if="gitRepositoryTotal(block) !== null" class="pub-m3-soft-chip">
                  {{ gitRepositoryTotal(block) }} репо
                </span>
              </div>
              <template v-if="gitUsername(block)">
                <div class="pub-divider" />
                <div v-if="block.config.show_repository_stats && gitRepositoryStatsList(block).length" class="pub-faceit-stats">
                  <div v-for="s in gitRepositoryStatsList(block)" :key="s.label" class="pub-faceit-stat pub-m3-stat">
                    <div class="pub-fstat-v">{{ s.value }}</div>
                    <div class="pub-fstat-l">{{ s.label }}</div>
                  </div>
                </div>
                <div v-if="block.config.show_contributions && gitContributionCells(block).length" class="pub-gh-grid-wrap">
                  <div class="pub-gh-grid" :aria-label="gitActivitySummary(block)">
                    <span
                      v-for="(day, index) in gitContributionCells(block)"
                      :key="day.date || `pad-${index}`"
                      class="pub-gh-cell"
                      :class="`pub-gh-l${gitContributionLevel(day)}`"
                      :title="gitContributionTitle(day)"
                    />
                  </div>
                </div>
                <div v-if="block.config.show_contributions && gitActivitySummary(block)" class="pub-gh-count">
                  {{ gitActivitySummary(block) }}
                </div>
                <template v-if="block.config.show_pinned_repos && gitPinnedRepositories(block).length">
                  <div class="pub-sub-label pub-m3-pin-label">Закреплённые репозитории</div>
                  <div class="pub-gh-repos">
                    <a v-for="r in gitPinnedRepositories(block)" :key="r.id || r.full_name" class="pub-gh-repo pub-m3-repo" :href="r.url || '#'" target="_blank" rel="noopener">
                      <i aria-hidden="true" class="ri-git-repository-line" />
                      <span>{{ r.full_name || r.name }}</span>
                    </a>
                  </div>
                </template>
              </template>
            </template>

            <template v-else-if="block.block_type === 'pc_config'">
              <div class="pub-wh pub-m3-widget-head">
                <div class="pub-wh-left">
                  <div class="pub-w-ico-bg pub-m3-service-icon pub-m3-pc">
                    <i aria-hidden="true" class="ri-computer-fill" />
                  </div>
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

            <template v-else-if="block.block_type === 'widget_faceit'">
              <div class="pub-wh pub-m3-widget-head">
                <div class="pub-wh-left">
                  <div class="pub-w-ico-bg pub-m3-service-icon pub-m3-faceit">
                    <FaceitLogo class="pub-faceit-logo" />
                  </div>
                  <div>
                    <div class="pub-w-name">FACEIT · CS2</div>
                    <div class="pub-w-id">{{ faceitDisplayName(block) }}</div>
                  </div>
                </div>
                <FaceitSkillLevel
                  v-if="faceitDataForBlock(block)"
                  class="pub-faceit-lvl"
                  :level="faceitDataForBlock(block)?.level || 0"
                  :accent-color="material3AccentColor"
                />
              </div>
              <template v-if="faceitDataForBlock(block)">
                <div class="pub-divider" />
                <div class="pub-faceit-stats">
                  <div v-for="s in faceitStatsList(block)" :key="s.label" class="pub-faceit-stat pub-m3-stat">
                    <div class="pub-fstat-v">{{ s.value }}</div>
                    <div class="pub-fstat-l">{{ s.label }}</div>
                  </div>
                </div>
              </template>
            </template>
          </article>
        </template>
      </div>

      <div class="pub-divider pub-m3-divider" />
      <div class="pub-footer">
        <NuxtLink to="/" class="pub-footer-link">
          <img src="/images/logos/logo.png" alt="" class="pub-footer-logo">
          Сделано на Stellalink
        </NuxtLink>
      </div>
    </section>

    <!-- ═══════════ LIQUID GLASS THEME ═══════════ -->
    <template v-else-if="theme === 'glass'">
      <div class="pub-card pub-card-glass">
        <div class="pub-card-glass-scroll">
        <!-- Header -->
        <div class="pub-glass-header">
          <div class="pub-header-glass-row">
            <div class="pub-avatar-glass-wrap">
              <div class="pub-avatar pub-avatar-glass">
                <img v-if="avatarSrc" :src="avatarSrc" class="pub-avatar-img" alt="">
                <span v-else>{{ initial }}</span>
              </div>
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
                      <i aria-hidden="true" v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                      <i aria-hidden="true" v-else class="ri-link pub-link-icon" />
                    </span>
                    <span class="pub-link-label">{{ link.label || link.url }}</span>
                    <i aria-hidden="true" class="ri-arrow-right-up-line pub-link-arrow" />
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
                      <div class="pub-w-id">{{ steamDisplayName(block) }}</div>
                    </div>
                  </div>
                  <span v-if="steamStatusLabel(block)" class="pub-badge-green" :class="steamStatusClass(block)">
                    {{ steamStatusLabel(block) }}
                  </span>
                </div>
                <template v-if="block.config.show_recent_games && steamGamesList(block).length">
                  <div class="pub-divider" />
                  <div class="pub-sub-label">Недавно в игре</div>
                  <div v-for="g in steamGamesList(block)" :key="`${g.appid || g.name}`" class="pub-steam-row">
                    <span class="pub-steam-name">
                      {{ g.name }}
                      <small v-if="steamGameMeta(g)">{{ steamGameMeta(g) }}</small>
                    </span>
                    <span class="pub-steam-h">{{ steamTotalHours(g) }} ч</span>
                  </div>
                </template>
                <template v-if="block.config.show_profile_stats && steamStatsList(block).length">
                  <div class="pub-divider" />
                  <div class="pub-faceit-stats">
                    <div v-for="s in steamStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                </template>
                <p v-if="block.config.show_inventory_highlight && inventoryStatus(block)" class="pub-sub-label">
                  {{ inventoryStatus(block)?.title }}: {{ inventoryStatus(block)?.reason }}
                </p>
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
                    <div class="pub-w-ico-bg" style="background:rgba(255,255,255,0.06);color:#ececef"><i aria-hidden="true" :class="gitProviderIcon(block)" /></div>
                    <div>
                      <div class="pub-w-name">{{ gitProviderLabel(block) }}</div>
                      <div class="pub-w-id">@{{ gitUsername(block) || '—' }}</div>
                    </div>
                  </div>
                  <span v-if="gitRepositoryTotal(block) !== null" class="pub-gh-repos-badge">
                    {{ gitRepositoryTotal(block) }} репо
                  </span>
                </div>
                <template v-if="gitUsername(block)">
                  <div class="pub-divider" />
                  <div v-if="block.config.show_repository_stats && gitRepositoryStatsList(block).length" class="pub-faceit-stats">
                    <div v-for="s in gitRepositoryStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                  <div v-if="block.config.show_contributions && gitContributionCells(block).length" class="pub-gh-grid-wrap">
                    <div class="pub-gh-grid" :aria-label="gitActivitySummary(block)">
                      <span
                        v-for="(day, index) in gitContributionCells(block)"
                        :key="day.date || `pad-${index}`"
                        class="pub-gh-cell"
                        :class="`pub-gh-l${gitContributionLevel(day)}`"
                        :title="gitContributionTitle(day)"
                      />
                    </div>
                  </div>
                  <div v-if="block.config.show_contributions && gitActivitySummary(block)" class="pub-gh-count">
                    {{ gitActivitySummary(block) }}
                  </div>
                  <template v-if="block.config.show_pinned_repos && gitPinnedRepositories(block).length">
                    <div class="pub-sub-label" style="margin-top:12px">Закреплённые репозитории</div>
                    <div class="pub-gh-repos">
                      <a v-for="r in gitPinnedRepositories(block)" :key="r.id || r.full_name" class="pub-gh-repo" :href="r.url || '#'" target="_blank" rel="noopener">
                        <i aria-hidden="true" class="ri-git-repository-line" />
                        <span>{{ r.full_name || r.name }}</span>
                      </a>
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
                    <div class="pub-w-ico-bg pub-faceit-icon-bg">
                      <FaceitLogo class="pub-faceit-logo" />
                    </div>
                    <div>
                      <div class="pub-w-name">FACEIT · CS2</div>
                      <div class="pub-w-id">{{ faceitDisplayName(block) }}</div>
                    </div>
                  </div>
                  <FaceitSkillLevel
                    v-if="faceitDataForBlock(block)"
                    class="pub-faceit-lvl"
                    :level="faceitDataForBlock(block)?.level || 0"
                  />
                </div>
                <template v-if="faceitDataForBlock(block)">
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

    </template>

    <!-- ═══════════ FLUENT THEME ═══════════ -->
    <template v-else-if="theme === 'fluent'">
      <div class="pub-card pub-card-fluent">
        <!-- Header -->
        <fluent-card class="pub-fluent-section pub-fluent-header-card">
          <div class="pub-header">
            <div class="pub-avatar">
              <img v-if="avatarSrc" :src="avatarSrc" class="pub-avatar-img" alt="">
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
                      <i aria-hidden="true" v-if="link.icon" :class="`ri-${link.icon}-fill`" class="pub-link-icon" />
                      <i aria-hidden="true" v-else class="ri-link pub-link-icon" />
                    </span>
                    <span class="pub-link-label">{{ link.label || link.url }}</span>
                    <i aria-hidden="true" class="ri-arrow-right-up-line pub-link-arrow" />
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
                      <div class="pub-w-id">{{ steamDisplayName(block) }}</div>
                    </div>
                  </div>
                  <fluent-badge
                    v-if="steamStatusLabel(block)"
                    :appearance="steamIsOnline(block) ? 'accent' : 'neutral'"
                    class="pub-fluent-badge-online"
                  >
                    {{ steamStatusLabel(block) }}
                  </fluent-badge>
                </div>
                <template v-if="block.config.show_recent_games && steamGamesList(block).length">
                  <div class="pub-divider" />
                  <div class="pub-sub-label">Недавно в игре</div>
                  <div v-for="g in steamGamesList(block)" :key="`${g.appid || g.name}`" class="pub-steam-row">
                    <span class="pub-steam-name">
                      {{ g.name }}
                      <small v-if="steamGameMeta(g)">{{ steamGameMeta(g) }}</small>
                    </span>
                    <span class="pub-steam-h">{{ steamTotalHours(g) }} ч</span>
                  </div>
                </template>
                <template v-if="block.config.show_profile_stats && steamStatsList(block).length">
                  <div class="pub-divider" />
                  <div class="pub-faceit-stats">
                    <div v-for="s in steamStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                </template>
                <p v-if="block.config.show_inventory_highlight && inventoryStatus(block)" class="pub-sub-label">
                  {{ inventoryStatus(block)?.title }}: {{ inventoryStatus(block)?.reason }}
                </p>
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
                    <div class="pub-w-ico-bg" style="background:rgba(255,255,255,0.06);color:#ececef"><i aria-hidden="true" :class="gitProviderIcon(block)" /></div>
                    <div>
                      <div class="pub-w-name">{{ gitProviderLabel(block) }}</div>
                      <div class="pub-w-id">@{{ gitUsername(block) || '—' }}</div>
                    </div>
                  </div>
                  <fluent-badge v-if="gitRepositoryTotal(block) !== null" appearance="neutral">
                    {{ gitRepositoryTotal(block) }} репо
                  </fluent-badge>
                </div>
                <template v-if="gitUsername(block)">
                  <div class="pub-divider" />
                  <div v-if="block.config.show_repository_stats && gitRepositoryStatsList(block).length" class="pub-faceit-stats">
                    <div v-for="s in gitRepositoryStatsList(block)" :key="s.label" class="pub-faceit-stat">
                      <div class="pub-fstat-v">{{ s.value }}</div>
                      <div class="pub-fstat-l">{{ s.label }}</div>
                    </div>
                  </div>
                  <div v-if="block.config.show_contributions && gitContributionCells(block).length" class="pub-gh-grid-wrap">
                    <div class="pub-gh-grid" :aria-label="gitActivitySummary(block)">
                      <span
                        v-for="(day, index) in gitContributionCells(block)"
                        :key="day.date || `pad-${index}`"
                        class="pub-gh-cell"
                        :class="`pub-gh-l${gitContributionLevel(day)}`"
                        :title="gitContributionTitle(day)"
                      />
                    </div>
                  </div>
                  <div v-if="block.config.show_contributions && gitActivitySummary(block)" class="pub-gh-count">
                    {{ gitActivitySummary(block) }}
                  </div>
                  <template v-if="block.config.show_pinned_repos && gitPinnedRepositories(block).length">
                    <div class="pub-sub-label" style="margin-top:12px">Закреплённые репозитории</div>
                    <div class="pub-gh-repos">
                      <a v-for="r in gitPinnedRepositories(block)" :key="r.id || r.full_name" class="pub-gh-repo" :href="r.url || '#'" target="_blank" rel="noopener">
                        <i aria-hidden="true" class="ri-git-repository-line" />
                        <span>{{ r.full_name || r.name }}</span>
                      </a>
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
                    <div class="pub-w-ico-bg pub-faceit-icon-bg">
                      <FaceitLogo class="pub-faceit-logo" />
                    </div>
                    <div>
                      <div class="pub-w-name">FACEIT · CS2</div>
                      <div class="pub-w-id">{{ faceitDisplayName(block) }}</div>
                    </div>
                  </div>
                  <FaceitSkillLevel
                    v-if="faceitDataForBlock(block)"
                    class="pub-faceit-lvl"
                    :level="faceitDataForBlock(block)?.level || 0"
                  />
                </div>
                <template v-if="faceitDataForBlock(block)">
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

    </template>
  </div>
</template>

<script setup lang="ts">
import type { Block } from '~/stores/profile'


interface Link { label: string; url: string; icon?: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }
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

interface GitContributionDay {
  date?: string
  count?: number
  level?: number
  empty?: boolean
}

type ThemeColorMode = 'light' | 'dark'
type Material3Layout = 'compact' | 'wide'

interface ProfileThemeTokens {
  colorMode?: ThemeColorMode
  material3Layout?: Material3Layout
  [key: string]: unknown
}

definePageMeta({ layout: 'landing' })

const route = useRoute()
const config = useRuntimeConfig()
const requestUrl = useRequestURL()
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
  theme_tokens: Record<string, unknown> | null
  accent_color: string | null
} | null>(`${config.public.apiBase}/u/${slug}`, {
  default: () => null,
  onResponseError() { return null },
})

const avatarSrc = computed(() =>
  profile.value?.avatar_url
    ? resolveAvatarUrl(profile.value.avatar_url, config.public.apiBase as string)
    : null
)
const pageTitle = computed(() => {
  const name = profile.value?.display_name
  return name ? `${name} — Stellalink` : `${slug} — Stellalink`
})
const seoDescription = computed(() =>
  profile.value?.bio || 'Живой профиль Stellalink в одном URL',
)
const seoImage = computed(() => {
  const image = avatarSrc.value || '/images/logos/logo_big.png'
  return new URL(image, requestUrl.origin).toString()
})

useSeoMeta({
  title: () => pageTitle.value,
  description: () => seoDescription.value,
  ogTitle: () => pageTitle.value,
  ogDescription: () => seoDescription.value,
  ogImage: () => seoImage.value,
  ogUrl: () => new URL(route.fullPath, requestUrl.origin).toString(),
  twitterCard: 'summary_large_image',
  twitterTitle: () => pageTitle.value,
  twitterDescription: () => seoDescription.value,
  twitterImage: () => seoImage.value,
})

const theme = computed(() => profile.value?.theme_preset || 'material3')
const themeTokens = computed<ProfileThemeTokens>(() => {
  const tokens = profile.value?.theme_tokens
  return tokens && typeof tokens === 'object' ? tokens as ProfileThemeTokens : {}
})
const themeMode = computed<ThemeColorMode>(() => {
  const mode = themeTokens.value.colorMode
  if (mode === 'light' || mode === 'dark') return mode
  return theme.value === 'material3' ? 'light' : 'dark'
})
const isMaterial3Wide = computed(() =>
  theme.value === 'material3' && themeTokens.value.material3Layout === 'wide',
)
const material3AccentColor = computed(() => theme.value === 'material3' ? (profile.value?.accent_color || '#6750a4') : null)
const initial = computed(() => profile.value?.display_name?.[0]?.toUpperCase() ?? '?')
const visibleBlocks = computed(() => profile.value?.blocks.filter(b => b.is_visible) ?? [])

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const normalized = hex.trim().replace('#', '')
  if (!/^[0-9a-f]{6}$/i.test(normalized)) return null
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  }
}

const accentVars = computed(() => {
  if (theme.value !== 'material3') return ''
  const c = profile.value?.accent_color
  if (!c) return ''
  const rgb = hexToRgb(c)
  if (!rgb) return `--t-accent:${c}`
  return [
    `--t-accent:${c}`,
    `--t-accent20:rgba(${rgb.r},${rgb.g},${rgb.b},0.20)`,
    `--t-accent30:rgba(${rgb.r},${rgb.g},${rgb.b},0.30)`,
    `--t-accent12:rgba(${rgb.r},${rgb.g},${rgb.b},0.12)`,
  ].join(';')
})

// Liquid Glass — SVG displacement filter applied once after mount
type DisplacementUtils = {
  getDisplacementFilter(opts: { height: number; width: number; radius: number; depth: number; strength: number; chromaticAberration: number }): string
}

let glassApplied = false
let glassResizeTimeout: ReturnType<typeof setTimeout> | null = null

function applyLiquidGlass() {
  if (typeof window === 'undefined') return
  if (theme.value !== 'glass') return

  const utils = (window as unknown as { DisplacementUtils?: DisplacementUtils }).DisplacementUtils
  if (!utils) {
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

function scheduleLiquidGlass() {
  if (typeof window === 'undefined') return
  if (glassResizeTimeout) window.clearTimeout(glassResizeTimeout)
  glassResizeTimeout = window.setTimeout(() => {
    glassResizeTimeout = null
    glassApplied = false
    applyLiquidGlass()
  }, 180)
}

onMounted(() => {
  nextTick(() => setTimeout(applyLiquidGlass, 200))
  window.addEventListener('resize', scheduleLiquidGlass, { passive: true })
})

onBeforeUnmount(() => {
  if (typeof window === 'undefined') return
  window.removeEventListener('resize', scheduleLiquidGlass)
  if (glassResizeTimeout) window.clearTimeout(glassResizeTimeout)
})

watch(theme, () => { glassApplied = false; nextTick(() => setTimeout(applyLiquidGlass, 200)) })

function normalizeUrl(url: string | undefined): string {
  if (!url) return '#'
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

function steamGamesList(block: Block): SteamGame[] {
  const liveGames = Array.isArray(block.config.steam_recent_games) ? block.config.steam_recent_games as SteamGame[] : []
  return liveGames
}

function steamDisplayName(block: Block): string {
  const steamProfile = block.config.steam_profile as Record<string, unknown> | undefined
  return String(block.config.steam_display_name || steamProfile?.personaname || 'Steam не привязан')
}

function steamPersonaState(block: Block): number | null {
  const steamProfile = block.config.steam_profile as Record<string, unknown> | undefined
  const rawState = steamProfile?.personastate ?? block.config.steam_persona_state
  const state = Number(rawState)
  return Number.isFinite(state) ? state : null
}

function steamStatusLabel(block: Block): string {
  const state = steamPersonaState(block)
  if (state === null) return ''
  const labels: Record<number, string> = {
    0: 'Не в сети',
    1: 'Online',
    2: 'Занят',
    3: 'Отошел',
    4: 'Спит',
    5: 'Готов к обмену',
    6: 'Готов играть',
  }
  return labels[state] ?? 'Статус Steam'
}

function steamIsOnline(block: Block): boolean {
  return steamPersonaState(block) === 1
}

function steamStatusClass(block: Block): Record<string, boolean> {
  return {
    online: steamIsOnline(block),
    offline: steamPersonaState(block) === 0,
    away: [2, 3, 4, 5, 6].includes(steamPersonaState(block) ?? -1),
  }
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

function steamStatsList(block: Block) {
  const stats = block.config.steam_profile_stats as Record<string, unknown> | undefined
  if (!stats) return []
  return [
    { label: 'Level', value: stats.level },
    { label: 'Badges', value: stats.badge_count },
    { label: 'XP', value: stats.player_xp },
  ].filter(item => item.value !== undefined && item.value !== null && item.value !== '')
}

function inventoryStatus(block: Block) {
  const item = block.config.steam_inventory_highlight as Record<string, unknown> | undefined
  if (!item) return null
  return {
    title: String(item.title || 'Инвентарь'),
    reason: String(item.reason || 'Источник цен не настроен.'),
  }
}

function gitProviderLabel(block: Block): string {
  const provider = String(block.config.git_provider || block.config.provider || 'github')
  return String(block.config.git_provider_label || ({ github: 'GitHub', gitlab: 'GitLab', gitea: 'Gitea' } as Record<string, string>)[provider] || 'Git')
}

function gitProviderIcon(block: Block): string {
  const provider = String(block.config.git_provider || block.config.provider || 'github')
  return ({ github: 'ri-github-fill', gitlab: 'ri-gitlab-fill', gitea: 'ri-git-repository-line' } as Record<string, string>)[provider] || 'ri-git-repository-line'
}

function gitUsername(block: Block): string {
  const live = block.config.git_profile as Record<string, unknown> | undefined
  return String(block.config.username || live?.username || '')
}

function gitRepositoryStats(block: Block): Record<string, unknown> {
  const stats = block.config.git_repository_stats as Record<string, unknown> | undefined
  return stats && typeof stats === 'object' ? stats : {}
}

function gitRepositoryTotal(block: Block): number | null {
  const total = gitRepositoryStats(block).total_repositories
  return typeof total === 'number' ? total : null
}

function gitRepositoryStatsList(block: Block) {
  const stats = gitRepositoryStats(block)
  return [
    { label: 'Repos', value: stats.total_repositories },
    { label: 'Stars', value: stats.stars },
    { label: 'Forks', value: stats.forks },
    { label: 'Private', value: stats.private_repositories },
  ].filter(item => item.value !== undefined && item.value !== null && item.value !== '')
}

function gitPinnedRepositories(block: Block): GitRepository[] {
  const repos = Array.isArray(block.config.git_pinned_repositories) ? block.config.git_pinned_repositories as GitRepository[] : []
  return repos.slice(0, 6)
}

function gitContributionDays(block: Block): GitContributionDay[] {
  const activity = block.config.git_contributions as Record<string, unknown> | undefined
  return Array.isArray(activity?.days) ? activity.days as GitContributionDay[] : []
}

function gitContributionCells(block: Block): GitContributionDay[] {
  const days = gitContributionDays(block)
  if (!days.length) return []
  const first = new Date(String(days[0].date || ''))
  const pad = Number.isNaN(first.getTime()) ? 0 : first.getDay()
  return [
    ...Array.from({ length: pad }, () => ({ empty: true, count: 0, level: 0 })),
    ...days,
  ]
}

function gitContributionLevel(day: GitContributionDay): number {
  if (day.empty) return 0
  const level = Number(day.level || 0)
  return Math.max(0, Math.min(4, Number.isFinite(level) ? level : 0))
}

function gitContributionTitle(day: GitContributionDay): string {
  if (day.empty || !day.date) return ''
  const date = formatLastPlayed(day.date)
  const count = Number(day.count || 0)
  return `${date || day.date}: ${count} событий`
}

function gitActivitySummary(block: Block): string {
  const activity = block.config.git_contributions as Record<string, unknown> | undefined
  if (!activity || !Array.isArray(activity.days)) return ''
  const total = Number(activity.total || 0)
  const days = Number(activity.window_days || block.config.contributions_days || 30)
  return total > 0
    ? `Активность за ${days} дней: ${total} событий`
    : `Нет активности за ${days} дней`
}

function faceitDataForBlock(block: Block) {
  const live = block.config.faceit_profile as Record<string, any> | undefined
  if (live) {
    return {
      level: Number(live.skill_level || live.skill_level_label || 0),
      elo: live.faceit_elo || '—',
      kd: live.stats?.kd || '—',
      winRate: live.stats?.win_rate || '—',
      matches: live.stats?.matches || '—',
    }
  }
  return null
}

function faceitDisplayName(block: Block): string {
  const live = block.config.faceit_profile as Record<string, any> | undefined
  return String(block.config.faceit_display_name || block.config.nickname || live?.nickname || 'FACEIT не найден')
}

function faceitStatsList(block: Block) {
  const data = faceitDataForBlock(block)
  if (!data) return []
  return [
    { value: data.elo, label: 'ELO' },
    { value: data.kd, label: 'K/D' },
    { value: String(data.winRate).includes('%') ? data.winRate : `${data.winRate}%`, label: 'Win Rate' },
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
  font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
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

@media (prefers-color-scheme: light) {
  .pub-loading {
    background: #fffbff;
  }

  .pub-spinner {
    border-color: rgba(0, 0, 0, 0.12);
    border-top-color: #49454f;
  }

  .pub-notfound {
    background: #fffbff;
    color: #1d1b20;
  }

  .pub-notfound p {
    color: #625b71;
  }

  .pub-nf-logo {
    mix-blend-mode: multiply;
  }

  .pub-home-btn {
    background: rgba(103, 80, 164, 0.08);
    border-color: rgba(103, 80, 164, 0.18);
    color: #4f378b;
  }
}

/* ── Theme tokens ────────────────────────────────────────────────────────────── */
.pub-page {
  --t-accent:   #6750a4;
  --t-accent20: rgba(103,80,164,0.20);
  --t-accent30: rgba(103,80,164,0.30);
  --t-accent12: rgba(103,80,164,0.12);
  --t-bg:       #121116;
  --t-surface:  #f5eff7;
  --t-card-bg:  #fffbff;
  --t-card-border: rgba(73,69,79,0.18);
  --t-text:     #1d1b20;
  --t-muted:    #514d58;
  --t-dim:      #6e6876;
  --t-border:   rgba(73,69,79,0.16);
  --t-glow:     rgba(103,80,164,0.20);
  --t-tag-bg:   #e8def8;
  --t-tag-c:    #4f378b;
  --t-radius:   32px;
  --t-radius-sm: 18px;
  --t-blur:     none;
  --t-card-shadow: 0 24px 80px rgba(0,0,0,0.28), 0 2px 8px rgba(0,0,0,0.10);
  --t-block-shadow: 0 3px 10px rgba(0,0,0,0.08);
  --m3-primary: color-mix(in srgb, var(--t-accent) 72%, #34205f);
  --m3-on-primary: #ffffff;
  --m3-primary-container: color-mix(in srgb, var(--t-accent) 24%, #ffffff);
  --m3-on-primary-container: color-mix(in srgb, var(--t-accent) 46%, #1d1b20);
  --m3-secondary: #006b5f;
  --m3-secondary-container: #a9f2df;
  --m3-on-secondary-container: #00201c;
  --m3-tertiary: #8f4c38;
  --m3-tertiary-container: #ffdad0;
  --m3-on-tertiary-container: #3a0a00;
  --m3-surface: #fffbff;
  --m3-surface-container-low: #f8f2fa;
  --m3-surface-container: #f1ebf4;
  --m3-surface-container-high: #e9e3ed;
  --m3-outline: rgba(73,69,79,0.22);
  --m3-focus: color-mix(in srgb, var(--t-accent) 60%, #ffffff);
  --m3-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
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
  font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-start;
  padding: 24px 16px 48px; position: relative; overflow-x: clip;
}

[data-theme="material3"].pub-page {
  justify-content: center;
  padding: clamp(14px, 3vh, 28px) 14px;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--t-accent) 14%, transparent) 0%, transparent 42%),
    linear-gradient(180deg, #19171f 0%, #111014 100%);
}

[data-theme="material3"][data-mode="light"].pub-page {
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--t-accent) 14%, transparent) 0%, transparent 44%),
    linear-gradient(180deg, #fffbff 0%, #f4eff7 100%);
}

[data-theme="material3"][data-mode="dark"].pub-page {
  --t-bg: #111014;
  --t-surface: #211f26;
  --t-card-bg: #1d1b20;
  --t-card-border: rgba(230, 224, 233, 0.16);
  --t-text: #f4eff7;
  --t-muted: rgba(244, 239, 247, 0.72);
  --t-dim: rgba(244, 239, 247, 0.48);
  --t-border: rgba(230, 224, 233, 0.14);
  --t-tag-bg: color-mix(in srgb, var(--t-accent) 22%, #211f26);
  --t-tag-c: color-mix(in srgb, var(--t-accent) 40%, #ffffff);
  --m3-primary: color-mix(in srgb, var(--t-accent) 78%, #ffffff);
  --m3-on-primary: #1d1b20;
  --m3-primary-container: color-mix(in srgb, var(--t-accent) 28%, #211f26);
  --m3-on-primary-container: color-mix(in srgb, var(--t-accent) 34%, #ffffff);
  --m3-secondary-container: #0d4f47;
  --m3-on-secondary-container: #c6fff0;
  --m3-tertiary-container: #63372b;
  --m3-on-tertiary-container: #ffdad0;
  --m3-surface: #1d1b20;
  --m3-surface-container-low: #211f26;
  --m3-surface-container: #2b2930;
  --m3-surface-container-high: #36343b;
  --m3-outline: rgba(230, 224, 233, 0.18);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--t-accent) 16%, transparent) 0%, transparent 44%),
    linear-gradient(180deg, #19171f 0%, #111014 100%);
}

[data-theme="glass"][data-mode="light"] {
  --t-bg: #eff6ff;
  --t-surface: rgba(255,255,255,0.48);
  --t-card-bg: rgba(255,255,255,0.42);
  --t-card-border: rgba(50,70,110,0.18);
  --t-text: #172033;
  --t-muted: rgba(23,32,51,0.68);
  --t-dim: rgba(23,32,51,0.46);
  --t-border: rgba(50,70,110,0.14);
  --t-tag-bg: rgba(255,255,255,0.54);
  --t-tag-c: #24527a;
  --t-card-shadow: 0 28px 70px rgba(57,78,120,0.2), inset 0 1px 0 rgba(255,255,255,0.42);
}

[data-theme="fluent"][data-mode="light"] {
  --t-bg: #f6f8fb;
  --t-surface: rgba(255,255,255,0.76);
  --t-card-bg: rgba(255,255,255,0.82);
  --t-card-border: rgba(17,24,39,0.10);
  --t-text: #1f1f1f;
  --t-muted: rgba(31,31,31,0.68);
  --t-dim: rgba(31,31,31,0.46);
  --t-border: rgba(31,31,31,0.10);
  --t-tag-bg: rgba(96,205,255,0.13);
  --t-tag-c: #006aa6;
  --t-card-shadow: 0 18px 48px rgba(17,24,39,0.16);
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

/* ── Material 3 Expressive ─────────────────────────────────────────────────── */
.pub-card-m3 {
  max-width: 420px;
  max-height: none;
  color: var(--t-text);
  background:
    linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,251,255,0.98)),
    var(--m3-surface);
  border: 1px solid rgba(255,255,255,0.72);
  border-radius: 34px;
  box-shadow: var(--t-card-shadow);
  overflow: clip;
  isolation: isolate;
}
.pub-card-m3::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--t-accent) 20%, transparent), transparent 34%),
    linear-gradient(225deg, rgba(169,242,223,0.28), transparent 30%),
    linear-gradient(0deg, transparent 72%, rgba(255,218,208,0.38));
  opacity: 0.9;
  z-index: 0;
}
.pub-card-m3 > * {
  position: relative;
  z-index: 1;
}

[data-theme="material3"][data-mode="dark"] .pub-card-m3 {
  background:
    linear-gradient(180deg, rgba(33,31,38,0.96), rgba(29,27,32,0.98)),
    var(--m3-surface);
  border-color: rgba(230,224,233,0.12);
}

[data-theme="material3"][data-mode="dark"] .pub-card-m3::before {
  opacity: 0.54;
}

.pub-card-m3-wide {
  max-width: min(980px, calc(100vw - 32px));
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr) auto;
  align-items: stretch;
}

.pub-card-m3-wide .pub-m3-hero {
  grid-column: 1;
  grid-row: 1 / 3;
  min-height: 0;
  border-right: 1px solid var(--m3-outline);
  border-bottom: 0;
}

.pub-card-m3-wide .pub-m3-hero-row {
  flex-direction: column;
  align-items: flex-start;
}

.pub-card-m3-wide .pub-tags-m3 {
  justify-content: flex-start;
}

.pub-card-m3-wide > .pub-m3-divider {
  display: none;
}

.pub-card-m3-wide > .pub-blocks {
  grid-column: 2;
  grid-row: 1;
  min-height: 0;
  overflow: auto;
}

.pub-card-m3-wide .pub-blocks {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: start;
}

.pub-card-m3-wide .pub-block-links {
  grid-column: 1 / -1;
}

.pub-card-m3-wide > .pub-footer {
  grid-column: 2;
  grid-row: 2;
}

.pub-m3-hero {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 22px 18px;
  background:
    linear-gradient(135deg, var(--m3-primary-container), rgba(255,255,255,0.64) 48%),
    linear-gradient(225deg, var(--m3-tertiary-container), transparent 58%);
  border-bottom: 1px solid rgba(73,69,79,0.10);
}

[data-theme="material3"][data-mode="dark"] .pub-m3-hero {
  background:
    linear-gradient(135deg, var(--m3-primary-container), color-mix(in srgb, var(--m3-surface-container) 72%, transparent) 52%),
    linear-gradient(225deg, var(--m3-tertiary-container), transparent 58%);
  border-color: var(--m3-outline);
}

[data-theme="material3"][data-mode="dark"] .pub-card-m3 .pub-avatar-m3 {
  box-shadow:
    0 12px 32px color-mix(in srgb, var(--t-accent) 30%, transparent),
    0 0 0 6px rgba(33,31,38,0.78);
}

.pub-m3-hero-row {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}
.pub-m3-avatar-wrap {
  position: relative;
  flex: 0 0 auto;
}
.pub-avatar-m3 {
  width: 82px;
  height: 82px;
  border-radius: 28px 28px 22px 28px;
  overflow: hidden;
  background:
    linear-gradient(145deg, var(--m3-primary), color-mix(in srgb, var(--m3-primary) 58%, var(--m3-tertiary)));
  color: var(--m3-on-primary);
  box-shadow:
    0 12px 32px color-mix(in srgb, var(--t-accent) 28%, transparent),
    0 0 0 6px rgba(255,255,255,0.58);
  font-size: 30px;
  transition: transform 320ms var(--m3-spring), border-radius 320ms var(--m3-spring);
}
.pub-card-m3:hover .pub-avatar-m3 {
  border-radius: 24px 30px 24px 30px;
  transform: translateY(-1px) rotate(-1deg);
}
.pub-m3-identity {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}
.pub-card-m3 .pub-name {
  color: var(--t-text);
  font-size: 23px;
  line-height: 1.12;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}
.pub-card-m3 .pub-bio {
  max-width: 100%;
  color: var(--t-muted);
  font-size: 13px;
  line-height: 1.46;
}
.pub-tags-m3 {
  justify-content: flex-start;
  gap: 7px;
}
.pub-m3-chip,
.pub-m3-soft-chip,
.pub-m3-status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  color: var(--m3-on-primary-container);
  background: color-mix(in srgb, var(--m3-primary-container) 72%, #ffffff);
  border: 1px solid rgba(73,69,79,0.10);
}
.pub-m3-chip {
  padding: 0 12px;
}
.pub-m3-soft-chip,
.pub-m3-status-pill {
  padding: 0 10px;
}
.pub-m3-status-pill {
  gap: 7px;
  color: #0b3d2d;
  background: color-mix(in srgb, #a9f2df 78%, #ffffff);
}

.pub-m3-status-pill.offline {
  color: var(--t-muted);
  background: color-mix(in srgb, var(--m3-surface-container) 88%, #ffffff);
}

.pub-m3-status-pill.away {
  color: #7a4b00;
  background: color-mix(in srgb, #ffe2a8 76%, #ffffff);
}

.pub-m3-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #0f9f6e;
  box-shadow: 0 0 0 5px rgba(15,159,110,0.12);
}

.pub-m3-status-pill.offline .pub-m3-status-dot {
  background: #8b95a5;
  box-shadow: 0 0 0 5px rgba(139,149,165,0.14);
}

.pub-m3-status-pill.away .pub-m3-status-dot {
  background: #d08300;
  box-shadow: 0 0 0 5px rgba(208,131,0,0.16);
}
.pub-m3-divider {
  margin: 0;
  background: linear-gradient(90deg, transparent, rgba(73,69,79,0.16), transparent);
}
.pub-card-m3 .pub-blocks {
  min-height: 0;
  overflow-y: auto;
  padding: 12px 14px 14px;
  gap: 10px;
  overscroll-behavior: contain;
}

.pub-card-m3:not(.pub-card-m3-wide) .pub-blocks {
  overflow-y: visible;
}

.pub-card-m3 .pub-blocks::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--t-accent) 30%, rgba(73,69,79,0.22));
}
.pub-block-m3,
.pub-link-m3 {
  border: 1px solid var(--m3-outline);
  background: color-mix(in srgb, var(--m3-surface-container-low) 86%, #ffffff);
  box-shadow: var(--t-block-shadow);
  transition:
    transform 260ms var(--m3-spring),
    border-color 260ms var(--m3-spring),
    background 260ms var(--m3-spring),
    box-shadow 260ms var(--m3-spring);
  animation: m3Enter 360ms var(--m3-spring) both;
}
.pub-block-m3 {
  padding: 16px;
  border-radius: 24px;
}
.pub-link-m3 {
  min-height: 58px;
  padding: 10px 12px;
  border-radius: 22px;
}
.pub-link-m3:hover,
.pub-block-m3:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--t-accent) 38%, rgba(73,69,79,0.22));
  background: color-mix(in srgb, var(--m3-primary-container) 42%, #ffffff);
  box-shadow: 0 10px 28px rgba(0,0,0,0.12);
}
.pub-link-m3:active {
  transform: translateY(0) scale(0.99);
}
.pub-link-m3:focus-visible,
.pub-footer-link:focus-visible {
  outline: 3px solid var(--m3-focus);
  outline-offset: 3px;
}
.pub-m3-link-icon,
.pub-m3-service-icon {
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 16px;
  color: var(--m3-on-primary);
  background: var(--m3-primary);
  box-shadow: inset 0 -1px 0 rgba(0,0,0,0.10);
}
.pub-m3-link-action {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: var(--m3-on-primary-container);
  background: rgba(255,255,255,0.58);
  transition: transform 260ms var(--m3-spring), background 260ms var(--m3-spring);
}
.pub-link-m3:hover .pub-m3-link-action {
  transform: rotate(8deg);
  background: var(--m3-surface);
}
.pub-m3-widget-head {
  gap: 12px;
  margin-bottom: 0;
}
.pub-m3-steam {
  color: #ffffff;
  background: #1b6ea8;
}
.pub-m3-lastfm {
  color: #ffffff;
  background: #c81f32;
}
.pub-m3-github {
  color: #ffffff;
  background: #24292f;
}
.pub-m3-pc {
  color: var(--m3-on-primary);
  background: var(--m3-primary);
}
.pub-m3-faceit {
  color: #ff5500;
  background: rgba(255,85,0,0.14);
}
.pub-faceit-icon-bg {
  color: #ff8c42;
  background: rgba(255,90,0,0.15);
}
.pub-faceit-logo {
  width: 20px;
  height: 20px;
  display: block;
}
.pub-card-m3 .pub-divider {
  background: rgba(73,69,79,0.12);
}
.pub-card-m3 .pub-sub-label,
.pub-card-m3 .pub-np-label,
.pub-card-m3 .pub-fstat-l,
.pub-card-m3 .pub-group-title {
  letter-spacing: 0;
}
.pub-text-m3 {
  color: var(--t-muted);
  border-left-color: var(--m3-primary);
  background: color-mix(in srgb, var(--m3-primary-container) 34%, transparent);
  border-radius: 0 18px 18px 0;
  padding-block: 4px;
}
.pub-card-m3 .pub-gh-l0 {
  background: rgba(73,69,79,0.10);
}
.pub-card-m3 .pub-gh-l1 {
  background: color-mix(in srgb, var(--t-accent) 22%, #ffffff);
}
.pub-card-m3 .pub-gh-l2 {
  background: color-mix(in srgb, var(--t-accent) 42%, #ffffff);
}
.pub-card-m3 .pub-gh-l3 {
  background: color-mix(in srgb, var(--t-accent) 62%, #ffffff);
  opacity: 1;
}
.pub-card-m3 .pub-gh-l4 {
  background: var(--m3-primary);
}
.pub-m3-pin-label {
  margin-top: 14px;
}
.pub-m3-repo,
.pub-m3-stat {
  background: var(--m3-surface-container);
  border-color: rgba(73,69,79,0.12);
}
.pub-card-m3 .pub-footer {
  border-top: 0;
  background: rgba(255,251,255,0.74);
  backdrop-filter: blur(14px);
}
.pub-card-m3 .pub-footer-link {
  color: var(--t-dim);
  border-radius: 999px;
  padding: 7px 11px;
}
.pub-card-m3 .pub-footer-link:hover {
  color: var(--m3-on-primary-container);
  background: var(--m3-primary-container);
}

@keyframes m3Enter {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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

[data-theme="fluent"][data-mode="light"] .pub-card-fluent {
  background: rgba(255,255,255,0.88);
  border-color: rgba(31,35,43,0.10);
  box-shadow: 0 12px 42px rgba(40,48,65,0.16);
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

[data-theme="fluent"][data-mode="light"] .pub-card-fluent :deep(fluent-card) {
  --fill-color: rgba(255,255,255,0.74);
  background: rgba(255,255,255,0.74);
  border-color: rgba(31,35,43,0.10);
  color: var(--t-text);
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
  font-family: 'Roboto Flex', 'Segoe UI', sans-serif;
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
.pub-name { font-size: 20px; font-weight: 800; letter-spacing: 0; margin: 0; }
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
  letter-spacing: 0; color: var(--t-dim); padding: 0 4px;
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
/* Material 3 icon surface */
.pub-card-m3 .pub-link-icon-wrap {
  display: flex; align-items: center; justify-content: center;
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 16px;
  color: var(--m3-on-primary);
  background: var(--m3-primary);
  box-shadow: inset 0 -1px 0 rgba(0,0,0,0.10);
  font-size: 18px;
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
.pub-card-m3 .pub-m3-service-icon {
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 16px;
  box-shadow: inset 0 -1px 0 rgba(0,0,0,0.10);
}
.pub-card-m3 .pub-avatar-m3 {
  width: 82px;
  height: 82px;
  border-radius: 28px 28px 22px 28px;
  overflow: hidden;
  background:
    linear-gradient(145deg, var(--m3-primary), color-mix(in srgb, var(--m3-primary) 58%, var(--m3-tertiary)));
  color: var(--m3-on-primary);
  box-shadow:
    0 12px 32px color-mix(in srgb, var(--t-accent) 28%, transparent),
    0 0 0 6px rgba(255,255,255,0.58);
  font-size: 30px;
  margin-bottom: 0;
}
.pub-card-m3 .pub-link-m3 {
  min-height: 58px;
  padding: 10px 12px;
  border-radius: 22px;
  transition:
    transform 260ms var(--m3-spring),
    border-color 260ms var(--m3-spring),
    background 260ms var(--m3-spring),
    box-shadow 260ms var(--m3-spring);
}
.pub-card-m3 .pub-block-m3 {
  padding: 16px;
  border-radius: 24px;
}
.pub-card-m3 .pub-text-m3 {
  color: var(--t-muted);
  border-left-color: var(--m3-primary);
  background: color-mix(in srgb, var(--m3-primary-container) 34%, transparent);
  border-radius: 0 18px 18px 0;
  padding-block: 4px;
}
.pub-card-m3 .pub-divider {
  margin: 12px 0;
}
.pub-card-m3 > .pub-m3-divider {
  margin: 0;
}
.pub-card-m3 .pub-group-title,
.pub-card-m3 .pub-sub-label {
  letter-spacing: 0;
}
.pub-card-m3 .pub-np-disc {
  color: var(--m3-on-tertiary-container);
  background: var(--m3-tertiary-container);
  border-color: rgba(143,76,56,0.18);
}
.pub-card-m3 .pub-m3-repo,
.pub-card-m3 .pub-m3-stat {
  background: var(--m3-surface-container);
  border-color: rgba(73,69,79,0.12);
}
.pub-card-m3 .pub-faceit-lvl {
  box-shadow: 0 5px 16px rgba(0,0,0,0.18);
}
.pub-card-m3 .pub-footer-logo {
  opacity: 0.58;
  mix-blend-mode: normal;
}
.pub-w-name { font-size: 14px; font-weight: 700; line-height: 1.2; }
.pub-w-id { font-size: 12px; color: var(--t-muted); margin-top: 1px; }
.pub-divider { height: 1px; background: var(--t-border); margin: 12px 0; }
[data-theme="glass"] .pub-divider {
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
}
.pub-sub-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; color: var(--t-dim); margin-bottom: 8px; }

.pub-badge-green {
  font-size: 11px; font-weight: 600; color: #4ade80;
  background: rgba(74,222,128,0.10); border: 1px solid rgba(74,222,128,0.20);
  border-radius: 100px; padding: 2px 9px;
}

.pub-badge-green.offline {
  color: #a1a1aa;
  background: rgba(161,161,170,0.10);
  border-color: rgba(161,161,170,0.20);
}

.pub-badge-green.away {
  color: #fbbf24;
  background: rgba(251,191,36,0.10);
  border-color: rgba(251,191,36,0.22);
}

/* ── Steam ──────────────────────────────────────────────────────────────────── */
.pub-steam-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--t-border); font-size: 13px;
}
.pub-steam-row:last-child { border-bottom: none; }
.pub-steam-name {
  min-width: 0; display: grid; gap: 2px; color: var(--t-text); overflow-wrap: anywhere;
}
.pub-steam-name small { color: var(--t-dim); font-size: 11px; line-height: 1.35; }
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
.pub-np-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; color: #e5343a; margin-bottom: 2px; }
.pub-np-track { font-size: 14px; font-weight: 700; line-height: 1.2; }
.pub-np-artist { font-size: 12px; color: var(--t-muted); margin-top: 2px; }

/* ── Git repositories ───────────────────────────────────────────────────────── */
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
  text-decoration: none;
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
  width: 38px;
  height: 38px;
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
.pub-fstat-l { font-size: 10px; color: var(--t-dim); margin-top: 4px; text-transform: uppercase; letter-spacing: 0; }

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
@media (max-width: 760px) {
  .pub-card-m3-wide {
    max-width: 420px;
    display: flex;
    flex-direction: column;
  }

  .pub-card-m3-wide .pub-m3-hero {
    border-right: 0;
    border-bottom: 1px solid var(--m3-outline);
  }

  .pub-card-m3-wide .pub-m3-hero-row {
    flex-direction: row;
    align-items: center;
  }

  .pub-card-m3-wide .pub-blocks {
    grid-template-columns: 1fr;
    overflow: visible;
  }

  .pub-card-m3-wide > .pub-footer {
    grid-column: auto;
    grid-row: auto;
  }
}

@media (max-width: 540px) {
  .pub-page { padding: 12px 8px 32px; }
  .pub-card { border-radius: calc(var(--t-radius) * 0.7); max-height: calc(96vh - 24px); }
  .pub-header { padding: 20px 14px 12px; }
  .pub-blocks { padding: 8px 10px 12px; }
  [data-theme="material3"].pub-page { padding: 10px; }
  .pub-card-m3 {
    max-height: none;
    border-radius: 28px;
  }
  .pub-m3-hero {
    padding: 18px 16px 14px;
    gap: 12px;
  }
  .pub-m3-hero-row {
    align-items: flex-start;
    gap: 12px;
  }
  .pub-card-m3 .pub-avatar-m3 {
    width: 68px;
    height: 68px;
    border-radius: 24px 24px 18px 24px;
    font-size: 25px;
  }
  .pub-card-m3 .pub-name {
    font-size: 20px;
  }
  .pub-card-m3 .pub-bio {
    font-size: 12px;
  }
  .pub-card-m3 .pub-blocks {
    padding: 10px;
  }
  .pub-link-m3 {
    min-height: 54px;
    border-radius: 20px;
  }
  .pub-faceit-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pub-card-m3 *,
  .pub-card-m3 *::before,
  .pub-card-m3 *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .pub-card-m3:hover .pub-avatar-m3,
  .pub-link-m3:hover,
  .pub-block-m3:hover {
    transform: none;
  }
}
</style>
