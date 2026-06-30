<script setup lang="ts">
import { computed, watch } from 'vue'

const page = defineModel<number>('page', { required: true })
const pageSize = defineModel<number>('pageSize', { required: true })

const props = withDefaults(
  defineProps<{
    total: number
    pageSizeOptions?: readonly number[]
  }>(),
  {
    pageSizeOptions: () => [10, 20, 50, 100],
  },
)

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / pageSize.value)))
const pageStart = computed(() => (props.total === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const pageEnd = computed(() => Math.min(page.value * pageSize.value, props.total))

const visiblePages = computed<(number | '...')[]>(() => {
  const total = totalPages.value
  const current = page.value

  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => index + 1)
  }

  if (current <= 4) {
    return [1, 2, 3, 4, 5, '...', total]
  }

  if (current >= total - 3) {
    return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  }

  return [1, '...', current - 1, current, current + 1, '...', total]
})

watch(pageSize, () => {
  page.value = 1
})

watch(totalPages, (pages) => {
  if (page.value > pages) page.value = pages
})

function goToPage(target: number) {
  page.value = Math.min(Math.max(1, target), totalPages.value)
}
</script>

<template>
  <div
    class="mt-5 flex flex-col gap-4 rounded-xl border border-slate-100 bg-slate-50/80 px-5 py-4 text-sm text-slate-500 lg:flex-row lg:items-center lg:justify-between"
  >
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
      <span>
        共 <span class="font-mono font-semibold text-slate-800">{{ total }}</span> 条
      </span>
      <span>
        当前显示
        <span class="font-mono font-semibold text-slate-800">{{ pageStart }}</span>
        -
        <span class="font-mono font-semibold text-slate-800">{{ pageEnd }}</span>
        条
      </span>
      <label class="flex items-center gap-2">
        <span>每页</span>
        <select
          v-model.number="pageSize"
          class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm text-slate-700 outline-none transition-colors hover:border-slate-300 focus:border-teal-500"
        >
          <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }} 条</option>
        </select>
      </label>
    </div>

    <div class="flex flex-wrap items-center gap-1.5">
      <button
        type="button"
        class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-600 transition-colors hover:border-teal-300 hover:text-teal-600 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="page === 1"
        @click="goToPage(page - 1)"
      >
        上一页
      </button>

      <template v-for="(item, index) in visiblePages" :key="`${item}-${index}`">
        <span
          v-if="item === '...'"
          class="flex h-8 min-w-8 items-center justify-center px-1 font-mono text-slate-400"
        >
          ...
        </span>
        <button
          v-else
          type="button"
          class="h-8 min-w-8 rounded-lg border px-2 font-mono text-sm font-semibold transition-colors"
          :class="
            item === page
              ? 'border-teal-500 bg-teal-500 text-white shadow-sm'
              : 'border-slate-200 bg-white text-slate-600 hover:border-teal-300 hover:text-teal-600'
          "
          @click="goToPage(item)"
        >
          {{ item }}
        </button>
      </template>

      <button
        type="button"
        class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-600 transition-colors hover:border-teal-300 hover:text-teal-600 disabled:cursor-not-allowed disabled:opacity-40"
        :disabled="page === totalPages"
        @click="goToPage(page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>
