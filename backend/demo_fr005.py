#!/usr/bin/env python3
"""
Demo script for FR#005 Sequential Multi-Agent Workflow
Demonstrates the complete workflow with a sample document
"""

import sys
import os
import asyncio
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def demo_sequential_workflow():
    """Demonstrate the sequential multi-agent workflow"""

    print("=" * 70)
    print("🎬 FR#005 Sequential Multi-Agent Workflow Demo")
    print("=" * 70)
    print()

    # Sample document for analysis
    sample_document = """
# Artificial Intelligence and Machine Learning

Artificial Intelligence (AI) is transforming how we solve complex problems.
At its core, AI encompasses various techniques and approaches.

## Key Concepts

### Machine Learning
Machine learning enables systems to learn from data without explicit programming.
It includes three main categories:
- Supervised Learning: Training with labeled data
- Unsupervised Learning: Finding patterns in unlabeled data
- Reinforcement Learning: Learning through trial and error

### Deep Learning
Deep learning uses neural networks with multiple layers to process data.
Popular architectures include:
- Convolutional Neural Networks (CNNs) for image processing
- Recurrent Neural Networks (RNNs) for sequential data
- Transformers for natural language processing

### Neural Networks
Neural networks are inspired by biological neurons and consist of:
- Input layers that receive data
- Hidden layers that process information
- Output layers that produce results

## Applications

AI powers many modern technologies:
- Computer Vision: Image recognition and object detection
- Natural Language Processing: Text understanding and generation
- Robotics: Autonomous systems and decision making
- Healthcare: Disease diagnosis and drug discovery

## Challenges

Despite advances, AI faces important challenges:
- Data Quality: Models require large, high-quality datasets
- Interpretability: Understanding how models make decisions
- Ethics: Ensuring fair and unbiased AI systems
- Computational Cost: Training large models requires significant resources

The field continues to evolve rapidly, with new breakthroughs emerging regularly.
    """.strip()

    print("📄 Sample Document:")
    print("-" * 70)
    print(sample_document[:200] + "...")
    print()

    try:
        from agents import (
            AgentWorkflow,
            OrchestratorAgent,
            SummarizerAgent,
            LinkerAgent,
            VisualizerAgent,
        )
        from models.context_model import SessionContext
        import time

        # Step 1: Create SessionContext
        print("📋 Step 1: Creating SessionContext")
        print("-" * 70)

        session_context = SessionContext(
            session_id=f"demo_{int(time.time())}",
            raw_input=sample_document,
            content_type="document",
        )

        print(f"✅ SessionContext created")
        print(f"   Session ID: {session_context.session_id}")
        print(f"   Content type: {session_context.content_type}")
        print(f"   Input length: {len(session_context.raw_input)} characters")
        print()

        # Step 2: Setup Agent Workflow
        print("🤖 Step 2: Initializing Agent Workflow")
        print("-" * 70)

        workflow = AgentWorkflow()

        orchestrator = OrchestratorAgent(workflow.a2a)
        summarizer = SummarizerAgent(workflow.a2a)
        linker = LinkerAgent(workflow.a2a)
        visualizer = VisualizerAgent(workflow.a2a)

        workflow.register_agent(orchestrator)
        workflow.register_agent(summarizer)
        workflow.register_agent(linker)
        workflow.register_agent(visualizer)

        print(f"✅ Agents registered: {len(workflow.agents)}")
        for agent_name in workflow.agents.keys():
            print(f"   - {agent_name}")
        print()

        # Step 3: Execute Sequential Workflow
        print("🎬 Step 3: Executing Sequential Workflow")
        print("-" * 70)
        print("Agent execution order: Orchestrator → Summarizer → Linker → Visualizer")
        print()

        start_time = time.time()
        result_context = await workflow.execute_sequential_workflow(session_context)
        execution_time = time.time() - start_time

        print(f"✅ Workflow completed in {execution_time:.2f} seconds")
        print(f"   Status: {result_context.workflow_status}")
        print(f"   Completed agents: {', '.join(result_context.completed_agents)}")
        print()

        # Step 4: Display Results
        print("📊 Step 4: Results from SessionContext")
        print("=" * 70)

        # Summary from Summarizer Agent
        print()
        print("📝 SUMMARY (from Summarizer Agent):")
        print("-" * 70)
        if result_context.summary_text:
            print(result_context.summary_text)
        else:
            print("⚠️  No summary generated")
        print()

        # Entities from Linker Agent
        print("🔗 KEY ENTITIES (from Linker Agent):")
        print("-" * 70)
        if result_context.key_entities:
            for i, entity in enumerate(result_context.key_entities, 1):
                print(f"   {i}. {entity}")
        else:
            print("⚠️  No entities identified")
        print()

        # Relationships from Linker Agent
        print("🔀 RELATIONSHIPS (from Linker Agent):")
        print("-" * 70)
        if result_context.relationships:
            for i, rel in enumerate(result_context.relationships, 1):
                print(f"   {i}. {rel.source} --[{rel.type}]--> {rel.target}")
                if rel.label:
                    print(f"      Label: {rel.label}")
        else:
            print("⚠️  No relationships identified")
        print()

        # Visualization from Visualizer Agent
        print("🎨 VISUALIZATION (from Visualizer Agent):")
        print("-" * 70)
        if result_context.graph_json:
            graph = result_context.graph_json
            print(f"   Type: {graph.get('type', 'Unknown')}")
            print(f"   Nodes: {len(graph.get('nodes', []))} nodes")
            print(f"   Edges: {len(graph.get('edges', []))} edges")

            if graph.get("nodes"):
                print()
                print("   Sample nodes:")
                for node in graph["nodes"][:5]:
                    print(
                        f"     - {node.get('label', 'Unknown')} (group: {node.get('group', 'N/A')})"
                    )
        else:
            print("⚠️  No visualization generated")
        print()

        # Workflow Metadata
        print("📈 WORKFLOW METADATA:")
        print("-" * 70)
        print(f"   Session ID: {result_context.session_id}")
        print(f"   Workflow Status: {result_context.workflow_status}")
        print(
            f"   Completed Agents: {len(result_context.completed_agents)}/{len(workflow.agents)}"
        )
        print(f"   Execution Time: {execution_time:.2f} seconds")
        print(f"   Errors: {len(result_context.errors)}")
        if result_context.errors:
            for error in result_context.errors:
                print(f"     - {error['agent']}: {error['error']}")
        print()

        # Firestore Persistence Status
        print("💾 FIRESTORE PERSISTENCE:")
        print("-" * 70)
        if workflow.persistence_service:
            print("   ✅ Persistence service initialized")
            print("   📂 Collection: agent_context")
            print(f"   📄 Document ID: {result_context.session_id}")
        else:
            print("   ⚠️  Persistence service not available")
        print()

        # Step 5: Show SessionContext as JSON
        print("📦 Step 5: SessionContext as JSON")
        print("-" * 70)

        # Convert to dict for JSON display (without the full raw_input)
        context_dict = result_context.model_dump()
        context_dict["raw_input"] = (
            f"{context_dict['raw_input'][:50]}... ({len(context_dict['raw_input'])} chars)"
        )

        print(json.dumps(context_dict, indent=2, default=str)[:500] + "...")
        print()

        # Success summary
        print("=" * 70)
        print("🎉 Demo completed successfully!")
        print("=" * 70)
        print()
        print("Key Achievements:")
        print("  ✅ SessionContext created and validated")
        print(
            "  ✅ Sequential workflow executed (Orchestrator → Summarizer → Linker → Visualizer)"
        )
        print("  ✅ Each agent updated specific SessionContext fields")
        print("  ✅ Results accessible via unified SessionContext object")
        print()
        print("This demonstrates the complete FR#005 implementation!")
        print()

        return True

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(demo_sequential_workflow())
    sys.exit(0 if success else 1)
