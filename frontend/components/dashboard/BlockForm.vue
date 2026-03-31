<template>
  <div class="bf-wrap">

    <!-- ── Links ──────────────────────────────────────────────────────────────── -->
    <template v-if="type === 'links'">
      <div v-for="(group, gi) in (config.groups as Group[])" :key="gi" class="bf-group">
        <div class="bf-group-header">
          <input v-model="group.title" class="bf-input" placeholder="Название группы (необязательно)">
          <button class="bf-icon-btn bf-del" @click="(config.groups as Group[]).splice(gi, 1)">
            <i class="ri-delete-bin-line" />
          </button>
        </div>
        <div class="bf-links">
          <div v-for="(link, li) in group.links" :key="li" class="bf-link-block">
            <div class="bf-link-row">
              <input v-model="link.label" class="bf-input" placeholder="Telegram">
              <input v-model="link.url" class="bf-input bf-url" placeholder="https://...">
              <button class="bf-icon-btn bf-del" @click="group.links.splice(li, 1)">
                <i class="ri-close-line" />
              </button>
            </div>
            <div class="bf-icon-chips">
              <button
                v-for="ic in POPULAR_ICONS"
                :key="ic"
                class="bf-ic"
                :class="{ active: link.icon === ic }"
                type="button"
                :title="ic"
                @click="link.icon = link.icon === ic ? '' : ic"
              >
                <i :class="`ri-${ic}-fill`" />
              </button>
            </div>
            <div class="bf-link-icon-row">
              <span v-if="link.icon" class="bf-icon-preview"><i :class="`ri-${link.icon}-fill`" /></span>
              <input v-model="link.icon" class="bf-input bf-icon-input" placeholder="Или введи иконку: github, vk...">
            </div>
          </div>
        </div>
        <button class="bf-add-link" @click="group.links.push({ label: '', url: '', icon: '' })">
          + Добавить ссылку
        </button>
      </div>
      <button class="bf-add-group" @click="(config.groups as Group[]).push({ title: '', links: [] })">
        + Добавить группу
      </button>
    </template>

    <!-- ── Text ───────────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'text'">
      <div class="bf-field">
        <label>Содержимое</label>
        <textarea v-model="config.content" class="bf-textarea" rows="8" placeholder="Напиши что-нибудь..." />
      </div>
    </template>

    <!-- ── Steam ──────────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'widget_steam'">
      <div class="bf-field">
        <label>Steam ID</label>
        <input v-model="config.steam_id" class="bf-input" placeholder="76561198...">
        <div class="bf-hint">Найди свой Steam ID на <strong>steamid.io</strong> или в настройках профиля Steam</div>
      </div>
      <label class="bf-check">
        <input v-model="config.show_recent_games" type="checkbox">
        Показывать последние игры
      </label>
    </template>

    <!-- ── Last.fm ────────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'widget_lastfm'">
      <div class="bf-field">
        <label>Никнейм Last.fm</label>
        <input v-model="config.username" class="bf-input" placeholder="username">
        <div class="bf-hint">Твой никнейм на last.fm/user/<strong>username</strong></div>
      </div>
      <label class="bf-check">
        <input v-model="config.show_now_playing" type="checkbox">
        Показывать «сейчас играет»
      </label>
    </template>

    <!-- ── GitHub ─────────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'widget_github'">
      <div class="bf-field">
        <label>GitHub username</label>
        <input v-model="config.username" class="bf-input" placeholder="octocat">
        <div class="bf-hint">Твой никнейм на github.com/<strong>username</strong></div>
      </div>
      <label class="bf-check">
        <input v-model="config.show_contributions" type="checkbox">
        Показывать граф contributions
      </label>
      <label class="bf-check">
        <input v-model="config.show_pinned_repos" type="checkbox">
        Показывать закреплённые репозитории
      </label>
    </template>

    <!-- ── FACEIT ─────────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'widget_faceit'">
      <div class="bf-field">
        <label>FACEIT никнейм</label>
        <input v-model="config.nickname" class="bf-input" placeholder="nickname">
        <div class="bf-hint">Твой никнейм на faceit.com/en/players/<strong>nickname</strong></div>
      </div>
      <div class="bf-field">
        <label>Игра</label>
        <div class="bf-game-select">
          <button
            class="bf-game-btn"
            :class="{ active: !config.game || config.game === 'cs2' }"
            type="button"
            @click="config.game = 'cs2'"
          >CS2</button>
          <button
            class="bf-game-btn"
            :class="{ active: config.game === 'csgo' }"
            type="button"
            @click="config.game = 'csgo'"
          >CS:GO</button>
        </div>
      </div>
    </template>

    <!-- ── PC Config ──────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'pc_config'">
      <div class="bf-field">
        <label>Название конфига</label>
        <input v-model="config.title" class="bf-input" placeholder="My Rig">
      </div>
      <div class="bf-field">
        <label>Компоненты</label>
        <div class="bf-group">
          <div v-for="(comp, ci) in (config.components as Component[])" :key="ci" class="bf-comp-row">
            <input v-model="comp.category" class="bf-input bf-cat" placeholder="CPU">
            <input v-model="comp.name" class="bf-input" placeholder="AMD Ryzen 5 7500F">
            <button class="bf-icon-btn bf-del" @click="(config.components as Component[]).splice(ci, 1)">
              <i class="ri-close-line" />
            </button>
          </div>
          <button class="bf-add-link" @click="(config.components as Component[]).push({ category: '', name: '' })">
            + Добавить компонент
          </button>
        </div>
        <div class="bf-hint">CPU, GPU, RAM, SSD, Case, Cooler, PSU, MB...</div>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
