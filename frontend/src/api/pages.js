// src/todos.js
import apiClient from './axios'

export const pagesApi = {
  getAll() {
    return apiClient.get('/pages/')
  },

  getOne(id) {
    return apiClient.get(`/pages/${id}/`)
  },

  create(todoData) {
    return apiClient.post('/pages/', todoData)
  },

  update(id, todoData) {
    return apiClient.put(`/pages/${id}/`, todoData)
  },

  delete(id) {
    return apiClient.delete(`/pages/${id}/`)
  },
}

