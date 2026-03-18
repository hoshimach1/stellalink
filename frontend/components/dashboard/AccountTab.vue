<template>
  <div class="acc-wrap">

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
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const config = useRuntimeConfig()

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
    await $fetch(`${config.public.apiBase}/auth/change-password`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
      body: { old_password: oldPass.value, new_password: newPass.value },
    })
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
.acc-wrap { max-width: 480px; display: flex; flex-direction: column; gap: 16px; }

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
