<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import catalogData from '../generated/northstar.json'
import LabResult from './LabResult.vue'

const catalog: any = catalogData
const props = defineProps<{ lesson?: string }>()
const key = ref(props.lesson || 'C0')
const lesson = computed(() => catalog.lessons[key.value])
const role = ref(lesson.value.role)
const panel = ref(lesson.value.panel)
const question = ref(lesson.value.request?.question || '取消事件有哪些 consumer 影响')
const disabledChannels = ref<string[]>(lesson.value.request?.disabled_channels || [])
const validAt = ref(''), observedAt = ref('')
const seed = ref('event-order-cancelled')
const note = ref('新增核验说明：checkpointalpha')
const taskNote = ref('')
const scenario = ref(lesson.value.scenario || 'change')
const goal = ref(catalog.scenarios[scenario.value].goal)
const sourceIndex = ref(0)
const ready = ref(false), hasSession = ref(false), busy = ref(false)
const status = ref('公开阅读模式'), error = ref(''), result = ref<any>(null)
const origin = ref(''), tasks = ref<any[]>([]), selectedTask = ref(''), clock = ref('')
const source = computed(() => lesson.value.sources[sourceIndex.value] || lesson.value.sources[0])
const activeTask = computed(() => tasks.value.find(t => t.id === selectedTask.value))
const canRun = computed(() => ready.value && hasSession.value && !busy.value)
const panels = { resources: '资源目录', search: '检索实验', model: '模型与语义', trace: '关系导航', wiki: 'Wiki', architecture: '架构核对', tasks: '任务空间', update: '资源更新' }
const roles = { developer: '开发者', support: '客服', sre: '值班 SRE', incident_commander: '事故负责人', executive: '经营负责人', strategy: '战略分析', revops: '营收运营', product: '产品负责人' }
const scenarioNames = { change: '代码变更影响', incident: '退款积压处置', strategy: '经营分析' }

async function request(path: string, payload: any) {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Northstar-Lab': '1' }, body: JSON.stringify(payload), signal: AbortSignal.timeout(15000) })
  const data = await response.json()
  if (!response.ok) throw new Error(data.error || `请求失败：${response.status}`)
  return data
}
async function refresh() {
  const data = await request('/api/lab', { op: 'overview', role: role.value })
  tasks.value = data.tasks
  clock.value = data.clock
  hasSession.value = true
  if (selectedTask.value && !tasks.value.some(t => t.id === selectedTask.value)) selectedTask.value = ''
}
async function start(fresh: boolean) {
  busy.value = true; error.value = ''; result.value = null
  try {
    if (fresh) { await request('/api/session', {}); selectedTask.value = '' }
    await refresh()
    status.value = '本地 Python 已连接 · 实验自动保存'
    if (fresh) window.dispatchEvent(new Event('northstar-space-created'))
  } catch (e: any) { error.value = e.message } finally { busy.value = false }
}
async function run(payload: any) {
  if (!canRun.value) return
  busy.value = true; error.value = ''; result.value = null
  try {
    result.value = await request('/api/lab', { ...payload, role: role.value })
    origin.value = '本地 Python 实际返回（业务数据为教学模拟）'
    if (payload.op === 'task.create') selectedTask.value = result.value.id
    await refresh()
  } catch (e: any) { error.value = e.message } finally { busy.value = false }
}
function experiment() {
  const op = panel.value === 'update' ? 'policy.update' : panel.value
  run({ op, question: question.value, seed: seed.value, note: note.value,
    disabled_channels: disabledChannels.value, valid_at: validAt.value, observed_at: observedAt.value })
}
function taskAction(op: string) {
  const task = activeTask.value
  const contract = task?.package?.query_contract
  run({ op, task_id: selectedTask.value, note: taskNote.value,
    params_hash: task?.preview?.params_hash,
    confirmation: contract ? Object.fromEntries(Object.entries(contract).filter(([k]) => k !== 'confirmed')) : undefined })
}
function createTask() {
  run({ op: 'task.create', kind: scenario.value, ...catalog.scenarios[scenario.value], goal: goal.value })
}
function sample() {
  result.value = lesson.value.sample
  origin.value = catalog.sample_notice
  error.value = ''
}
watch(scenario, () => { goal.value = catalog.scenarios[scenario.value].goal })
watch(key, () => {
  panel.value = lesson.value.panel; role.value = lesson.value.role; sourceIndex.value = 0
  question.value = lesson.value.request?.question || '取消事件有哪些 consumer 影响'
  disabledChannels.value = lesson.value.request?.disabled_channels || []
  scenario.value = lesson.value.scenario || 'change'; result.value = null; error.value = ''
})
watch(role, async () => {
  result.value = null; error.value = ''; selectedTask.value = ''; tasks.value = []
  if (ready.value && hasSession.value) {
    busy.value = true
    try { await refresh() } catch (e: any) { error.value = e.message } finally { busy.value = false }
  }
})
async function spaceChanged() {
  if (!ready.value) return
  result.value = null; selectedTask.value = ''; error.value = ''
  try { await refresh(); status.value = '本地 Python 已连接 · 实验自动保存' }
  catch (e: any) { error.value = e.message; hasSession.value = false }
}
onMounted(async () => {
  window.addEventListener('northstar-space-created', spaceChanged)
  // A public site never probes a visitor's local network or sends it fixture data.
  if (!['127.0.0.1', 'localhost'].includes(location.hostname)) return
  try {
    const response = await fetch('/api/health', { signal: AbortSignal.timeout(2000) })
    if (!response.ok) return
    const health = await response.json()
    if (health.service !== 'northstar-lab') return
    if (health.source_revision !== catalog.source_revision) {
      status.value = '页面与 Python 版本不一致，请重新运行 npm run lab'; return
    }
    ready.value = true; status.value = '本地服务就绪，请创建或恢复实验空间'
    try { await refresh(); status.value = '本地 Python 已连接 · 实验自动保存' } catch { /* New visitors choose to create a space. */ }
  } catch { /* Static previews retain the readable sample and source code. */ }
})
onUnmounted(() => window.removeEventListener('northstar-space-created', spaceChanged))
</script>

