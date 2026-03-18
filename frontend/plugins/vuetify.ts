import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    theme: {
      defaultTheme: 'dark',
      themes: {
        dark: {
          dark: true,
          colors: {
            primary: '#D0BCFF',
            secondary: '#CCC2DC',
            surface: '#1C1B1F',
            background: '#141218',
            error: '#F2B8B5',
          },
        },
        light: {
          dark: false,
          colors: {
            primary: '#6750A4',
            secondary: '#625B71',
            surface: '#FFFBFE',
            background: '#F6F2FF',
            error: '#B3261E',
          },
        },
      },
    },
  })
  app.vueApp.use(vuetify)
})
