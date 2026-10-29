from io import BytesIO
import zipfile
import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from core import KnowledgeBase, load_document, answer, create_model


def test_pptx_page_source():
    data = BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        for page, content in [(2, 'RAG 检索增强生成'), (1, '课程首页')]:
            z.writestr(f'ppt/slides/slide{page}.xml',
                       f'<a:root xmlns:a="urn:test"><a:t>{content}</a:t></a:root>')
    docs = load_document('demo.pptx', data.getvalue())
    assert docs[1].metadata == {'source': 'demo.pptx', 'page': 2}
    assert docs[0].page_content == '课程首页'


def test_retrieval_and_no_evidence():
    docs = load_document('notes.md', 'RAG 检索增强生成：先检索资料再生成答案。'.encode())
    kb = KnowledgeBase(docs)
    assert kb.search('RAG 的步骤')[0].document.metadata['source'] == 'notes.md'
    assert kb.search('xyz987654') == []
    assert '资料不足' in answer('xyz', [], None)


def test_reordered_pptx():
    data = BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('ppt/presentation.xml', '<p:root xmlns:p="urn:p" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldId r:id="r2"/><p:sldId r:id="r1"/></p:root>')
        z.writestr('ppt/_rels/presentation.xml.rels', '<Relationships><Relationship Id="r1" Target="slides/slide1.xml"/><Relationship Id="r2" Target="slides/slide2.xml"/></Relationships>')
        for i in [1, 2]:
            z.writestr(f'ppt/slides/slide{i}.xml', f'<a:root xmlns:a="urn:a"><a:t>内容{i}</a:t></a:root>')
    docs = load_document('reordered.pptx', data.getvalue())
    assert docs[0].page_content == '内容2'
    assert docs[0].metadata['page'] == 1


def test_real_langchain_pipeline_with_fake_model():
    kb = KnowledgeBase(load_document('a.txt', 'LangChain 使用提示模板构造模型输入。'.encode()))
    model = FakeListChatModel(responses=['使用提示模板。[1]'])
    assert answer('LangChain', kb.search('LangChain'), model) == '使用提示模板。[1]'


@pytest.mark.parametrize('name,data', [('a.txt', b''), ('a.pdf', b'abc'), ('a.pptx', b'bad'), ('a.txt', b'\xff')])
def test_bad_documents(name, data):
    with pytest.raises(ValueError):
        load_document(name, data)


def test_configuration_errors():
    with pytest.raises(ValueError):
        create_model('DeepSeek 在线模型', 'deepseek-chat')
    with pytest.raises(ValueError):
        create_model('Ollama 本地模型', 'qwen', base_url='https://example.com')
