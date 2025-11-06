"""
Unit tests for Suggestion Agent and API endpoints (FR#201)

Tests verify that the Suggestion Agent correctly analyzes prompts,
provides optimization suggestions, generates structured schemas,
and integrates with the ADK/A2A Protocol.

Required Coverage: 70%+ for all new code
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.main import app
from backend.agents import SuggestionAgent, A2AProtocol
from backend.models.suggestion_models import (
    PromptSuggestionRequest,
    PromptSuggestionResponse,
    StructuredOutputSchema,
    FunctionCallingHint,
)

# TestClient with base_url to satisfy TrustedHostMiddleware
client = TestClient(app, base_url="http://localhost")


class TestSuggestionAgentCore:
    """Test core Suggestion Agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test Suggestion Agent can be initialized properly"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        assert agent.name == "suggestion"
        assert agent.a2a == a2a
        assert agent.state.value == "idle"
    
    @pytest.mark.asyncio
    async def test_agent_process_with_valid_prompt(self):
        """Test agent processes valid prompt and returns suggestions"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        # Mock Gemini service
        with patch("services.gemini_client.reason_with_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = """
OPTIMIZATION_SUGGESTIONS:
- Add input validation requirements
- Specify the programming language
- Include error handling expectations

STRUCTURED_OUTPUT_SCHEMA:
{"type": "object", "properties": {"code": {"type": "string"}}}

FUNCTION_CALLING_HINT:
NOT_APPLICABLE

QUALITY_SCORE: 7
STRENGTHS: Clear task definition
WEAKNESSES: Lacks context
ACTIONABLE_IMPROVEMENTS: Specify programming language
"""
            
            context = {
                "prompt_text": "Write a function that calculates factorial",
                "user_context": "Educational tutorial",
            }
            
            result = await agent.process(context)
            
            assert result["agent"] == "suggestion"
            assert "optimization_suggestions" in result
            assert len(result["optimization_suggestions"]) > 0
            assert result["quality_score"] >= 1
            assert result["quality_score"] <= 10
            assert result["processing_complete"] is True
    
    @pytest.mark.asyncio
    async def test_agent_process_empty_prompt_raises_error(self):
        """Test agent raises ValueError for empty prompt"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        context = {"prompt_text": ""}
        
        with pytest.raises(ValueError, match="Prompt text is required"):
            await agent.process(context)
    
    @pytest.mark.asyncio
    async def test_agent_fallback_analysis(self):
        """Test agent uses fallback analysis when Gemini fails"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        # Mock Gemini service to fail
        with patch(
            "services.gemini_client.reason_with_gemini",
            new_callable=AsyncMock,
            side_effect=Exception("Gemini service unavailable"),
        ):
            context = {
                "prompt_text": "Write a short story",
                "user_context": "",
            }
            
            result = await agent.process(context)
            
            # Should still return valid result with fallback
            assert result["agent"] == "suggestion"
            assert "optimization_suggestions" in result
            assert result["quality_score"] > 0
    
    @pytest.mark.asyncio
    async def test_agent_a2a_notification(self):
        """Test agent sends A2A Protocol notification on completion"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        with patch("services.gemini_client.reason_with_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = """
OPTIMIZATION_SUGGESTIONS:
- Test suggestion

STRUCTURED_OUTPUT_SCHEMA:
NOT_APPLICABLE

FUNCTION_CALLING_HINT:
NOT_APPLICABLE

QUALITY_SCORE: 5
STRENGTHS: Basic structure
WEAKNESSES: Limited detail
ACTIONABLE_IMPROVEMENTS: Add more context
"""
            
            context = {"prompt_text": "Test prompt"}
            
            # Spy on A2A message sending
            with patch.object(a2a, "send_message", new_callable=AsyncMock) as mock_send:
                await agent.process(context)
                
                # Verify A2A message was sent
                assert mock_send.called
                call_args = mock_send.call_args[0][0]
                assert call_args.from_agent == "suggestion"
                assert call_args.message_type == "suggestion_complete"


class TestSuggestionAgentParsing:
    """Test Suggestion Agent response parsing"""
    
    @pytest.mark.asyncio
    async def test_parse_structured_schema(self):
        """Test parsing of structured output schema"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        with patch("services.gemini_client.reason_with_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = """
OPTIMIZATION_SUGGESTIONS:
- Test

STRUCTURED_OUTPUT_SCHEMA:
{"type": "object", "properties": {"result": {"type": "number"}}, "required": ["result"]}

FUNCTION_CALLING_HINT:
NOT_APPLICABLE

