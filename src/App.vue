<script setup lang="ts">
import { onMounted } from 'vue'
import LayoutHeader from './components/LayoutHeader.vue'
import { useAirQualityData } from './composables/useAirQualityData'

const { initData } = useAirQualityData()
onMounted(() => initData())
</script>

<template>
  <div class="flex min-h-screen flex-col bg-slate-50 text-slate-800 antialiased">
    <LayoutHeader />
    <main class="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
      <RouterView />
    </main>
  </div>
</template>
