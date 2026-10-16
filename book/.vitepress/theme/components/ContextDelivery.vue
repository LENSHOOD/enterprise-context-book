<script setup lang="ts">
import LabFields from './LabFields.vue'
defineProps<{ package: any }>()
const kinds: Record<string, string> = { observed: '直接观察', computed: '可复算结果' }
</script>

<template>
  <div v-if="package.delivery_schema" class="ns-block">
    <h4>本次调查条件</h4>
    <LabFields :value="package.task_conditions" />
    <h4>已经查明什么</h4>
    <p v-if="!package.findings?.length" class="ns-muted">本轮尚未形成可独立核对的观察或计算结论；请检查返回材料和缺口。</p>
    <div v-for="finding in package.findings" :key="finding.id" class="ns-card">
      <strong>{{ kinds[finding.kind] || finding.kind }}</strong>
      <p>{{ finding.text }}</p><p class="ns-muted">{{ finding.scope }}</p>
      <details v-for="id in finding.evidence_ids" :key="id"><summary>核对这项发现的依据 · {{ id }}</summary>
        <LabFields :value="package.references?.find((item: any) => item.id === id) || { missing_reference: id }" />
      </details>
    </div>
    <details v-if="package.business_records"><summary>核对业务记录：申请 {{ package.business_records.applications }} 笔，尝试 {{ package.business_records.attempts }} 次</summary><LabFields :value="package.business_records" /></details>
    <div v-if="package.interpretation"><h4>待复核的解释</h4><p>{{ package.interpretation.text }}</p><p class="ns-muted">这段解释由模型或教学脚本提出，尚未逐句核验。</p></div>
    <h4>依据和下一步</h4>
    <p v-if="package.coverage?.status === 'partial'" class="ns-muted">本轮仍有明确缺口，材料覆盖尚不完整。</p>
    <p v-else class="ns-muted">材料覆盖尚未核验；已取得的材料和发现不代表满足本次任务的全部要求。</p>
    <ul v-if="package.missing?.length"><li v-for="(item, i) in package.missing" :key="i">{{ item }}</li></ul>
    <p v-else>尚未列出明确缺口，请按任务要求继续核对。空缺口列表不表示证据齐全，根因和业务完成情况也需另行核实。</p>
    <ul><li v-for="limit in package.investigation_limits" :key="limit">{{ limit }}</li></ul>
    <details v-if="package.continuation"><summary>与上轮引用相比，哪些需要重查</summary><LabFields :value="package.continuation" /></details>
    <details><summary>全部证据引用 · {{ package.references?.length || 0 }}</summary><LabFields :value="package.references" /></details>
  </div>
</template>
