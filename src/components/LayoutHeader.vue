<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const nav = [
  { to: '/dashboard', label: '数据大屏' },
  { to: '/data', label: '数据明细' },
  { to: '/dataset', label: '数据集展示' },
  { to: '/about', label: '关于项目' },
] as const

const currentTime = ref('')
let timer: ReturnType<typeof setInterval> | undefined

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

const activePath = computed(() => route.path)

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <header
    class="glass-effect sticky top-0 z-50 border-b border-slate-100 bg-white/90 shadow-sm backdrop-blur-md"
  >
    <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-3">
        <RouterLink to="/dashboard" class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded bg-gradient-to-br from-emerald-400 to-teal-500 text-xl font-bold text-white"
          >
            AQ
          </div>
          <h1 class="text-xl font-bold text-slate-800">城市空气质量全景洞察</h1>
        </RouterLink>
      </div>
      <div class="flex items-center gap-4 sm:gap-6">
        <nav class="hidden gap-4 sm:flex">
          <RouterLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="border-b-2 pb-1 text-sm font-medium transition-colors"
            :class="
              activePath === item.to || (item.to === '/dashboard' && activePath === '/')
                ? 'border-teal-500 text-teal-600'
                : 'border-transparent text-slate-500 hover:text-teal-500'
            "
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="rounded bg-slate-100 px-3 py-1 font-mono text-sm text-slate-500">
          {{ currentTime }}
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm text-slate-500 hover:text-teal-600"
          title="GitHub 仓库"
        >
          GitHub
        </a>
        <button
          type="button"
          class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-500"
          title="深浅色模式（预留）"
          disabled
        >
          主题
        </button>
      </div>
    </div>
    <nav class="flex gap-2 border-t border-slate-100 px-4 py-2 sm:hidden">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="rounded-lg px-3 py-1.5 text-sm font-medium"
        :class="
          activePath === item.to || (item.to === '/dashboard' && activePath === '/')
            ? 'bg-teal-50 text-teal-700'
            : 'text-slate-600'
        "
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </header>
</template>
