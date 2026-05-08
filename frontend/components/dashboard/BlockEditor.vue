<template>
  <Teleport to="body">
    <div class="be-overlay" @click.self="$emit('close')">
      <div class="be-modal" role="dialog" aria-modal="true" :aria-label="`${label} - редактор`">
        <div class="be-header">
          <span class="be-title">{{ label }} - редактор</span>
          <button class="be-close" type="button" aria-label="Закрыть" @click="$emit('close')">
            <i class="ri-close-line" />
          </button>
        </div>
        <div class="be-body">
          <DashboardBlockForm :type="block.block_type" :config="localConfig" />
        </div>
        <div class="be-footer">
          <button class="be-cancel" type="button" @click="$emit('close')">Отмена</button>
          <button class="be-save" type="button" @click="save">Сохранить</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Block } from '~/stores/profile'
import { blockLabel } from '~/utils/dashboard-studio'

const props = defineProps<{ block: Block }>()
const emit = defineEmits<{ save: [{ config: Record<string, unknown> }]; close: [] }>()

const label = computed(() => blockLabel(props.block.block_type))
const localConfig = reactive(JSON.parse(JSON.stringify(props.block.config)))

function save() {
  emit('save', { config: JSON.parse(JSON.stringify(localConfig)) })
}
</script>

<style scoped>
.be-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(8, 12, 20, 0.72);
  backdrop-filter: blur(10px);
}

.be-modal {
  width: min(100%, 560px);
  max-height: min(84vh, 760px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--dash-outline, rgba(203, 213, 225, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  box-shadow: 0 28px 90px rgba(0, 0, 0, 0.34);
}

.be-header,
.be-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-color: var(--dash-outline, rgba(203, 213, 225, 0.18));
}

.be-header {
  justify-content: space-between;
  border-bottom: 1px solid var(--dash-outline, rgba(203, 213, 225, 0.18));
}

.be-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--dash-outline, rgba(203, 213, 225, 0.18));
}

.be-title {
  font-size: 15px;
  font-weight: 900;
}

.be-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
}

.be-close,
.be-cancel,
.be-save {
  border: 1px solid var(--dash-outline, rgba(203, 213, 225, 0.18));
  border-radius: 999px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  font-weight: 900;
  cursor: pointer;
}

.be-close {
  width: 38px;
  height: 38px;
  display: inline-grid;
  place-items: center;
  padding: 0;
  font-size: 18px;
}

.be-cancel,
.be-save {
  min-height: 40px;
  padding: 0 16px;
}

.be-save {
  border-color: transparent;
  background: var(--dash-accent, #345EA8);
  color: #fff;
}
</style>