<template>
  <section class="northstar-lab" :aria-label="`${lesson.title}交互实验`">
    <div class="ns-heading"><span class="ns-eyebrow">NORTHSTAR · {{ props.lesson ? key : '工作台与章节实验' }}</span><span class="ns-badge">{{ status }}</span></div>
    <label v-if="!props.lesson" class="ns-label">构建检查点<select v-model="key" :disabled="busy"><option v-for="(item, id) in catalog.lessons" :value="id" :key="id">{{ id }} · {{ item.title }}</option></select></label>
    <h3>{{ lesson.title }}</h3>
    <p>{{ lesson.why }}</p>
    <p class="ns-build"><strong>这一小步怎样构建：</strong>{{ lesson.build }}</p>
    <div class="ns-connection">
      <template v-if="ready"><button :disabled="busy" @click="start(true)">新建实验空间</button><button :disabled="busy" @click="start(false)">恢复已有空间</button><small>新建会切换到独立数据副本；已有记录仍保存在本地数据库。</small></template>
      <template v-else><p>要实际运行：在仓库根目录执行 <code>npm ci</code> 和 <code>npm run lab</code>，再打开终端显示的本地地址。公开页面上的示例是构建时输出。</p></template>
      <button class="ns-secondary" :disabled="busy" @click="sample">查看构建时示例</button>
      <a :href="withBase('/lab')">工作台与启动说明</a>
    </div>
    <div class="ns-controls">
      <label class="ns-label">模拟角色<select v-model="role" :disabled="busy"><option v-for="(name, id) in roles" :value="id" :key="id">{{ name }} · {{ id }}</option></select></label>
      <label class="ns-label">操作区域<select v-model="panel" :disabled="busy" @change="result = null"><option v-for="(name, id) in panels" :value="id" :key="id">{{ name }}</option></select></label>
    </div>
    <div v-if="panel === 'search'" class="ns-form">
      <label class="ns-label">查询问题<input v-model="question" :disabled="busy" /></label>
      <div class="ns-controls"><label><input v-model="disabledChannels" type="checkbox" value="bm25" :disabled="busy" /> 关闭 BM25</label><label><input v-model="disabledChannels" type="checkbox" value="semantic_proxy" :disabled="busy" /> 关闭离线语义代理</label></div>
      <div class="ns-controls"><label class="ns-label">业务有效时间（可留空）<input v-model="validAt" placeholder="2026-07-01T12:00:00Z" :disabled="busy" /></label><label class="ns-label">平台已知时间（可留空）<input v-model="observedAt" placeholder="2026-08-27T10:00:00Z" :disabled="busy" /></label></div>
    </div>
    <label v-if="panel === 'trace'" class="ns-label">起点对象<input v-model="seed" :disabled="busy" /></label>
    <div v-if="panel === 'update'"><label class="ns-label">追加到政策副本的说明<textarea v-model="note" maxlength="500" :disabled="busy" /></label><p class="ns-muted">由 product 角色维护。将重建当前空间资源，并标记旧任务需重新取证；不修改仓库原文件。</p></div>
    <template v-if="panel === 'tasks'">
      <div class="ns-task-create">
        <label class="ns-label">工作线<select v-model="scenario" :disabled="busy"><option v-for="(name, id) in scenarioNames" :key="id" :value="id">{{ name }}</option></select></label>
        <label class="ns-label">任务目标<textarea v-model="goal" :disabled="busy" /></label>
        <p><strong>范围：</strong>{{ catalog.scenarios[scenario].scope }}</p><p><strong>完成条件：</strong>{{ catalog.scenarios[scenario].completion }}</p>
        <button :disabled="!canRun" @click="createTask">创建任务</button><small>需要 {{ roles[catalog.scenarios[scenario].role as keyof typeof roles] }} 角色；本实验的业务范围和完成条件固定。</small>
      </div>
      <label class="ns-label">当前角色可见的任务<select v-model="selectedTask" :disabled="busy" @change="taskAction('task.get')"><option value="" disabled>请选择任务</option><option v-for="task in tasks" :key="task.id" :value="task.id">{{ scenarioNames[task.kind as keyof typeof scenarioNames] }} · {{ task.id }} · {{ task.state }}</option></select></label>
      <div v-if="activeTask" class="ns-task-actions">
        <div class="ns-controls"><button :disabled="!canRun" @click="taskAction('task.get')">读取已保存任务</button><button v-if="!activeTask.approval_only" :disabled="!canRun" @click="taskAction('task.context')">构造本次上下文</button></div>
        <div v-if="activeTask.kind === 'strategy' && activeTask.package?.query_contract" class="ns-controls"><button :disabled="!canRun || activeTask.package.query_contract.confirmed" @click="taskAction('task.confirm_definition')">确认下方展示的指标契约</button><small>确认后再次构造上下文，才会计算差异。</small></div>
        <div v-if="activeTask.kind === 'incident'" class="ns-controls">
          <template v-if="role === 'sre'"><button :disabled="!canRun || activeTask.state !== 'diagnosing'" @click="taskAction('action.prepare')">准备动作预览</button><button :disabled="!canRun || !['approved', 'verifying', 'resolved'].includes(activeTask.state)" @click="taskAction('action.execute')">执行／重试同一动作</button><button :disabled="!canRun || activeTask.state !== 'verifying'" @click="taskAction('action.verify')">验证业务观察</button></template>
          <template v-if="role === 'incident_commander'"><button :disabled="!canRun || activeTask.state !== 'action_proposed'" @click="taskAction('action.confirm')">批准这份具体预览</button><button :disabled="!canRun || activeTask.state !== 'action_proposed'" @click="taskAction('action.reject')">拒绝这份预览</button></template>
        </div>
        <template v-if="!activeTask.approval_only"><label class="ns-label">工作笔记或复核说明<textarea v-model="taskNote" :disabled="busy" placeholder="已核对什么、还缺什么；用户声明仍需证据支持" /></label><div class="ns-controls"><button :disabled="!canRun || !taskNote.trim()" @click="taskAction('task.note')">保存工作笔记</button><button v-if="activeTask.kind !== 'incident'" :disabled="!canRun || !taskNote.trim() || activeTask.state !== 'ready_for_review'" @click="taskAction('task.review')">登记人工复核</button></div></template>
      </div>
      <div class="ns-clock"><span>教学时钟：{{ clock || '尚未连接' }}</span><button :disabled="!canRun" @click="run({ op: 'clock.advance' })">推进61秒，测试过期</button><small>时钟不会随现实等待自动前进。过期后可新建空间重做实验。</small></div>
    </template>
    <button v-else class="ns-run" :disabled="!canRun" @click="experiment">{{ panel === 'update' ? '更新政策并重建' : '执行当前实验' }}</button>
    <p v-if="busy" role="status">正在调用本地 Python…</p>
    <p v-if="error" class="ns-warning" role="alert">{{ error }}</p>
    <div v-if="result" class="ns-output" aria-live="polite"><p class="ns-origin">{{ origin }}</p><LabResult :result="result" /></div>
    <div class="ns-reading"><p><strong>观察结果：</strong>{{ lesson.expect }}</p><p><strong>再试一个边界：</strong>{{ lesson.failure }}</p></div>
    <details class="ns-source" :open="Boolean(props.lesson)"><summary>阅读这一步的真实实现</summary><label class="ns-label">源码与输入位置<select v-model="sourceIndex"><option v-for="(item, index) in lesson.sources" :key="`${item.path}:${item.symbol}`" :value="index">{{ item.path.split('/').pop() }} · {{ item.symbol }}</option></select></label><p class="ns-citation">{{ source.path }}:{{ source.start }} · 源码标识 {{ catalog.source_revision }}</p><pre><code>{{ source.code }}</code></pre><p class="ns-muted">片段在构建书站时从真实源文件提取。修改源码后，停止旧服务并重新运行 npm run lab，更新页面和执行端。</p><p>在仓库根目录验证这一步：</p><pre><code>{{ lesson.test }}</code></pre></details>
  </section>
</template>
