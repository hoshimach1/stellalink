export default defineNuxtConfig({
  devtools: { enabled: true },

  app: {
    head: {
      link: [
        { rel: 'icon', type: 'image/png', href: '/images/logos/logo.png' },
        { rel: 'apple-touch-icon', href: '/images/logos/logo_big.png' },
      ],
    },
  },

  modules: ['@pinia/nuxt'],

  vite: {
    vue: {
      template: {
        compilerOptions: {
          isCustomElement: (tag: string) =>
            tag.startsWith('fluent-') || tag.startsWith('md-'),
        },
      },
    },
  },

  runtimeConfig: {
    apiProxyTarget: process.env.NUXT_API_PROXY_TARGET || 'http://localhost:8000',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
    },
  },

  compatibilityDate: '2024-11-01',
})
