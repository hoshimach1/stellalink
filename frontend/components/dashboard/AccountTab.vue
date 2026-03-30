<template>
  <Teleport to="body">
    <div v-if="cropModal" class="crop-overlay" @mousedown.self="closeCrop">
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
        <div class="crop-hint">Прокрути для масштабирования · Тяни для перемещения</div>
        <div v-if="avatarError" class="acc-error crop-error">{{ avatarError }}</div>
        <div class="crop-actions">
          <button class="crop-btn-cancel" @click="closeCrop">Отмена</button>
          <button class="crop-btn-save" :disabled="avatarLoading" @click="confirmCrop">
            <span v-if="avatarLoading" class="acc-spinner" />
            <span v-else>Сохранить</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <div class="acc-wrap">

    <!-- Avatar -->
    <div class="acc-card">
      <div class="acc-card-title">Аватар</div>
      <div class="acc-avatar-row">
        <div class="acc-avatar-wrap">
          <img v-if="avatarSrc" :src="avatarSrc" class="acc-avatar-img" alt="avatar">
          <div v-else class="acc-avatar-placeholder">{{ auth.user?.email?.[0]?.toUpperCase() ?? '?' }}</div>
          <label class="acc-avatar-overlay" :class="{ loading: avatarLoading }" title="Загрузить фото">
            <span v-if="avatarLoading" class="acc-spinner" />
            <i v-else class="ri-camera-line" />
            <input ref="fileInputRef" type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="acc-file-input" @change="onAvatarFile">
          </label>
        </div>
        <div class="acc-avatar-meta">
          <div class="acc-avatar-hint">JPEG, PNG, WebP или GIF · до 5 МБ</div>
          <div v-if="avatarError && !cropModal" class="acc-error">{{ avatarError }}</div>
          <div v-if="avatarOk" class="acc-ok">Аватар обновлён ✓</div>
          <button v-if="auth.user?.avatar_url" class="acc-del-btn" :disabled="avatarLoading" @click="removeAvatar">
            <i class="ri-delete-bin-line" /> Удалить
          </button>
        </div>
      </div>
    </div>

    <!-- Email -->
    <div class="acc-card">
      <div class="acc-card-title">Email</div>
      <div class="acc-row">
        <span class="acc-email">{{ auth.user?.email }}</span>
      </div>
    </div>

    <!-- Change password -->
    <div class="acc-card">
      <div class="acc-card-title">Смена пароля</div>
      <form class="acc-form" @submit.prevent="changePassword">
        <div class="acc-field">
          <label>Текущий пароль</label>
          <input v-model="oldPass" type="password" autocomplete="current-password" placeholder="••••••••">
        </div>
        <div class="acc-field">
          <label>Новый пароль</label>
          <input v-model="newPass" type="password" autocomplete="new-password" placeholder="••••••••" minlength="8">
        </div>
        <div class="acc-field">
          <label>Повтори новый пароль</label>
          <input v-model="confirmPass" type="password" autocomplete="new-password" placeholder="••••••••">
        </div>
        <div v-if="passError" class="acc-error">{{ passError }}</div>
        <div v-if="passOk" class="acc-ok">Пароль изменён ✓</div>
        <button type="submit" class="acc-btn" :disabled="passLoading">
          <span v-if="passLoading" class="acc-spinner" />
          <span v-else>Изменить пароль</span>
        </button>
      </form>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const config = useRuntimeConfig()

// ─── Avatar cache-busting ───────────────────────────────────────────────────
const avatarTimestamp = ref(Date.now())
const avatarSrc = computed(() => {
  const url = auth.user?.avatar_url
  if (!url) return null
  return `${url}?t=${avatarTimestamp.value}`
})

// ─── Avatar upload state ────────────────────────────────────────────────────
const avatarLoading = ref(false)
const avatarError = ref('')
const avatarOk = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

function onAvatarFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  ;(e.target as HTMLInputElement).value = ''
  avatarError.value = ''
  avatarOk.value = false
  openCropModal(file)
}

async function removeAvatar() {
  avatarError.value = ''
  avatarOk.value = false
  avatarLoading.value = true
  try {
    await auth.deleteAvatar()
    avatarTimestamp.value = Date.now()
  } catch {
    avatarError.value = 'Ошибка удаления'
  } finally {
    avatarLoading.value = false
  }
}

// ─── Crop modal ─────────────────────────────────────────────────────────────
const CANVAS_SIZE = 320
const CROP_R = 140

const cropModal = ref(false)
const cropCanvasRef = ref<HTMLCanvasElement | null>(null)
const isDragging = ref(false)

let cropImgEl: HTMLImageElement | null = null
let cropX = 0
let cropY = 0
let cropScale = 1
let dragStartX = 0
let dragStartY = 0
let dragImgX = 0
let dragImgY = 0
let lastTouchDist = 0

function openCropModal(file: File) {
  const reader = new FileReader()
  reader.onload = (ev) => {
    const img = new Image()
    img.onload = () => {
      cropImgEl = img
      const scale = Math.max((CROP_R * 2) / img.width, (CROP_R * 2) / img.height)
      cropScale = scale
      cropX = CANVAS_SIZE / 2 - (img.width * scale) / 2
      cropY = CANVAS_SIZE / 2 - (img.height * scale) / 2
      cropModal.value = true
      nextTick(() => drawCrop())
    }
    img.src = ev.target?.result as string
  }
  reader.readAsDataURL(file)
}

function drawCrop() {
  const canvas = cropCanvasRef.value
  if (!canvas || !cropImgEl) return
  const ctx = canvas.getContext('2d')!
  const w = CANVAS_SIZE
  const h = CANVAS_SIZE
  canvas.width = w
  canvas.height = h

  ctx.clearRect(0, 0, w, h)
  ctx.drawImage(cropImgEl, cropX, cropY, cropImgEl.width * cropScale, cropImgEl.height * cropScale)

  // Dark overlay with circular hole
  ctx.beginPath()
  ctx.rect(0, 0, w, h)
  ctx.arc(w / 2, h / 2, CROP_R, 0, Math.PI * 2, true)
  ctx.fillStyle = 'rgba(5,5,18,0.78)'
  ctx.fill('evenodd')

  // Circle border
  ctx.beginPath()
  ctx.arc(w / 2, h / 2, CROP_R, 0, Math.PI * 2)
  ctx.strokeStyle = 'rgba(61,142,255,0.75)'
  ctx.lineWidth = 2
  ctx.stroke()
}

function closeCrop() {
  cropModal.value = false
  cropImgEl = null
}

async function confirmCrop() {
  if (!cropImgEl) return
  avatarLoading.value = true
  avatarError.value = ''

  const size = 400
  const off = document.createElement('canvas')
  off.width = size
  off.height = size
  const ctx = off.getContext('2d')!

  ctx.beginPath()
  ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2)
  ctx.clip()

  const cx = CANVAS_SIZE / 2
  const cy = CANVAS_SIZE / 2
  const srcX = (cx - CROP_R - cropX) / cropScale
  const srcY = (cy - CROP_R - cropY) / cropScale
  const srcW = (CROP_R * 2) / cropScale
  const srcH = (CROP_R * 2) / cropScale
  ctx.drawImage(cropImgEl, srcX, srcY, srcW, srcH, 0, 0, size, size)

  cropModal.value = false

  off.toBlob(async (blob) => {
    if (!blob) { avatarLoading.value = false; return }
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })
    try {
      await auth.uploadAvatar(file)
      avatarTimestamp.value = Date.now()
      avatarOk.value = true
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } }
      avatarError.value = e.data?.detail ?? 'Ошибка загрузки'
    } finally {
      avatarLoading.value = false
    }
  }, 'image/jpeg', 0.92)
}

