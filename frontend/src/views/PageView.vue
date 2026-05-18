<script setup>
// ---------------------------------------------------------------------------
// PageView
// ---------------------------------------------------------------------------
// The page screen. Owns:
//   - loading / error UI
//   - title input (saved on blur, separate from the editor)
//   - mounting <PageEditor> once the page + its block have loaded
//
// Why the editor lives in a child component:
// Milkdown reads its initial document once, at setup time. Mounting
// <PageEditor> only in the v-else branch (after loading finishes) means it
// is created with the final markdown already known -- no flicker, no
// re-mounting Milkdown on the same instance (which ProseMirror dislikes).
// ---------------------------------------------------------------------------

import { ref, onMounted, nextTick, defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";
import { pagesApi } from "../api";

// Lazy: the editor (Crepe + CodeMirror grammars) is a large bundle and is
// only ever rendered after the page loads (the v-else branch below), so it
// is split into its own chunk fetched on first page open.
const PageEditor = defineAsyncComponent(
  () => import("../components/PageEditor.vue"),
);

const route = useRoute();

const page = ref(null);
const loading = ref(true);
const error = ref(null);
const titleRef = ref(null);

// Passed straight to <PageEditor>. Set before loading flips to false, so the
// editor mounts already knowing its content.
const initialMarkdown = ref("");
const initialBlockUid = ref(null);

onMounted(async () => {
  try {
    const [pageRes, blocksRes] = await Promise.all([
      pagesApi.getOne(route.params.uid),
      pagesApi.getPageBlocks(route.params.uid),
    ]);
    page.value = pageRes.data;

    // A page has 0 or 1 block in Phase 1. Take the first if present.
    const [block] = blocksRes.data;
    if (block) {
      initialMarkdown.value = block.content;
      initialBlockUid.value = block.uid;
    }
  } catch {
    error.value = "Failed to load page";
  } finally {
    loading.value = false;
    nextTick(() => {
      if (titleRef.value) autoResize(titleRef.value);
    });
  }
});

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}

async function saveTitle() {
  if (!page.value) return;
  await pagesApi.update(route.params.uid, { title: page.value.title });
}
</script>

<template>
  <div v-if="loading" class="loading">Loading...</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <div v-else class="page-editor">
    <textarea
      ref="titleRef"
      v-model="page.title"
      class="page-title"
      placeholder="New Page"
      rows="1"
      @blur="saveTitle"
      @input="autoResize($event.target)"
    />
    <hr />
    <PageEditor
      :page-uid="page.uid"
      :initial-markdown="initialMarkdown"
      :initial-block-uid="initialBlockUid"
      class="page-editor-surface"
    />
  </div>
</template>

<style scoped>
.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #888;
}

.page-editor {
  margin: 0 auto;
  padding: 3rem 1rem;
}

.page-title {
  width: 100%;
  font-size: 2.5rem;
  font-weight: 700;
  font-family: inherit;
  border: none;
  outline: none;
  background: transparent;
  margin-bottom: 1rem;
  color: #1a1a1a;
  resize: none;
  overflow: hidden;
}

.page-editor-surface {
  font-size: 1rem;
  line-height: 1.6;
  color: #1a1a1a;
}
</style>
