<template>
  <Teleport to="body">
    <div class="be-overlay" @click.self="$emit('close')">
      <div class="be-modal">
        <div class="be-header">
          <span class="be-title">{{ label }} — редактор</span>
          <button class="be-close" @click="$emit('close')"><i class="ri-close-line" /></button>
        </div>
        <div class="be-body">
          <DashboardBlockForm :type="block.block_type" :config="localConfig" />
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
const emit = defineEmits<{ save: [{ config: Record<string, unknown> }]; close: [] }>()

const labels: Record<string, string> = {
  links: 'Ссылки', text: 'Текст', widget_steam: 'Steam',
  widget_lastfm: 'Last.fm', widget_github: 'GitHub', pc_config: 'ПК конфиг',
}
const label = computed(() => labels[props.block.block_type] ?? props.block.block_type)
const localConfig = reactive(JSON.parse(JSON.stringify(props.block.config)))

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
  padding: 16px 20px; border-bottom: 1px solid rgba(61,142,255,0.08); flex-shrink: 0;
}
.be-title { font-size: 14px; font-weight: 700; }
.be-close {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(61,142,255,0.12);
  border-radius: 7px; width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  color: #6a6a90; cursor: pointer; font-size: 17px;
}
.be-body { padding: 20px; overflow-y: auto; flex: 1; }
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
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF); border: none;
  border-radius: 8px; padding: 8px 22px; color: #fff;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif; cursor: pointer;
}
</style>
