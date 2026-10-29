# 课伴 CourseMate

一个基于 LangChain 的课程资料问答应用。上传课件或笔记后，可以围绕资料提问，也可以让它整理某个知识点的复习提纲、生成练习题。回答下方会显示参考原文，方便回到资料里核对。

仓库地址：https://github.com/feitiansiyan/cousemate-Langchain

## 功能

- 上传 PPTX、TXT 和 Markdown 文件。
- 根据资料回答问题，显示参考文件和幻灯片页码。
- 围绕指定主题整理提纲、解释概念、生成练习题。
- 保留最近的对话，支持下载 Markdown 格式的学习记录。
- 接入 DeepSeek 在线模型，也可以配置 Ollama 本地模型。
- 未配置模型时，可以先使用“检索体验”查看相关原文。

目前已使用 DeepSeek 完成实际问答测试。Ollama 的接入代码已实现，但还没有进行本地模型的实际运行测试。

## 实现方法

应用采用 Python 开发，界面使用 Streamlit，模型调用和提示词处理使用 LangChain。

提问时，程序先从资料中找出相关内容，再把这些内容和问题一起交给大模型生成回答，也就是 RAG（检索增强生成）。具体过程如下：

1. 读取文件中的文字，保存文件名和页码。
2. 使用 `RecursiveCharacterTextSplitter` 将文字拆成小段，每段最多 700 个字符，相邻段保留 100 个字符的重叠。
3. 使用 TF-IDF 建立索引，根据问题与片段的相似程度选出相关内容。
4. 通过 `ChatPromptTemplate` 组织问题、参考内容和最近的对话。
5. 调用 `ChatDeepSeek` 或 `ChatOllama`，再由 `StrOutputParser` 取出回答文本。

LangChain 中的生成流程使用下面的方式连接：

```python
chain = prompt | model | StrOutputParser()
```

检索部分使用 TF-IDF，主要是为了减少安装和运行时的依赖，不需要另外下载嵌入模型。它对资料中出现过的词语比较有效，但对同义词和比较含糊的问题处理得还不够好。

## 运行方法

建议使用 Python 3.11。先下载项目：

```bash
git clone https://github.com/feitiansiyan/cousemate-Langchain.git
cd cousemate-Langchain
```

在 Windows PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

启动后，在浏览器打开 http://127.0.0.1:8501 。

如果使用 macOS 或 Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

`requirements-lock.txt` 保存了本次测试环境的依赖版本，需要相同版本时，可以用它替换安装命令中的 `requirements.txt`。

## 使用方法

### 使用 DeepSeek

1. 在 [DeepSeek 开放平台](https://platform.deepseek.com/) 创建 API Key。
2. 在应用左侧选择“DeepSeek 在线模型”。
3. 填入完整的 API Key，模型名称默认使用 `deepseek-chat`。
4. 点击“检查密钥连接（不生成回答）”，确认认证通过。
5. 上传资料，在页面底部输入问题。

也可以把 `.env.example` 复制为 `.env`，填写 `DEEPSEEK_API_KEY`，启动时会自动读取。真实密钥不要上传到仓库。

连接检查只验证接口认证，实际问答还需要账户有可用额度。遇到 401 错误时检查密钥，遇到 402 错误时检查余额。

### 问答示例

第一次使用可以保留“加入内置示例笔记”，输入：

> RAG 的基本流程是什么？

上传自己的资料后，可以取消内置示例，再根据资料内容提问，例如：

> LangChain 的核心模块有哪些？
>
> 总结 RAG 的复习提纲。
>
> 围绕 RAG 出三道练习题，并给出答案和依据。

回答后展开“查看本轮参考原文”，可以看到相关片段。需要保存时，点击“下载学习记录”。

### 使用 Ollama

安装 [Ollama](https://ollama.com/)，下载需要的模型，例如：

```bash
ollama pull qwen2.5:3b
ollama list
```

在应用中选择“Ollama 本地模型”，模型名称填写为 `ollama list` 中显示的名称，服务地址默认是 `http://localhost:11434`。如果服务没有启动，可以运行 `ollama serve`。

首次下载模型需要联网，下载完成后可以在本机运行，速度取决于电脑配置。

## 目录结构

```text
├── app.py                  # 页面、对话记录和文件上传
├── core.py                 # 文件解析、检索和模型调用
├── data/sample.md          # 示例笔记
├── tests/                  # 自动化测试
├── docs/                   # 测试记录等说明
├── requirements.txt        # 项目依赖
├── requirements-lock.txt   # 测试环境的具体版本
├── .env.example            # 环境变量示例
└── LICENSE                 # MIT 许可证
```

## 测试

在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

目前 22 项自动化测试通过，主要检查文件解析、页码顺序、检索、密钥格式处理、错误提示和页面交互。GitHub Actions 会在推送后自动运行测试。

自动化测试中的模型响应使用模拟数据，实际 DeepSeek 问答已另行运行成功。

## 目前的不足

- PPTX 只能读取文字，不能识别图片里的内容，暂时不支持 PDF 和 Word。
- 检索依赖问题中的词语。提问太笼统，或者追问只写“它有什么用”，可能找不到合适的片段，最好带上具体的知识点名称。
- 复习提纲根据检索到的片段生成，不一定覆盖整份资料。模型回答也可能有误，需要结合参考原文检查。
- 资料和对话保存在运行时内存中，没有接入数据库。重启后需要重新上传资料，重要记录可以提前下载。

后续可以尝试加入中文嵌入模型，改善同义词检索，并增加 PDF 支持。

## 许可证

项目代码采用 MIT 许可证，详见 [LICENSE](LICENSE)。
