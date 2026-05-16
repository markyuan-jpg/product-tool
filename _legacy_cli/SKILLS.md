# GStack Skills 完整列表

> 最后更新: 2026-05-03

## 🔍 浏览器/测试 (Browser/Testing)

| Skill | 用途 |
|-------|------|
| **browse** | headless浏览器QA测试，导航页面、交互元素、验证状态、截图、响应式检查 |
| **gstack** | 同browse（备用名） |
| **open-gstack-browser** | 启动可见浏览器窗口，实时观看操作，有侧边栏 |
| **scrape** | 从网页拉取数据，首次调用返回JSON，后续调用缓存复用 |
| **setup-browser-cookies** | 从真实Chrome导入cookies到headless会话，用于认证页面测试 |
| **pair-agent** | 配对远程AI agent到你的浏览器，生成设置密钥 |
| **hackernews-frontpage** | 抓取HN首页（标题、分数、评论数） |

---

## 📋 规划/评审 (Planning/Review)

| Skill | 用途 |
|-------|------|
| **autoplan** | 自动运行CEO+设计+工程+DX评审 sequentially，用6个决策原则，最终审批门 |
| **plan-ceo-review** | CEO/创始人模式评审，重思考问题，挑战前提，扩展/紧缩scope，4种模式 |
| **plan-design-review** | 设计师视角plan评审，interactive，评分0-10，解释如何拿10分 |
| **plan-eng-review** | 工程经理模式评审，锁定执行计划，架构/数据流/边界/测试/性能 |
| **plan-devex-review** | 开发者体验plan评审，探索personas，benchmarks，magical moments，3种模式 |

---

## 🏥 代码质量 (Code Quality)

| Skill | 用途 |
|-------|------|
| **health** | 代码质量仪表板，包装项目工具（type checker/linter/test），加权0-10分 |
| **review** | Pre-landing PR review，分析diff，SQL安全/LLM信任边界/条件副作用 |
| **cso** | 首席安全官模式，基础设施安全审计：secrets/依赖链/CI/CD，OWASP Top 10 |
| **benchmark** | 性能回归检测，Core Web Vitals/bundle size/load time，建立baseline |
| **benchmark-models** | 跨模型benchmark，Claude/GPT/Gemini对比latency/tokens/cost |
| **web-design-guidelines** | Web Interface Guidelines合规审查 |

---

## 🔧 调试 (Debugging)

| Skill | 用途 |
|-------|------|
| **investigate** | 系统调试+根因分析，4阶段：investigate/analyze/hypothesize/implement |
| **gstack-openclaw-investigate** | 同investigate（openclaw版本） |
| **qa** | 系统QA测试web应用+修bug，3层：Quick/Standard/Exhaustive |
| **qa-only** | 只报告QA测试，不修bug |
| **systematic-debugging** | 遇到bug/test failure/意外行为时使用，提出修复前必用 |

---

## 🚀 部署 (Deployment)

| Skill | 用途 |
|-------|------|
| **ship** | 发货workflow：检测+合并base分支，运行测试，review diff，bump VERSION，更新CHANGELOG，commit，push，创建PR |
| **land-and-deploy** | 合并PR，等待CI+部署，通过canary检查验证production健康 |
| **canary** | Post-deploy监控，watch console错误/性能回归/页面失败，定期截图 |
| **setup-deploy** | 配置land-and-deploy的部署设置，检测平台/URL/health check |

---

## 📄 文档处理 (Document Processing)

| Skill | 用途 |
|-------|------|
| **docx** | 创建/读取/编辑Word文档(.docx)，表格/图/追踪更改/格式 |
| **pdf** | PDF操作：读取/提取/合并/拆分/旋转/水印/OCR |
| **pptx** | 创建/读取/编辑PPT幻灯片，模板/布局/演讲者笔记 |
| **xlsx** | 读取/编辑/创建Excel电子表格，公式/图表/数据清洗 |
| **make-pdf** | Markdown转出版级PDF，1英寸边距/智能分页/页码/封面/TOC/水印 |
| **document-release** | Post-ship文档更新，交叉reference diff，更新README/CHANGELOG |

---

## ⚙️ 开发工作流 (Development Workflow)

| Skill | 用途 |
|-------|------|
| **brainstorming** | 任何creative work前必���：创建功能/组件/添加功能/修改行为 |
| **writing-plans** | 有spec/需求的多步骤任务前必用 |
| **executing-plans** | 在separate session执行实施计划，有review checkpoints |
| **subagent-driven-development** | 执行实施计划，independent任务，two-stage review（spec+quality） |
| **using-git-worktrees** | 开始feature需要isolation时，创建isolated git worktrees |
| **context-save** | 保存工作上下文，git状态+决策+剩余工作 |
| **context-restore** | 恢复之前保存的工作上下文 |
| **finishing-a-development-branch** | 实现完成，测试通过，决定如何集成工作 |
| **requesting-code-review** | 完成任务、实现主要功能、合并前验证 |
| **receiving-code-review** | 收到代码review反馈后，实现建议前必用 |
| **test-driven-development** | 实现任何feature/bugfix前必用 |

