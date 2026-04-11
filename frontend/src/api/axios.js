// src/api/axios.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  headers: {
    "Content-Type": "application/json",
  },
});

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
