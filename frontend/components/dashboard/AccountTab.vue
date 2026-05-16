<template>
  <CropAvatarModal :file="cropFile" :saving="avatarLoading" @save="onCropSave" @cancel="cropFile = null" />

  <div class="account-shell">
    <section class="account-summary">
      <div class="account-id">
        <div class="account-avatar">
          <img v-if="avatarSrc" :src="avatarSrc" alt="">
          <span v-else>{{ userInitial }}</span>
          <label class="avatar-camera" :class="{ loading: avatarLoading }" title="Обновить аватар">
            <span v-if="avatarLoading" class="account-spinner dark" />
            <i v-else class="ri-camera-line" />
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden @change="onAvatarFile">
          </label>
        </div>
        <div class="account-copy">
          <p class="account-kicker">Аккаунт</p>
          <h2>{{ auth.user?.email ?? 'Stellalink account' }}</h2>
          <span>{{ auth.user?.email_verified ? 'Email подтвержден' : 'Email ожидает подтверждения' }}</span>
        </div>
      </div>

      <div class="account-badges">
        <span class="account-badge" :class="{ ok: auth.user?.email_verified }">
          <i :class="auth.user?.email_verified ? 'ri-shield-check-line' : 'ri-mail-warning-line'" />
          {{ auth.user?.email_verified ? 'Защищен' : 'Нужно письмо' }}
        </span>
        <span v-if="createdLabel" class="account-badge">
          <i class="ri-calendar-line" />
          {{ createdLabel }}
        </span>
      </div>

      <div v-if="avatarError" class="account-note error account-summary-note">{{ avatarError }}</div>
      <div v-if="avatarOk" class="account-note success account-summary-note">Аватар обновлен.</div>
    </section>

    <section class="account-grid">
      <article v-if="profile.profile" class="account-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-id-card-line" /></span>
          <div>
            <h3>Публичная идентичность</h3>
            <p>Имя и адрес страницы можно менять и здесь.</p>
          </div>
        </div>

        <form class="account-form" @submit.prevent="saveIdentity">
          <label class="account-field">
            <span>Имя или ник</span>
            <input v-model="editName" type="text" placeholder="Alex K." autocomplete="off">
          </label>

          <label class="account-field">
            <span>Адрес страницы</span>
            <div class="slug-field">
              <span>{{ requestHost }}/</span>
              <input v-model="editSlug" type="text" placeholder="username" autocomplete="off">
            </div>
          </label>

          <div v-if="identityError" class="account-note error">{{ identityError }}</div>
          <div v-if="identityOk" class="account-note success">Профиль обновлен.</div>

          <button class="filled-btn" type="submit" :disabled="identityLoading || !identityHasChanges">
            <span v-if="identityLoading" class="account-spinner" />
            <span v-else>Сохранить</span>
          </button>
        </form>
      </article>

      <article class="account-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-mail-settings-line" /></span>
          <div>
            <h3>Email</h3>
            <p>{{ auth.user?.email }}</p>
          </div>
        </div>

        <div class="email-status" :class="{ verified: auth.user?.email_verified }">
          <i :class="auth.user?.email_verified ? 'ri-checkbox-circle-line' : 'ri-error-warning-line'" />
          <span>{{ auth.user?.email_verified ? 'Адрес подтвержден' : 'Адрес не подтвержден' }}</span>
        </div>

        <button v-if="!auth.user?.email_verified" class="outline-btn" type="button" :disabled="verifyLoading" @click="sendVerification">
          <span v-if="verifyLoading" class="account-spinner dark" />
          <template v-else>
            <i class="ri-send-plane-line" />
            <span>Отправить письмо</span>
          </template>
        </button>

        <div v-if="verifyNotice" class="account-note" :class="verifyNoticeTone">{{ verifyNotice }}</div>
      </article>

      <article class="account-card">
        <div class="card-head">
          <span class="card-icon"><i class="ri-lock-password-line" /></span>
          <div>
            <h3>Пароль</h3>
            <p>Минимум 8 символов, буква и цифра.</p>
          </div>
        </div>

        <form class="account-form" @submit.prevent="changePassword">
          <label class="account-field">
            <span>Текущий пароль</span>
            <input v-model="oldPass" type="password" autocomplete="current-password" placeholder="Введите текущий пароль">
          </label>

          <label class="account-field">
            <span>Новый пароль</span>
            <input v-model="newPass" type="password" autocomplete="new-password" placeholder="Новый пароль" minlength="8">
          </label>

          <label class="account-field">
            <span>Повторите пароль</span>
            <input v-model="confirmPass" type="password" autocomplete="new-password" placeholder="Еще раз">
          </label>

          <div class="strength-meter" :class="passwordStrength.tone">
            <span :style="{ width: passwordStrength.width }" />
          </div>

          <div v-if="passError" class="account-note error">{{ passError }}</div>
          <div v-if="passOk" class="account-note success">Пароль обновлен.</div>

          <button class="filled-btn" type="submit" :disabled="passLoading || !canSubmitPass">
            <span v-if="passLoading" class="account-spinner" />
            <span v-else>Сменить пароль</span>
          </button>
        </form>
      </article>

    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRequestURL } from '#app'
