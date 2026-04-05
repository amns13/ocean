// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/",
    redirect: "/pages",
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginView.vue"),
    meta: { requiresGuest: true },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("../views/RegisterView.vue"),
    meta: { requiresGuest: true },
  },
  {
    // All authenticated routes are nested under this layout
    path: "/",
    component: () => import("../components/AuthLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "pages",
        name: "PageList",
        component: () => import("../views/PageListView.vue"),
      },
      {
        path: "pages/:uid/:slug",
        name: "Page",
        component: () => import("../views/PageView.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation Guard
router.beforeEach((to, from) => {
  const authStore = useAuthStore();

  // Route requires auth but user is not logged in
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "Login" };
  }

  // Route requires guest (login/register) but user is already logged in
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return { name: "PageList" };
  }
});

export default router;
