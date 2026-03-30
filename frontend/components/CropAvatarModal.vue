<template>
  <Teleport to="body">
    <div v-if="visible" class="crop-overlay" @mousedown.self="cancel">
      <div class="crop-dialog">
        <div class="crop-title">Обрезать аватар</div>
        <div
          class="crop-canvas-wrap"
          :class="{ dragging: isDragging }"
          @mousedown="onDragStart"
          @touchstart.prevent="onTouchStart"
          @touchmove.prevent="onTouchMove"
          @touchend="onTouchEnd"
          @wheel.prevent="onWheel"
        >
          <canvas ref="cropCanvasRef" class="crop-canvas" />
        </div>
        <div class="crop-hint">Прокрути для масштаба · Тяни для позиции</div>
        <div class="crop-actions">
          <button class="crop-btn-cancel" @click="cancel">Отмена</button>
          <button class="crop-btn-save" :disabled="saving" @click="confirm">
            <span v-if="saving" class="crop-spinner" />
            <span v-else>Сохранить</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{ file: File | null; saving?: boolean }>()
const emit = defineEmits<{ save: [blob: Blob]; cancel: [] }>()

const CANVAS_SIZE = 320
const CROP_R = 140

const visible = ref(false)
const cropCanvasRef = ref<HTMLCanvasElement | null>(null)
const isDragging = ref(false)

let cropImgEl: HTMLImageElement | null = null
let cropX = 0, cropY = 0, cropScale = 1, minCropScale = 1
let dragStartX = 0, dragStartY = 0, dragImgX = 0, dragImgY = 0
let lastTouchDist = 0

watch(() => props.file, file => {
  if (file) openModal(file)
})

function openModal(file: File) {
  const reader = new FileReader()
  reader.onload = ev => {
    const img = new Image()
    img.onload = () => {
      cropImgEl = img
      const scale = Math.max((CROP_R * 2) / img.width, (CROP_R * 2) / img.height)
      cropScale = scale
      minCropScale = scale
      cropX = CANVAS_SIZE / 2 - (img.width * scale) / 2
      cropY = CANVAS_SIZE / 2 - (img.height * scale) / 2
      visible.value = true
      nextTick(() => draw())
    }
    img.src = ev.target?.result as string
  }
  reader.readAsDataURL(file)
}

function clampCrop() {
  if (!cropImgEl) return
  const cx = CANVAS_SIZE / 2, cy = CANVAS_SIZE / 2
  const imgW = cropImgEl.width * cropScale
  const imgH = cropImgEl.height * cropScale
  cropX = Math.min(cx - CROP_R, Math.max(cx + CROP_R - imgW, cropX))
  cropY = Math.min(cy - CROP_R, Math.max(cy + CROP_R - imgH, cropY))
}

function draw() {
  const canvas = cropCanvasRef.value
  if (!canvas || !cropImgEl) return
  const ctx = canvas.getContext('2d')!
  const w = CANVAS_SIZE, h = CANVAS_SIZE
  canvas.width = w; canvas.height = h
  ctx.clearRect(0, 0, w, h)
  ctx.drawImage(cropImgEl, cropX, cropY, cropImgEl.width * cropScale, cropImgEl.height * cropScale)
  ctx.beginPath()
  ctx.rect(0, 0, w, h)
  ctx.arc(w / 2, h / 2, CROP_R, 0, Math.PI * 2, true)
  ctx.fillStyle = 'rgba(5,5,18,0.78)'
  ctx.fill('evenodd')
  ctx.beginPath()
  ctx.arc(w / 2, h / 2, CROP_R, 0, Math.PI * 2)
  ctx.strokeStyle = 'rgba(61,142,255,0.75)'
  ctx.lineWidth = 2
  ctx.stroke()
}

function cancel() {
  visible.value = false
  cropImgEl = null
  emit('cancel')
}

function confirm() {
  if (!cropImgEl) return
  const size = 400
  const off = document.createElement('canvas')
  off.width = size; off.height = size
  const ctx = off.getContext('2d')!
  const cx = CANVAS_SIZE / 2, cy = CANVAS_SIZE / 2
  const srcX = (cx - CROP_R - cropX) / cropScale
  const srcY = (cy - CROP_R - cropY) / cropScale
  const srcW = (CROP_R * 2) / cropScale
  const srcH = (CROP_R * 2) / cropScale
  ctx.drawImage(cropImgEl, srcX, srcY, srcW, srcH, 0, 0, size, size)
  off.toBlob(blob => {
    if (!blob) return
    visible.value = false
    cropImgEl = null
    emit('save', blob)
  }, 'image/jpeg', 0.92)
}

