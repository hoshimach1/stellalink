import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

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

  build: {
    transpile: ['vuetify'],
  },

  modules: [
    '@pinia/nuxt',
    (_options, nuxt) => {
      nuxt.hooks.hook('vite:extendConfig', (config) => {
        config.plugins?.push(vuetify({ autoImport: true }))
      })
    },
  ],

  vite: {
    vue: {
      template: {
        transformAssetUrls,
        compilerOptions: {
          isCustomElement: (tag: string) => tag.startsWith('fluent-'),
        },
      },
    },
    ssr: {
      noExternal: ['vuetify'],
      external: ['@wxperia/liquid-glass-vue'],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },

  compatibilityDate: '2024-11-01',
})
