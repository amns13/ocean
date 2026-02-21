<script setup>
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { usePageStore } from "../stores/pages";

const router = useRouter();
const route = useRoute();
const pageStore = usePageStore();

const editing = ref(false);
const saving = ref(false);
const updateError = ref(null);
const editForm = ref({ title: "", description: "", completed: false });

onMounted(() => {
  pageStore.fetchPage(route.params.id);
});

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString();
}

function startEditing() {
  const page = pageStore.currentPage;
  editForm.value = {
    title: page.title,
    description: page.description || "",
    completed: page.completed,
  };
  editing.value = true;
}

function cancelEditing() {
  editing.value = false;
  updateError.value = null;
}

async function handleToggle() {
  await pageStore.updatePage(pageStore.currentPage.id, {
    completed: !pageStore.currentPage.completed,
  });
}

async function handleUpdate() {
  saving.value = true;
  updateError.value = null;
  try {
    await pageStore.updatePage(pageStore.currentPage.id, editForm.value);
    editing.value = false;
  } catch (err) {
    updateError.value = "Failed to save changes. Please try again.";
  } finally {
    saving.value = false;
  }
}

async function handleDelete() {
  if (!confirm("Are you sure you want to delete this page?")) return;
  try {
    await pageStore.deletePage(pageStore.currentPage.id);
    router.push({ name: "PageList" });
  } catch (err) {
    console.error("Failed to delete page", err);
  }
}
</script>

<template>
  <div>
    <!-- Back Button -->
    <button @click="router.push({ name: 'PageList' })" class="btn-back">
      ← Back to pages
    </button>

    <!-- Loading -->
    <div v-if="pageStore.loading" class="loading">Loading...</div>

    <!-- Error -->
    <div v-else-if="pageStore.error" class="error-message">
      {{ pageStore.error }}
    </div>

    <!-- Page Detail -->
    <div v-else-if="pageStore.currentPage" class="detail-card">
      <!-- View Mode -->
      <div v-if="!editing">
        <div class="detail-header">
          <div class="title-row">
            <input
              type="checkbox"
              :checked="pageStore.currentPage.completed"
              @change="handleToggle"
              class="page-checkbox"
            />
            <h2 :class="{ completed: pageStore.currentPage.completed }">
              {{ pageStore.currentPage.title }}
            </h2>
          </div>
          <span
            class="status-badge"
            :class="pageStore.currentPage.completed ? 'done' : 'pending'"
          >
            {{ pageStore.currentPage.completed ? "Completed" : "Pending" }}
          </span>
        </div>

        <p class="description">
          {{ pageStore.currentPage.description || "No description provided." }}
        </p>

        <div class="meta">
          <span
            >Created: {{ formatDate(pageStore.currentPage.created_at) }}</span
          >
          <span v-if="pageStore.currentPage.updated_at">
            Updated: {{ formatDate(pageStore.currentPage.updated_at) }}
          </span>
        </div>

        <div class="detail-actions">
          <button @click="startEditing" class="btn-primary">Edit</button>
          <button @click="handleDelete" class="btn-delete">Delete</button>
        </div>
      </div>

      <!-- Edit Mode -->
      <div v-else>
        <h2 class="edit-heading">Edit Page</h2>
        <form @submit.prevent="handleUpdate">
          <div class="form-group">
            <label for="title">Title</label>
            <input id="title" v-model="editForm.title" type="text" required />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              v-model="editForm.description"
              rows="4"
              placeholder="Add a description (optional)"
            />
          </div>

          <div class="form-group checkbox-group">
            <input
              id="completed"
              v-model="editForm.completed"
              type="checkbox"
              class="page-checkbox"
            />
            <label for="completed">Mark as completed</label>
          </div>

          <p v-if="updateError" class="error-message">{{ updateError }}</p>

          <div class="edit-actions">
            <button type="submit" :disabled="saving" class="btn-primary">
              {{ saving ? "Saving..." : "Save changes" }}
            </button>
            <button type="button" @click="cancelEditing" class="btn-cancel">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
<style scoped>
.btn-back {
  background: none;
  border: none;
  color: #4f46e5;
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0;
  margin-bottom: 1.25rem;
  transition: color 0.2s;
}

.btn-back:hover {
  color: #4338ca;
}

.loading,
.error-message {
  text-align: center;
  padding: 2rem;
  color: #888;
}

.error-message {
  color: #dc2626;
}

.detail-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 2rem;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #4f46e5;
  flex-shrink: 0;
}

h2 {
  font-size: 1.4rem;
  font-weight: 700;
}

h2.completed {
  text-decoration: line-through;
  color: #999;
}

.status-badge {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  white-space: nowrap;
}

.status-badge.done {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.pending {
  background: #fef9c3;
  color: #ca8a04;
}

.description {
  color: #555;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  overflow-wrap: anywhere;
}

.meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.8rem;
  color: #aaa;
  margin-bottom: 1.75rem;
}

.detail-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-heading {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 0.6rem;
}

label {
  font-size: 0.9rem;
  font-weight: 500;
}

input[type="text"],
textarea {
  padding: 0.65rem 0.85rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
  resize: vertical;
}

input[type="text"]:focus,
textarea:focus {
  border-color: #4f46e5;
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
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
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-cancel {
  padding: 0.65rem 1.25rem;
  background: transparent;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #aaa;
  color: #333;
}

.btn-delete {
  padding: 0.65rem 1.25rem;
  background: transparent;
  color: #dc2626;
  border: 1px solid #dc2626;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #dc2626;
  color: white;
}
</style>
