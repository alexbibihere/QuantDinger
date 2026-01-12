// eslint-disable-next-line
import { UserLayout, BasicLayout, BlankLayout } from '@/layouts'

export const asyncRouterMap = [
  {
    path: '/',
    name: 'index',
    component: BasicLayout,
    meta: { title: 'menu.home' },
    redirect: '/dashboard',
    children: [
      // 仪表盘
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard'),
        meta: { title: 'menu.dashboard', keepAlive: true, icon: 'dashboard', permission: ['dashboard'] }
      },
      // AI 分析
      {
        path: '/ai-analysis/:pageNo([1-9]\\d*)?',
        name: 'Analysis',
        component: () => import('@/views/ai-analysis'),
        meta: { title: 'menu.dashboard.analysis', keepAlive: false, icon: 'thunderbolt', permission: ['dashboard'] }
      },
      // 指标分析
      {
        path: '/indicator-analysis',
        name: 'Indicator',
        component: () => import('@/views/indicator-analysis'),
        meta: { title: 'menu.dashboard.indicator', keepAlive: true, icon: 'line-chart', permission: ['dashboard'] }
      },
      // 交易助手
      {
        path: '/trading-assistant',
        name: 'TradingAssistant',
        component: () => import('@/views/trading-assistant'),
        meta: { title: 'menu.dashboard.tradingAssistant', keepAlive: true, icon: 'robot', permission: ['dashboard'] }
      },
      // 指标社区（keepAlive disabled intentionally for iframe page)
      {
        path: '/indicator-community',
        name: 'IndicatorCommunity',
        component: () => import('@/views/indicator-community'),
        meta: { title: 'menu.dashboard.community', keepAlive: false, icon: 'shop', permission: ['dashboard'] }
      },
      // 智能监控中心 (合并了涨幅榜分析和HAMA监控)
      {
        path: '/smart-monitor',
        name: 'SmartMonitor',
        component: () => import('@/views/smart-monitor'),
        meta: { title: 'menu.smartMonitor', keepAlive: true, icon: 'thunderbolt', permission: ['dashboard'] }
      },
      // 多交易所对比
      {
        path: '/multi-exchange',
        name: 'MultiExchange',
        component: () => import('@/views/multi-exchange'),
        meta: { title: 'menu.multiExchange', keepAlive: true, icon: 'stock', permission: ['dashboard'] }
      },
      // TradingView Scanner
      {
        path: '/tradingview-scanner',
        name: 'TradingViewScanner',
        component: () => import('@/views/tradingview-scanner'),
        meta: { title: 'menu.tradingviewScanner', keepAlive: true, icon: 'line-chart', permission: ['dashboard'] }
      },
      // 系统设置
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/settings'),
        meta: { title: 'menu.settings', keepAlive: false, icon: 'setting', permission: ['dashboard'] }
      }

      // other
      /*
      {
        path: '/other',
        name: 'otherPage',
        component: PageView,
        meta: { title: '其他组件', icon: 'slack', permission: [ 'dashboard' ] },
        redirect: '/other/icon-selector',
        children: [
          {
            path: '/other/icon-selector',
            name: 'TestIconSelect',
            component: () => import('@/views/other/IconSelectorView'),
            meta: { title: 'IconSelector', icon: 'tool', keepAlive: true, permission: [ 'dashboard' ] }
          },
          {
            path: '/other/list',
            component: RouteView,
            meta: { title: '业务布局', icon: 'layout', permission: [ 'support' ] },
            redirect: '/other/list/tree-list',
            children: [
              {
                path: '/other/list/tree-list',
                name: 'TreeList',
                component: () => import('@/views/other/TreeList'),
                meta: { title: '树目录表格', keepAlive: true }
              },
              {
                path: '/other/list/edit-table',
                name: 'EditList',
                component: () => import('@/views/other/TableInnerEditList'),
                meta: { title: '内联编辑表格', keepAlive: true }
              },
              {
                path: '/other/list/user-list',
                name: 'UserList',
                component: () => import('@/views/other/UserList'),
                meta: { title: '用户列表', keepAlive: true }
              },
              {
                path: '/other/list/role-list',
                name: 'RoleList',
                component: () => import('@/views/other/RoleList'),
                meta: { title: '角色列表', keepAlive: true }
              },
              {
                path: '/other/list/system-role',
                name: 'SystemRole',
                component: () => import('@/views/role/RoleList'),
                meta: { title: '角色列表2', keepAlive: true }
              },
              {
                path: '/other/list/permission-list',
                name: 'PermissionList',
                component: () => import('@/views/other/PermissionList'),
                meta: { title: '权限列表', keepAlive: true }
              }
            ]
          }
        ]
      }
      */
    ]
  },
  {
    path: '*',
    redirect: '/404',
    hidden: true
  }
]

/**
 * 基础路由
 * @type { *[] }
 */
export const constantRouterMap = [
  {
    path: '/user',
    component: UserLayout,
    redirect: '/user/login',
    hidden: true,
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import(/* webpackChunkName: "user" */ '@/views/user/Login')
      },
      {
        path: 'recover',
        name: 'recover',
        component: undefined
      }
    ]
  },

  {
    path: '/404',
    component: () => import(/* webpackChunkName: "fail" */ '@/views/exception/404')
  }
]
