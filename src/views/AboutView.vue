<script setup lang="ts">
const techStack = ['Vue 3', 'TypeScript', 'Vite', 'Tailwind CSS', 'ECharts 6', 'Hadoop', 'Hive', 'Spark']

const modules = [
  { name: '数据大屏', desc: '展示 AQI 趋势、污染物结构、城市等级分布和重点城市画像。' },
  { name: '数据明细', desc: '提供统一数据源下的城市、等级筛选、分页浏览和 CSV 导出。' },
  { name: '数据集展示', desc: '支持关键字、城市、等级、季节筛选，以及分页、排序、JSON/CSV 导出。' },
  { name: '算法分析', desc: '集中呈现 Top-N、聚类、分类和预测模型的参数与结果。' },
]

const algorithmResults = [
  { label: '风险排名', value: 'Top-N', desc: '识别高污染风险城市' },
  { label: '聚类分析', value: 'K=3', desc: '低、中、高污染画像划分' },
  { label: '风险分类', value: 'F1 0.8276', desc: 'Logistic Regression' },
  { label: 'AQI 预测', value: 'RMSE 1.0608', desc: 'Ridge Regression' },
]

const members = [
  { name: '刘嘉晨', role: '组长', work: '负责整体方案设计、数据建设、平台材料整理与前端页面集成。' },
  { name: '顾跃庭', role: '组员', work: '负责数据处理算法、分析模型、可视化优化与项目文档完善。' },
]
</script>

<template>
  <div class="animate-fade-in-up space-y-6">
    <section class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
      <div class="max-w-3xl">
        <p class="text-sm font-bold text-teal-600">互联网大数据应用技术实践</p>
        <h2 class="mt-2 text-2xl font-bold text-slate-900">城市空气质量大数据分析与可视化系统</h2>
        <p class="mt-4 leading-7 text-slate-600">
          本项目围绕城市空气质量数据完成从数据建设、平台部署、数据处理、算法分析到前端可视化展示的完整实践流程。
          系统以统一数据源为基础，结合 Hadoop/Hive/Spark 平台材料与机器学习分析结果，形成面向课程评分细则的综合性大数据应用项目。
        </p>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
        <h3 class="text-lg font-bold text-slate-900">技术路线</h3>
        <div class="mt-4 flex flex-wrap gap-2">
          <span
            v-for="tech in techStack"
            :key="tech"
            class="rounded-full border border-teal-100 bg-teal-50 px-3 py-1 text-sm font-semibold text-teal-700"
          >
            {{ tech }}
          </span>
        </div>
        <div class="mt-6 space-y-3">
          <div v-for="module in modules" :key="module.name" class="border-t border-slate-100 pt-3">
            <p class="font-semibold text-slate-800">{{ module.name }}</p>
            <p class="mt-1 text-sm text-slate-500">{{ module.desc }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
        <h3 class="text-lg font-bold text-slate-900">算法分析成果</h3>
        <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div
            v-for="result in algorithmResults"
            :key="result.label"
            class="rounded-lg border border-slate-100 bg-slate-50/80 p-4"
          >
            <p class="text-sm font-semibold text-slate-500">{{ result.label }}</p>
            <p class="mt-1 font-mono text-xl font-bold text-slate-900">{{ result.value }}</p>
            <p class="mt-1 text-sm text-slate-500">{{ result.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-xl border border-slate-100 bg-white p-8 shadow-sm">
      <h3 class="text-lg font-bold text-slate-900">团队成员</h3>
      <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div
          v-for="member in members"
          :key="member.name"
          class="rounded-lg border border-slate-100 bg-slate-50/80 p-5"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-teal-300 to-emerald-400 font-bold text-white">
              {{ member.name.slice(0, 1) }}
            </div>
            <div>
              <p class="font-bold text-slate-900">{{ member.name }}</p>
              <p class="text-sm text-teal-600">{{ member.role }}</p>
            </div>
          </div>
          <p class="mt-4 text-sm leading-6 text-slate-500">{{ member.work }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
