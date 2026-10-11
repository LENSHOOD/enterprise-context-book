<script setup lang="ts">
import LabFields from './LabFields.vue'
const props = defineProps<{ result: any }>()
function name(id: string) {
  return props.result.documents.find((item: any) => item.id === id)?.title || id
}
</script>

<template>
  <div class="ns-discovery">
    <div class="ns-block">
      <h4>本次退款查证过程</h4>
      <p>下面按执行顺序展示固定路线的结果。找到资料只表示取得了依据，尚未确认根因或完成业务处理。</p>
      <ol class="ns-timeline">
        <li v-for="(step, index) in result.discovery_steps" :key="index">
          <strong>{{ index + 1 }}. {{ step.title }}</strong>
          <small>{{ step.status === 'complete' ? '已取得结果' : '有待补充' }}</small>
          <p>{{ step.purpose }}</p><p>{{ step.summary }}</p>
          <details v-if="step.object_ids.length"><summary>查看这一步找到的对象 · {{ step.object_ids.length }}</summary>
            <ul><li v-for="id in step.object_ids" :key="id">{{ name(id) }} <code>{{ id }}</code></li></ul>
          </details>
          <details><summary>查看本步调用与条件</summary><p>{{ step.tool }}</p><LabFields :value="step.args" /></details>
        </li>
      </ol>
    </div>
    <div class="ns-block">
      <h4>当前运行观察</h4>
      <div v-for="item in result.observations" :key="item.resource">
        <div class="ns-metrics"><div><small>队列积压（条）</small><strong>{{ item.queue_depth }}</strong></div><div><small>消费延迟（秒）</small><strong>{{ item.consumer_lag_seconds }}</strong></div><div><small>支付方错误率</small><strong>{{ item.provider_error_rate * 100 }}%</strong></div></div>
        <p class="ns-citation">资源 {{ item.resource }} · 采样 {{ item.observed_at }} · 有效期 {{ item.ttl_seconds }} 秒 · 观察版本 {{ item.revision }}</p>
      </div>
      <p v-if="!result.observations.length" class="ns-muted">本次没有取得新鲜的运行观察，不能据此判断队列没有积压。</p>
    </div>
    <div class="ns-block">
      <h4>处置手册与下一步</h4>
      <p v-if="result.runbooks.length">{{ result.runbooks.map(name).join('、') }}。在下方“可检查的材料”中展开手册，阅读正文和来源。</p>
      <p v-else>本次没有取得可见的处置手册。</p>
      <ul v-if="result.missing.length" class="ns-warning"><li v-for="item in result.missing" :key="item">{{ item }}</li></ul>
      <p>{{ result.next_step }}</p>
      <p class="ns-muted">这条路线尚未自动接入 C9 的规划或 C6 的任务包。C9 练习助手选择下一步，C6 练习批准和执行；本实验展示资料怎样相连、当前状态怎样取得。</p>
    </div>
  </div>
</template>
