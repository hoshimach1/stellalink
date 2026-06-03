<template>
  <CropAvatarModal :file="cropFile" :saving="avatarLoading" @save="onCropSave" @cancel="cropFile = null" />

  <div class="account-shell">
    <section class="account-layout">
      <article v-if="profile.profile" class="account-card account-card-main">
        <div class="account-main-identity">
          <div class="account-person">
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
              <strong>{{ profile.profile?.display_name || auth.user?.email || 'Stellalink' }}</strong>
              <span>{{ auth.user?.email ?? 'Email не указан' }}</span>
              <NuxtLink v-if="profile.profile" class="account-link" :to="`/${profile.profile.slug}`">
                <i class="ri-external-link-line" />
                <span>{{ requestHost }}/{{ profile.profile.slug }}</span>
              </NuxtLink>
            </div>
          </div>

          <div class="account-status-row">
            <span class="account-chip" :class="{ ok: auth.user?.email_verified }">
              <i :class="auth.user?.email_verified ? 'ri-shield-check-line' : 'ri-mail-warning-line'" />
              {{ auth.user?.email_verified ? 'Email подтвержден' : 'Нужно подтвердить email' }}
            </span>
            <span v-if="createdLabel" class="account-chip">
              <i class="ri-calendar-line" />
              С {{ createdLabel }}
            </span>
          </div>

        </div>

        <div class="card-head">
          <div>
            <h3>Данные профиля</h3>
            <p>Имя и адрес, которые видят посетители.</p>
          </div>
        </div>

        <form class="account-form" @submit.prevent="saveIdentity">
          <div class="account-field-grid">
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
          </div>

          <div class="form-actions">
            <span class="form-hint">{{ identityHasChanges ? 'Есть несохраненные изменения' : 'Все изменения сохранены' }}</span>
            <button class="filled-btn" type="submit" :disabled="identityLoading || !identityHasChanges">
              <span v-if="identityLoading" class="account-spinner" />
              <span v-else>Сохранить</span>
            </button>
          </div>
        </form>
      </article>

      <div class="account-stack">
        <article class="account-card">
          <div class="card-head split">
            <div>
              <h3>Email</h3>
              <p>{{ auth.user?.email }}</p>
            </div>
            <span
              class="mini-icon email-status"
              :class="{ ok: auth.user?.email_verified }"
              tabindex="0"
              :aria-label="emailStatusTooltip"
              :data-tooltip="emailStatusTooltip"
            >
              <i :class="auth.user?.email_verified ? 'ri-checkbox-circle-line' : 'ri-error-warning-line'" />
              <span>{{ emailStatusLabel }}</span>
            </span>
          </div>

          <form class="account-form" @submit.prevent="changeEmail">
            <label class="account-field">
              <span>Новый email</span>
              <input v-model="editEmail" type="email" autocomplete="email" placeholder="name@example.com">
            </label>

            <label class="account-field">
              <span>Текущий пароль</span>
              <input v-model="emailPassword" type="password" autocomplete="current-password" placeholder="Подтвердите изменение паролем">
            </label>

            <div class="form-actions">
              <span class="form-hint">{{ emailHasChanges ? 'После смены нужно подтвердить новый email' : 'Введите новый адрес, чтобы изменить email' }}</span>
              <button class="filled-btn" type="submit" :disabled="emailLoading || !canSubmitEmail">
                <span v-if="emailLoading" class="account-spinner" />
                <span v-else>Сменить email</span>
              </button>
            </div>
          </form>

          <button v-if="!auth.user?.email_verified" class="outline-btn" type="button" :disabled="verifyLoading" @click="sendVerification">
            <span v-if="verifyLoading" class="account-spinner dark" />
            <template v-else>
              <i class="ri-send-plane-line" />
              <span>Отправить письмо</span>
            </template>
          </button>

        </article>

        <article class="account-card">
          <div class="card-head split">
            <div>
              <h3>Пароль</h3>
              <p>Минимум 8 символов, буква и цифра.</p>
            </div>
            <span class="mini-icon"><i class="ri-lock-password-line" /></span>
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

            <button class="filled-btn" type="submit" :disabled="passLoading || !canSubmitPass">
              <span v-if="passLoading" class="account-spinner" />
              <span v-else>Сменить пароль</span>
            </button>
          </form>
        </article>
      </div>

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
const { pushToast } = useAppToast()

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
const cropFile = ref<File | null>(null)

