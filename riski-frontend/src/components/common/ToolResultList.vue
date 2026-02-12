<script setup lang="ts">
import { ref } from 'vue';
import type { ToolCallResult } from "@/types/RiskiAnswer.ts";

const props = defineProps<{
    result: ToolCallResult;
}>();

const isOpen = ref(false);

function toggle() {
    isOpen.value = !isOpen.value;
}

function truncate(text: string, maxLength: number = 60): string {
    return text.length > maxLength ? text.slice(0, maxLength) + "…" : text;
}
</script>

<template>
    <div class="tool-results">
        <button @click="toggle" class="toggle-button" type="button">
            <span class="toggle-icon">{{ isOpen ? '▼' : '▶' }}</span>
            <span class="summary-text">
                <template v-if="result.proposals.length > 0">
                    {{ result.proposals.length }} Anträge
                </template>
                <template v-if="result.proposals.length > 0 && result.documents.length > 0">, </template>
                <template v-if="result.documents.length > 0">
                    {{ result.documents.length }} Dokumente
                </template>
                gefunden
            </span>
        </button>

        <div v-show="isOpen" class="results-content">
            <div v-if="result.proposals.length > 0" class="result-group">
                <span class="result-label">Anträge</span>
                <ul class="result-list">
                    <li v-for="proposal in result.proposals" :key="proposal.identifier">
                        <a v-if="proposal.risUrl" :href="proposal.risUrl" target="_blank" rel="noopener noreferrer"
                            class="result-link" :title="proposal.name">{{ proposal.identifier }} – {{
                                truncate(proposal.name)
                            }}</a>
                        <span v-else>{{ proposal.identifier }} – {{ truncate(proposal.name) }}</span>
                    </li>
                </ul>
            </div>
            <div v-if="result.documents.length > 0" class="result-group">
                <span class="result-label">Dokumente</span>
                <ul class="result-list">
                    <li v-for="doc in result.documents" :key="doc.risUrl || doc.name">
                        <a v-if="doc.risUrl" :href="doc.risUrl" target="_blank" rel="noopener noreferrer"
                            class="result-link" :title="doc.name">{{ truncate(doc.name) }}</a>
                        <span v-else>{{ truncate(doc.name) }}</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<style scoped>
.tool-results {
    margin-top: 6px;
    padding-left: 24px;
    font-size: 0.88em;
}

.toggle-button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: inherit;
    color: #555;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
    width: 100%;
    text-align: left;
}

.toggle-button:hover {
    color: #333;
}

.toggle-icon {
    font-size: 0.75em;
    width: 12px;
    display: inline-block;
}

.results-content {
    margin-top: 6px;
    padding-left: 4px;
}

.result-group {
    margin-bottom: 8px;
}

.result-label {
    font-weight: 500;
    color: #555;
    font-size: 0.92em;
    display: block;
    margin-bottom: 2px;
}

.result-list {
    margin: 0 0 0 18px;
    padding: 0;
    list-style: disc;
}

.result-list li {
    margin-bottom: 2px;
}

.result-link {
    color: #005a9f;
    text-decoration: none;
}

.result-link:hover {
    text-decoration: underline;
    color: #003d6e;
}
</style>
