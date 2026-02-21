<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { usePageStore } from "../stores/pages";

const router = useRouter();
const pageStore = usePageStore();

const newTitle = ref("");
const creating = ref(false);

onMounted(() => {
  pageStore.fetchPages();
});

async function handleCreate() {
  if (!newTitle.value.trim()) return;
  creating.value = true;
  try {
    await pageStore.createPage({ title: newTitle.value.trim() });
    newTitle.value = "";
  } catch (err) {
    console.error("Failed to create page", err);
  } finally {
    creating.value = false;
  }
}

async function handleToggle(page) {
  try {
    await pageStore.updatePage(page.id, { completed: !page.completed });
  } catch (err) {
    console.error("Failed to update page", err);
  }
}

async function handleDelete(id) {
  if (!confirm("Are you sure you want to delete this page?")) return;
  try {
    await pageStore.deletePage(id);
  } catch (err) {
    console.error("Failed to delete page", err);
  }
}
</script>

<template>
  <div>
    <!-- Create Page Form -->
    <div class="create-card">
      <h2>My Pages</h2>
      <form @submit.prevent="handleCreate" class="create-form">
        <input
          v-model="newTitle"
          type="text"
          placeholder="What needs to be done?"
          required
        />
        <button type="submit" :disabled="creating" class="btn-primary">
          {{ creating ? "Adding..." : "Add Page" }}
        </button>
      </form>
    </div>

    <!-- Error -->
    <p v-if="pageStore.error" class="error-message">{{ pageStore.error }}</p>

    <!-- Loading -->
    <div v-if="pageStore.loading" class="loading">Loading pages...</div>

    <!-- Empty State -->
    <div v-else-if="pageStore.pages.length === 0" class="empty-state">
      <p>No pages yet. Add one above to get started!</p>
    </div>

    <!-- Page List -->
    <ul v-else class="page-list">
      <li
        v-for="page in pageStore.pages"
        :key="page.id"
        class="page-item"
        :class="{ completed: page.completed }"
      >
        <input
          type="checkbox"
          :checked="page.completed"
          @change="handleToggle(page)"
          class="page-checkbox"
        />

        <span class="page-title">{{ page.title }}</span>

        <div class="page-actions">
          <button
            @click="
              router.push({ name: 'PageDetail', params: { id: page.id } })
            "
            class="btn-view"
          >
            View
          </button>
          <button @click="handleDelete(page.id)" class="btn-delete">
            Delete
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.create-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 1.5rem;
}

h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.create-form {
  display: flex;
  gap: 0.75rem;
}

.create-form input {
  flex: 1;
  padding: 0.65rem 0.85rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.create-form input:focus {
  border-color: #4f46e5;
}

.btn-primary {
  padding: 0.65rem 1.25rem;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.loading {
  text-align: center;
  color: #888;
  padding: 2rem;
}

.empty-state {
  text-align: center;
  color: #888;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.page-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.page-item {
  background: white;
  padding: 1rem 1.25rem;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: opacity 0.2s;
}

.page-item.completed {
  opacity: 0.6;
}

.page-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #4f46e5;
  flex-shrink: 0;
}

.page-title {
  flex: 1;
  font-size: 1rem;
}

.page-item.completed .page-title {
  text-decoration: line-through;
  color: #999;
}

.page-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-view {
  padding: 0.35rem 0.85rem;
  background: transparent;
  color: #4f46e5;
  border: 1px solid #4f46e5;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-view:hover {
  background: #4f46e5;
  color: white;
}

.btn-delete {
  padding: 0.35rem 0.85rem;
  background: transparent;
  color: #dc2626;
  border: 1px solid #dc2626;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #dc2626;
  color: white;
}
</style>
