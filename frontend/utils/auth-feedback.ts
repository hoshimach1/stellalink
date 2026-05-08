type FetchErrorShape = {
  data?: {
    detail?: unknown
  }
  message?: string
}

const AUTH_MESSAGE_MAP: Record<string, string> = {
  'Email already registered': 'Этот email уже зарегистрирован.',
  'Invalid email or password': 'Неверный email или пароль.',
  'Invalid or expired refresh token': 'Сессия истекла. Войдите снова.',
  'Email is already verified': 'Email уже подтвержден.',
  'Invalid or expired verification token': 'Ссылка для подтверждения недействительна или устарела.',
  'Invalid verification payload': 'Не удалось подтвердить email. Запросите новое письмо.',
  'Password reset email sent if account exists': 'Если аккаунт с таким email существует, мы отправили письмо для сброса пароля.',
  'Verification email sent if account exists': 'Если аккаунт найден, письмо для подтверждения уже отправлено.',
  'Invalid or expired reset token': 'Ссылка для сброса пароля недействительна или устарела.',
  'Invalid reset payload': 'Не удалось сбросить пароль. Запросите новую ссылку.',
  'New password must be different from current password': 'Новый пароль должен отличаться от текущего.',
  'Current password is incorrect': 'Текущий пароль указан неверно.',
  'Password must be at least 8 characters': 'Пароль должен быть не короче 8 символов.',
  'Password must include at least one letter': 'Добавьте в пароль хотя бы одну букву.',
  'Password must include at least one digit': 'Добавьте в пароль хотя бы одну цифру.',
  'Invalid or expired token': 'Срок действия сессии истек. Войдите снова.',
  'User not found': 'Пользователь не найден.',
  'Profile already exists': 'Профиль уже создан.',
  'Profile not found': 'Профиль не найден.',
  'Slug already taken': 'Этот адрес страницы уже занят.',
}

export function translateAuthMessage(message?: string, fallback = 'Что-то пошло не так. Попробуйте еще раз.'): string {
  const normalized = message?.trim()
  if (!normalized) return fallback

  if (AUTH_MESSAGE_MAP[normalized]) return AUTH_MESSAGE_MAP[normalized]

  if (/value is not a valid email address/i.test(normalized) || /@-sign/i.test(normalized)) {
    return 'Укажите корректный email.'
  }

  const lockoutMatch = normalized.match(/Too many failed login attempts\. Try again in (\d+) minute\(s\)\./i)
  if (lockoutMatch) {
    const minutes = lockoutMatch[1]
    return `Слишком много неудачных попыток входа. Попробуйте снова через ${minutes} мин.`
  }

  return normalized
}

export function extractAuthError(error: unknown, fallback: string): string {
  if (!error || typeof error !== 'object') return fallback

  const maybeError = error as FetchErrorShape
  const detail = maybeError.data?.detail

  if (typeof detail === 'string') {
    return translateAuthMessage(detail, fallback)
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const firstItem = detail[0] as { msg?: string } | undefined
    if (firstItem?.msg) return translateAuthMessage(firstItem.msg, fallback)
  }

  return translateAuthMessage(maybeError.message, fallback)
}
