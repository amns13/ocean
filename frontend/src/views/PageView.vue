<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { pagesApi, blocksApi } from "../api";

import { MdEditor } from "md-editor-v3";
import "md-editor-v3/lib/style.css";

const route = useRoute();

const page = ref(null);
const blocks = ref([]);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const [pageRes, blocksRes] = await Promise.all([
      pagesApi.getOne(route.params.uid),
      pagesApi.getPageBlocks(route.params.uid),
    ]);
    page.value = pageRes.data;
    blocks.value =
      blocksRes.data.length > 0 ? blocksRes.data : [{ uid: null, content: "" }];
  } catch {
    error.value = "Failed to load page";
  } finally {
    loading.value = false;
    nextTick(() => {
      if (titleRef.value) autoResize(titleRef.value);
    });
  }
});

async function saveTitle() {
  await pagesApi.update(route.params.uid, { title: page.value.title });
}

const titleRef = ref(null);
const blockRefs = ref([]);

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}

async function onBlockBlur(index) {
  const block = blocks.value[index];
  if (block.uid !== null) {
    // TODO: Only send content if content has actually changed
    const response = await blocksApi.update(block.uid, {
      content: block.content,
    });
    blocks.value[index] = response.data;
  } else {
    const response = await blocksApi.create({
      page: page.value.uid,
      content: block.content,
    });
    blocks.value[index] = response.data;
  }
}

const handleSave = (index, value, html) => {
  onBlockBlur(index);
};
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
    <div class="blocks">
      <MdEditor
        language="en-US"
        v-for="(block, index) in blocks"
        :key="block.uid"
        :ref="(el) => (blockRefs[index] = el)"
        v-model="block.content"
        class="block"
        @blur="onBlockBlur(index)"
        @onSave="(value, html) => handleSave(index, value, html)"
      />
    </div>
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
  max-width: 680px;
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

.blocks {
  display: flex;
  flex-direction: column;
}

.block {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 1rem;
  font-family: inherit;
  line-height: 1.6;
  padding: 0.15rem 0;
  color: #1a1a1a;
  resize: none;
  overflow: hidden;
}
</style>
