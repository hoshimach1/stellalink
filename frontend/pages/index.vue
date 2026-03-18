<template>
  <div>
    <LandingAppNav @open-auth="authOpen = true" />
    <LandingHeroSection @open-auth="authOpen = true" />
    <LandingDemoCard />
    <LandingFeaturesSection />
    <LandingBlocksSection />
    <LandingHowtoSection />
    <LandingCompareSection />
    <LandingCtaSection @open-auth="(slug) => { initialSlug = slug; authOpen = true }" />
    <LandingAppFooter />

    <LandingAuthModal v-model="authOpen" :initial-slug="initialSlug" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'landing' })

useHead({
  title: 'Stellalink — твой живой профиль',
  meta: [
    { name: 'description', content: 'Не статичная визитка — живое отражение тебя. Steam, Faceit, Last.fm, GitHub — всё в одном месте, обновляется само.' },
  ],
  link: [
    { rel: 'stylesheet', href: 'https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css' },
  ],
})

const authOpen = ref(false)
const initialSlug = ref('')

onMounted(() => {
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible')
        revealObs.unobserve(entry.target)
      }
    })
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' })

  document.querySelectorAll('.stagger').forEach(parent => {
    ;[...parent.children].forEach((child, i) => {
      child.classList.add('reveal')
      ;(child as HTMLElement).style.transitionDelay = `${i * 0.07}s`
    })
  })

  document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el))
})
</script>

<style src="~/assets/css/landing.css" />