const editName = ref(profile.profile?.display_name ?? '')
const editSlug = ref(profile.profile?.slug ?? '')
const identityLoading = ref(false)

watch(() => profile.profile, () => {
  editName.value = profile.profile?.display_name ?? ''
  editSlug.value = profile.profile?.slug ?? ''
}, { deep: false })

const identityHasChanges = computed(() => {
  if (!profile.profile) return false
  return editName.value !== profile.profile.display_name
    || normalizeSlug(editSlug.value) !== profile.profile.slug
})

const editEmail = ref(auth.user?.email ?? '')
const emailPassword = ref('')
const emailLoading = ref(false)

const emailStatusLabel = computed(() => auth.user?.email_verified ? 'Подтвержден' : 'Не подтвержден')
const emailStatusTooltip = computed(() => auth.user?.email_verified
  ? 'Адрес подтвержден. Его можно использовать для входа и восстановления доступа.'
  : 'Адрес не подтвержден. Отправьте письмо и перейдите по ссылке, чтобы защитить аккаунт.')
const emailHasChanges = computed(() => {
  if (!auth.user?.email) return false
  return normalizeEmail(editEmail.value) !== normalizeEmail(auth.user.email)
})
const canSubmitEmail = computed(() =>
  emailHasChanges.value
    && emailPassword.value.length > 0
    && editEmail.value.trim().length > 0,
)

watch(() => auth.user?.email, (email) => {
  editEmail.value = email ?? ''
  emailPassword.value = ''
})

const verifyLoading = ref(false)

const oldPass = ref('')
const newPass = ref('')
const confirmPass = ref('')
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

function normalizeEmail(value: string) {
  return value.trim().toLowerCase()
}

function onAvatarFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  cropFile.value = file
}

