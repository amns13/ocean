// src/api/auth.js
import apiClient from "./axios";

export const authApi = {
  register(userData) {
    return apiClient.post("/auth/register/", userData);
  },

  login(creds) {
    return apiClient.post("/auth/login/", creds);
  },

  logout() {
    return apiClient.post("/auth/logout/");
  },
};
