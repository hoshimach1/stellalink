<template>
  <ClientOnly>
    <Teleport to="body">
      <TransitionGroup name="app-toast" tag="div" class="app-toast-host" aria-live="polite">
        <article
          v-for="toast in toasts"
          :key="toast.id"
          class="app-toast"
          :class="`tone-${toast.tone}`"
          :role="toast.tone === 'error' ? 'alert' : 'status'"
        >
          <span class="app-toast-icon">
            <i :class="toastIcon(toast.tone)" />
          </span>
          <span class="app-toast-copy">
            <strong>{{ toast.title }}</strong>
            <span>{{ toast.message }}</span>
          </span>
          <button class="app-toast-close" type="button" aria-label="Закрыть уведомление" @click="removeToast(toast.id)">
            <i class="ri-close-line" />
          </button>
          <span
            v-if="toast.timeout > 0"
            class="app-toast-progress"
            :style="{ animationDuration: `${toast.timeout}ms` }"
          />
        </article>
      </TransitionGroup>
    </Teleport>
  </ClientOnly>
</template>

<script setup lang="ts">
import type { AppToastTone } from '~/composables/useAppToast'

const { removeToast, toasts } = useAppToast()

function toastIcon(tone: AppToastTone) {
  if (tone === 'success') return 'ri-checkbox-circle-line'
  if (tone === 'error') return 'ri-error-warning-line'
  if (tone === 'warning') return 'ri-alert-line'
  return 'ri-information-line'
}
</script>

<style scoped>
.app-toast-host {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 4000;
  display: grid;
  gap: 10px;
  width: min(420px, calc(100vw - 24px));
  pointer-events: none;
}

.app-toast {
  position: relative;
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  overflow: hidden;
  padding: 13px 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: #151A24;
  color: #F8FAFC;
  box-shadow: 0 18px 46px rgba(0, 0, 0, 0.26);
  pointer-events: auto;
}

.app-toast-icon {
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(148, 163, 184, 0.16);
  color: #CBD5E1;
  font-size: 18px;
}

.app-toast.tone-success .app-toast-icon {
  background: rgba(34, 197, 94, 0.18);
  color: #7DDC9B;
}

.app-toast.tone-error .app-toast-icon {
  background: rgba(248, 113, 113, 0.18);
  color: #FDA4A4;
}

.app-toast.tone-warning .app-toast-icon {
  background: rgba(245, 158, 11, 0.2);
  color: #FCD181;
}

.app-toast-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.app-toast-copy strong,
.app-toast-copy span {
  overflow-wrap: anywhere;
}

.app-toast-copy strong {
  font-size: 13px;
  line-height: 1.25;
  font-weight: 900;
}

.app-toast-copy span {
  color: #D9E2EF;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 700;
}

.app-toast-close {
  width: 32px;
  height: 32px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  color: #CBD5E1;
  cursor: pointer;
  font-size: 17px;
}

.app-toast-close:focus-visible {
  outline: 2px solid rgba(248, 250, 252, 0.5);
  outline-offset: 2px;
}

.app-toast-progress {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #7DDC9B, #93C5FD);
  transform-origin: left center;
  animation: app-toast-progress linear forwards;
}

.app-toast.tone-error .app-toast-progress {
  background: linear-gradient(90deg, #FDA4A4, #FCD181);
}

.app-toast.tone-warning .app-toast-progress {
  background: linear-gradient(90deg, #FCD181, #93C5FD);
}

.app-toast-enter-active,
.app-toast-leave-active,
.app-toast-move {
  transition:
    opacity 220ms cubic-bezier(0.2, 0, 0, 1),
    transform 220ms cubic-bezier(0.2, 0, 0, 1);
}

.app-toast-enter-from,
.app-toast-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

@keyframes app-toast-progress {
  to { transform: scaleX(0); }
}

@media (max-width: 560px) {
  .app-toast-host {
    right: 8px;
    bottom: 10px;
    width: calc(100vw - 16px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-toast-enter-active,
  .app-toast-leave-active,
  .app-toast-move,
  .app-toast-progress {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
  }
}
</style>
