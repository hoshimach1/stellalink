<template>
  <section class="demo-wrap" id="demo">
    <div class="demo-layout">
      <md-filled-card class="demo-story reveal">
        <div class="demo-story-label md-typescale-label-large">Проверочный экран</div>
        <h2 class="demo-story-title md-typescale-headline-medium">Одна страница вместо пяти вкладок</h2>
        <p class="demo-story-sub md-typescale-body-large">Игры, музыка, контакты и железо собираются в одном профиле. Не ссылкосвалка, а живой контекст о человеке.</p>
        <div class="demo-story-stats">
          <md-outlined-card class="demo-stat">
            <div class="demo-stat-num">4</div>
            <div class="demo-stat-key">активных сервиса</div>
          </md-outlined-card>
          <md-outlined-card class="demo-stat">
            <div class="demo-stat-num">10с</div>
            <div class="demo-stat-key">на считывание профиля</div>
          </md-outlined-card>
          <md-outlined-card class="demo-stat">
            <div class="demo-stat-num">1</div>
            <div class="demo-stat-key">ссылка для bio</div>
          </md-outlined-card>
        </div>
      </md-filled-card>

      <div class="demo-mosaic stagger">
        <md-elevated-card class="demo-card demo-profile">
          <div class="demo-profile-head">
            <div class="avatar-wrap">
              <div class="avatar">A</div>
              <div class="avatar-online" />
            </div>
            <div>
              <div class="demo-name md-typescale-title-medium">Alexander K.</div>
              <div class="demo-bio md-typescale-body-small">Геймер · Меломан · Живу в онлайне</div>
            </div>
          </div>
          <md-chip-set class="demo-tags">
            <md-suggestion-chip label="CS2" />
            <md-suggestion-chip label="Музыка" />
            <md-suggestion-chip label="Аниме" />
            <md-suggestion-chip label="Кофе" />
          </md-chip-set>
        </md-elevated-card>

        <md-outlined-card class="demo-card demo-live">
          <div class="widget-label"><span class="widget-icon" style="background:#1b2838;"><i class="ri-steam-fill" /></span>Сейчас в игре <span class="live-pill">live</span></div>
          <div class="demo-live-main">Counter-Strike 2</div>
          <div class="demo-live-sub">2,847 ч · онлайн сейчас</div>
          <md-divider />
          <div class="widget-label"><span class="widget-icon" style="background:#b90000;"><i class="ri-lastfm-fill" /></span>Сейчас слушает <span class="live-pill">live</span></div>
          <div class="demo-live-main">Fluorescent Adolescent</div>
          <div class="demo-live-sub">Arctic Monkeys</div>
        </md-outlined-card>

        <md-outlined-card class="demo-card demo-metrics">
          <div class="widget-label"><span class="widget-icon faceit-widget-icon"><FaceitLogo /></span>Faceit / CS2</div>
          <FaceitSkillLevel class="demo-faceit-level" :level="8" />
          <div class="demo-metric-grid">
            <div class="demo-metric-item"><span>1847</span><small>ELO</small></div>
            <div class="demo-metric-item"><span>1.24</span><small>K/D</small></div>
            <div class="demo-metric-item"><span>54%</span><small>WR</small></div>
          </div>
        </md-outlined-card>

        <md-outlined-card class="demo-card demo-links">
          <div class="widget-label"><i class="ri-links-fill" style="margin-right:6px;color:var(--accent);" />Контакты и ссылки</div>
          <div class="link-list">
            <div class="link-item"><div class="link-icon" style="background:#24292e;"><i class="ri-github-fill" /></div>GitHub / alexkirilin<span class="link-arrow"><i class="ri-arrow-right-up-line" /></span></div>
            <div class="link-item"><div class="link-icon" style="background:#229ed9;"><i class="ri-telegram-fill" /></div>Telegram канал<span class="link-arrow"><i class="ri-arrow-right-up-line" /></span></div>
          </div>
        </md-outlined-card>
      </div>
    </div>
  </section>
</template>
