#!/usr/bin/env python3
"""Test script for Suggestion Agent."""
import asyncio
import os
import sys
from app.agents.suggestion import SuggestionAgent

async def test_analyze_prompt():
    """Test analyzing an existing prompt."""
    print("=" * 60)
    print("Testing Suggestion Agent - Prompt Analysis")
    print("=" * 60)
    
    # Initialize agent
    agent = SuggestionAgent()
    
    if not agent.model:
        print("❌ ERROR: Gemini API not configured")
        print("   Please set GEMINI_API_KEY environment variable")
        return
    
    # Test prompt
    test_prompt = """Write a function that sorts a list of numbers."""
    
    print(f"\n📝 Analyzing prompt:\n{test_prompt}\n")
    
    try:
        result = await agent.process({
            "prompt_text": test_prompt,
            "session_id": "test-session-123",
        })
        
        print("✅ Analysis complete!")
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        
        suggestions = result.get("suggestions", {})
        
        # Print optimization suggestions
        if "optimization_suggestions" in suggestions:
            print("\n📊 Optimization Suggestions:")
            for suggestion in suggestions["optimization_suggestions"]:
                print(f"  • [{suggestion.get('priority', 'medium').upper()}] {suggestion.get('type', 'unknown')}")
                print(f"    {suggestion.get('suggestion', 'N/A')}")
        
        # Print structured output
        if "structured_output" in suggestions:
            print("\n📋 Structured Output Recommendation:")
            so = suggestions["structured_output"]
            if so.get("recommended"):
                print("  ✅ Recommended")
                if "schema" in so:
                    print(f"  Schema: {so['schema']}")
            else:
                print("  ❌ Not recommended for this prompt")
        
        # Print function calling
        if "function_calling" in suggestions:
            print("\n🔧 Function Calling Recommendation:")
            fc = suggestions["function_calling"]
            if fc.get("recommended"):
                print("  ✅ Recommended")
                if "functions" in fc:
                    for func in fc["functions"]:
                        print(f"  • {func.get('name', 'unknown')}: {func.get('description', 'N/A')}")
            else:
                print("  ❌ Not recommended for this prompt")
        
        # Print assessment
        if "assessment" in suggestions:
            print("\n📈 Overall Assessment:")
            assessment = suggestions["assessment"]
            print(f"  Strength Score: {assessment.get('strength_score', 'N/A')}/10")
            print(f"  Strengths: {', '.join(assessment.get('strengths', []))}")
            print(f"  Weaknesses: {', '.join(assessment.get('weaknesses', []))}")
            print(f"  Priority Improvements: {', '.join(assessment.get('priority_improvements', []))}")
        
        # Print analysis metadata
        if "analysis" in result:
            print("\n📊 Analysis Metadata:")
            analysis = result["analysis"]
            print(f"  Prompt Length: {analysis.get('prompt_length', 'N/A')} characters")
            print(f"  Has System Instructions: {analysis.get('has_system_instructions', 'N/A')}")
            print(f"  Has Examples: {analysis.get('has_examples', 'N/A')}")
            print(f"  Has Constraints: {analysis.get('has_constraints', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_generate_from_requirements():
    """Test generating prompts from requirements."""
    print("\n" + "=" * 60)
    print("Testing Suggestion Agent - Generate from Requirements")
    print("=" * 60)
    
    agent = SuggestionAgent()
    
    if not agent.model:
        print("❌ ERROR: Gemini API not configured")
        return
    
    requirements = {
        "purpose": "Code review assistant that analyzes pull requests",
        "target_model": "gemini-pro",
        "constraints": ["Must output JSON", "Include severity levels"],
        "examples": []
    }
    
    print(f"\n📋 Requirements:\n{requirements}\n")
    
    try:
        result = await agent.process({
            "requirements": requirements,
            "session_id": "test-session-456",
        })
        
        print("✅ Generation complete!")
        print("\n" + "=" * 60)
        print("GENERATED SUGGESTIONS:")
        print("=" * 60)
        
        suggestions = result.get("suggestions", [])
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n📝 Suggestion #{i}:")
            print(f"  Confidence: {suggestion.get('confidence', 'N/A')}")
            print(f"  Rationale: {suggestion.get('rationale', 'N/A')}")
            print(f"  Features: {', '.join(suggestion.get('features', []))}")
            print(f"\n  Prompt:\n  {suggestion.get('prompt', 'N/A')[:200]}...")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set")
        print("   Export it with: export GEMINI_API_KEY='your-key-here'")
        print("\n   Continuing anyway to test error handling...\n")
    
    # Test 1: Analyze prompt
    await test_analyze_prompt()
    
    # Test 2: Generate from requirements
    await test_generate_from_requirements()


if __name__ == "__main__":
    asyncio.run(main())

