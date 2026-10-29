import httpx
import pytest
from core import normalize_api_key, model_error_message, create_model, check_deepseek_key


def test_key_whitespace_and_official_endpoint(monkeypatch):
    import langchain_deepseek
    monkeypatch.setenv('DEEPSEEK_API_BASE', 'https://example.invalid')
    monkeypatch.setattr(langchain_deepseek, 'ChatDeepSeek', lambda **kwargs: kwargs)
    result = create_model('DeepSeek 在线模型', 'deepseek-chat', '  test-key\n')
    assert result['api_key'] == 'test-key'
    assert result['base_url'] == 'https://api.deepseek.com'


@pytest.mark.parametrize('key', ['', 'Bearer test', 'a\nb', '"test"', 'sk-****'])
def test_invalid_key_format(key):
    with pytest.raises(ValueError):
        normalize_api_key(key)


@pytest.mark.parametrize('status', [401, 402, 403, 404, 429])
def test_safe_specific_errors(status):
    response = httpx.Response(status, request=httpx.Request('GET', 'https://api.deepseek.com/models'))
    exc = httpx.HTTPStatusError('PRIVATE_TEST_SECRET', request=response.request, response=response)
    message = model_error_message(exc)
    assert str(status) in message
    assert 'PRIVATE_TEST_SECRET' not in message


def test_key_check_sends_only_to_models(monkeypatch):
    real_client = httpx.Client
    def handle(request):
        assert str(request.url) == 'https://api.deepseek.com/models'
        assert request.method == 'GET'
        assert request.headers['Authorization'] == 'Bearer test-key'
        return httpx.Response(200, json={'data': []})
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: real_client(
        transport=httpx.MockTransport(handle), **kwargs))
    check_deepseek_key(' test-key ')
