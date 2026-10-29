from pathlib import Path
import hashlib
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
import streamlit as st

from core import KnowledgeBase, answer, create_model, format_context, load_document

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
st.set_page_config(page_title='课伴 · 课程资料智能助手', page_icon='📖', layout='wide')
st.title('📖 课伴 CourseMate')
st.caption('把课件变成可追溯的学习对话 · LangChain + RAG')

with st.sidebar:
    st.header('模型与资料')
    provider = st.selectbox('运行模式', ['检索体验（不调用大模型）', 'DeepSeek 在线模型', 'Ollama 本地模型'])
    key, model_name, url = '', '', ''
    if provider == 'DeepSeek 在线模型':
        key = st.text_input('API Key', type='password', value=os.getenv('DEEPSEEK_API_KEY', ''))
        model_name = st.text_input('模型名称', os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'))
        st.caption('提问时，会把问题、相关资料片段和最近对话发送给 DeepSeek。')
    elif provider == 'Ollama 本地模型':
        model_name = st.text_input('本地模型名称', os.getenv('OLLAMA_MODEL', 'qwen2.5:3b'))
        url = st.text_input('Ollama 地址', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
    else:
        st.info('此模式只展示检索原文，不生成 AI 回答。正式演示请切换到大模型模式。')
    use_sample = st.checkbox('加入内置示例笔记', value=True)
    files = st.file_uploader('上传课件或笔记', type=['pptx', 'txt', 'md'], accept_multiple_files=True)
    k = st.slider('最多检索片段数', 2, 6, 4)
    if st.button('清空对话'):
        st.session_state.messages = []

payloads = []
if use_sample:
    payloads.append(('示例学习笔记.md', (ROOT / 'data' / 'sample.md').read_bytes()))
payloads.extend((f.name, f.getvalue()) for f in files)
if len(payloads) > 10:
    st.error('一次最多加载 10 个文件。')
    st.stop()
fingerprint = hashlib.sha256()
for name, data in payloads:
    fingerprint.update(name.encode())
    fingerprint.update(data)
signature = fingerprint.hexdigest()
if st.session_state.get('signature') != signature:
    st.session_state.pop('kb', None)
    st.session_state.messages = []
    try:
        docs = [d for name, data in payloads for d in load_document(name, data)]
        if docs:
            st.session_state.kb = KnowledgeBase(docs)
            st.session_state.signature = signature
    except Exception as exc:
        st.error(f'资料处理失败：{type(exc).__name__}。请检查格式、编码和文件大小。')
        st.stop()

kb = st.session_state.get('kb')
if kb is None:
    st.info('请上传资料，或勾选内置示例笔记。')
    st.stop()
st.success(f'知识库已就绪：{len(payloads)} 个文件，{len(kb.chunks)} 个文本片段。')
st.caption('可问：“RAG 包括哪些步骤？”“总结 RAG 的复习提纲”“围绕 LangChain 出三道练习题”。追问时请保留主题关键词。')
if 'messages' not in st.session_state:
    st.session_state.messages = []


def show_sources(sources):
    if sources:
        with st.expander('查看本轮参考原文'):
            st.text(sources)


for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        show_sources(msg.get('sources'))

question = st.chat_input('输入课程问题，或指定一个复习主题', max_chars=2000)
if question:
    with st.chat_message('user'):
        st.markdown(question)
    with st.chat_message('assistant'):
        try:
            hits = kb.search(question, k)
            sources = format_context(hits)
            if provider == '检索体验（不调用大模型）':
                result = ('**检索结果（未调用大模型）**\n\n' + sources if hits
                          else '当前资料不足以回答。请补充资料或调整关键词。')
            else:
                model = create_model(provider, model_name, key, url)
                history = [HumanMessage(content=m['content']) if m['role'] == 'user'
                           else AIMessage(content=m['content'])
                           for m in st.session_state.messages[-6:]]
                with st.spinner('正在根据资料生成回答…'):
                    result = answer(question, hits, model, history)
            st.markdown(result)
            show_sources(sources)
            st.session_state.messages.extend([
                {'role': 'user', 'content': question},
                {'role': 'assistant', 'content': result, 'sources': sources, 'provider': provider}])
            st.session_state.messages = st.session_state.messages[-20:]
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f'模型调用失败（{type(exc).__name__}）。请检查密钥、余额、网络，或 Ollama 服务及模型名称。')
            st.caption('失败请求不会写入对话。未显示服务端原始错误，以免意外暴露密钥。')

if st.session_state.messages:
    transcript = '# 课伴学习记录\n\n' + '\n\n'.join(
        f'## {"提问" if m["role"] == "user" else "回答"}\n\n{m["content"]}'
        + (f'\n\n运行模式：{m["provider"]}\n\n### 参考原文\n\n{m["sources"]}' if 'sources' in m else '')
        for m in st.session_state.messages)
    st.download_button('下载学习记录（Markdown）', transcript, '学习记录.md', 'text/markdown')
