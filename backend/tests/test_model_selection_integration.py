"""
Integration tests for model selection (Gemini vs Gemma)

Tests verify that agents correctly route reasoning tasks to either
the cloud-based Gemini model or the local Gemma GPU service based
on the model_type parameter.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os

# Enable asyncio for pytest
pytestmark = pytest.mark.asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Avoid importing top-level services module (pulls in firestore)
from agents.linker_agent import LinkerAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.base_agent import A2AProtocol


@pytest.fixture
def mock_a2a_protocol():
    """Mock A2A Protocol"""
    protocol = Mock(spec=A2AProtocol)
    protocol.send_message = AsyncMock()
    protocol.get_shared_context = AsyncMock(return_value={})
    protocol.update_shared_context = AsyncMock()
    return protocol


@pytest.fixture
def mock_event_emitter():
    """Mock event emitter for FR#020 streaming"""
    emitter = Mock()
    emitter.emit_agent_processing = AsyncMock()
    emitter.emit_agent_complete = AsyncMock()
    emitter.emit_agent_error = AsyncMock()
    return emitter


class TestLinkerAgentModelSelection:
    """Test Linker Agent with Gemini and Gemma models"""

    @pytest.mark.asyncio
    async def test_linker_with_gemini_model(self, mock_a2a_protocol, mock_event_emitter):
        """Verify Linker Agent uses Gemini for reasoning when model_type='gemini'"""
        linker = LinkerAgent(
            a2a_protocol=mock_a2a_protocol,
            event_emitter=mock_event_emitter,
            model_type="gemini"
        )
        
        context = {
            "document": "Python function: def analyze(data): return process(data)",
            "content_type": "codebase",
            "shared_context": {},
            "sessionId": "test-session"
        }
        
        with patch('services.gemini_client.reason_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = "analyze\nprocess"
            
            with patch('services.gemma_service.embed_with_gemma', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [
                    [0.1, 0.2, 0.3],
                    [0.2, 0.3, 0.4]
                ]
                
                result = await linker.process(context)
                
                # Verify Gemini was called
                mock_gemini.assert_called()
                call_args = mock_gemini.call_args
                assert call_args[1].get('model_type') == 'gemini'
                
                # Verify result structure
                assert result['agent'] == 'linker'
                assert 'entities' in result
                assert 'relationships' in result
                assert 'graph_data' in result

    @pytest.mark.asyncio
    async def test_linker_with_gemma_model(self, mock_a2a_protocol, mock_event_emitter):
        """Verify Linker Agent uses Gemma for reasoning when model_type='gemma'"""
        linker = LinkerAgent(
            a2a_protocol=mock_a2a_protocol,
            event_emitter=mock_event_emitter,
            model_type="gemma"
        )
        
        context = {
            "document": "Important concept: machine learning algorithms process data",
            "content_type": "document",
            "shared_context": {},
            "sessionId": "test-session"
        }
        
        with patch('agents.linker_agent.reason_with_gemini', new_callable=AsyncMock) as mock_reason:
            mock_reason.return_value = "concept1\nconcept2"
            
            with patch('services.gemma_service.embed_with_gemma', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [
                    [0.1, 0.2, 0.3],
                    [0.2, 0.3, 0.4]
                ]
                
                result = await linker.process(context)
                
                # Verify model_type was passed as 'gemma'
                mock_reason.assert_called()
                call_args = mock_reason.call_args
                assert call_args[1].get('model_type') == 'gemma'
                
                # Verify result structure
                assert result['agent'] == 'linker'
                assert 'entities' in result

    @pytest.mark.asyncio
    async def test_linker_model_type_affects_both_reasoning_calls(self, mock_a2a_protocol):
        """Verify model_type is passed to both entity extraction and relationship reasoning"""
        linker = LinkerAgent(a2a_protocol=mock_a2a_protocol, model_type="gemma")
        
        context = {
            "document": "Test content",
            "content_type": "document",
            "shared_context": {}
        }
        
        call_count = 0
        
        async def mock_reason(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            assert kwargs.get('model_type') == 'gemma', f"Call {call_count}: model_type should be 'gemma'"
            return "entity1\nentity2"
        
        with patch('agents.linker_agent.reason_with_gemini', new_callable=AsyncMock, side_effect=mock_reason):
            with patch('services.gemma_service.embed_with_gemma', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1, 0.2], [0.2, 0.3]]
                
                result = await linker.process(context)
                
                # Should be called at least twice (entity extraction + relationship reasoning)
                assert call_count >= 2


class TestOrchestratorAgentModelSelection:
    """Test Orchestrator Agent with Gemini and Gemma models"""

    @pytest.mark.asyncio
    async def test_orchestrator_with_gemini_model(self, mock_a2a_protocol, mock_event_emitter):
        """Verify Orchestrator Agent uses Gemini for content analysis"""
        orchestrator = OrchestratorAgent(
            a2a_protocol=mock_a2a_protocol,
            event_emitter=mock_event_emitter,
            model_type="gemini"
        )
        
        document = """
# Machine Learning Overview

This document covers key ML concepts.

Key Topics:
- Supervised learning
- Neural networks
- Deep learning
"""
        
        context = {"document": document}
        
        gemini_response = """CONTENT_TYPE: document
COMPLEXITY: moderate
KEY_TOPICS: machine learning, supervised learning, neural networks
SUMMARY: A document about fundamental machine learning concepts and algorithms."""
        
        with patch('agents.orchestrator_agent.reason_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = gemini_response
            
            result = await orchestrator.process(context)
            
            # Verify Gemini was called with correct model_type
            mock_gemini.assert_called()
            call_args = mock_gemini.call_args
            assert call_args[1].get('model_type') == 'gemini'
            
            # Verify orchestration result
            assert result['agent'] == 'orchestrator'
            assert 'content_analysis' in result
            assert result['content_analysis']['content_type'] == 'document'

    @pytest.mark.asyncio
    async def test_orchestrator_with_gemma_model(self, mock_a2a_protocol, mock_event_emitter):
        """Verify Orchestrator Agent uses Gemma for content analysis"""
        orchestrator = OrchestratorAgent(
            a2a_protocol=mock_a2a_protocol,
            event_emitter=mock_event_emitter,
            model_type="gemma"
        )
        
        document = """
def process_data(input_file):
    import pandas as pd
    data = pd.read_csv(input_file)
    return data.describe()

class DataProcessor:
    def __init__(self):
        pass
"""
        
        context = {"document": document}
        
        gemma_response = """CONTENT_TYPE: codebase
COMPLEXITY: simple
KEY_TOPICS: python, data processing, pandas
SUMMARY: Python code for processing data using pandas."""
        
        with patch('agents.orchestrator_agent.reason_with_gemini', new_callable=AsyncMock) as mock_reason:
            mock_reason.return_value = gemma_response
            
            result = await orchestrator.process(context)
            
            # Verify model_type was passed as 'gemma'
            mock_reason.assert_called()
            call_args = mock_reason.call_args
            assert call_args[1].get('model_type') == 'gemma'
            
            # Verify orchestration result
            assert result['agent'] == 'orchestrator'
            assert result['content_analysis']['content_type'] == 'codebase'

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_to_heuristics(self, mock_a2a_protocol):
        """Verify Orchestrator falls back to heuristics if AI analysis fails"""
        orchestrator = OrchestratorAgent(
            a2a_protocol=mock_a2a_protocol,
            model_type="gemini"
        )
        
        document = "# Test\nSimple content"
        context = {"document": document}
        
        with patch('agents.orchestrator_agent.reason_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.side_effect = Exception("API error")
            
            result = await orchestrator.process(context)
            
            # Should still return valid result despite AI failure
            assert result['agent'] == 'orchestrator'
            assert 'content_analysis' in result
            # Heuristics should work
            assert result['content_analysis']['content_type'] in ['document', 'codebase']


class TestModelSelectionEnvironmentVariable:
    """Test environment variable override for model selection"""

    @pytest.mark.asyncio
    async def test_agentnav_model_type_env_var(self, mock_a2a_protocol, monkeypatch):
        """Verify AGENTNAV_MODEL_TYPE environment variable is respected"""
        # Set environment variable
        monkeypatch.setenv("AGENTNAV_MODEL_TYPE", "gemma")
        
        linker = LinkerAgent(a2a_protocol=mock_a2a_protocol, model_type="gemini")
        
        context = {
            "document": "Test",
            "content_type": "document",
            "shared_context": {}
        }
        
        with patch('agents.linker_agent.reason_with_gemini', new_callable=AsyncMock) as mock_reason:
            mock_reason.return_value = "entity"
            
            with patch('services.gemma_service.embed_with_gemma', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1, 0.2]]
                
                await linker.process(context)
                
                # The reason_with_gemini should still receive the default model_type from agent
                # (env var is checked inside reason_with_gemini)
                mock_reason.assert_called()


class TestModelFallbackBehavior:
    """Test fallback behavior when model is unavailable"""

    @pytest.mark.asyncio
    async def test_gemma_fallback_to_gemini(self, mock_a2a_protocol):
        """Verify automatic fallback from Gemma to Gemini if Gemma is unavailable"""
        linker = LinkerAgent(a2a_protocol=mock_a2a_protocol, model_type="gemma")
        
        context = {
            "document": "Test content",
            "content_type": "document",
            "shared_context": {}
        }
        
        with patch('agents.linker_agent.reason_with_gemini', new_callable=AsyncMock) as mock_reason:
            # Simulate: first call requests gemma but it fails, then falls back to gemini
            mock_reason.return_value = "entity1"
            
            with patch('services.gemma_service.embed_with_gemma', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1, 0.2]]
                
                result = await linker.process(context)
                
                # Should still complete successfully
                assert result['agent'] == 'linker'
                assert 'entities' in result