// ─── Drag ────────────────────────────────────────────────────────────────────
function onDragStart(e: MouseEvent) {
  isDragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragImgX = cropX
  dragImgY = cropY
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e: MouseEvent) {
  cropX = dragImgX + (e.clientX - dragStartX)
  cropY = dragImgY + (e.clientY - dragStartY)
  drawCrop()
}

function onDragEnd() {
  isDragging.value = false
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
}

// ─── Wheel zoom ──────────────────────────────────────────────────────────────
function onWheel(e: WheelEvent) {
  const factor = e.deltaY > 0 ? 0.92 : 1.08
  const newScale = Math.max(0.05, Math.min(20, cropScale * factor))
  const cx = CANVAS_SIZE / 2
  const cy = CANVAS_SIZE / 2
  cropX = cx - (cx - cropX) * (newScale / cropScale)
  cropY = cy - (cy - cropY) * (newScale / cropScale)
  cropScale = newScale
  drawCrop()
}

// ─── Touch ──────────────────────────────────────────────────────────────────
function onTouchStart(e: TouchEvent) {
  if (e.touches.length === 1) {
    isDragging.value = true
    dragStartX = e.touches[0].clientX
    dragStartY = e.touches[0].clientY
    dragImgX = cropX
    dragImgY = cropY
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
    drawCrop()
  } else if (e.touches.length === 2) {
    const dist = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    )
    if (lastTouchDist > 0) {
      const ratio = dist / lastTouchDist
      const cx = CANVAS_SIZE / 2
      const cy = CANVAS_SIZE / 2
      const newScale = Math.max(0.05, Math.min(20, cropScale * ratio))
      cropX = cx - (cx - cropX) * (newScale / cropScale)
      cropY = cy - (cy - cropY) * (newScale / cropScale)
      cropScale = newScale
      drawCrop()
    }
    lastTouchDist = dist
  }
}

function onTouchEnd() {
  isDragging.value = false
  lastTouchDist = 0
}

// ─── Password change ─────────────────────────────────────────────────────────
const oldPass = ref('')
const newPass = ref('')
const confirmPass = ref('')
const passError = ref('')
const passOk = ref(false)
const passLoading = ref(false)

async function changePassword() {
  passError.value = ''
  passOk.value = false
  if (newPass.value !== confirmPass.value) {
    passError.value = 'Пароли не совпадают'
    return
  }
  if (newPass.value.length < 8) {
    passError.value = 'Минимум 8 символов'
    return
  }
  passLoading.value = true
  try {
    const res = await fetch(`${config.public.apiBase}/auth/change-password`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${auth.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ old_password: oldPass.value, new_password: newPass.value }),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw { data }
    }
    passOk.value = true
    oldPass.value = ''
    newPass.value = ''
    confirmPass.value = ''
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string } }
    passError.value = err.data?.detail ?? 'Ошибка смены пароля'
  } finally {
    passLoading.value = false
  }
}
</script>

