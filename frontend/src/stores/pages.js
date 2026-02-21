import { defineStore } from 'pinia'
import { ref } from 'vue'
import { pagesApi } from '../api'

export const usePageStore = defineStore('pages', () => {
  const pages = ref([])
  const currentPage = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchPages() {
    loading.value = true
    error.value = null
    try {
      const response = await pagesApi.getAll()
      pages.value = response.data
    } catch (err) {
      error.value = 'Failed to load pages'
    } finally {
      loading.value = false
    }
  }

  async function fetchPage(id) {
    loading.value = true
    error.value = null
    try {
      const response = await pagesApi.getOne(id)
      currentPage.value = response.data
    } catch (err) {
      error.value = 'Page not found'
    } finally {
      loading.value = false
    }
  }

  async function createPage(pageData) {
    const response = await pagesApi.create(pageData)
    pages.value.push(response.data)
    return response.data
  }

  async function updatePage(id, pageData) {
    const response = await pagesApi.update(id, pageData)
    const index = pages.value.findIndex(t => t.id === id)
    if (index !== -1) {
      pages.value[index] = response.data
    }
    if (currentPage.value?.id === id) {
      currentPage.value = response.data
    }
    return response.data
  }

  async function deletePage(id) {
    await pagesApi.delete(id)
    pages.value = pages.value.filter(t => t.id !== id)
  }

  return {
    pages,
    currentPage,
    loading,
    error,
    fetchPages,
    fetchPage,
    createPage,
    updatePage,
    deletePage,
  }
})

