import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authApi } from "../api";

export const useAuthStore = defineStore("auth", () => {
    const userUid = ref(localStorage.getItem("user_uid") || null);
    const user = ref(null);
    const isAuthenticated = computed(() => !!userUid.value);

    function setUserDetails(userData) {
        userUid.value = userData.uid;
        localStorage.setItem("user_uid", userData.uid);
        localStorage.setItem("user_email", userData.email);
        localStorage.setItem("user_username", userData.username);
    }

    async function register(username, email, password) {
        const response = await authApi.register({ username, email, password });
        return response.data;
    }

    async function login(username, password) {
        const response = await authApi.login({ username, password });
        setUserDetails(response.data);
        user.value = { username };
    }

    async function logout() {
        localStorage.removeItem("user_uid");
        localStorage.removeItem("user_email");
        localStorage.removeItem("user_username");
        user.value = null;
        userUid.value = null;
        await authApi.logout();
    }

    // Rehydrate username from localStorage on page refresh
    function initialize() {
        try {
            user.value = { username: localStorage.getItem("user_username") };
            if (!user.value) {
                logout();
            }
        } catch {
            logout();
        }
    }

    return { user, isAuthenticated, register, login, logout, initialize };
});
