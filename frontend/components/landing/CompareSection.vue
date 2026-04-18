<template>
  <section id="compare">
    <div class="section-label md-typescale-label-large reveal">Сравнение</div>
    <h2 class="section-title md-typescale-headline-large reveal">Чем отличается<br>от Linktree?</h2>
    <p class="section-sub md-typescale-body-large reveal">Linktree — это просто список ссылок. Stellalink — живой профиль, который рассказывает кто ты есть прямо сейчас.</p>
    <md-outlined-card class="compare-wrap reveal">
      <md-divider />
      <table class="compare-table">
        <thead>
          <tr>
            <th>Что умеет</th>
            <th class="col-stella">Stellalink</th>
            <th>Linktree</th>
            <th>about.me</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.label">
            <td>{{ row.label }}</td>
            <td><span :class="row.stella.cls">{{ row.stella.text }}</span></td>
            <td><span :class="row.linktree.cls">{{ row.linktree.text }}</span></td>
            <td><span :class="row.about.cls">{{ row.about.text }}</span></td>
          </tr>
        </tbody>
      </table>
    </md-outlined-card>
  </section>
</template>

<script setup lang="ts">
const yes = { cls: 'check', text: '✓' }
const no  = { cls: 'cross', text: '—' }
const rows = [
  { label: 'Список ссылок',                     stella: yes, linktree: yes, about: yes },
  { label: 'Показывает что ты делаешь сейчас',  stella: yes, linktree: no,  about: no  },
  { label: 'Виджет Steam и игровой статистики',  stella: yes, linktree: no,  about: no  },
  { label: 'Сейчас слушает музыку',              stella: yes, linktree: no,  about: no  },
  { label: 'Перетаскивание блоков',              stella: yes, linktree: { cls: 'partial', text: 'только ссылки' }, about: no },
  { label: 'Полная кастомизация внешнего вида',  stella: yes, linktree: { cls: 'partial', text: 'только платно' }, about: { cls: 'partial', text: 'ограниченно' } },
  { label: 'Красиво выглядит при репосте',       stella: yes, linktree: { cls: 'partial', text: 'частично' }, about: yes },
  { label: 'Карточка с железом ПК',              stella: yes, linktree: no,  about: no  },
]
</script>