---

## 🎨 设计 (Design)

| Skill | 用途 |
|-------|------|
| **design-shotgun** | 设计shotgun：生成多个AI设计变体，打开对比板，收集反馈，迭代 |
| **design-consultation** | 设计consultation，研究propose完整设计系统，生成DESIGN.md |
| **design-html** | 设计finalization，生成production质量HTML/CSS |
| **design-review** | 设计师视角QA，找到视觉不一致/spacing问题/AI slop，迭代修复 |
| **frontend-design** | 创建distinctive production级前端界面，高设计质量 |

---

## 💪 PUA/驱动模式 (PUA/Motivation)

| Skill | 用途 |
|-------|------|
| **pua** | 用大厂PUA话术穷尽一切方案，任务失败2+次或用户不满时触发 |
| **pua-en** | Western big-tech性能文化，structured调试 |
| **pua-ja** | 日本企业詰め文化，systematic调试方法论 |
| **yes** | SB Leader夸夸模式，ENFP型领导，情绪价值+鼓励 |
| **mama** | 中国式妈妈nutting话术，旁白风格切换 |
| **pro** | PUA Pro扩展：自进化追踪/KPI报告/leaderboard |
| **shot** | PUA浓缩v2，449行全量注入，最强效果 |
| **pua-loop** | 自主循环迭代开发，autoresearch风格gate protocol，运行到verified done |

---

## 👔 职业/团队 (Career/Team)

| Skill | 用途 |
|-------|------|
| **p7** | Senior Engineer模式，方案驱动执行 under P8 supervision |
| **p9** | Tech Lead模式，写Task Prompts，管理P8 agent团队，不自己写代码 |
| **p10** | CTO模式，战略方向，设计org topology，管理P9团队 |

---

## 🛠️ 其他工具 (Utilities)

| Skill | 用途 |
|-------|------|
| **caveman** | Ultra-compressed沟通模式，cut token usage ~75%，说smart caveman |
| **caveman-commit** | Ultra-compressed commit message生成器 |
| **caveman-review** | Ultra-compressed code review comments，1行：位置+问题+修复 |
| **caveman-help** | caveman模式快速参考卡 |
| **careful** | Safety guardrails for destructive commands，rm -rf/DROP TABLE警告 |
| **freeze** | 限制文件edits到指定目录，阻止外部编辑 |
| **unfreeze** | 清除freeze边界，允许所有edits |
| **guard** | Full安全模式：careful + freeze组合 |
| **learn** | 管理项目learnings，搜索/修剪/导出跨session的learnings |
| **retro** | Weekly工程retrospective，分析commit历史/work patterns/代码质量 |
| **gstack-openclaw-retro** | 同retro（openclaw版本） |
| **office-hours** | YC Office Hours，startup mode（6个forcing问题）+ builder mode |
| **gstack-openclaw-office-hours** | 同office-hours（openclaw版本） |
| **skill-creator** | 创建新skills，修改现有skills，measure性能 |
| **skillify** | 将最近successful /scrape flow codified为permanent浏览器skill |
| **karpathy-check** | 代码review评估plans/implementation approaches的rigor/simplicity/correctness |
| **karpathy-guidelines** | 行为指南减少常见LLM coding mistakes |
| **dispatching-parallel-agents** | 面对2+ independent任务时可并行dispatch |
| **find-skills** | 发���和安装agent skills |
| **planning-with-files-zh** | Manus风格文件规划，task_plan.md/findings.md/progress.md |
| **planner** | 任务管理，类似Microsoft Planner |
| **nlm-index** | 为NotebookLM索引文档站点或GitHub repos |
| **ui-ux-pro-max** | UI/UX设计 intelligence with searchable database |
| **best-minds** | 模拟器思维，问"世界上谁最懂这个？TA会怎么说？" |

---

## 🔌 集成技能 (Integration Skills)

| Skill | 用途 |
|-------|------|
| **using-superpowers** | 开始任何conversation时使用，建立如何find和使用skills |
| **verification-before-completion** | 声称工作完成/修好/测试通过前必用，运行验证命令，确认输出 |
| **loaded_skills** | 列出当前session所有preloaded skills |

---

# 使用说明

## 如何调用 Skill

在对话中直接说明要使用的 skill：
- `/skill-name` - 调用指定skill
- "用 XXX skill" - 中文触发
- "use XXX skill" - 英文触发

## 常用命令

| 命令 | 用途 |
|------|------|
| `/caveman` | 切换到 caveman 模式 |
| `/caveman-help` | 查看 caveman 命令 |
| `/ship` | 发货流程 |
| `/context-save` | 保存进度 |
| `/health` | 代码质量检查 |

---

**共约 85 个 skills，按功能分类如上。**