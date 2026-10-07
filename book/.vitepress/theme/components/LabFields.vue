<script setup lang="ts">
defineProps<{ value: any }>()
const names: Record<string, string> = {
  goal: '任务目标', scope: '适用范围', completion: '完成条件', time: '时间',
  from: '起点', to: '终点', type: '类型', evidence: '依据', citation: '来源引用',
  version: '版本', valid_from: '开始生效', valid_to: '失效时间', observed_at: '观察时间',
  task_conditions: '任务条件', missing: '证据缺口', hypotheses: '待验证假设',
  query_contract: '指标确认契约', metric_definition: '指标定义', source_snapshot: '数据快照',
  semantic_contract: '语义契约', entity_types: '对象类型', relations: '关系契约',
  authorized_documents: '可见候选数', degraded_channels: '关闭的检索通道',
  h1: 'H1', h2: 'H2', delta: '变化额', change_rate: '变化率', unit: '单位',
  total: '全公司', decomposition_views: '各维度独立分解', target_gap: '与目标的差距',
  label: '名称', dimension: '维度', items: '分项', sources: '来源',
  observations: '运行观察', task_state: '构造时任务状态', allowed_tools: '构造时允许工具',
  captured_at: '上下文采集时间',
  task_id: '任务ID', tool: '工具', tenant_scope: '租户范围', observation_revision: '观察版本',
  preview_id: '预览ID', tenant: '租户', user_id: '用户ID', role: '角色',
  queue_depth: '队列深度', provider_error_rate: '支付方错误率', ttl_seconds: '有效秒数',
  message_count: '重放条数', target_queue: '目标队列', expires_at: '到期时间',
  prepared_by: '准备者', params_hash: '参数散列', side_effects: '副作用',
  receipt_id: '回执', replayed: '已重放条数', verified: '验证通过', observation: '验证观察',
  before_queue_depth: '执行前队列深度', executed_by: '执行者', executed_at: '执行时间',
  owner: '责任人', name: '名称', state: '状态', status: '状态', text: '说明',
  manifest: '资源版本', before_manifest: '更新前版本', after_manifest: '更新后版本',
  invalidated_tasks: '待重新取证的任务', rule: '更新规则',
  declared_and_evidenced: '声明与证据一致', declared_not_evidenced: '声明缺少证据',
  evidenced_not_declared: '证据尚未登记到声明',
}
const simple = (v: any) => v === null || typeof v !== 'object'
const display = (v: any) => v === null ? '未设置' : v === true ? '是' : v === false ? '否' : String(v)
</script>

<template>
  <span v-if="simple(value)">{{ display(value) }}</span>
  <span v-else-if="Object.keys(value).length === 0" class="ns-muted">无</span>
  <ol v-else-if="Array.isArray(value)" class="ns-field-list">
    <li v-for="(item, index) in value" :key="index">
      <span v-if="simple(item)">{{ display(item) }}</span>
      <details v-else><summary>{{ item.title || item.name || item.label || item.id || item.type || `第 ${index + 1} 项` }}</summary><LabFields :value="item" /></details>
    </li>
  </ol>
  <dl v-else class="ns-fields">
    <template v-for="(item, key) in value" :key="key">
      <dt>{{ names[String(key)] || key }}</dt>
      <dd><LabFields v-if="simple(item)" :value="item" /><details v-else><summary>展开{{ Array.isArray(item) ? ` ${item.length} 项` : '' }}</summary><LabFields :value="item" /></details></dd>
    </template>
  </dl>
</template>
