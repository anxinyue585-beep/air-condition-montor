import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('../views/DataCenterView.vue'),
    },
    {
      path: '/dataset',
      name: 'dataset',
      component: () => import('../views/DatasetShowcaseView.vue'),
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('../views/AnalysisView.vue'),
    },
    {
      path: '/spatial',
      name: 'spatial',
      component: () => import('../views/SpatialMapView.vue'),
    },
    {
      path: '/warning',
      name: 'warning',
      component: () => import('../views/PollutionWarningView.vue'),
    },
    {
      path: '/live',
      name: 'live',
      component: () => import('../views/LiveDataView.vue'),
    },
    {
      path: '/lineage',
      name: 'lineage',
      component: () => import('../views/LineageView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
