<template>
  <Teleport to="body">
    <div class="be-overlay" @click.self="$emit('close')">
      <div class="be-modal">
        <div class="be-header">
          <span class="be-title">{{ blockLabel }} — редактор</span>
          <button class="be-close" @click="$emit('close')"><i class="ri-close-line" /></button>
        </div>

        <div class="be-body">
          <!-- Links editor -->
          <template v-if="block.block_type === 'links'">
            <div v-for="(group, gi) in localConfig.groups" :key="gi" class="be-group">
              <div class="be-group-header">
                <input v-model="group.title" class="be-input be-group-title" placeholder="Название группы">
                <button class="be-icon-btn be-del" @click="removeGroup(gi)"><i class="ri-delete-bin-line" /></button>
              </div>
              <div class="be-links">
                <div v-for="(link, li) in group.links" :key="li" class="be-link-row">
                  <input v-model="link.label" class="be-input" placeholder="Telegram">
                  <input v-model="link.url" class="be-input be-url" placeholder="https://...">
                  <button class="be-icon-btn be-del" @click="removeLink(gi, li)"><i class="ri-close-line" /></button>
                </div>
              </div>
              <button class="be-add-link" @click="addLink(gi)">+ Добавить ссылку</button>
            </div>
            <button class="be-add-group" @click="addGroup">+ Добавить группу</button>
          </template>

          <!-- Text editor -->
          <template v-else-if="block.block_type === 'text'">
            <div class="be-field">
              <label>Содержимое</label>
              <textarea v-model="localConfig.content" rows="8" class="be-textarea" placeholder="Напиши что-нибудь..." />
            </div>
          </template>

          <!-- Steam -->
          <template v-else-if="block.block_type === 'widget_steam'">
            <div class="be-field">
              <label>Steam ID</label>
              <input v-model="localConfig.steam_id" class="be-input" placeholder="76561198...">
            </div>
            <div class="be-field">
              <label class="be-check-label">
                <input v-model="localConfig.show_recent_games" type="checkbox">
                Показывать последние игры
              </label>
            </div>
          </template>

          <!-- Last.fm -->
          <template v-else-if="block.block_type === 'widget_lastfm'">
            <div class="be-field">
              <label>Имя пользователя Last.fm</label>
              <input v-model="localConfig.username" class="be-input" placeholder="username">
            </div>
            <div class="be-field">
              <label class="be-check-label">
                <input v-model="localConfig.show_now_playing" type="checkbox">
                Показывать что сейчас играет
              </label>
            </div>
          </template>

          <!-- GitHub -->
          <template v-else-if="block.block_type === 'widget_github'">
            <div class="be-field">
              <label>GitHub username</label>
              <input v-model="localConfig.username" class="be-input" placeholder="octocat">
            </div>
            <div class="be-field">
              <label class="be-check-label">
                <input v-model="localConfig.show_contributions" type="checkbox">
                Показывать contributions
              </label>
            </div>
            <div class="be-field">
              <label class="be-check-label">
                <input v-model="localConfig.show_pinned_repos" type="checkbox">
                Показывать закреплённые репо
              </label>
            </div>
          </template>

          <!-- PC Config -->
          <template v-else-if="block.block_type === 'pc_config'">
            <div class="be-field">
              <label>Название</label>
              <input v-model="localConfig.title" class="be-input" placeholder="Main Rig">
            </div>
            <div class="be-group">
              <div v-for="(comp, ci) in localConfig.components" :key="ci" class="be-link-row">
                <input v-model="comp.category" class="be-input" style="max-width:110px" placeholder="CPU">
                <input v-model="comp.name" class="be-input" placeholder="AMD Ryzen 5 7500F">
                <button class="be-icon-btn be-del" @click="localConfig.components.splice(ci, 1)"><i class="ri-close-line" /></button>
              </div>
              <button class="be-add-link" @click="localConfig.components.push({ category: '', name: '' })">+ Добавить компонент</button>
            </div>
          </template>
        </div>

        <div class="be-footer">
          <button class="be-cancel" @click="$emit('close')">Отмена</button>
          <button class="be-save" @click="save">Сохранить</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Block } from '~/stores/profile'

