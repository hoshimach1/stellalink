<template>
  <div class="demo-wrap">
    <div class="demo-floater">
      <div class="demo-float-label">Пример профиля</div>
      <md-elevated-card class="demo-card">
        <div class="demo-header">
          <div class="avatar-wrap">
            <div class="avatar">A</div>
            <div class="avatar-online" />
          </div>
          <div style="flex:1;min-width:0;">
            <div class="demo-name md-typescale-title-medium">Alexander K.</div>
            <div class="demo-bio md-typescale-body-small">Геймер · Меломан · Живу в онлайне</div>
            <md-chip-set class="demo-tags">
              <md-suggestion-chip label="CS2" />
              <md-suggestion-chip label="Музыка" />
              <md-suggestion-chip label="Аниме" />
              <md-suggestion-chip label="Кофе" />
            </md-chip-set>
          </div>
        </div>
        <div class="demo-body">
          <md-outlined-card class="widget">
            <div class="widget-label">
              <span class="widget-icon" style="background:#1b2838;"><i class="ri-steam-fill" /></span>
              Steam<span class="live-pill">live</span>
            </div>
            <div class="steam-game">
              <div class="game-img"><i class="ri-focus-3-fill" /></div>
              <div>
                <div class="game-name">Counter-Strike 2</div>
                <div class="game-hours">2,847 ч · онлайн сейчас</div>
              </div>
            </div>
          </md-outlined-card>
          <md-outlined-card class="widget">
            <div class="widget-label">
              <span class="widget-icon" style="background:#ff5500;"><i class="ri-trophy-fill" /></span>Faceit
            </div>
            <div class="faceit-row">
              <div class="elo-badge"><div class="elo-num">8</div><div class="elo-label">lvl</div></div>
              <div class="faceit-stats">
                <div class="stat-col"><div class="stat-num">1847</div><div class="stat-key">ELO</div></div>
                <div class="stat-col"><div class="stat-num" style="color:var(--accent2);">1.24</div><div class="stat-key">K/D</div></div>
                <div class="stat-col"><div class="stat-num">54%</div><div class="stat-key">WR</div></div>
              </div>
            </div>
          </md-outlined-card>
          <md-outlined-card class="widget">
            <div class="widget-label">
              <span class="widget-icon" style="background:#b90000;"><i class="ri-lastfm-fill" /></span>
              Сейчас слушает<span class="live-pill">live</span>
            </div>
            <div class="music-row">
              <div class="album-art" />
              <div class="track-info">
                <div class="track-name">Fluorescent Adolescent</div>
                <div class="track-artist">Arctic Monkeys</div>
              </div>
              <div class="music-bars">
                <div class="bar" /><div class="bar" /><div class="bar" /><div class="bar" />
              </div>
            </div>
          </md-outlined-card>
          <md-outlined-card class="widget">
            <div class="widget-label"><i class="ri-links-fill" style="margin-right:6px;color:var(--accent);" />Ссылки</div>
            <div class="link-list">
              <div class="link-item">
                <div class="link-icon" style="background:#24292e;"><i class="ri-github-fill" /></div>
                GitHub / alexkirilin<span class="link-arrow"><i class="ri-arrow-right-up-line" /></span>
              </div>
              <div class="link-item">
                <div class="link-icon" style="background:#229ed9;"><i class="ri-telegram-fill" /></div>
                Telegram канал<span class="link-arrow"><i class="ri-arrow-right-up-line" /></span>
              </div>
            </div>
          </md-outlined-card>
          <md-outlined-card class="widget">
            <div class="widget-label"><i class="ri-computer-fill" style="margin-right:6px;color:var(--accent);" />PC конфиг</div>
            <div class="pc-grid">
              <div class="pc-item"><div class="pc-key">CPU</div><div class="pc-val">R5 7500F</div></div>
              <div class="pc-item"><div class="pc-key">GPU</div><div class="pc-val">RTX 2070S</div></div>
              <div class="pc-item"><div class="pc-key">RAM</div><div class="pc-val">32GB DDR5</div></div>
              <div class="pc-item"><div class="pc-key">SSD</div><div class="pc-val">2TB NVMe</div></div>
            </div>
          </md-outlined-card>
        </div>
        <div class="demo-fade-bottom" />
      </md-elevated-card>
    </div>
  </div>
</template>
