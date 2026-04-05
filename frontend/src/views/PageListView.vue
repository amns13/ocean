<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { usePageStore } from "../stores/pages";

const router = useRouter();
const pageStore = usePageStore();

onMounted(() => {
  pageStore.fetchPages();
});

async function handleCreate() {
  try {
    const page = await pageStore.createPage({ title: "Untitled" });
    router.push({ name: "Page", params: { uid: page.uid, slug: page.slug } });
  } catch (err) {
    console.error("Failed to create page", err);
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
    <div class="header-card">
      <h2>My Pages</h2>
      <button @click="handleCreate" class="btn-new">New Page</button>
    </div>

    <!-- Error -->
    <p v-if="pageStore.error" class="error-message">{{ pageStore.error }}</p>

    <!-- Loading -->
    <div v-if="pageStore.loading" class="loading">Loading pages...</div>

    <!-- Empty State -->
    <div v-else-if="pageStore.pages.length === 0" class="empty-state">
      <p>No pages yet.</p>
    </div>

    <!-- Page List -->
    <ul v-else class="page-list">
      <li v-for="page in pageStore.pages" :key="page.uid" class="page-item">
        <div
          class="page-info"
          @click="
            router.push({
              name: 'Page',
              params: { uid: page.uid, slug: page.slug },
            })
          "
        >
          <span class="page-title">{{ page.title }}</span>
          <span class="page-meta">{{ page.slug }} &middot; {{ page.uid }}</span>
        </div>

        <div class="page-actions">
          <button @click="handleDelete(page.uid)" class="btn-delete">
            Delete
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.header-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-new {
  padding: 0.4rem 1rem;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-new:hover {
  background: #4338ca;
}

h2 {
  font-size: 1.4rem;
  font-weight: 700;
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
}

.page-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  cursor: pointer;
}

.page-title {
  font-size: 1rem;
}

.page-meta {
  font-size: 0.75rem;
  color: #888;
}

.page-actions {
  display: flex;
  gap: 0.5rem;
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