QUALITY_SCORE: 8
STRENGTHS: Good
WEAKNESSES: None
ACTIONABLE_IMPROVEMENTS: None
"""
            
            context = {"prompt_text": "Test"}
            result = await agent.process(context)
            
            assert result["structured_output_schema"] is not None
            assert result["structured_output_schema"]["type"] == "object"
            assert "properties" in result["structured_output_schema"]
    
    @pytest.mark.asyncio
    async def test_parse_function_hint(self):
        """Test parsing of function calling hint"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        with patch("services.gemini_client.reason_with_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = """
OPTIMIZATION_SUGGESTIONS:
- Test

STRUCTURED_OUTPUT_SCHEMA:
NOT_APPLICABLE

FUNCTION_CALLING_HINT:
{"name": "calculate", "description": "Performs calculation", "parameters": {"type": "object"}}

QUALITY_SCORE: 7
STRENGTHS: Good
WEAKNESSES: None
ACTIONABLE_IMPROVEMENTS: None
"""
            
            context = {"prompt_text": "Test"}
            result = await agent.process(context)
            
            assert result["function_calling_hint"] is not None
            assert result["function_calling_hint"]["name"] == "calculate"
    
    @pytest.mark.asyncio
    async def test_parse_list_items(self):
        """Test parsing of list items with various formats"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        # Test with bullet points
        lines = ["- First item", "- Second item", "• Third item", "* Fourth item"]
        parsed = agent._parse_list_items(lines)
        
        assert len(parsed) == 4
        assert "First item" in parsed
        assert "Second item" in parsed


class TestSuggestionAPIEndpoints:
    """Test Suggestion API endpoints"""
    
    def test_analyze_endpoint_success(self):
        """Test /api/v1/suggestions/analyze endpoint with valid request"""
        with (
            patch("backend.agents.SuggestionAgent") as mock_agent_class,
            patch("backend.agents.A2AProtocol") as mock_a2a,
        ):
            # Mock agent execution
            mock_agent = MagicMock()
            mock_agent.execute = AsyncMock(return_value={
                "agent": "suggestion",
                "prompt_analyzed": "Test prompt...",
                "optimization_suggestions": ["Add more detail", "Specify format"],
                "structured_output_schema": None,
                "function_calling_hint": None,
                "quality_score": 7,
                "strengths": ["Clear"],
                "weaknesses": ["Too brief"],
                "actionable_improvements": ["Add examples"],
                "processing_complete": True,
                "timestamp": 1699999999.0,
            })
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/v1/suggestions/analyze",
                json={
                    "prompt_text": "Test prompt",
                    "user_context": "Testing",
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent"] == "suggestion"
            assert "optimization_suggestions" in data
            assert data["quality_score"] == 7
    
    def test_analyze_endpoint_empty_prompt(self):
        """Test analyze endpoint rejects empty prompt"""
        response = client.post(
            "/api/v1/suggestions/analyze",
            json={"prompt_text": ""},
        )
        
        # Should return validation error
        assert response.status_code == 422  # Pydantic validation error
    
    def test_analyze_endpoint_missing_prompt(self):
        """Test analyze endpoint requires prompt_text"""
        response = client.post(
            "/api/v1/suggestions/analyze",
            json={"user_context": "Test"},
        )
        
        assert response.status_code == 422  # Missing required field
    
    def test_analyze_endpoint_agent_unavailable(self):
        """Test analyze endpoint handles agent unavailability"""
        with patch(
            "backend.agents.SuggestionAgent",
            side_effect=ImportError("Agent not available"),
        ):
            response = client.post(
                "/api/v1/suggestions/analyze",
                json={"prompt_text": "Test prompt"},
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "error" in data["detail"]
    
    def test_health_endpoint_success(self):
        """Test /api/v1/suggestions/health endpoint"""
        with (
            patch("backend.agents.SuggestionAgent") as mock_agent_class,
            patch("backend.agents.A2AProtocol") as mock_a2a,
        ):
            mock_agent = MagicMock()
            mock_agent.name = "suggestion"
            mock_agent.state.value = "idle"
            mock_agent_class.return_value = mock_agent
            
            response = client.get("/api/v1/suggestions/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["agent"] == "suggestion"
            assert data["available"] is True
    
    def test_health_endpoint_agent_unavailable(self):
        """Test health endpoint when agent is unavailable"""
        with patch(
            "backend.agents.SuggestionAgent",
            side_effect=ImportError("Agent not available"),
        ):
            response = client.get("/api/v1/suggestions/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"
            assert data["available"] is False
    
    def test_examples_endpoint(self):
        """Test /api/v1/suggestions/examples endpoint"""
        response = client.get("/api/v1/suggestions/examples")
        
        assert response.status_code == 200
        data = response.json()
        assert "examples" in data
        assert len(data["examples"]) > 0
        assert "usage_tips" in data
        
        # Verify example structure
        first_example = data["examples"][0]
        assert "name" in first_example
        assert "prompt_text" in first_example
        assert "expected_suggestions" in first_example


class TestSuggestionModels:
    """Test Pydantic models for suggestion API"""
    
    def test_prompt_suggestion_request_validation(self):
        """Test PromptSuggestionRequest validation"""
        # Valid request
        request = PromptSuggestionRequest(
            prompt_text="Test prompt",
            user_context="Testing",
        )
        assert request.prompt_text == "Test prompt"
        assert request.user_context == "Testing"
        
        # Empty prompt should fail
        with pytest.raises(ValueError):
            PromptSuggestionRequest(prompt_text="")
    
    def test_prompt_suggestion_request_whitespace_trimming(self):
        """Test request trims whitespace from prompt"""
        request = PromptSuggestionRequest(prompt_text="  Test prompt  ")
        assert request.prompt_text == "Test prompt"
    
    def test_structured_output_schema_model(self):
        """Test StructuredOutputSchema model"""
        schema = StructuredOutputSchema(
            type="object",
            properties={"field": {"type": "string"}},
            required=["field"],
            description="Test schema",
        )
        
        assert schema.type == "object"
        assert "field" in schema.properties
        assert "field" in schema.required
    
    def test_function_calling_hint_model(self):
        """Test FunctionCallingHint model"""
        hint = FunctionCallingHint(
            name="test_function",
            description="Test function",
            parameters={"type": "object"},
            rationale="For testing",
        )
        
        assert hint.name == "test_function"
        assert hint.description == "Test function"
    
    def test_prompt_suggestion_response_model(self):
        """Test PromptSuggestionResponse model"""
        response = PromptSuggestionResponse(
            agent="suggestion",
            prompt_analyzed="Test...",
            optimization_suggestions=["Suggestion 1"],
            quality_score=8,
            strengths=["Good"],
            weaknesses=["Could improve"],
            actionable_improvements=["Add detail"],
            timestamp=1699999999.0,
        )
        
        assert response.agent == "suggestion"
        assert response.quality_score == 8
        assert len(response.optimization_suggestions) == 1
    
    def test_quality_score_validation(self):
        """Test quality score must be between 1 and 10"""
        # Valid scores
        response = PromptSuggestionResponse(
            prompt_analyzed="Test",
            quality_score=5,
            timestamp=1699999999.0,
        )
        assert response.quality_score == 5
        
        # Invalid score (too high)
        with pytest.raises(ValueError):
            PromptSuggestionResponse(
                prompt_analyzed="Test",
                quality_score=11,
                timestamp=1699999999.0,
            )
        
        # Invalid score (too low)
        with pytest.raises(ValueError):
            PromptSuggestionResponse(
                prompt_analyzed="Test",
                quality_score=0,
                timestamp=1699999999.0,
            )


class TestSuggestionAgentIntegration:
    """Integration tests for Suggestion Agent with ADK/A2A Protocol"""
    
    @pytest.mark.asyncio
    async def test_agent_workflow_integration(self):
        """Test Suggestion Agent integrates with AgentWorkflow"""
        from backend.agents import AgentWorkflow
        
        workflow = AgentWorkflow()
        a2a = workflow.a2a
        agent = SuggestionAgent(a2a)
        
        workflow.register_agent(agent)
        
        assert "suggestion" in workflow.agents
        assert workflow.agents["suggestion"] == agent
    
    @pytest.mark.asyncio
    async def test_a2a_message_handling(self):
        """Test agent handles A2A Protocol messages"""
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        from backend.agents.base_agent import A2AMessage
        
        # Create task delegation message
        message = A2AMessage(
            message_id="test_001",
            from_agent="orchestrator",
            to_agent="suggestion",
            message_type="task_delegation",
            data={"task": "analyze_prompt", "prompt_text": "Test"},
        )
        
        # Agent should handle message without error
        await agent._handle_a2a_message(message)
        
        # Verify message was processed (logged)
        assert True  # No exception means success


# Coverage target: 70%+
# This test suite covers:
# - Agent initialization and core functionality
# - Prompt processing and analysis
# - Response parsing (schemas, functions, lists)
# - API endpoint behavior (success and error cases)
# - Pydantic model validation
# - ADK/A2A Protocol integration
# - Error handling and fallback mechanisms
