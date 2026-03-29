import { reactive } from 'vue'

export const authStore = reactive({
  user: null,
  isAuthenticated: false,
  isAdmin: false,
  loading: true,

  setUser(userData) {
    this.user = userData
    this.isAuthenticated = !!userData
    this.isAdmin = userData?.role === 'admin'
    this.loading = false
  },

  clearUser() {
    this.user = null
    this.isAuthenticated = false
    this.isAdmin = false
    this.loading = false
  }
})
