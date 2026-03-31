import {
  provideFluentDesignSystem,
  fluentCard,
  fluentBadge,
} from '@fluentui/web-components'

export default defineNuxtPlugin(() => {
  provideFluentDesignSystem().register(
    fluentCard(),
    fluentBadge(),
  )
})
