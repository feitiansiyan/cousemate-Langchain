# 测试记录

记录日期：2026-10-29。

## 测试范围

- UTF-8 文本及 PPTX 解析，来源页码保持。
- 相关问题检索、无命中时拒答。
- 使用 LangChain FakeListChatModel 验证真实 LCEL 链路。
- 空文件、错误格式、错误编码、损坏 PPTX、缺失密钥、非本机地址。
- Streamlit 页面启动、检索体验、清空对话。

## 验证状态

环境：Windows，Python 3.11.4。精确依赖版本见 `requirements-lock.txt`。

执行 `python -m pytest -q`：**10 passed in 4.85s**。

认证诊断改进后复测：**22 passed in 3.93s**。新增测试验证密钥空白处理、异常格式拒绝、官方接口固定、不同 HTTP 错误的安全提示，以及模拟模型列表请求。未使用用户真实密钥。

其中 9 项覆盖核心功能（含参数化异常输入），1 项使用 Streamlit AppTest 验证页面启动、提问检索与清空对话。测试使用模拟模型，不产生在线模型费用。

实际课件验证：成功解析用户提供的 76 页 PPTX，清除高频重复页脚后建立 86 个片段。针对“LangChain 的核心模块有哪些？”的检索能够优先返回第 37 页。此为功能检查，不代表全面的检索准确率评测。

已成功构造 ChatDeepSeek 和 ChatOllama 客户端。DeepSeek 构造测试使用无效测试字符串，未发送请求，不能证明鉴权通过。

Streamlit 已在 `127.0.0.1:8501` 启动。首次在受限执行环境中测试时，Windows asyncio 的本地 socketpair 通信受阻；获得本机通信运行权限后，完整测试通过。这属于测试环境限制。

真实 DeepSeek 和 Ollama 推理尚未验收：当前没有用户提供的 API Key，也未发现 Ollama 命令。模拟模型测试不得作为真实模型调用成功的证据。