import { resolveAvatarUrl } from '~/composables/useAvatarUrl'
import { useAuthStore } from '~/stores/auth'
import { useProfileStore } from '~/stores/profile'
import { extractAuthError, translateAuthMessage } from '~/utils/auth-feedback'

const auth = useAuthStore()
const profile = useProfileStore()
const config = useRuntimeConfig()
const requestHost = useRequestURL().host

const avatarTimestamp = ref(Date.now())
const avatarSrc = computed(() =>
  resolveAvatarUrl(auth.user?.avatar_url ?? null, config.public.apiBase as string, avatarTimestamp.value),
)
const userInitial = computed(() => auth.user?.email?.trim().charAt(0).toUpperCase() ?? '?')
const createdLabel = computed(() => {
  if (!auth.user?.created_at) return ''
  try {
    return new Intl.DateTimeFormat('ru', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(auth.user.created_at))
  } catch {
    return ''
  }
})

const avatarLoading = ref(false)
const avatarError = ref('')
const avatarOk = ref(false)
const cropFile = ref<File | null>(null)

const editName = ref(profile.profile?.display_name ?? '')
const editSlug = ref(profile.profile?.slug ?? '')
const identityLoading = ref(false)
const identityError = ref('')
const identityOk = ref(false)

watch(() => profile.profile, () => {
  editName.value = profile.profile?.display_name ?? ''
  editSlug.value = profile.profile?.slug ?? ''
}, { deep: false })

const identityHasChanges = computed(() => {
  if (!profile.profile) return false
  return editName.value !== profile.profile.display_name
    || normalizeSlug(editSlug.value) !== profile.profile.slug
})

const verifyLoading = ref(false)
const verifyNotice = ref('')
const verifyNoticeTone = ref<'success' | 'error'>('success')

const oldPass = ref('')
const newPass = ref('')
const confirmPass = ref('')
const passError = ref('')
const passOk = ref(false)
const passLoading = ref(false)

const passwordStrength = computed(() => {
  let score = 0
  if (newPass.value.length >= 8) score += 1
  if (/[a-zа-я]/i.test(newPass.value)) score += 1
  if (/\d/.test(newPass.value)) score += 1
  if (/[^a-zа-я0-9]/i.test(newPass.value)) score += 1
  if (!newPass.value) return { tone: 'empty', width: '0%' }
  if (score <= 1) return { tone: 'weak', width: '28%' }
  if (score === 2) return { tone: 'medium', width: '56%' }
  if (score === 3) return { tone: 'good', width: '78%' }
  return { tone: 'strong', width: '100%' }
})

const canSubmitPass = computed(() =>
  oldPass.value.length > 0
    && newPass.value.length >= 8
    && confirmPass.value.length >= 8,
)

function normalizeSlug(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9_-]/g, '').slice(0, 50)
}

function onAvatarFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  avatarError.value = ''
  avatarOk.value = false
  cropFile.value = file
}

async function onCropSave(blob: Blob) {
  cropFile.value = null
  avatarLoading.value = true
  avatarError.value = ''
  avatarOk.value = false
  try {
    await auth.uploadAvatar(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    avatarTimestamp.value = Date.now()
    avatarOk.value = true
  } catch (error) {
    avatarError.value = extractAuthError(error, 'Не удалось загрузить аватар.')
  } finally {
    avatarLoading.value = false
  }
}

async function saveIdentity() {
  if (!profile.profile) return
  identityLoading.value = true
  identityError.value = ''
  identityOk.value = false
  try {
    await profile.update({
      display_name: editName.value.trim() || profile.profile.display_name,
      slug: normalizeSlug(editSlug.value) || profile.profile.slug,
    })
    identityOk.value = true
  } catch (error) {
    identityError.value = extractAuthError(error, 'Не удалось сохранить профиль.')
  } finally {
    identityLoading.value = false
  }
}

async function sendVerification() {
  verifyLoading.value = true
  verifyNotice.value = ''
  try {
    const response = await auth.requestEmailVerification()
    verifyNoticeTone.value = 'success'
    verifyNotice.value = translateAuthMessage(response.detail, 'Письмо отправлено.')
  } catch (error) {
    verifyNoticeTone.value = 'error'
    verifyNotice.value = extractAuthError(error, 'Не удалось отправить письмо.')
  } finally {
    verifyLoading.value = false
  }
}

async function changePassword() {
  passError.value = ''
  passOk.value = false
  if (newPass.value !== confirmPass.value) {
    passError.value = 'Пароли не совпадают.'
    return
  }
  if (newPass.value.length < 8) {
    passError.value = 'Минимум 8 символов.'
    return
  }
  passLoading.value = true
  try {
    await auth.changePassword(oldPass.value, newPass.value)
    passOk.value = true
    oldPass.value = ''
    newPass.value = ''
    confirmPass.value = ''
  } catch (error) {
    passError.value = extractAuthError(error, 'Не удалось сменить пароль.')
  } finally {
    passLoading.value = false
  }
}

</script>

<style scoped>
.account-shell {
  display: grid;
  width: 100%;
  min-width: 0;
  gap: 16px;
}

.account-shell,
.account-shell * {
  box-sizing: border-box;
}

.account-card {
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 90%, transparent);
  box-shadow: var(--dash-shadow, 0 16px 42px rgba(48, 63, 92, 0.11));
  min-width: 0;
}

