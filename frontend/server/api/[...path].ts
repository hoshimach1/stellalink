import {
  createError,
  defineEventHandler,
  getHeaders,
  getMethod,
  getRequestURL,
  readRawBody,
} from 'h3'

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
])

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const targetBase = String(config.apiProxyTarget || '').replace(/\/$/, '')

  if (!targetBase) {
    throw createError({
      statusCode: 500,
      statusMessage: 'API proxy target is not configured',
    })
  }

  const requestUrl = getRequestURL(event)
  const targetPath = requestUrl.pathname.replace(/^\/api(?=\/|$)/, '') || '/'
  const targetUrl = `${targetBase}${targetPath}${requestUrl.search}`
  const method = getMethod(event)

  const headers = { ...getHeaders(event) }
  for (const header of Object.keys(headers)) {
    if (HOP_BY_HOP_HEADERS.has(header.toLowerCase())) {
      delete headers[header]
    }
  }

  const body = method === 'GET' || method === 'HEAD'
    ? undefined
    : await readRawBody(event, false)

  let response
  try {
    response = await $fetch.raw<ArrayBuffer>(targetUrl, {
      method,
      headers,
      body,
      ignoreResponseError: true,
      responseType: 'arrayBuffer',
    })
  } catch (err) {
    const mockResponse = handleMock(targetPath, method, body)
    if (mockResponse) {
      return mockResponse
    }
    throw err
  }

  const responseHeaders = new Headers()

  response.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      responseHeaders.set(key, value)
    }
  })

  return new Response(response._data, {
    status: response.status,
    headers: responseHeaders,
  })
})

function handleMock(targetPath: string, method: string, rawBody: any) {
  const cleanPath = targetPath.split('?')[0].replace(/\/$/, '')
  console.log(`[Mock API Proxy] Intercepted ${method} ${cleanPath}`)

  let parsedBody: any = {}
  if (rawBody) {
    try {
      parsedBody = JSON.parse(new TextDecoder().decode(rawBody))
    } catch {
      // ignore
    }
  }

  if (cleanPath === '/auth/login' || cleanPath === '/auth/register') {
    return new Response(JSON.stringify({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/auth/refresh') {
    return new Response(JSON.stringify({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/auth/me') {
    return new Response(JSON.stringify({
      id: 'mock-user-123',
      email: 'admin@stellalink.app',
      email_verified: true,
      is_admin: true,
      avatar_url: null,
      created_at: '2026-06-04T12:00:00Z'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/profiles/me') {
    return new Response(JSON.stringify({
      id: 'mock-profile-123',
      slug: 'admin',
      status: 'published',
      display_name: 'Администратор',
      bio: 'Управление Stellalink',
      tags: ['admin'],
      blocks: [],
      theme_preset: 'material3',
      theme_tokens: null,
      accent_color: null,
      avatar_url: null
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/admin/smtp-settings') {
    const settings = {
      enabled: parsedBody.enabled !== undefined ? parsedBody.enabled : true,
      host: parsedBody.host !== undefined ? parsedBody.host : 'smtp.stellalink.app',
      port: parsedBody.port !== undefined ? parsedBody.port : 587,
      username: parsedBody.username !== undefined ? parsedBody.username : 'no-reply',
      password_set: true,
      use_ssl: parsedBody.use_ssl !== undefined ? parsedBody.use_ssl : false,
      use_tls: parsedBody.use_tls !== undefined ? parsedBody.use_tls : true,
      force_ipv4: false,
      timeout_seconds: parsedBody.timeout_seconds !== undefined ? parsedBody.timeout_seconds : 15,
      from_email: parsedBody.from_email !== undefined ? parsedBody.from_email : 'no-reply@stellalink.app',
      from_name: parsedBody.from_name !== undefined ? parsedBody.from_name : 'Stellalink',
      frontend_base_url: parsedBody.frontend_base_url !== undefined ? parsedBody.frontend_base_url : 'http://localhost:3000',
      email_verification_ttl_seconds: parsedBody.email_verification_ttl_seconds !== undefined ? parsedBody.email_verification_ttl_seconds : 86400,
      password_reset_ttl_seconds: parsedBody.password_reset_ttl_seconds !== undefined ? parsedBody.password_reset_ttl_seconds : 3600
    }
    return new Response(JSON.stringify(settings), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/admin/api-settings') {
    const settings = {
      steam_api_key_set: true,
      steam_api_key_hint: 'ABCD',
      faceit_api_key_set: true,
      faceit_api_key_hint: '1234',
      github_oauth_client_id: parsedBody.github_oauth_client_id !== undefined ? parsedBody.github_oauth_client_id : 'github_client_id_12345',
      github_oauth_client_secret_set: true,
      github_oauth_client_secret_hint: 'XYZ',
      gitlab_oauth_client_id: parsedBody.gitlab_oauth_client_id !== undefined ? parsedBody.gitlab_oauth_client_id : 'gitlab_client_id_12345',
      gitlab_oauth_client_secret_set: false,
      gitlab_oauth_client_secret_hint: null,
      gitea_oauth_client_id: parsedBody.gitea_oauth_client_id !== undefined ? parsedBody.gitea_oauth_client_id : 'gitea_client_id_12345',
      gitea_oauth_client_secret_set: true,
      gitea_oauth_client_secret_hint: 'GITEA',
      spotify_oauth_client_id: parsedBody.spotify_oauth_client_id !== undefined ? parsedBody.spotify_oauth_client_id : 'spotify_client_id_12345',
      spotify_oauth_client_secret_set: true,
      spotify_oauth_client_secret_hint: 'SPOT',
      code_provider_token_auth_enabled: parsedBody.code_provider_token_auth_enabled !== undefined ? parsedBody.code_provider_token_auth_enabled : true,
      steam_inventory_app_id: parsedBody.steam_inventory_app_id !== undefined ? parsedBody.steam_inventory_app_id : 730,
      steam_inventory_context_id: parsedBody.steam_inventory_context_id !== undefined ? parsedBody.steam_inventory_context_id : '2',
      steam_inventory_price_source: 'steam'
    }
    return new Response(JSON.stringify(settings), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/admin/smtp-settings/test') {
    return new Response(JSON.stringify({
      detail: `Тестовое письмо успешно отправлено на ${parsedBody.to_email || 'admin@stellalink.app'}`
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (cleanPath === '/auth/logout') {
    return new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  return null
}