<style scoped>
/* ── Crop overlay ─────────────────────────────────────────────────────────── */
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
.crop-title {
  font-size: 15px; font-weight: 700; color: #eeeef8; align-self: flex-start;
}
.crop-canvas-wrap {
  position: relative; border-radius: 50%; overflow: hidden;
  width: 320px; height: 320px; flex-shrink: 0;
  cursor: grab; user-select: none;
}
.crop-canvas-wrap.dragging { cursor: grabbing; }
.crop-canvas { display: block; width: 320px; height: 320px; }
.crop-hint { font-size: 11px; color: #6a6a90; }
.crop-error { align-self: stretch; }
.crop-actions {
  display: flex; gap: 10px; align-self: flex-end;
}
.crop-btn-cancel {
  background: none; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px; padding: 8px 18px; color: #8888aa;
  font-size: 13px; font-weight: 600; font-family: 'Onest', sans-serif;
  cursor: pointer; transition: background 0.2s;
}
.crop-btn-cancel:hover { background: rgba(255,255,255,0.06); }
.crop-btn-save {
  background: rgba(61,142,255,0.15); border: 1px solid rgba(61,142,255,0.35);
  border-radius: 8px; padding: 8px 22px; color: #90beff;
  font-size: 13px; font-weight: 700; font-family: 'Onest', sans-serif;
  cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background 0.2s;
}
.crop-btn-save:hover:not(:disabled) { background: rgba(61,142,255,0.25); }
.crop-btn-save:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── Account wrap ─────────────────────────────────────────────────────────── */
.acc-wrap { max-width: 480px; display: flex; flex-direction: column; gap: 16px; }

.acc-avatar-row { display: flex; align-items: center; gap: 20px; }
.acc-avatar-wrap { position: relative; flex-shrink: 0; width: 72px; height: 72px; }
.acc-avatar-img {
  width: 72px; height: 72px; border-radius: 50%; object-fit: cover;
  border: 2px solid rgba(61,142,255,0.20);
}
.acc-avatar-placeholder {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #2b7ef0, #3D8EFF);
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 800; color: #fff;
}
.acc-avatar-overlay {
  position: absolute; inset: 0; border-radius: 50%;
  background: rgba(0,0,0,0.50); display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s; cursor: pointer; font-size: 22px; color: #fff;
}
.acc-avatar-overlay.loading { opacity: 1; }
.acc-avatar-wrap:hover .acc-avatar-overlay { opacity: 1; }
.acc-file-input { display: none; }

.acc-avatar-meta { display: flex; flex-direction: column; gap: 8px; }
.acc-avatar-hint { font-size: 12px; color: #6a6a90; }
.acc-del-btn {
  align-self: flex-start; background: none; border: 1px solid rgba(255,80,80,0.22);
  border-radius: 7px; padding: 5px 12px; color: #ff7070;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
  display: flex; align-items: center; gap: 5px; transition: background 0.2s;
}
.acc-del-btn:hover { background: rgba(255,80,80,0.10); }
.acc-del-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.acc-card {
  background: #0d0d1c; border: 1px solid rgba(61,142,255,0.10);
  border-radius: 16px; padding: 20px 24px;
}
.acc-card-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #6a6a90; margin-bottom: 16px;
}
.acc-email { font-size: 15px; color: #eeeef8; }

.acc-form { display: flex; flex-direction: column; gap: 14px; }
.acc-field { display: flex; flex-direction: column; gap: 6px; }
.acc-field label { font-size: 12px; font-weight: 600; color: #6a6a90; }
.acc-field input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(61,142,255,0.14);
  border-radius: 8px; padding: 9px 12px; color: #eeeef8;
  font-size: 14px; font-family: 'Onest', sans-serif; outline: none;
  transition: border-color 0.2s;
}
.acc-field input:focus { border-color: rgba(61,142,255,0.40); }

.acc-error {
  background: rgba(255,80,80,0.10); border: 1px solid rgba(255,80,80,0.22);
  border-radius: 8px; padding: 9px 12px; color: #ff7070; font-size: 13px;
}
.acc-ok {
  background: rgba(93,224,193,0.10); border: 1px solid rgba(93,224,193,0.22);
  border-radius: 8px; padding: 9px 12px; color: #5de0c1; font-size: 13px;
}
.acc-btn {
  align-self: flex-start;
  background: rgba(61,142,255,0.12); border: 1px solid rgba(61,142,255,0.24);
  border-radius: 8px; padding: 9px 20px; color: #90beff;
  font-size: 13px; font-weight: 600; font-family: 'Onest', sans-serif; cursor: pointer;
  display: flex; align-items: center; gap: 8px;
  transition: background 0.2s;
}
.acc-btn:hover { background: rgba(61,142,255,0.20); }
.acc-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.acc-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid rgba(144,190,255,0.3); border-top-color: #90beff;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
