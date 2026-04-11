// src/api/axios.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — attach JWT token to every request if it exists
apiClient.interceptors.request.use(
  (config) => {
    config.withCredentials = true;
    config.withXSRFToken = true;
    config.xsrfCookieName = "csrftoken";
    config.xsrfHeaderName = "X-CSRFToken";
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — if token is expired or invalid, log the user out
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("user_uid");
      localStorage.removeItem("user_email");
      localStorage.removeItem("user_username");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default apiClient;
