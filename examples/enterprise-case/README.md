# Northstar Commerce：渐进式企业上下文案例

Northstar 是本书第四部分的可运行案例。它不是电商平台的缩小复刻，而是一个可检查的教学世界：读者先看到战略分析、影响分析和退款处置三类任务的最终结果，再从原始来源逐步构造对象与检索；从能力问题、术语、概念和源映射编译知识模型；随后生成关系、Wiki、Context Package 和受控动作。

## 先分清三层

| 层次 | 内容 | 本仓库的状态 |
|---|---|---|
| 目标企业 | 订单、支付、库存、履约、通知五个逻辑服务及其协作 | 业务地图，用来解释问题 |
| 教学 fixture | 19 个对象、13 条关系、3 个代码消费者、1 个逻辑仓 | 可运行、可审阅、故意很小 |
| 生产化扩展 | 真实连接器、PostgreSQL/pgvector、Tree-sitter、SCIP、MCP/REST、持久任务 | 只给替换边界，不宣称已交付 |

## 八个检查点

| 检查点 | 你完成的能力 | 主要文件 | 证明 |
|---|---|---|---|
| C0 | 阅读原始政策、Runbook、事件、代码与测试 | `data/raw/` | 来源仍可人工检查 |
| C1 | 编译版本化对象并做 ACL-first BM25 | `src/build_baseline.py`、`src/context_demo.py` | `test_build_baseline.py` |
| C2 | 加入离线语义代理、RRF 与时间语义 | `src/northstar.py` | `test_northstar.py` |
| C3 | 从能力问题和企业语言编译、验证知识模型 | `data/modeling/`、`src/modeling.py` | 术语边界、时间边、实例闭合测试 |
| C4 | 以能力问题约束图遍历，并建立 Wiki、记忆与 EA 检测 | `data/relations.json`、`data/architecture-claims.json` | 正反向导航、ACL、Wiki、EA 测试 |
| C5 | 组装能力问题、语义切片、Context Package 与实时观察 | `NorthstarPlatform.context()` | Context Package 测试 |
| C6 | SRE 诊断、负责人确认、SRE 执行并验证 | `action_demo.py` | `test_action_boundary.py` |
| C7 | C-level 只读战略分析：指标、分解、架构上下文、假设和缺口 | `data/strategy-context.json`、`src/strategy.py` | `test_strategy.py` |

## 从成品开始运行

所有命令只需要 Python 标准库。默认模拟时钟固定为 2026-08-27 10:00 UTC，传感器初始化后读数只在 TTL 内有效；测试通过注入时钟检查过期，不把该时钟用于真实业务。

```bash
cd examples/enterprise-case

# C0-C1：从可读来源编译最小基线，再验证开发者能定位代码。
python3 src/build_baseline.py
python3 src/build_knowledge.py
python3 src/context_demo.py \
  "handle_order_cancelled create_refund" \
  --role developer \
  --data generated/baseline-knowledge.json

# C2：验证双时间选择；混合检索由后续 northstar.py 命令共同展示。
python3 src/time_demo.py
python3 src/tutorial_experiments.py change
python3 src/tutorial_experiments.py ablation

# C3：把四类可评审建模输入编译成领域模型，并验证实际对象和边。
python3 src/build_domain_model.py

# C4：完成后的影响分析、角色安全域 Wiki 与企业架构差异。
python3 src/northstar.py "修改 order.cancelled 会影响什么" \
  --role developer --graph-seed event-order-cancelled \
  --competency-question CQ-EVENT-001
python3 src/northstar.py "退款网关 API 变化会影响什么" \
  --role developer --graph-seed api-create-refund \
  --competency-question CQ-IMPACT-001
python3 src/northstar.py --wiki --role support
python3 src/northstar.py --architecture-consistency --role developer

# C5：SRE 的诊断包同时包含语义契约、静态证据和实时队列观察。
python3 src/northstar.py "退款积压如何排查" \
  --role sre --runtime-resource refund-queue --task INC-1042

# C6：SRE 准备动作，incident_commander 确认，SRE 执行并验证。
python3 src/action_demo.py

# C7：第一次请求只确认指标、时间、场景和范围。
python3 src/strategy_demo.py "H2 的销售情况为什么比 H1 差这么多？"
# 确认固定教学快照后，生成企业级只读战略分析包。
python3 src/strategy_demo.py "H2 的销售情况为什么比 H1 差这么多？" \
  --confirm-definition

python3 -m unittest discover -s tests -v
```

模型构建应报告 12 个术语、12 种实体、8 种关系和 3 条全部得到连通实例支持的能力问题；所有声明类型与关系都应被 fixture 使用，时间关系必须携带时间信封。事件影响分析应返回三个 `CONSUMED_BY` 消费者及其测试引用；API 影响分析应从 API 反向导航到调用服务和实现仓，再找到值班团队和 Runbook，同时仍保持边的原始方向。Context Package 中的 `semantic_contract` 应同时给出能力问题、最小模型切片和 `competency_coverage`；任务契约完整不等于本次证据已经完整。SRE 诊断应返回 Runbook、历史事故和队列观察。动作示例应显示 `prepared_by: sre-oncall`、100 条消息的上限、负责人确认，以及队列由 842 降至 742 的验证观察。战略示例应先返回待确认的指标契约，确认后才返回 H1/H2 差异、产品/区域/客群/渠道分解、战略目标、业务能力、组织、应用、数据产品和待验证假设；四个分解维度分别与公司总额核对，不能跨维度相加；它不能把候选事件直接写成因果结论。

这套 Golden Questions 现在还包含 3 条 C7 题，分别检查战略指标口径确认、已授权角色的只读战略分析，以及未授权角色的拒绝。

## 角色边界

`support` 只能读取客服所需的政策和自己租户的状态；`developer` 可以读取代码与工程资料；`sre` 负责收集事故证据、准备和执行受控动作；`incident_commander` 只读取运行状态和动作预览，并在待确认阶段批准或拒绝；`executive`、`strategy`、`revops` 和 `product` 可以读取 C7 的固定战略快照。负责人不会因为拥有确认权而获得 SRE 的静态证据访问权，也不会获得执行令牌；C7 的教学快照对四类战略角色共享可见性，生产系统必须补充组织和对象范围过滤。

## 实现边界

`context_demo.py` 是 C1 的单文件 BM25 基线。`data/modeling/` 是人工评审的模型输入，`generated/domain-model.json` 和验证报告是可删除重建的产物；不要反向手改生成文件。`build_knowledge.py` 把五份 raw 编译结果与十四个补充 fixture 对象合并；运行时与 C3 使用同一函数，原始政策的变化因此会进入检索和 Wiki。图边仍由人编写。`northstar.py` 是 C2-C7 的统一入口：操作任务沿 C2-C6 运行，战略题通过 `--mode strategic` 或 `strategy_demo.py` 读取 C7 的独立战略快照，但最终仍使用同一个 Context Package 入口、Manifest 和主体边界。战略快照是虚构的、已结算的教学数据，不是实时业务数据，也不实现自动因果推断。离线语义代理是同义词扩展与 Jaccard 相似度，不是向量检索；双向导航不改变关系语义；内存队列和任务记忆不等同于真实运行系统。生产化组件可以替换实现，但不应绕过本例由测试保护的对象、ACL、引用、模型、状态机和审计契约。

Docker Compose 也可执行全部验证：

```bash
docker compose up --build --abort-on-container-exit verify
docker compose --profile query run --rm query
```

容器禁用网络、使用只读文件系统，并固定 Python 3.12.5 镜像 manifest 摘要。