interface Link { label: string; url: string; icon: string }
interface Group { title: string; links: Link[] }
interface Component { category: string; name: string }

defineProps<{ type: string; config: Record<string, unknown> }>()

const POPULAR_ICONS = [
  'telegram', 'vk', 'github', 'twitter-x', 'instagram',
  'youtube', 'discord', 'twitch', 'tiktok', 'linkedin',
  'spotify', 'steam', 'reddit', 'behance', 'dribbble',
]
</script>

<style scoped>
.bf-wrap { display: flex; flex-direction: column; gap: 14px; }
.bf-field { display: flex; flex-direction: column; gap: 5px; }
.bf-field label { font-size: 11px; font-weight: 700; color: #71717a; text-transform: uppercase; letter-spacing: 0.8px; }
.bf-hint { font-size: 11px; color: #52525b; line-height: 1.4; }
.bf-hint strong { color: #71717a; }

.bf-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 7px; padding: 7px 10px; color: #ececef;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; width: 100%;
  transition: border-color 0.2s;
}
.bf-input:focus { border-color: rgba(255,255,255,0.20); }
.bf-textarea {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 7px; padding: 9px 10px; color: #ececef;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; resize: vertical; width: 100%;
  transition: border-color 0.2s;
}
.bf-textarea:focus { border-color: rgba(255,255,255,0.20); }

.bf-check { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #a1a1aa; cursor: pointer; }
.bf-check input[type="checkbox"] { accent-color: #fafafa; width: 14px; height: 14px; cursor: pointer; }

.bf-group {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 9px; padding: 10px; display: flex; flex-direction: column; gap: 8px;
}
.bf-group-header { display: flex; gap: 7px; }
.bf-links { display: flex; flex-direction: column; gap: 8px; }
.bf-link-row { display: flex; gap: 5px; align-items: center; }
.bf-url { flex: 1; }
.bf-icon-btn { background: none; border: none; cursor: pointer; font-size: 15px; display: flex; align-items: center; padding: 3px; flex-shrink: 0; }
.bf-del { color: #3f3f46; transition: color 0.2s; }
.bf-del:hover { color: #ff7070; }

.bf-link-block { display: flex; flex-direction: column; gap: 6px; }
.bf-icon-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.bf-ic {
  width: 28px; height: 28px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03); color: #71717a;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; cursor: pointer; transition: all 0.15s; flex-shrink: 0;
}
.bf-ic:hover { background: rgba(255,255,255,0.08); color: #d4d4d8; border-color: rgba(255,255,255,0.14); }
.bf-ic.active { background: rgba(255,255,255,0.12); color: #fafafa; border-color: rgba(255,255,255,0.25); }

.bf-link-icon-row { display: flex; align-items: center; gap: 6px; }
.bf-icon-preview { font-size: 16px; color: #a1a1aa; flex-shrink: 0; width: 20px; text-align: center; }
.bf-icon-input { font-size: 12px; color: #a1a1aa; }

.bf-add-link {
  background: none; border: none; color: #d4d4d8;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
  text-align: left; padding: 2px 0;
}
.bf-add-group {
  background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.12);
  border-radius: 7px; padding: 8px; color: #a1a1aa;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer; width: 100%;
  transition: background 0.2s;
}
.bf-add-group:hover { background: rgba(255,255,255,0.06); }

/* Faceit game select */
.bf-game-select { display: flex; gap: 6px; }
.bf-game-btn {
  flex: 1; padding: 8px; border-radius: 7px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
  color: #71717a; font-size: 13px; font-weight: 600; font-family: 'Onest', sans-serif;
  cursor: pointer; transition: all 0.15s;
}
.bf-game-btn:hover { border-color: rgba(255,255,255,0.14); color: #a1a1aa; }
.bf-game-btn.active { background: rgba(255,255,255,0.10); border-color: rgba(255,255,255,0.20); color: #fafafa; }

/* PC Config */
.bf-comp-row { display: flex; gap: 5px; align-items: center; }
.bf-cat { max-width: 72px; }
</style>
