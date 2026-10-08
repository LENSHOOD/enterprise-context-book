<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import catalogData from '../generated/northstar.json'
import LabFields from './LabFields.vue'
const props = defineProps<{ kind: 'resource' | 'query' }>()
const catalog: any = catalogData
const resource = computed(() => props.kind === 'resource')
const role = ref(resource.value ? 'product' : 'sre')
const mode = ref('fixture'), connected = ref(false), session = ref(false), busy = ref(false)
const error = ref(''), notice = ref('公开阅读模式'), result = ref<any>(null)
const records = ref<any[]>([]), sources = ref<any[]>([]), selected = ref(''), sourceId = ref('')
const raw = ref(catalog.assistant_source), goal = ref('退款积压需要检查哪些材料？')
const answer = ref(''), review = ref(''), sourceIndex = ref(0)
const preview = ref(false)
const snippets = computed(() => catalog.assistants[props.kind].sources)
const snippet = computed(() => snippets.value[sourceIndex.value])
const canRun = computed(() => connected.value && session.value && !busy.value)
const states: Record<string, string> = { drafting: '等待生成建议', ready: '可以继续取证', needs_confirmation: '等待确认',
  needs_review: '候选已通过结构检查，等待人工审核', ready_for_review: '材料已交付，等待请求方复核',
  published: '已发布到当前实验空间', rejected: '已拒绝', budget_exhausted: '已达到步骤预算' }
async function request(path: string, payload: any) {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Northstar-Lab': '1' },
    body: JSON.stringify(payload), signal: AbortSignal.timeout(60000) })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error || `请求失败 ${response.status}`)
  return value
}
async function refresh() {
  const data = await request('/api/lab', { op: 'assist.list', role: role.value })
  records.value = resource.value ? data.drafts : data.requests
  sources.value = data.sources; session.value = true
  if (selected.value) result.value = records.value.find(r => r.id === selected.value) || null
}
async function run(op: string, values: any = {}) {
  if (!canRun.value) return
  busy.value = true; error.value = ''; preview.value = false
  try {
    const data = await request('/api/lab', { op, role: role.value, ...values })
    if (op === 'resource.register' || op === 'resource.revise') sourceId.value = data.id
    else if (data.id) { selected.value = data.id; result.value = data }
    await refresh()
  } catch (e: any) { error.value = e.message } finally { busy.value = false }
}
async function connect(fresh: boolean) {
  busy.value = true; error.value = ''; preview.value = false
  try {
    if (fresh) {
      await request('/api/session', {}); selected.value = ''; sourceId.value = ''; result.value = null
      window.dispatchEvent(new Event('northstar-space-created'))
    }
    await refresh(); notice.value = '本地 Python 已连接 · 记录自动保存'
  } catch (e: any) { error.value = e.message } finally { busy.value = false }
}
function selectRecord() { preview.value = false; result.value = records.value.find(x => x.id === selected.value) || null }
function selectSource() { raw.value = sources.value.find(x => x.id === sourceId.value)?.text || catalog.assistant_source }
async function changed() {
  if (!connected.value || busy.value) return
  selected.value = ''; sourceId.value = ''; result.value = null
  try { await refresh() } catch { session.value = false }
}
watch(role, changed)
onMounted(async () => {
  window.addEventListener('northstar-space-created', changed)
  if (!['localhost', '127.0.0.1'].includes(location.hostname)) return
  try {
    const response = await fetch('/api/health')
    if (!response.ok) return
    const health = await response.json()
    if (health.service !== 'northstar-lab' || health.source_revision !== catalog.source_revision) return
    connected.value = true; notice.value = '本地服务就绪'
    try { await refresh() } catch { /* Reader creates a space. */ }
  } catch { /* Static site remains readable. */ }
})
onUnmounted(() => window.removeEventListener('northstar-space-created', changed))
</script>

