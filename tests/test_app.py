from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_retrieval_ui_and_clear():
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'))
    at.run(timeout=30)
    assert not at.exception
    at.chat_input[0].set_value('RAG 的基本流程是什么？').run(timeout=30)
    assert not at.exception
    assert len(at.chat_message) == 2
    assert '未调用大模型' in at.chat_message[1].markdown[0].value
    at.button[0].click().run()
    assert not at.exception
    assert len(at.chat_message) == 0
