<template>
  <div class="app">
    <header class="header">
      <span class="logo">📚 RAG Chatbot</span>
    </header>
    <main class="main">
      <DocumentPanel />
      <ChatPanel />
    </main>
  </div>
</template>

<script setup>
import DocumentPanel from './components/DocumentPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

.app { display: flex; flex-direction: column; height: 100vh; }

.header {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #dee2e6;
  flex-shrink: 0;
}
.logo { font-weight: 700; font-size: 1rem; color: #4361ee; }

.main { display: flex; flex: 1; overflow: hidden; }
</style>
