<script setup lang="ts">
import LabFields from './LabFields.vue'
defineProps<{ comparison: any }>()
const labels: Record<string, string> = { evidence_ready: '本轮必要证据已取得', incomplete: '仍缺必要证据', not_run: '未执行', budget_insufficient: '估计预算不足' }
</script>

<template>
  <div class="ns-block">
    <h4>先确定要查清什么</h4>
    <p>{{ comparison.logical_plan.goal }}</p>
    <p>队列：{{ comparison.logical_plan.scope.queue }}；环境：{{ comparison.logical_plan.scope.environment }}</p>
    <ul><li v-for="requirement in comparison.logical_plan.requirements" :key="requirement">{{ requirement }}</li></ul>
    <h4>执行前比较计划</h4>
    <p>{{ comparison.cost_basis }}</p>
    <p>预选：{{ comparison.plans.find((p: any) => p.id === comparison.selected)?.label || '无预算内计划' }}。实际核验：{{ labels[comparison.status] }}</p>
    <p class="ns-muted">{{ comparison.comparison_notice }}</p>
    <div class="ns-table-wrap"><table><thead><tr><th>候选路线</th><th>估计单位</th><th>实际工具调用</th><th>实际返回条目</th><th>核验结果</th></tr></thead>
      <tbody><tr v-for="plan in comparison.plans" :key="plan.id"><td>{{ plan.label }}</td><td>{{ plan.estimated_units }}</td><td>{{ plan.execution?.tool_calls ?? '—' }}</td><td>{{ plan.execution?.returned_items ?? '—' }}</td><td>{{ labels[plan.status] }}</td></tr></tbody>
    </table></div>
    <p class="ns-muted">返回条目是各次调用返回的文档、关系和观察数量之和，包含重复；不是扫描量或独立证据数。实际耗时只统计读取调用，不能据此推算生产提速比例。</p>
    <details v-for="plan in comparison.plans" :key="plan.id" class="ns-card">
      <summary>{{ plan.label }} · 查看执行与依据</summary>
      <p v-if="plan.reason">{{ plan.reason }}</p>
      <template v-if="plan.package">
        <ul><li v-for="check in plan.coverage.checks" :key="check.requirement">{{ check.met ? '已取得' : '待补充' }}：{{ check.requirement }}</li></ul>
        <ol><li v-for="(step, index) in plan.package.query_plan" :key="index">{{ step.tool }} · {{ step.purpose }}</li></ol>
        <p>正文字符返回量：{{ plan.execution.evidence_chars }}；工具读取耗时：{{ plan.execution.elapsed_ms }} ms。</p>
        <details><summary>查看上下文包、原文引用和缺口</summary><LabFields :value="plan.package" /></details>
      </template>
    </details>
    <p class="ns-muted">两条路线按同一组要求核验。取得这些材料不代表已经查明根因、获准重放或完成退款。</p>
  </div>
</template>
