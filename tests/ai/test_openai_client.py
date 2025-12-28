"""Tests for Azure OpenAI client wrapper."""

import sys
import types
import pytest
from unittest.mock import Mock
from src.ai.openai_client import AzureOpenAIClient


class TestAzureOpenAIClient:
    """Test suite for AzureOpenAIClient."""

    @pytest.fixture
    def mock_azure_modules(self):
        """Inject mocked Azure modules into sys.modules so client can import them.

        Returns the mocked OpenAIClient class and AzureKeyCredential class.
        """
        # Create module skeletons
        azure_pkg = types.ModuleType("azure")
        azure_ai_pkg = types.ModuleType("azure.ai")
        openai_mod = types.ModuleType("azure.ai.openai")
        azure_core_pkg = types.ModuleType("azure.core")
        core_creds_mod = types.ModuleType("azure.core.credentials")

        # Mock classes
        mock_client_class = Mock()
        mock_cred_class = Mock()

        # Assign into modules
        openai_mod.OpenAIClient = mock_client_class
        core_creds_mod.AzureKeyCredential = mock_cred_class

        # Register into sys.modules
        sys.modules["azure"] = azure_pkg
        sys.modules["azure.ai"] = azure_ai_pkg
        sys.modules["azure.ai.openai"] = openai_mod
        sys.modules["azure.core"] = azure_core_pkg
        sys.modules["azure.core.credentials"] = core_creds_mod

        return mock_client_class, mock_cred_class

    def test_init_with_env_vars(self, mock_azure_modules, monkeypatch):
        """Test initialization using environment variables."""
        mock_client_class, mock_cred_class = mock_azure_modules

        # Set environment vars
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        monkeypatch.setenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"
        )

        client = AzureOpenAIClient()
        assert client.endpoint == "https://test.openai.azure.com/"
        assert client.api_key == "test-key"
        assert client.chat_deployment == "gpt-4"
        assert client.embed_deployment == "text-embedding-ada-002"
        assert client._client is mock_client_class.return_value
        mock_cred_class.assert_called_once_with("test-key")
        mock_client_class.assert_called_once()

    def test_init_with_params(self, mock_azure_modules):
        """Test initialization with explicit parameters."""
        mock_client_class, mock_cred_class = mock_azure_modules
        client = AzureOpenAIClient(
            endpoint="https://custom.openai.azure.com/",
            api_key="custom-key",
            chat_deployment="custom-gpt",
            embed_deployment="custom-embed",
        )
        assert client.endpoint == "https://custom.openai.azure.com/"
        assert client.api_key == "custom-key"
        assert client.chat_deployment == "custom-gpt"
        assert client.embed_deployment == "custom-embed"
        assert client._client is mock_client_class.return_value
        mock_cred_class.assert_called_once_with("custom-key")
        mock_client_class.assert_called_once()

    def test_init_missing_sdk(self, monkeypatch):
        """Test initialization when SDK is not available."""
        # Ensure azure modules are not present and no env vars
        for key in list(sys.modules.keys()):
            if key.startswith("azure"):
                del sys.modules[key]
        client = AzureOpenAIClient(endpoint="test", api_key="test")
        assert client._client is None

    def test_chat_completion_success(self, mock_azure_modules):
        """Test successful chat completion."""
        mock_client_class, mock_cred_class = mock_azure_modules
        mock_client = mock_client_class.return_value

        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Test response"
        mock_response.choices = [mock_choice]
        mock_client.get_chat_completions.return_value = mock_response

        client = AzureOpenAIClient(
            endpoint="test", api_key="test", chat_deployment="gpt-4"
        )
        messages = [{"role": "user", "content": "Hello"}]

        result = client.chat_completion(messages)

        assert result["content"] == "Test response"
        assert result["raw"] == mock_response
        mock_client.get_chat_completions.assert_called_once_with(
            "gpt-4", messages=messages, max_tokens=1024
        )

    def test_chat_completion_with_custom_deployment(self, mock_azure_modules):
        """Test chat completion with custom deployment."""
        mock_client_class, mock_cred_class = mock_azure_modules
        mock_client = mock_client_class.return_value

        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_response.choices = [mock_choice]
        mock_client.get_chat_completions.return_value = mock_response

        client = AzureOpenAIClient(
            endpoint="test", api_key="test", chat_deployment="gpt-4"
        )
        messages = [{"role": "user", "content": "Hello"}]

        result = client.chat_completion(messages, deployment="custom-gpt")

        assert result["content"] == "Response"
        mock_client.get_chat_completions.assert_called_once_with(
            "custom-gpt", messages=messages, max_tokens=1024
        )

    def test_chat_completion_no_client(self):
        """Test chat completion when client is not initialized."""
        client = AzureOpenAIClient()  # No credentials
        with pytest.raises(RuntimeError, match="Azure OpenAI SDK not configured"):
            client.chat_completion([])

    def test_chat_completion_no_deployment(self, mock_azure_modules):
        """Test chat completion without deployment."""
        mock_client_class, mock_cred_class = mock_azure_modules
        mock_client = mock_client_class.return_value

        client = AzureOpenAIClient(endpoint="test", api_key="test")
        with pytest.raises(ValueError, match="chat deployment name is required"):
            client.chat_completion([])

    def test_create_embeddings_success(self, mock_azure_modules):
        """Test successful embedding creation."""
        mock_client_class, mock_cred_class = mock_azure_modules
        mock_client = mock_client_class.return_value

        mock_response = Mock()
        mock_data1 = Mock()
        mock_data1.embedding = [0.1, 0.2, 0.3]
        mock_data2 = Mock()
        mock_data2.embedding = [0.4, 0.5, 0.6]
        mock_response.data = [mock_data1, mock_data2]
        mock_client.get_embeddings.return_value = mock_response

        client = AzureOpenAIClient(
            endpoint="test", api_key="test", embed_deployment="embed-model"
        )
        texts = ["text1", "text2"]

        result = client.create_embeddings(texts)

        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_client.get_embeddings.assert_called_once_with("embed-model", input=texts)

    def test_create_embeddings_no_client(self):
        """Test embedding creation when client is not initialized."""
        client = AzureOpenAIClient()
        with pytest.raises(RuntimeError, match="Azure OpenAI SDK not configured"):
            client.create_embeddings([])

    def test_create_embeddings_no_deployment(self, mock_azure_modules):
        """Test embedding creation without deployment."""
        mock_client_class, mock_cred_class = mock_azure_modules
        mock_client = mock_client_class.return_value

        client = AzureOpenAIClient(endpoint="test", api_key="test")
        with pytest.raises(ValueError, match="embedding deployment name is required"):
            client.create_embeddings([])