const props = defineProps<{ block: Block }>()
const emit = defineEmits<{
  save: [data: { config: Record<string, unknown> }]
  close: []
}>()

const labels: Record<string, string> = {
  links: 'Ссылки', text: 'Текст',
  widget_steam: 'Steam', widget_lastfm: 'Last.fm',
  widget_github: 'GitHub', pc_config: 'ПК конфиг',
}
const blockLabel = computed(() => labels[props.block.block_type] ?? props.block.block_type)

const localConfig = reactive(JSON.parse(JSON.stringify(props.block.config)))

// Links helpers
function addGroup() {
  if (!localConfig.groups) localConfig.groups = []
  localConfig.groups.push({ title: '', links: [] })
}
function removeGroup(gi: number) { localConfig.groups.splice(gi, 1) }
function addLink(gi: number) { localConfig.groups[gi].links.push({ label: '', url: '' }) }
function removeLink(gi: number, li: number) { localConfig.groups[gi].links.splice(li, 1) }

function save() {
  emit('save', { config: JSON.parse(JSON.stringify(localConfig)) })
}
</script>

<style scoped>
.be-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.72); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.be-modal {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.18);
  border-radius: 18px; width: 100%; max-width: 520px;
  max-height: 80vh; display: flex; flex-direction: column;
  box-shadow: 0 40px 100px rgba(0,0,0,0.7);
}
.be-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid rgba(61,142,255,0.08);
  flex-shrink: 0;
}
.be-title { font-size: 14px; font-weight: 700; }
.be-close {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.12);
  border-radius: 7px; width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  color: #6a6a90; cursor: pointer; font-size: 17px; transition: all 0.2s;
}
.be-close:hover { color: #eeeef8; }
.be-body { padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 14px; }
.be-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 20px; border-top: 1px solid rgba(61,142,255,0.08); flex-shrink: 0;
}
.be-cancel {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 8px 18px; color: #6a6a90;
  font-size: 13px; font-family: 'Onest', sans-serif; cursor: pointer;
}
.be-save {
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  border: none; border-radius: 8px; padding: 8px 22px; color: #fff;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}

.be-field { display: flex; flex-direction: column; gap: 6px; }
.be-field label { font-size: 12px; font-weight: 600; color: #6a6a90; }
.be-input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 8px 12px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none;
  transition: border-color 0.2s; width: 100%;
}
.be-input:focus { border-color: rgba(61,142,255,0.40); }
.be-textarea {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 10px 12px; color: #eeeef8;
  font-size: 13px; font-family: 'Onest', sans-serif; outline: none; resize: vertical; width: 100%;
}
.be-check-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #aaaacc; cursor: pointer; }

.be-group { background: rgba(255,255,255,0.02); border: 1px solid rgba(61,142,255,0.08); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.be-group-header { display: flex; align-items: center; gap: 8px; }
.be-group-title { font-weight: 600; }
.be-links { display: flex; flex-direction: column; gap: 6px; }
.be-link-row { display: flex; align-items: center; gap: 6px; }
.be-url { flex: 1; }
.be-icon-btn { background: none; border: none; cursor: pointer; font-size: 16px; display: flex; align-items: center; padding: 4px; }
.be-del { color: #3a3a58; transition: color 0.2s; }
.be-del:hover { color: #ff7070; }
.be-add-link { background: none; border: none; color: #3D8EFF; font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer; padding: 2px 0; text-align: left; }
.be-add-group { background: rgba(61,142,255,0.08); border: 1px dashed rgba(61,142,255,0.22); border-radius: 8px; padding: 8px; color: #90beff; font-size: 13px; font-family: 'Onest', sans-serif; cursor: pointer; width: 100%; }
</style>
