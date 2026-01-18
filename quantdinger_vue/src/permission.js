import router, {
  resetRouter
} from './router'
import store from './store'
import storage from 'store'
import NProgress from 'nprogress' // progress bar
import '@/components/NProgress/nprogress.less' // progress bar custom style
import {
  setDocumentTitle,
  domTitle
} from '@/utils/domUtil'
import {
  ACCESS_TOKEN
} from '@/store/mutation-types'
import {
  i18nRender
} from '@/locales'

NProgress.configure({
  showSpinner: false
}) // NProgress Configuration

const loginRoutePath = '/user/login'
const defaultRoutePath = '/dashboard'

router.beforeEach((to, from, next) => {
  NProgress.start() // start progress bar
  to.meta && typeof to.meta.title !== 'undefined' && setDocumentTitle(`${i18nRender(to.meta.title)} - ${domTitle}`)

  // 移除登录验证，直接允许访问所有页面
  // 如果访问登录页，直接跳转到首页
  if (to.path === loginRoutePath) {
    next({ path: defaultRoutePath })
    NProgress.done()
    return
  }

  // 设置默认 token（如果不存在）
  const token = storage.get(ACCESS_TOKEN) || 'auto-login-token'
  if (!storage.get(ACCESS_TOKEN)) {
    storage.set(ACCESS_TOKEN, token)
  }

  // 检查路由是否已初始化
  const addRouters = store.getters.addRouters
  if (!addRouters || addRouters.length === 0) {
    // 设置默认角色
    if (store.getters.roles.length === 0) {
      store.commit('SET_ROLES', [{ id: 'default', permissionList: ['dashboard'] }])
    }

    // 生成路由
    store.dispatch('GenerateRoutes', { token }).then(() => {
      resetRouter()
      store.getters.addRouters.forEach(r => {
        router.addRoute(r)
      })
      next({ ...to, replace: true })
    }).catch(() => {
      next()
    })
  } else {
    next()
  }
})

router.afterEach(() => {
  NProgress.done() // finish progress bar
})