.account-id {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.account-avatar {
  position: relative;
  display: grid;
  place-items: center;
  --avatar-camera-offset: -5px;
  --avatar-camera-size: 34px;
  overflow: visible;
  background: linear-gradient(135deg, var(--dash-accent, #345EA8), #F59E0B);
  color: #fff;
  font-weight: 900;
}

.account-avatar {
  width: 88px;
  height: 88px;
  flex: 0 0 auto;
  border-radius: 8px;
  font-size: 34px;
}

.account-avatar img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  border-radius: inherit;
}

.avatar-camera {
  position: absolute;
  right: var(--avatar-camera-offset);
  bottom: var(--avatar-camera-offset);
  z-index: 1;
  width: var(--avatar-camera-size);
  height: var(--avatar-camera-size);
  display: grid;
  place-items: center;
  border: 3px solid var(--dash-surface-strong, #fff);
  border-radius: 50%;
  background: color-mix(in srgb, var(--dash-accent, #345EA8) 84%, white);
  color: #fff;
  cursor: pointer;
  line-height: 1;
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}

.avatar-camera i {
  font-size: 18px;
  line-height: 1;
}

.account-copy {
  min-width: 0;
}

.account-kicker,
.account-copy h2,
.account-copy span,
.card-head h3,
.card-head p {
  margin: 0;
}

.account-kicker {
  color: var(--dash-accent-strong, #163E86);
  font-size: 12px;
  font-weight: 900;
}

.account-copy h2 {
  margin-top: 4px;
  color: var(--dash-text-1, #10182b);
  font-size: 36px;
  line-height: 1.05;
  overflow-wrap: anywhere;
}

.account-copy span {
  display: block;
  margin-top: 6px;
  color: var(--dash-text-2, #475778);
  font-size: 14px;
}

.account-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.account-badge {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--dash-warn-soft, #FFF0CF);
  color: var(--dash-warn, #9B6200);
  font-size: 12px;
  font-weight: 900;
}

.account-badge.ok {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.account-card {
  display: grid;
  align-content: start;
  gap: 16px;
  padding: 18px;
}

.card-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.card-icon {
  width: 40px;
  height: 40px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 8px;
  background: var(--dash-accent-soft, rgba(52,94,168,0.12));
  color: var(--dash-accent-strong, #163E86);
  font-size: 20px;
}

.card-head h3 {
  color: var(--dash-text-1, #10182b);
  font-size: 19px;
}

.card-head p {
  margin-top: 3px;
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.account-form {
  display: grid;
  gap: 12px;
}

.account-field {
  display: grid;
  gap: 6px;
}

.account-field > span {
  color: var(--dash-text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.account-field input,
.slug-field {
  width: 100%;
  min-height: 46px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
  font: inherit;
  outline: none;
  transition: border-color 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1);
}

.account-field input {
  padding: 0 12px;
}

.slug-field {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 12px;
}

.slug-field span {
  flex: 0 0 auto;
  color: var(--dash-text-3, #66789c);
  font-size: 12px;
  font-weight: 800;
}

.slug-field input {
  min-width: 0;
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
}

.account-field input:focus,
.slug-field:focus-within {
  border-color: var(--dash-accent, #345EA8);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--dash-accent, #345EA8) 16%, transparent);
}

.outline-btn,
.filled-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 16px;
  font: inherit;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    background 180ms cubic-bezier(0.2, 0, 0, 1),
    border-color 180ms cubic-bezier(0.2, 0, 0, 1),
    color 180ms cubic-bezier(0.2, 0, 0, 1);
}

.outline-btn {
  background: var(--dash-surface-strong, #fff);
  color: var(--dash-text-1, #10182b);
}

.filled-btn {
  background: var(--dash-accent, #345EA8);
  color: #fff;
  border-color: transparent;
}

.outline-btn.danger {
  color: var(--dash-red, #B3323A);
}

.outline-btn.disabled,
.outline-btn:disabled,
.filled-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.email-status {
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-radius: 8px;
  background: var(--dash-warn-soft, #FFF0CF);
  color: var(--dash-warn, #9B6200);
  font-weight: 900;
}

.email-status.verified {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.account-note {
  padding: 11px 13px;
  border-radius: 8px;
  background: var(--dash-surface-soft, #F2F4F8);
  color: var(--dash-text-2, #475778);
  font-size: 13px;
  line-height: 1.45;
}

.account-note.success {
  background: var(--dash-green-soft, #E1F6EA);
  color: var(--dash-green, #188A55);
}

.account-note.error {
  background: var(--dash-red-soft, #FFE5E7);
  color: var(--dash-red, #B3323A);
}

.strength-meter {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--dash-surface-soft, #F2F4F8);
}

.strength-meter span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--dash-red, #B3323A);
  transition: width 220ms cubic-bezier(0.2, 0, 0, 1), background 220ms cubic-bezier(0.2, 0, 0, 1);
}

.strength-meter.medium span {
  background: var(--dash-warn, #9B6200);
}

.strength-meter.good span,
.strength-meter.strong span {
  background: var(--dash-green, #188A55);
}

.account-spinner {
  width: 18px;
  height: 18px;
  display: inline-block;
  border: 2px solid rgba(255,255,255,0.38);
  border-top-color: #fff;
  border-radius: 50%;
  animation: account-spin 0.78s linear infinite;
}

.account-spinner.dark {
  border-color: color-mix(in srgb, var(--dash-accent, #345EA8) 26%, transparent);
  border-top-color: var(--dash-accent, #345EA8);
}

@media (hover: hover) {
  .outline-btn:hover:not(:disabled),
  .filled-btn:hover:not(:disabled),
  .avatar-camera:hover {
    transform: translateY(-1px);
  }

  .outline-btn.danger:hover:not(:disabled) {
    background: var(--dash-red-soft, #FFE5E7);
    border-color: color-mix(in srgb, var(--dash-red, #B3323A) 32%, var(--dash-outline, #d4dbe8));
  }
}

@keyframes account-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 980px) {
  .account-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .account-id {
    align-items: stretch;
  }

  .account-id {
    flex-direction: column;
  }

  .account-badges {
    justify-content: flex-start;
  }

  .account-copy h2 {
    font-size: 28px;
  }

  .filled-btn,
  .outline-btn {
    width: 100%;
  }
}

.account-shell {
  max-width: 1060px;
  gap: 12px;
  margin: 0 auto;
}

.account-summary,
.account-card {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--dash-outline, rgba(82, 103, 138, 0.18));
  border-radius: 8px;
  background: color-mix(in srgb, var(--dash-surface-strong, #fff) 92%, transparent);
  box-shadow: 0 10px 28px rgba(48, 63, 92, 0.08);
}

.account-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  min-height: 124px;
  padding: 16px;
}

.account-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.account-card {
  gap: 14px;
  padding: 16px;
}

.account-avatar {
  --avatar-camera-offset: -4px;
  --avatar-camera-size: 32px;
  width: 76px;
  height: 76px;
  border-radius: 8px;
  font-size: 30px;
}

.account-copy h2 {
  max-width: 640px;
  font-size: 28px;
  line-height: 1.08;
}

.account-copy span {
  margin-top: 4px;
}

.account-badges {
  max-width: 260px;
}

.account-summary-note {
  flex: 1 0 100%;
}

.card-head {
  align-items: center;
}

.card-icon {
  width: 36px;
  height: 36px;
  font-size: 18px;
}

.card-head h3 {
  font-size: 17px;
}

.card-head p {
  font-size: 12px;
}

.account-field input,
.slug-field {
  min-height: 44px;
}

.email-status {
  min-height: 44px;
}

.outline-btn,
.filled-btn {
  min-height: 42px;
}

@media (max-width: 980px) {
  .account-shell {
    max-width: 720px;
  }

  .account-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .account-summary {
    align-items: flex-start;
    flex-direction: column;
    min-height: 0;
  }

  .account-id {
    width: 100%;
  }

  .account-badges {
    justify-content: flex-start;
    max-width: none;
  }

  .account-copy h2 {
    font-size: 23px;
  }

  .slug-field {
    display: grid;
    gap: 4px;
    min-height: 58px;
    padding: 8px 12px;
  }

  .slug-field span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
