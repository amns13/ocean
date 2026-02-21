<template>
  <div>
    <NavBar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import NavBar from "./NavBar.vue";
</script>

<style scoped>
.main-content {
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
</style>
