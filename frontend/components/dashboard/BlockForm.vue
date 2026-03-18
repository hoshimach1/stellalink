<template>
  <div class="bf-wrap">

    <!-- Links -->
    <template v-if="type === 'links'">
      <div v-for="(group, gi) in config.groups" :key="gi" class="bf-group">
        <div class="bf-group-header">
          <input v-model="group.title" class="bf-input" placeholder="Название группы">
          <button class="bf-icon-btn bf-del" @click="config.groups.splice(gi, 1)"><i class="ri-delete-bin-line" /></button>
        </div>
        <div class="bf-links">
          <div v-for="(link, li) in group.links" :key="li" class="bf-link-row">
            <input v-model="link.label" class="bf-input" placeholder="Telegram">
            <input v-model="link.url" class="bf-input bf-url" placeholder="https://...">
            <button class="bf-icon-btn bf-del" @click="group.links.splice(li, 1)"><i class="ri-close-line" /></button>
          </div>
        </div>
        <button class="bf-add-link" @click="group.links.push({ label: '', url: '' })">+ Добавить ссылку</button>
      </div>
      <button class="bf-add-group" @click="config.groups.push({ title: '', links: [] })">+ Группа</button>
    </template>

    <!-- Text -->
    <template v-else-if="type === 'text'">
      <div class="bf-field">
        <label>Содержимое</label>
        <textarea v-model="config.content" class="bf-textarea" rows="7" placeholder="Напиши что-нибудь..." />
      </div>
    </template>

    <!-- Steam -->
    <template v-else-if="type === 'widget_steam'">
      <div class="bf-field">
        <label>Steam ID</label>
        <input v-model="config.steam_id" class="bf-input" placeholder="76561198...">
      </div>
      <label class="bf-check"><input v-model="config.show_recent_games" type="checkbox"> Последние игры</label>
    </template>

    <!-- Last.fm -->
    <template v-else-if="type === 'widget_lastfm'">
      <div class="bf-field">
        <label>Username</label>
        <input v-model="config.username" class="bf-input" placeholder="username">
      </div>
      <label class="bf-check"><input v-model="config.show_now_playing" type="checkbox"> Now playing</label>
    </template>

    <!-- GitHub -->
    <template v-else-if="type === 'widget_github'">
      <div class="bf-field">
        <label>GitHub username</label>
        <input v-model="config.username" class="bf-input" placeholder="octocat">
      </div>
      <label class="bf-check"><input v-model="config.show_contributions" type="checkbox"> Contributions</label>
      <label class="bf-check"><input v-model="config.show_pinned_repos" type="checkbox"> Закреплённые репо</label>
    </template>

    <!-- PC Config -->
    <template v-else-if="type === 'pc_config'">
      <div class="bf-field">
        <label>Название</label>
        <input v-model="config.title" class="bf-input" placeholder="Main Rig">
      </div>
      <div class="bf-group">
        <div v-for="(comp, ci) in config.components" :key="ci" class="bf-link-row">
          <input v-model="comp.category" class="bf-input" style="max-width:100px" placeholder="CPU">
          <input v-model="comp.name" class="bf-input" placeholder="AMD Ryzen 5 7500F">
          <button class="bf-icon-btn bf-del" @click="config.components.splice(ci, 1)"><i class="ri-close-line" /></button>
        </div>
        <button class="bf-add-link" @click="config.components.push({ category: '', name: '' })">+ Компонент</button>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
defineProps<{ type: string; config: Record<string, unknown> }>()
</script>

<style scoped>
.bf-wrap { display: flex; flex-direction: column; gap: 12px; }
.bf-field { display: flex; flex-direction: column; gap: 5px; }
.bf-field label { font-size: 11px; font-weight: 600; color: #6a6a90; }
.bf-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 7px; padding: 7px 10px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; width: 100%;
  transition: border-color 0.2s;
}
.bf-input:focus { border-color: rgba(61,142,255,0.40); }
.bf-textarea {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 7px; padding: 9px 10px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; resize: vertical; width: 100%;
}
.bf-check { display: flex; align-items: center; gap: 7px; font-size: 13px; color: #aaaacc; cursor: pointer; }
.bf-group {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(61,142,255,0.08);
  border-radius: 9px; padding: 10px; display: flex; flex-direction: column; gap: 7px;
}
.bf-group-header { display: flex; gap: 7px; }
.bf-links { display: flex; flex-direction: column; gap: 5px; }
.bf-link-row { display: flex; gap: 5px; align-items: center; }
.bf-url { flex: 1; }
.bf-icon-btn { background: none; border: none; cursor: pointer; font-size: 15px; display: flex; align-items: center; padding: 3px; }
.bf-del { color: #3a3a58; transition: color 0.2s; }
.bf-del:hover { color: #ff7070; }
.bf-add-link { background: none; border: none; color: #3D8EFF; font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer; text-align: left; padding: 2px 0; }
.bf-add-group {
  background: rgba(61,142,255,0.06); border: 1px dashed rgba(61,142,255,0.20);
  border-radius: 7px; padding: 7px; color: #90beff;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer; width: 100%;
}
</style>
