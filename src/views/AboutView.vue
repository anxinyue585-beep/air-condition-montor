<script setup lang="ts">
const members = [
  { name: '刘嘉晨', role: '组长' },
  { name: '顾跃庭', role: '组员' },
  { name: '成员 3', role: '角色待填写' },
]
</script>

<template>
  <div class="animate-fade-in-up space-y-6">
    <div class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
      <h2 class="mb-4 text-2xl font-bold text-slate-800">项目背景与研究目标</h2>
      <p class="mb-6 leading-relaxed text-slate-600">
        本项目旨在通过现代化的前端可视化技术，对城市空气质量数据进行深度解析与多维呈现。系统基于实际监测数据，致力于发现空气污染的潜在规律，为环保决策提供直观的数据支撑。
      </p>
      <h3 class="mb-3 text-lg font-bold text-slate-800">技术栈与创新点</h3>
      <ul class="mb-6 list-inside list-disc space-y-2 text-slate-600">
        <li>
          前端框架：<span class="font-medium text-teal-600">Vue 3 (Composition API)</span
          >，提供高效的组件化响应式更新。
        </li>
        <li>
          视觉呈现：基于 <span class="font-medium text-teal-600">Tailwind CSS</span> 的极简留白与微拟态设计。
        </li>
        <li>
          数据可视化：集成 <span class="font-medium text-teal-600">ECharts 5</span
          >，实现平滑的数据过渡动画与多维交互分析。
        </li>
      </ul>
    </div>

    <div class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
      <h3 class="mb-4 text-lg font-bold text-slate-800">团队成员</h3>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
        <div
          v-for="member in members"
          :key="member.name"
          class="rounded-lg border border-slate-100 bg-slate-50/80 p-4 text-center"
        >
          <div class="mx-auto mb-2 h-12 w-12 rounded-full bg-gradient-to-br from-teal-200 to-emerald-300" />
          <p class="font-medium text-slate-800">{{ member.name }}</p>
          <p class="text-sm text-slate-500">{{ member.role }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
