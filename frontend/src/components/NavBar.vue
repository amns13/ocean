<template>
  <nav class="navbar">
    <div class="navbar-content">
      <RouterLink to="/pages" class="navbar-brand">
        🌊 Ocean
      </RouterLink>

      <div class="navbar-right">
        <span class="username">{{ authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">
          Logout
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.navbar {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-content {
  max-width: 720px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  font-size: 1.2rem;
  font-weight: 700;
  color: #4f46e5;
  text-decoration: none;
}

.navbar-brand:hover {
  color: #4338ca;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.username {
  font-size: 0.9rem;
  color: #555;
  font-weight: 500;
}

.btn-logout {
  padding: 0.4rem 1rem;
  background: transparent;
  color: #4f46e5;
  border: 1px solid #4f46e5;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: #4f46e5;
  color: white;
}
</style>

