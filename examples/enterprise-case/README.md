# Northstar Commerce：渐进式企业上下文案例

Northstar 是本书第四部分的可运行案例。它不是电商平台的缩小复刻，而是一个可检查的教学世界：读者先看到两个真实工作任务的最终结果，再从原始来源逐步构造对象与检索；从能力问题、术语、概念和源映射编译知识模型；随后生成关系、Wiki、Context Package 和受控动作。

## 先分清三层

| 层次 | 内容 | 本仓库的状态 |
|---|---|---|
| 目标企业 | 订单、支付、库存、履约、通知五个逻辑服务及其协作 | 业务地图，用来解释问题 |
| 教学 fixture | 19 个对象、13 条关系、3 个代码消费者、1 个逻辑仓 | 可运行、可审阅、故意很小 |
| 生产化扩展 | 真实连接器、PostgreSQL/pgvector、Tree-sitter、SCIP、MCP/REST、持久任务 | 只给替换边界，不宣称已交付 |

## 七个检查点

| 检查点 | 你完成的能力 | 主要文件 | 证明 |
|---|---|---|---|
| C0 | 阅读原始政策、Runbook、事件、代码与测试 | `data/raw/` | 来源仍可人工检查 |
| C1 | 编译版本化对象并做 ACL-first BM25 | `src/build_baseline.py`、`src/context_demo.py` | `test_build_baseline.py` |
| C2 | 加入离线语义代理、RRF 与时间语义 | `src/northstar.py` | `test_northstar.py` |
| C3 | 从能力问题和企业语言编译、验证知识模型 | `data/modeling/`、`src/modeling.py` | 术语边界、时间边、实例闭合测试 |
| C4 | 以能力问题约束图遍历，并建立 Wiki、记忆与 EA 检测 | `data/relations.json`、`data/architecture-claims.json` | 正反向导航、ACL、Wiki、EA 测试 |
| C5 | 组装能力问题、语义切片、Context Package 与实时观察 | `NorthstarPlatform.context()` | Context Package 测试 |
| C6 | SRE 诊断、负责人确认、SRE 执行并验证 | `action_demo.py` | `test_action_boundary.py` |

## 从成品开始运行

所有命令只需要 Python 标准库。

```bash
cd examples/enterprise-case

# C0-C1：从可读来源编译最小基线，再验证开发者能定位代码。
python3 src/build_baseline.py
python3 src/context_demo.py \
  "handle_order_cancelled create_refund" \
  --role developer \
  --data generated/baseline-knowledge.json

# C2：验证双时间选择；混合检索由后续 northstar.py 命令共同展示。
python3 src/time_demo.py

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

python3 -m unittest discover -s tests -v
```

模型构建应报告 12 个术语、12 种实体、8 种关系和 3 条全部得到连通实例支持的能力问题；所有声明类型与关系都应被 fixture 使用，时间关系必须携带时间信封。事件影响分析应返回三个 `CONSUMED_BY` 消费者及其测试引用；API 影响分析应从 API 反向导航到调用服务和实现仓，再找到值班团队与 Runbook，同时仍保持边的原始方向。Context Package 中的 `semantic_contract` 应同时给出能力问题、最小模型切片和 `competency_coverage`；任务契约完整不等于本次证据已经完整。SRE 诊断应返回 Runbook、历史事故和队列观察。动作示例应显示 `prepared_by: sre-oncall`、100 条消息的上限、负责人确认，以及队列由 842 降至 742 的验证观察。

## 角色边界

`support` 只能读取客服所需的政策和自己租户的状态；`developer` 可以读取代码与工程资料；`sre` 负责收集事故证据、准备和执行受控动作；`incident_commander` 只读取运行状态和动作预览，并在待确认阶段批准或拒绝。负责人不会因为拥有确认权而获得 SRE 的静态证据访问权，也不会获得执行令牌。

## 实现边界

`context_demo.py` 是 C1 的单文件 BM25 基线。`data/modeling/` 是人工评审的模型输入，`generated/domain-model.json` 和验证报告是可删除重建的产物；不要反向手改生成文件。`northstar.py` 是 C2-C6 的完成后纵向切片，启动时重新编译并校验模型；选中能力问题后，它还会把所需关系编译成图遍历白名单，并把问题契约放回 Context Package。离线语义代理是同义词扩展与 Jaccard 相似度，不是向量检索；双向导航不改变关系语义；内存队列和任务记忆不等同于真实运行系统。生产化组件可以替换实现，但不应绕过本例由测试保护的对象、ACL、引用、模型、状态机和审计契约。

Docker Compose 也可执行全部验证：

```bash
docker compose up --build --abort-on-container-exit verify
docker compose --profile query run --rm query
```

容器禁用网络、使用只读文件系统，并固定 Python 3.12.5 镜像 manifest 摘要。
