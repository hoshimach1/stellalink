import {
  createError,
  defineEventHandler,
  getHeaders,
  getMethod,
  getRequestURL,
  readRawBody,
  setHeader,
  setResponseStatus,
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

  const response = await $fetch.raw(targetUrl, {
    method,
    headers,
    body,
    ignoreResponseError: true,
    responseType: 'arrayBuffer',
  })

  setResponseStatus(event, response.status)

  response.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      setHeader(event, key, value)
    }
  })

  return response._data
})
