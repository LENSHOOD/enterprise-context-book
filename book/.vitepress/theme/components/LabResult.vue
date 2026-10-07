<script setup lang="ts">
import { computed } from 'vue'
import LabFields from './LabFields.vue'
const props = defineProps<{ result: any }>()
const data = computed(() => props.result?.package || props.result || {})
const evidence = computed(() => data.value.evidence || data.value.documents || [])
const relations = computed(() => Array.isArray(data.value.relations) ? data.value.relations : [])
const rest = computed(() => Object.fromEntries(Object.entries(data.value).filter(([key]) => ![
  'evidence', 'documents', 'relations', 'wiki', 'enterprise', 'memories', 'performance',
  'enterprise_context', 'context_layers', 'principal', 'trace_id', 'manifest',
  'id', 'kind', 'owner', 'conditions', 'state', 'preview', 'receipt', 'verification',
  'snapshots', 'events', 'stale', 'package', 'approval_only',
].includes(key))))
const events = computed(() => props.result?.events || data.value.memories || [])
const stateNames: Record<string, string> = { opened: '已创建', diagnosing: '诊断中', action_proposed: '等待批准',
  approved: '已批准，尚未执行', verifying: '已执行，等待验证', resolved: '本次有限验证通过',
  needs_human: '需要人工处理', needs_clarification: '需要确认口径或范围', ready_for_review: '等待人工复核', reviewed: '已登记人工复核' }
const eventNames: Record<string, string> = { task_created: '创建任务', context_built: '构造上下文',
  definition_confirmed: '确认指标口径', reader_note: '记录工作笔记', human_reviewed: '登记人工复核',
  'action.prepare': '准备动作预览', 'action.confirm': '批准动作', 'action.reject': '拒绝动作',
  'action.execute': '取得执行回执', 'action.verify': '检查执行结果' }
</script>

<template>
  <div class="ns-result">
    <p v-if="result.stale" class="ns-warning">资源已更新。下面保存的是旧快照，请重新取证；已有动作预览的事故任务需要重新创建。</p>
    <div v-if="result.state" class="ns-state">{{ stateNames[result.state] || result.state }} <small>{{ result.id }}</small></div>
    <div v-if="result.conditions" class="ns-block"><h4>这次工作的约定</h4><LabFields :value="result.conditions" /></div>
    <div v-if="result.preview" class="ns-block"><h4>待确认的具体动作</h4><LabFields :value="result.preview" /></div>
    <div v-if="result.receipt" class="ns-block"><h4>执行回执</h4><LabFields :value="result.receipt" /></div>
    <div v-if="result.verification" class="ns-block"><h4>结果验证</h4><LabFields :value="result.verification" /><p class="ns-muted">队列下降只表示本次有限检查通过，不表示全部退款到账或根因已经修复。</p></div>
    <p v-if="result.package" class="ns-muted">下方材料来自最近一次构造的上下文快照。包内状态和允许工具记录的是当时情况；当前任务进展以上方状态与服务端检查为准。</p>
    <div v-if="data.performance" class="ns-block">
      <h4>同一口径下的经营表现</h4>
      <div class="ns-metrics"><div><small>H1</small><strong>{{ data.performance.total.h1 }}</strong></div><div><small>H2</small><strong>{{ data.performance.total.h2 }}</strong></div><div><small>变化额</small><strong>{{ data.performance.total.delta }}</strong></div><div><small>与目标的差距</small><strong>{{ data.performance.target_gap }}</strong></div></div>
      <p class="ns-muted">单位：{{ data.performance.total.unit }}。以下四种分解分别回到公司总额，不能跨维度相加。</p>
      <div v-for="view in data.performance.decomposition_views" :key="view.dimension" class="ns-table-wrap"><table><caption>{{ view.dimension }}</caption><thead><tr><th>分项</th><th>H1</th><th>H2</th><th>变化额</th></tr></thead><tbody><tr v-for="item in view.items" :key="item.label"><td>{{ item.label }}</td><td>{{ item.h1 }}</td><td>{{ item.h2 }}</td><td>{{ item.delta }}</td></tr></tbody></table></div>
    </div>
    <div v-if="evidence.length" class="ns-block"><h4>可检查的材料 · {{ evidence.length }}</h4>
      <details v-for="item in evidence" :key="item.id" class="ns-card">
        <summary>{{ item.title || item.id }} <small>{{ item.version }} {{ item.kind }}</small></summary>
        <p v-if="item.text || typeof item.evidence === 'string'" class="ns-evidence">{{ item.text || item.evidence }}</p>
        <p v-if="item.citation" class="ns-citation">{{ item.citation }}</p>
        <LabFields :value="Object.fromEntries(Object.entries(item).filter(([key]) => !['text', 'evidence', 'citation', 'title'].includes(key)))" />
      </details>
    </div>
    <p v-else-if="'evidence' in data || 'documents' in data" class="ns-muted">本次没有可展示的证据。请检查角色、时间、检索通道及问题范围。</p>
    <div v-if="data.enterprise?.length" class="ns-block"><h4>企业对象 · {{ data.enterprise.length }}</h4><p>从商业模式、目标和能力，继续查看组织、应用与数据。</p><LabFields :value="data.enterprise" /></div>
    <div v-if="relations.length" class="ns-block"><h4>对象之间的关系 · {{ relations.length }}</h4>
      <div class="ns-table-wrap"><table><thead><tr><th>起点</th><th>关系 →</th><th>终点</th><th>依据</th></tr></thead><tbody><tr v-for="(edge, i) in relations" :key="i"><td>{{ edge.from }}</td><td>{{ edge.type }}</td><td>{{ edge.to }}</td><td><details><summary>查看依据</summary><LabFields :value="edge" /></details></td></tr></tbody></table></div>
    </div>
    <div v-if="data.wiki" class="ns-block"><h4>按角色生成的 Wiki</h4><details v-for="page in data.wiki" :key="page.page_id" class="ns-card"><summary>{{ page.title }}</summary><div v-for="section in page.sections" :key="section.title"><h5>{{ section.title }}</h5><p>{{ section.summary }}</p></div><details><summary>来源与派生输入</summary><LabFields :value="page.inputs" /></details></details></div>
    <div v-if="events.length" class="ns-block"><h4>工作进展</h4><ol class="ns-timeline"><li v-for="(event, i) in events" :key="i"><strong>{{ eventNames[event.type] || event.type }}</strong><small>{{ event.actor }} {{ event.at }}</small><p v-if="event.text">{{ event.text }}</p><span v-if="event.evidence_status" class="ns-muted">用户声明，尚未核实</span></li></ol></div>
    <details v-if="result.snapshots?.length" class="ns-block"><summary>已保存的 {{ result.snapshots.length }} 份上下文快照</summary><div v-for="(snapshot, index) in result.snapshots" :key="index"><details><summary>第 {{ index + 1 }} 份 · {{ snapshot.manifest }}</summary><LabFields :value="snapshot" /></details></div></details>
    <div v-if="Object.keys(rest).length" class="ns-block"><h4>{{ result.package ? '本次材料的含义与边界' : '返回内容' }}</h4><LabFields :value="rest" /></div>
    <details v-if="data.enterprise_context" class="ns-block"><summary>企业结构与查证对象</summary><LabFields :value="data.enterprise_context" /></details>
    <details class="ns-raw"><summary>检查原始 JSON</summary><pre>{{ JSON.stringify(result, null, 2) }}</pre></details>
  </div>
</template>
