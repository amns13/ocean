<script setup>
// ---------------------------------------------------------------------------
// PageEditor
// ---------------------------------------------------------------------------
// The WYSIWYG surface, built on Milkdown Crepe (the official
// batteries-included editor: slash menu, table editing, link tooltip,
// task lists, code highlighting, drag handle -- all bundled).
//
// Crepe is imperative (its own class), not the provider/useEditor model, so
// this is a single self-contained component -- no MilkdownProvider/child
// split is needed anymore.
//
// ---------------------------------------------------------------------------

import { ref, onMounted, onBeforeUnmount } from "vue";
import { Crepe, CrepeFeature } from "@milkdown/crepe";
import { languages } from "@codemirror/language-data";
import "@milkdown/crepe/theme/common/style.css";
import "@milkdown/crepe/theme/nord.css";

import { blocksApi } from "../api";

const props = defineProps({
  pageUid: { type: String, required: true },
  // Markdown the page currently holds (empty string for a brand-new page).
  initialMarkdown: { type: String, default: "" },
  // uid of the Block this markdown lives in, or null if the page has no
  // block yet (first save will create one).
  initialBlockUid: { type: String, default: null },
});

// The element Crepe mounts into.
const rootRef = ref(null);

// Plain (non-reactive) on purpose: nothing in the template depends on these,
// so reactivity would only add noise.
//
//   crepe             -- the editor instance; null until created / after
//                         destroy. Every entry point null-checks it.
//   blockUid          -- null until a block exists on the server.
//   lastSavedMarkdown -- the exact markdown last persisted; lets save() skip
//                         the request when nothing changed.
let crepe = null;
let blockUid = props.initialBlockUid;
let lastSavedMarkdown = props.initialMarkdown;

onMounted(async () => {
  crepe = new Crepe({
    root: rootRef.value,
    defaultValue: props.initialMarkdown,
    // Everything is on by default except TopBar/AI. We only turn OFF what we
    // don't want yet: ImageBlock (no upload backend) and Latex ( togglable
    // in future).
    features: {
      [CrepeFeature.ImageBlock]: false,
      [CrepeFeature.Latex]: false,
    },
    featureConfigs: {
      // Crepe ships NO code-block grammars by default (languages = []), so
      // without this code blocks have no syntax highlighting. These are
      // lazy LanguageDescription objects: each grammar is a separate chunk
      // loaded on demand the first time a code block uses that language --
      // nothing here is added to the editor's main bundle.
      [CrepeFeature.CodeMirror]: { languages },
    },
  });
  await crepe.create();
});

// Serialize the current document to markdown and persist it. Linear on
// purpose -- readability over cleverness:
//   1. editor not ready yet            -> nothing to do
//   2. markdown unchanged since save   -> skip the request
//   3. no block + empty doc            -> don't create an empty block
//   4. no block + has content          -> POST, remember the new uid
//   5. block exists                    -> PATCH its content
// On failure we deliberately leave lastSavedMarkdown untouched so the next
// trigger (blur / unmount) retries the same content.
async function save() {
  if (!crepe) return;

  const markdown = crepe.getMarkdown();
  if (markdown === lastSavedMarkdown) return;

  try {
    if (blockUid === null) {
      if (markdown.trim() === "") return;
      const { data } = await blocksApi.create({
        page: props.pageUid,
        content: markdown,
      });
      blockUid = data.uid;
    } else {
      await blocksApi.update(blockUid, { content: markdown });
    }
    lastSavedMarkdown = markdown;
  } catch {
    // Swallowed so a failed save never breaks a blur/navigation. The
    // unchanged lastSavedMarkdown means the next trigger will retry.
    console.error("Failed to save page content");
  }
}

// Save on the way out, THEN tear the editor down. Order matters:
// getMarkdown() after destroy() is invalid.
onBeforeUnmount(async () => {
  await save();
  await crepe?.destroy();
  crepe = null;
});
</script>

<template>
  <!--
    focusout (not blur) because blur does not bubble: this fires when focus
    leaves the editor entirely, which is our "save on blur" trigger. Spurious
    calls are harmless -- save() skips when the markdown is unchanged.
  -->
  <div ref="rootRef" class="page-editor-root" @focusout="save" />
</template>

<style scoped>
.page-editor-root {
  width: 100%;
}
</style>
