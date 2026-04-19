<template>
  <CropAvatarModal
    :file="cropFile"
    :saving="avatarLoading"
    @save="onCropSave"
    @cancel="cropFile = null"
  />

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
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="acc-file-input" @change="onAvatarFile">
          </label>
        </div>
        <div class="acc-avatar-meta">
          <div class="acc-avatar-hint">JPEG, PNG, WebP или GIF · до 5 МБ</div>
          <div v-if="avatarError" class="acc-error">{{ avatarError }}</div>
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
import { ref, computed } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const config = useRuntimeConfig()

// ─── Avatar ──────────────────────────────────────────────────────────────────
const avatarTimestamp = ref(Date.now())
const avatarSrc = computed(() => resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarTimestamp.value))

const avatarLoading = ref(false)
const avatarError = ref('')
const avatarOk = ref(false)
const cropFile = ref<File | null>(null)

function onAvatarFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  ;(e.target as HTMLInputElement).value = ''
  avatarError.value = ''
  avatarOk.value = false
  cropFile.value = file
}

async function onCropSave(blob: Blob) {
  cropFile.value = null
  avatarLoading.value = true
  try {
    await auth.uploadAvatar(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    avatarTimestamp.value = Date.now()
    avatarOk.value = true
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } }
    avatarError.value = e.data?.detail ?? 'Ошибка загрузки'
  } finally {
    avatarLoading.value = false
  }
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

// ─── Password ─────────────────────────────────────────────────────────────────
const oldPass = ref('')
const newPass = ref('')
const confirmPass = ref('')
const passError = ref('')
const passOk = ref(false)
const passLoading = ref(false)

async function changePassword() {
  passError.value = ''
  passOk.value = false
  if (newPass.value !== confirmPass.value) { passError.value = 'Пароли не совпадают'; return }
  if (newPass.value.length < 8) { passError.value = 'Минимум 8 символов'; return }
  passLoading.value = true
  try {
    await auth.changePassword(oldPass.value, newPass.value)
    passOk.value = true
    oldPass.value = ''; newPass.value = ''; confirmPass.value = ''
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string } }
    passError.value = err.data?.detail ?? 'Ошибка смены пароля'
  } finally {
    passLoading.value = false
  }
}
</script>

<style scoped>
.acc-wrap { max-width: 480px; display: flex; flex-direction: column; gap: 16px; }

.acc-avatar-row { display: flex; align-items: center; gap: 20px; }
.acc-avatar-wrap { position: relative; flex-shrink: 0; width: 72px; height: 72px; }
.acc-avatar-img { width: 72px; height: 72px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,0.10); }
.acc-avatar-placeholder {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, #27272a, #3f3f46);
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 800; color: #fafafa;
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
.acc-avatar-hint { font-size: 12px; color: #71717a; }
.acc-del-btn {
  align-self: flex-start; background: none; border: 1px solid rgba(255,80,80,0.22);
  border-radius: 7px; padding: 5px 12px; color: #ff7070;
  font-size: 12px; font-family: 'Onest', sans-serif; cursor: pointer;
  display: flex; align-items: center; gap: 5px; transition: background 0.2s;
}
.acc-del-btn:hover { background: rgba(255,80,80,0.10); }
.acc-del-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.acc-card { background: #0f0f12; border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 20px 24px; }
.acc-card-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #71717a; margin-bottom: 16px; }
.acc-email { font-size: 15px; color: #ececef; }

.acc-form { display: flex; flex-direction: column; gap: 14px; }
.acc-field { display: flex; flex-direction: column; gap: 6px; }
.acc-field label { font-size: 12px; font-weight: 600; color: #71717a; }
.acc-field input {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px; padding: 9px 12px; color: #ececef;
  font-size: 14px; font-family: 'Onest', sans-serif; outline: none; transition: border-color 0.2s;
}
.acc-field input:focus { border-color: rgba(255,255,255,0.20); }
.acc-error { background: rgba(255,80,80,0.10); border: 1px solid rgba(255,80,80,0.22); border-radius: 8px; padding: 9px 12px; color: #ff7070; font-size: 13px; }
.acc-ok { background: rgba(93,224,193,0.10); border: 1px solid rgba(93,224,193,0.22); border-radius: 8px; padding: 9px 12px; color: #5de0c1; font-size: 13px; }
.acc-btn {
  align-self: flex-start; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px; padding: 9px 20px; color: #d4d4d8;
  font-size: 13px; font-weight: 600; font-family: 'Onest', sans-serif; cursor: pointer;
  display: flex; align-items: center; gap: 8px; transition: background 0.2s;
}
.acc-btn:hover { background: rgba(255,255,255,0.10); }
.acc-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.acc-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.15); border-top-color: #d4d4d8;
  animation: spin 0.7s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
