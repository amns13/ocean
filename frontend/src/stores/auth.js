import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authApi } from "../api";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("access_token") || null);
  const user = ref(null);

  const isAuthenticated = computed(() => !!token.value);

  function setToken(newToken) {
    token.value = newToken;
    localStorage.setItem("access_token", newToken);
  }

  async function register(username, email, password) {
    const response = await authApi.register({ username, email, password });
    return response.data;
  }

  async function login(username, password) {
    const response = await authApi.login({ username, password });
    setToken(response.data.access);
    user.value = { username };
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem("access_token");
  }

  // Rehydrate username from token on page refresh
  function initialize() {
    if (token.value) {
      try {
        const payload = JSON.parse(atob(token.value.split(".")[1]));
        user.value = { username: payload.sub };
      } catch {
        logout();
      }
    }
  }

  return { token, user, isAuthenticated, register, login, logout, initialize };
});
