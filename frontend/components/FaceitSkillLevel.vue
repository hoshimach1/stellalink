<template>
  <svg
    class="faceit-skill-icon"
    viewBox="0 0 24 24"
    width="24"
    height="24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    :aria-label="`FACEIT skill level ${normalizedLevel}`"
    :style="levelStyle"
  >
    <title>Skill level {{ normalizedLevel }}</title>
    <defs>
      <radialGradient :id="barBgId" cx="0.5" cy="0.5" r="0.55">
        <stop offset="0.4" stop-color="#5D5D5D" />
        <stop offset="1" stop-color="#242424" />
      </radialGradient>
    </defs>

    <circle class="background" r="50%" cx="50%" cy="50%" fill="#060606" />
    <path
      class="bar-bg"
      d="M 6.5, 18.4 A 8.4, 8.4 0 1 1 17.5, 18.4"
      :stroke="`url(#${barBgId})`"
      stroke-width="2.4"
      stroke-linecap="round"
    />
    <path
      class="progress"
      d="M 6.5, 18.4 A 8.4, 8.4 0 1 1 17.5, 18.4"
      :stroke="levelColor"
      stroke-width="2.4"
      stroke-linecap="round"
      pathLength="10"
      :style="{ strokeDashoffset: `${dashOffset}px` }"
    />
    <text
      class="level-number"
      :x="normalizedLevel === 10 ? '49%' : numberX"
      y="49%"
      :fill="levelColor"
    >
      {{ normalizedLevel }}
    </text>
  </svg>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(defineProps<{
  level: number
  accentColor?: string | null
}>(), {
  level: 1,
  accentColor: null,
})

const rawId = useId().replace(/[^a-zA-Z0-9_-]/g, '')
const barBgId = `faceit-bar-bg-${rawId}`

const FACEIT_LEVEL_COLORS: Record<number, string> = {
  1: '#F1F1F1',
  2: '#D6D6D6',
  3: '#B9B9B9',
  4: '#FFCF33',
  5: '#FFB400',
  6: '#FF9A00',
  7: '#FF7A00',
  8: '#FF4D1A',
  9: '#FF1F1F',
  10: '#E80128',
}

const normalizedLevel = computed(() => {
  const value = Number.isFinite(props.level) ? Math.round(props.level) : 1
  return Math.min(10, Math.max(1, value))
})

const accentColor = computed(() => {
  const value = props.accentColor?.trim()
  return value && /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i.test(value) ? value : ''
})

const levelColor = computed(() => accentColor.value || FACEIT_LEVEL_COLORS[normalizedLevel.value] || FACEIT_LEVEL_COLORS[1])

const progress = computed(() => normalizedLevel.value === 1 ? 0.99 : normalizedLevel.value)
const dashOffset = computed(() => Math.max(0, 10 - progress.value))
const numberX = computed(() => [1, 4, 6].includes(normalizedLevel.value) ? '50%' : '51%')

const levelStyle = computed(() => ({ color: levelColor.value }))
</script>

<style scoped>
.faceit-skill-icon {
  display: block;
  flex: 0 0 auto;
}

.progress {
  stroke-dasharray: 10.1, 10000;
  transition: stroke-dashoffset 500ms ease;
}

.level-number {
  user-select: none;
  cursor: default;
  font-size: 8px;
  font-family: Arial, Helvetica, sans-serif;
  font-weight: 800;
  text-anchor: middle;
  dominant-baseline: central;
}
</style>