<template>
  <section class="northstar-lab" :aria-label="resource ? 'C8 资源建设助手' : 'C9 上下文调查助手'">
    <div class="ns-heading"><span class="ns-eyebrow">{{ resource ? 'C8 · 资源建设' : 'C9 · 上下文调查' }}</span><span class="ns-badge">{{ notice }}</span></div>
    <h3>{{ resource ? '从原始材料提出候选，再审核发布' : '从一个问题开始，逐步准备上下文' }}</h3>
    <p>{{ resource ? '先登记原文，再生成对象类型、服务关系和能力问题。检查引用与模型后，由维护者审核发布；原文件仍保留。' : '先确认目标与范围，再让助手每次选择一个取证步骤。查看它读到了什么、为什么继续，最后交付材料与缺口。' }}</p>
    <div class="ns-connection"><template v-if="connected"><button :disabled="busy" @click="connect(true)">新建实验空间</button><button :disabled="busy" @click="connect(false)">恢复已有空间</button></template><p v-else>在本地执行 <code>npm run lab</code>，再打开终端地址，才能实际运行。公开站点只展示示例和代码。</p>
      <button :disabled="busy" @click="result = catalog.assistants[props.kind].sample; preview = true">查看构建时示例</button></div>
    <div class="ns-controls"><label class="ns-label">模拟角色<select v-model="role" :disabled="busy"><option value="product">产品／资料维护者</option><option value="sre">值班 SRE</option><option value="developer">开发者</option><option value="executive">经营负责人</option><option value="support">客服</option></select></label>
      <label class="ns-label">新记录的决策方式<select v-model="mode" :disabled="busy"><option value="fixture">脚本演示（不调用模型）</option><option value="http">真实模型（使用服务端配置）</option></select></label></div>
    <p class="ns-muted">脚本演示只展示固定路线，不具备语言理解能力。真实模型会接收当前角色可见的材料；模型地址和密钥只在本地服务端配置。已有记录沿用创建时的模式。</p>
    <template v-if="resource">
      <label class="ns-label">原始说明材料<textarea v-model="raw" :disabled="busy" maxlength="6000" rows="5" /></label>
      <div class="ns-controls"><button :disabled="!canRun || !raw.trim()" @click="run('resource.register', { text: raw })">登记为新来源</button></div>
      <label class="ns-label">已登记的来源<select v-model="sourceId" :disabled="busy" @change="selectSource"><option value="" disabled>请选择来源</option><option v-for="s in sources" :key="s.id" :value="s.id">{{ s.id }} · r{{ s.revision }}</option></select></label>
      <div class="ns-controls"><button :disabled="!canRun || !sourceId" @click="run('resource.revise', { id: sourceId, text: raw })">保存原文新版本</button><button :disabled="!canRun || !sourceId" @click="run('resource.propose', { id: sourceId, mode })">建立资源建设任务</button></div>
    </template>
    <template v-else><label class="ns-label">外部用户或 Agent 的上下文请求<textarea v-model="goal" :disabled="busy" /></label><button :disabled="!canRun || !goal.trim()" @click="run('assist.start', { goal, mode })">建立调查请求</button></template>
    <label class="ns-label">当前角色的记录<select v-model="selected" :disabled="busy" @change="selectRecord"><option value="" disabled>请选择记录</option><option v-for="r in records" :key="r.id" :value="r.id">{{ r.id }} · {{ states[r.state] || r.state }}</option></select></label>
    <div v-if="result" class="ns-output">
      <p class="ns-origin">{{ preview ? '构建时脚本演示，不是实时模型输出' : '本地 Python 返回；业务和身份仍为教学模拟' }}</p>
      <div class="ns-state">{{ states[result.state] || result.state }}<small>{{ result.id }}</small></div>
      <p v-if="result.stale && result.state !== 'published'" class="ns-warning">资源版本已变化。旧记录保留；请建立新请求或新候选。</p>
      <p>决策方式：{{ result.provider?.label || result.mode }} · 剩余模型步骤：{{ result.remaining_steps }}</p>
      <button v-if="['drafting','ready'].includes(result.state)" :disabled="!canRun || preview || result.stale" @click="run('assist.step', { id: result.id, kind: props.kind })">{{ result.state === 'drafting' ? '生成本步建议' : '执行下一步取证' }}</button>
      <div v-if="result.pending" class="ns-block"><h4>请确认具体内容</h4>
        <LabFields v-if="result.pending.conditions" :value="result.pending.conditions" />
        <LabFields v-if="result.pending.metric_contract" :value="result.pending.metric_contract" />
        <p v-if="result.pending.question">{{ result.pending.question }}</p>
        <ul v-if="result.pending.questions?.length"><li v-for="question in result.pending.questions" :key="question">{{ question }}</li></ul>
        <label class="ns-label">确认说明或补充信息<textarea v-model="answer" :disabled="busy" /></label><button :disabled="!canRun || preview || result.stale || !answer.trim()" @click="run('assist.confirm', { id: result.id, confirmation_hash: result.confirmation_hash, answer })">确认以上内容并继续</button><p class="ns-muted">如目标或范围本身不正确，请用修正后的问题建立新请求；这里的补充说明不代替改写任务条件。</p></div>
      <div v-if="result.candidate" class="ns-block"><h4>拟发布的对象与关系</h4><LabFields :value="result.candidate" /><details><summary>对照原始材料</summary><pre>{{ result.source.text }}</pre></details><details><summary>结构校验结果</summary><LabFields :value="result.validation" /></details><p>结构检查只说明格式、类型和引用符合约定。请核对文字是否真的支持这项含义和关系。</p>
        <template v-if="result.state === 'needs_review'"><label class="ns-label">审核说明<textarea v-model="review" :disabled="busy" /></label><div class="ns-controls"><button :disabled="!canRun || preview || result.stale || !review.trim()" @click="run('resource.publish', { id: result.id, confirmation_hash: result.confirmation_hash, note: review })">审核通过并发布</button><button :disabled="!canRun || preview || !review.trim()" @click="run('resource.reject', { id: result.id, note: review })">拒绝候选</button></div></template>
      </div>
      <div v-if="result.state === 'published'" class="ns-block"><h4>发布后有什么变化</h4><p>新对象、模型、关系和 Wiki 已进入当前空间。可回到 C1、C3、C4 查询核对。</p><LabFields :value="{ before_manifest: result.manifest, after_manifest: result.after_manifest, object: result.published_object }" /><details><summary>重建的 Wiki</summary><LabFields :value="result.wiki" /></details></div>
      <div v-if="result.history?.length" class="ns-block"><h4>每一步做了什么</h4><ol class="ns-timeline"><li v-for="(step, i) in result.history" :key="i"><strong>{{ step.event === 'human_confirmed' ? '人确认了任务条件' : `第 ${step.step} 步 · ${step.decision?.action || step.purpose}` }}</strong><p v-if="step.decision?.reason">{{ step.decision.reason }}</p><p v-if="step.error" class="ns-warning">{{ step.error }}</p><details><summary>查看本步输入决定和结果</summary><LabFields :value="step" /></details></li></ol></div>
      <div v-if="result.package" class="ns-block"><h4>交给请求方的上下文包</h4><p>这里交付取证材料，尚未宣告业务问题已经解决。模型的解释仍需复核。</p><LabFields :value="result.package" /></div>
      <details class="ns-raw"><summary>检查原始 JSON</summary><pre>{{ JSON.stringify(result, null, 2) }}</pre></details>
    </div>
    <p v-if="busy" role="status">正在处理；页面最多等候60秒，模型网络读写超时设为45秒。页面超时不等于服务端已取消，请先恢复记录再决定是否重试。等待模型期间不会锁住其他实验的写入。</p>
    <p v-if="error" class="ns-warning" role="alert">{{ error }}</p>
    <details class="ns-source"><summary>阅读对应实现</summary><label class="ns-label">源码位置<select v-model="sourceIndex"><option v-for="(s, i) in snippets" :key="s.symbol" :value="i">{{ s.symbol }}</option></select></label><p class="ns-citation">{{ snippet.path }}:{{ snippet.start }}</p><pre><code>{{ snippet.code }}</code></pre></details>
  </section>
</template>
