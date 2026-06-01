# W5 Plan — Pilot 安全 + Web 前端

> 日期：2026-06-01
> 上一周：W4 完成（PedCoT 评分 + SQLite + 备份/恢复 + Reranker 生产）

---

## 需要人类介入的任务

| 任务 | 需要人做什么 | 阻塞程度 |
|------|-------------|---------|
| **DeepSeek API key 旋转** | 去 platform.deepseek.com 生成新 key，吊销旧 key，更新 `.env` | ⚠️ 安全：旧 key 曾在公开 GitHub 历史上暴露 |
| W5.5 学生试用 | 找 5-10 名 A-Level 学生，发问卷，收反馈 | blocker for W6 pilot report |
| W5.6 演示视频 | 录屏 3-5 分钟展示全流程 | 非阻塞（可以先写好 README） |
| QP+MS 对照验证 | 人工抽查 VLM 提取的 question→MS 映射是否准确（抽查 10%） | 非阻塞（可以先自动提取，人工后验） |

## 不需要人类介入的任务（我可以独立完成）

| # | 任务 | 说明 | 预估 |
|---|------|------|------|
| W5.0 | Gradio Web 前端 | Blocks 界面：聊天 + 图片上传 + `/grade` + `/cost` 面板 + **LLM 处理动画** | 2-3h |
| W5.1 | RAG / 文件上传安全护栏 | 上传文件转纯文本/图片层；检索内容标记 untrusted；工具调用只接受系统路由 | 1-2h |
| W5.2 | Prompt injection 测试集 | 30 个藏在 PDF/OCR/图片里的注入样例 | 1-2h |
| W5.3 | 文件卫生 | 类型白名单、大小限制、EXIF 去除、会话删除/导出 | 1h |
| W5.4 | Docker Compose | 一键启动：Ollama + LM Studio volume + ChromaDB volume + 环境变量模板 | 2-3h |
| W5.7 | Pilot 总结报告 | 从 dev logs (w1-w5.md) 自动汇总 | 1h |
| W5.8 | 多科目校准（9701/02/08） | 每科 10 题，PedCoT 评分对照（无真人对比但可跨科比较 MAE） | 2-3h |
| W5.9 | QP+MS 自动映射 | VLM 离线批量提取 QP→MS 对照集（20 题/科） | 3-4h |

## 建议执行顺序

```
W5.0 Gradio Web ──→ W5.1 安全护栏 ──→ W5.2 Prompt injection ──→ W5.3 文件卫生
                                                        ↓
                                              W5.4 Docker Compose
                                                        ↓
                                              W5.7 Pilot 总结报告
                                                        ↓
                                ← 需要人：旋转 API key、找学生 →
                                                        ↓
                                              W5.8-5.9 多科目校准 + QP+MS
```

## 当前 W5 可以立即开始的

- W5.0（Gradio Web）— 无依赖，可立即开始
- W5.1-W5.3（安全）— 无依赖，可并行
- W5.4（Docker）— 依赖 W5.0（需要 Web 入口文件）

## W5 退出标准

1. `docker-compose up` 一键启动全栈（CLI 聊天 + Web 界面 + ChromaDB + Ollama）
2. 30 个 prompt injection 案例全拦截（不泄露 system prompt、不越权调用工具、不写 memory）
3. 文件上传白名单 + EXIF 清除
4. 成本面板在 Web 中可见
5. 多科目校准 MAE < 0.5（每科 10 题）
6. QP→MS 映射表 ≥ 20 条（含人工验证标记）