async function onCropSave(blob: Blob) {
  cropFile.value = null
  avatarLoading.value = true
  try {
    await auth.uploadAvatar(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    avatarTimestamp.value = Date.now()
    pushToast('Аватар обновлен.', 'success')
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось загрузить аватар.'), 'error')
  } finally {
    avatarLoading.value = false
  }
}

async function saveIdentity() {
  if (!profile.profile) return
  identityLoading.value = true
  try {
    await profile.update({
      display_name: editName.value.trim() || profile.profile.display_name,
      slug: normalizeSlug(editSlug.value) || profile.profile.slug,
    })
    pushToast('Профиль обновлен.', 'success')
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось сохранить профиль.'), 'error')
  } finally {
    identityLoading.value = false
  }
}

async function sendVerification() {
  verifyLoading.value = true
  try {
    const response = await auth.requestEmailVerification()
    pushToast(translateAuthMessage(response.detail, 'Письмо отправлено.'), 'success')
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось отправить письмо.'), 'error')
  } finally {
    verifyLoading.value = false
  }
}

async function changeEmail() {
  if (!emailHasChanges.value) {
    pushToast('Введите email, который отличается от текущего.', 'warning')
    return
  }
  if (!emailPassword.value) {
    pushToast('Введите текущий пароль.', 'warning')
    return
  }

  emailLoading.value = true
  try {
    await auth.changeEmail(editEmail.value, emailPassword.value)
    emailPassword.value = ''
    pushToast('Email обновлен. Мы отправили письмо для подтверждения нового адреса.', 'success')
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось сменить email.'), 'error')
  } finally {
    emailLoading.value = false
  }
}

async function changePassword() {
  if (newPass.value !== confirmPass.value) {
    pushToast('Пароли не совпадают.', 'warning')
    return
  }
  if (newPass.value.length < 8) {
    pushToast('Минимум 8 символов.', 'warning')
    return
  }
  passLoading.value = true
  try {
    await auth.changePassword(oldPass.value, newPass.value)
    pushToast('Пароль обновлен.', 'success')
    oldPass.value = ''
    newPass.value = ''
    confirmPass.value = ''
  } catch (error) {
    pushToast(extractAuthError(error, 'Не удалось сменить пароль.'), 'error')
  } finally {
    passLoading.value = false
  }
}

</script>

<style scoped>
.account-shell {
  display: grid;
  width: min(100%, 1060px);
  min-width: 0;
  gap: 12px;
  margin: 0 auto;
}

.account-shell,
.account-shell * {
  box-sizing: border-box;
}

.account-card {
  width: 100%;
  min-width: 0;
  border: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 86%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #fff) 94%, transparent);
  box-shadow: 0 10px 28px color-mix(in srgb, var(--text-1, #10182b) 7%, transparent);
}

.account-person {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.account-avatar {
  position: relative;
  width: 68px;
  height: 68px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  overflow: visible;
  border-radius: 18px;
  background:
    radial-gradient(circle at 28% 20%, rgba(255,255,255,0.35), transparent 30%),
    linear-gradient(135deg, var(--primary, #345EA8), color-mix(in srgb, var(--primary, #345EA8) 50%, var(--success, #188A55)));
  color: #fff;
  font-size: 28px;
  font-weight: 900;
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
  right: -5px;
  bottom: -5px;
  z-index: 1;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 3px solid var(--surface, #fff);
  border-radius: 50%;
  background: var(--primary, #345EA8);
  color: #fff;
  cursor: pointer;
  line-height: 1;
  box-shadow: 0 8px 18px color-mix(in srgb, var(--text-1, #10182b) 18%, transparent);
  transition: transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)), background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.avatar-camera::before {
  content: "";
  position: absolute;
  inset: -6px;
  border-radius: 50%;
}

.avatar-camera i {
  font-size: 17px;
  line-height: 1;
}

.account-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.account-copy strong,
.account-copy span,
.card-head h3,
.card-head p {
  margin: 0;
}

.account-copy strong {
  color: var(--text-1, #10182b);
  font-size: 22px;
  line-height: 1.12;
  font-weight: 900;
  overflow-wrap: anywhere;
}

.account-copy span {
  color: var(--text-2, #475778);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.account-link {
  width: fit-content;
  max-width: 100%;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
}

.account-link span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-status-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.account-chip {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  border-radius: 999px;
  background: var(--warning-container, #FFF0CF);
  color: var(--warning, #9B6200);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.account-chip.ok {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.account-wide-note {
  grid-column: 1 / -1;
}

.account-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
  gap: 12px;
  align-items: start;
}

.account-stack {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.account-card {
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 16px;
}

.account-card-main {
  align-self: start;
  gap: 16px;
}

.account-main-identity {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--outline, #d4dbe8) 72%, transparent);
}

.account-card-main .account-status-row {
  justify-content: flex-start;
}

.card-head {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.card-head > div {
  min-width: 0;
}

.card-head.split {
  align-items: flex-start;
}

.card-head h3 {
  color: var(--text-1, #10182b);
  font-size: 17px;
  line-height: 1.2;
}

.card-head p {
  margin-top: 3px;
  color: var(--text-2, #475778);
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.mini-icon {
  position: relative;
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 14px;
  background: var(--primary-container, rgba(52,94,168,0.12));
  color: var(--on-primary-container, #163E86);
  font-size: 18px;
}

.mini-icon.ok {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.mini-icon.email-status {
  width: auto;
  min-height: 36px;
  height: auto;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  justify-content: center;
  padding: 0 11px;
  border-radius: 999px;
  background: var(--warning-container, #FFF0CF);
  color: var(--warning, #9B6200);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.mini-icon.email-status.ok {
  background: var(--success-container, #E1F6EA);
  color: var(--success, #188A55);
}

.mini-icon.email-status i {
  font-size: 17px;
  line-height: 1;
}

.mini-icon[data-tooltip]::before,
.mini-icon[data-tooltip]::after {
  position: absolute;
  right: 0;
  z-index: 5;
  opacity: 0;
  pointer-events: none;
  transition:
    opacity 160ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    transform 160ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.mini-icon[data-tooltip]::before {
  content: "";
  top: calc(100% + 3px);
  border: 6px solid transparent;
  border-bottom-color: #151A24;
  transform: translateY(-4px);
}

.mini-icon[data-tooltip]::after {
  content: attr(data-tooltip);
  top: calc(100% + 14px);
  width: max-content;
  max-width: min(260px, 72vw);
  padding: 9px 10px;
  border-radius: 12px;
  background: #151A24;
  color: #F8FAFC;
  box-shadow: 0 12px 28px color-mix(in srgb, var(--text-1, #10182b) 22%, transparent);
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  text-align: left;
  white-space: normal;
  transform: translateY(-4px);
}

.account-form {
  display: grid;
  gap: 12px;
}

.account-field-grid {
  display: grid;
  gap: 12px;
}

.account-field {
  display: grid;
  gap: 6px;
}

.account-field > span {
  color: var(--text-2, #475778);
  font-size: 12px;
  font-weight: 900;
}

.account-field input,
.slug-field {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #fff) 96%, transparent);
  color: var(--text-1, #10182b);
  font: inherit;
  outline: none;
  transition:
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    box-shadow 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
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
  flex: 0 1 auto;
  min-width: 0;
  color: var(--text-3, #66789c);
  font-size: 12px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slug-field input {
  min-width: 88px;
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
}

.account-field input:focus,
.slug-field:focus-within {
  border-color: var(--primary, #345EA8);
  background: var(--surface, #fff);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary, #345EA8) 15%, transparent);
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 2px;
}

.form-hint {
  color: var(--text-3, #66789c);
  font-size: 12px;
  font-weight: 800;
}

.outline-btn,
.filled-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--outline, rgba(82, 103, 138, 0.18));
  border-radius: 999px;
  padding: 0 16px;
  font: inherit;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    background 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    border-color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)),
    color 180ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.outline-btn {
  background: var(--surface, #fff);
  color: var(--text-1, #10182b);
}

.filled-btn {
  background: var(--primary, #345EA8);
  color: #fff;
  border-color: transparent;
}

.outline-btn:disabled,
.filled-btn:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.strength-meter {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-low, #F2F4F8);
}

.strength-meter span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--error, #B3323A);
  transition: width 220ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1)), background 220ms var(--m3-motion, cubic-bezier(0.2, 0, 0, 1));
}

.strength-meter.medium span {
  background: var(--warning, #9B6200);
}

.strength-meter.good span,
.strength-meter.strong span {
  background: var(--success, #188A55);
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
  border-color: color-mix(in srgb, var(--primary, #345EA8) 26%, transparent);
  border-top-color: var(--primary, #345EA8);
}

.account-link:focus-visible,
.avatar-camera:focus-visible,
.mini-icon:focus-visible,
.outline-btn:focus-visible,
.filled-btn:focus-visible,
.account-field input:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--primary, #345EA8) 32%, transparent);
  outline-offset: 2px;
}

@media (hover: hover) {
  .outline-btn:hover:not(:disabled),
  .filled-btn:hover:not(:disabled),
  .avatar-camera:hover {
    transform: translateY(-1px);
  }

  .account-link:hover {
    background: color-mix(in srgb, var(--primary-container, rgba(52,94,168,0.12)) 72%, white);
  }

  .mini-icon[data-tooltip]:hover::before,
  .mini-icon[data-tooltip]:hover::after {
    opacity: 1;
    transform: translateY(0);
  }
}

.mini-icon[data-tooltip]:focus-visible::before,
.mini-icon[data-tooltip]:focus-visible::after {
  opacity: 1;
  transform: translateY(0);
}

@keyframes account-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 980px) {
  .account-shell {
    max-width: 760px;
  }

  .account-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .account-card {
    border-radius: 16px;
    padding: 14px;
  }

  .account-person {
    align-items: flex-start;
  }

  .account-avatar {
    width: 58px;
    height: 58px;
    border-radius: 16px;
    font-size: 23px;
  }

  .account-copy strong {
    font-size: 18px;
  }

  .account-status-row {
    gap: 6px;
  }

  .account-chip {
    min-height: 30px;
    padding: 0 9px;
  }

  .form-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .filled-btn,
  .outline-btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .account-shell *,
  .account-shell *::before,
  .account-shell *::after {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
  }
}
</style>