// ── Drag ──
function onDragStart(e: MouseEvent) {
  isDragging.value = true
  dragStartX = e.clientX; dragStartY = e.clientY
  dragImgX = cropX; dragImgY = cropY
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd)
}
function onDragMove(e: MouseEvent) {
  cropX = dragImgX + (e.clientX - dragStartX)
  cropY = dragImgY + (e.clientY - dragStartY)
  clampCrop()
  draw()
}
function onDragEnd() {
  isDragging.value = false
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
}

// ── Wheel ──
function onWheel(e: WheelEvent) {
  const f = e.deltaY > 0 ? 0.92 : 1.08
  const ns = Math.max(minCropScale, Math.min(20, cropScale * f))
  const cx = CANVAS_SIZE / 2, cy = CANVAS_SIZE / 2
  cropX = cx - (cx - cropX) * (ns / cropScale)
  cropY = cy - (cy - cropY) * (ns / cropScale)
  cropScale = ns
  clampCrop()
  draw()
}

// ── Touch ──
function onTouchStart(e: TouchEvent) {
  if (e.touches.length === 1) {
    isDragging.value = true
    dragStartX = e.touches[0].clientX; dragStartY = e.touches[0].clientY
    dragImgX = cropX; dragImgY = cropY
  } else if (e.touches.length === 2) {
    isDragging.value = false
    lastTouchDist = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    )
  }
}
function onTouchMove(e: TouchEvent) {
  if (e.touches.length === 1 && isDragging.value) {
    cropX = dragImgX + (e.touches[0].clientX - dragStartX)
    cropY = dragImgY + (e.touches[0].clientY - dragStartY)
    clampCrop()
    draw()
  } else if (e.touches.length === 2) {
    const dist = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    )
    if (lastTouchDist > 0) {
      const r = dist / lastTouchDist
      const ns = Math.max(minCropScale, Math.min(20, cropScale * r))
      const cx = CANVAS_SIZE / 2, cy = CANVAS_SIZE / 2
      cropX = cx - (cx - cropX) * (ns / cropScale)
      cropY = cy - (cy - cropY) * (ns / cropScale)
      cropScale = ns
      clampCrop()
      draw()
    }
    lastTouchDist = dist
  }
}
function onTouchEnd() {
  isDragging.value = false
  lastTouchDist = 0
}
</script>

<style scoped>
.crop-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.72);
  display: flex; align-items: center; justify-content: center;
}
.crop-dialog {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.18);
  border-radius: 18px; padding: 24px;
  display: flex; flex-direction: column; align-items: center; gap: 14px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
}
.crop-title { font-size: 15px; font-weight: 700; color: #eeeef8; align-self: flex-start; font-family: 'Onest', sans-serif; }
.crop-canvas-wrap {
  position: relative; border-radius: 50%; overflow: hidden;
  width: 320px; height: 320px; flex-shrink: 0;
  cursor: grab; user-select: none;
}
.crop-canvas-wrap.dragging { cursor: grabbing; }
.crop-canvas { display: block; width: 320px; height: 320px; }
.crop-hint { font-size: 11px; color: #6a6a90; font-family: 'Onest', sans-serif; }
.crop-actions { display: flex; gap: 10px; align-self: flex-end; }
.crop-btn-cancel {
  background: none; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px; padding: 8px 18px; color: #8888aa;
  font-size: 13px; font-weight: 600; font-family: 'Onest', sans-serif; cursor: pointer;
}
.crop-btn-save {
  background: rgba(61,142,255,0.15); border: 1px solid rgba(61,142,255,0.35);
  border-radius: 8px; padding: 8px 22px; color: #90beff;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif;
  cursor: pointer; display: flex; align-items: center; gap: 8px;
}
.crop-btn-save:disabled { opacity: 0.55; cursor: not-allowed; }
.crop-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid rgba(144,190,255,0.3); border-top-color: #90beff;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
