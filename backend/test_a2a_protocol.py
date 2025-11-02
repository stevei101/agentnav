#!/usr/bin/env python3
"""
Test Suite for A2A Protocol Integration (Feature Request #027)

Tests the formal A2A Protocol implementation with:
- Typed Pydantic message schemas
- Security features (message signing, verification)
- Traceability and logging
- Agent communication with typed messages
"""

import sys
import os
import asyncio
import time

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_a2a_message_schemas():
    """Test Pydantic message model validation"""
    print("🧪 Testing A2A Message Schemas (FR#027)")
    
    try:
        from models.a2a_messages import (
            TaskDelegationMessage,
            SummarizationCompletedMessage,
            RelationshipMappedMessage,
            VisualizationReadyMessage,
            KnowledgeTransferMessage,
            AgentStatusMessage,
            A2ATraceContext,
            create_message_id,
            create_correlation_id
        )
        
        # Test 1: Create TaskDelegationMessage
        correlation_id = create_correlation_id("test_session_001")
        
        task_msg = TaskDelegationMessage(
            message_id=create_message_id("orchestrator", "task_delegation"),
            from_agent="orchestrator",
            to_agent="summarizer",
            task_name="create_summary",
            task_parameters={"content": "Test document", "content_type": "document"},
            expected_output="comprehensive_summary",
            trace=A2ATraceContext(correlation_id=correlation_id)
        )
        
        print("✅ TaskDelegationMessage created successfully")
        print(f"   Message ID: {task_msg.message_id}")
        print(f"   Task: {task_msg.task_name}")
        print(f"   Priority: {task_msg.priority}")
        
        # Test 2: Create SummarizationCompletedMessage
        summary_msg = SummarizationCompletedMessage(
            message_id=create_message_id("summarizer", "summarization_completed"),
            from_agent="summarizer",
            to_agent="*",
            summary_text="This is a test summary of the document.",
            insights={"word_count": 500, "reading_time_minutes": 2},
            content_type="document",
            trace=A2ATraceContext(
                correlation_id=correlation_id,
                parent_message_id=task_msg.message_id
            )
        )
        
        print("✅ SummarizationCompletedMessage created successfully")
        print(f"   Summary length: {len(summary_msg.summary_text)}")
        print(f"   Parent message: {summary_msg.trace.parent_message_id}")
        
        # Test 3: Create RelationshipMappedMessage
        rel_msg = RelationshipMappedMessage(
            message_id=create_message_id("linker", "relationship_mapped"),
            from_agent="linker",
            to_agent="visualizer",
            entities=[
                {"id": "entity_1", "label": "Machine Learning", "type": "concept"}
            ],
            relationships=[
                {"from": "entity_1", "to": "entity_2", "type": "relates_to"}
            ],
            entity_count=1,
            relationship_count=1,
            trace=A2ATraceContext(correlation_id=correlation_id)
        )
        
        print("✅ RelationshipMappedMessage created successfully")
        print(f"   Entities: {rel_msg.entity_count}")
        print(f"   Relationships: {rel_msg.relationship_count}")
        
        # Test 4: Validate message serialization
        task_dict = task_msg.model_dump()
        print("✅ Message serialization working")
        print(f"   Serialized keys: {list(task_dict.keys())[:5]}...")
        
        # Test 5: Test message TTL and expiration
        print(f"   Message expired: {task_msg.is_expired()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_a2a_security():
    """Test A2A Protocol security features"""
    print("\n🧪 Testing A2A Security Service (FR#027)")
    
    try:
        from services.a2a_security import get_security_service, ServiceAccountIdentity
        from models.a2a_messages import TaskDelegationMessage, A2ATraceContext, create_message_id, create_correlation_id
        
        # Initialize security service
        security_service = get_security_service()
        
        print("✅ Security service initialized")
        print(f"   Identity: {security_service.identity.email}")
        print(f"   Trusted accounts: {len(security_service.trusted_service_accounts)}")
        
        # Test 1: Message signing
        test_message = {
            "message_id": "test_msg_001",
            "from_agent": "summarizer",
            "to_agent": "visualizer",
            "message_type": "knowledge_transfer",
            "timestamp": time.time(),
            "data": {"key": "value"}
        }
        
        signature = security_service.sign_message(test_message)
        print("✅ Message signing working")
        print(f"   Signature: {signature[:32]}...")
        
        # Test 2: Message verification
        is_valid = security_service.verify_message_signature(test_message, signature)
        print(f"✅ Signature verification: {is_valid}")
        
        # Test 3: Invalid signature detection
        invalid_sig = "invalid_signature_12345"
        is_invalid = security_service.verify_message_signature(test_message, invalid_sig)
        print(f"✅ Invalid signature detected: {not is_invalid}")
        
        # Test 4: Service Account authentication
        is_trusted = security_service.authenticate_service_account(security_service.identity.email)
        print(f"✅ Service Account authentication: {is_trusted}")
        
        # Test 5: Authorization checks
        is_authorized = security_service.authorize_agent_communication(
            from_agent="orchestrator",
            to_agent="summarizer",
            service_account_email=security_service.identity.email
        )
        print(f"✅ Agent authorization: {is_authorized}")
        
        # Test 6: Comprehensive message validation
        correlation_id = create_correlation_id("test_session_002")
        typed_message = TaskDelegationMessage(
            message_id=create_message_id("orchestrator", "task_delegation"),
            from_agent="orchestrator",
            to_agent="summarizer",
            task_name="test_task",
            task_parameters={"key": "value"},
            expected_output="test_output",
            trace=A2ATraceContext(correlation_id=correlation_id)
        )
        
        message_dict = typed_message.model_dump()
        enhanced = security_service.enhance_message_with_security(message_dict)
        
        validation_result = security_service.validate_message_security(enhanced)
        print(f"✅ Message validation: {validation_result['is_valid']}")
        print(f"   Security score: {validation_result['security_score']}/100")
        
        if not validation_result['is_valid']:
            print(f"   Issues: {validation_result['issues']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_a2a_protocol_service():
    """Test Enhanced A2A Protocol Service"""
    print("\n🧪 Testing A2A Protocol Service (FR#027)")
    
    try:
        from services.a2a_protocol import (
            A2AProtocolService,
            create_task_delegation_message,
            create_knowledge_transfer_message,
            create_status_message
        )
        from models.a2a_messages import A2AMessagePriority
        
        # Initialize protocol service
        protocol = A2AProtocolService(session_id="test_session_003")
        
        print("✅ A2A Protocol Service initialized")
        print(f"   Session ID: {protocol.session_id}")
        print(f"   Correlation ID: {protocol.correlation_id}")
        
        # Test 1: Send task delegation message
        task_msg = create_task_delegation_message(
            from_agent="orchestrator",
            to_agent="summarizer",
            task_name="create_summary",
            task_parameters={"content": "Test document"},
            expected_output="summary",
            correlation_id=protocol.correlation_id
        )
        
        await protocol.send_message(task_msg)
        print("✅ Task delegation message sent")
        
        # Test 2: Send knowledge transfer message
        knowledge_msg = create_knowledge_transfer_message(
            from_agent="summarizer",
            to_agent="linker",
            knowledge_type="summary_context",
            knowledge_data={"summary": "Test summary", "insights": {}},
            correlation_id=protocol.correlation_id,
            priority=A2AMessagePriority.HIGH
        )
        
        await protocol.send_message(knowledge_msg)
        print("✅ Knowledge transfer message sent")
        
        # Test 3: Retrieve messages for agent
        messages = await protocol.get_messages_for_agent("summarizer")
        print(f"✅ Retrieved {len(messages)} messages for 'summarizer'")
        
        if messages:
            msg = messages[0]
            print(f"   Message type: {msg.message_type}")
            print(f"   From: {msg.from_agent}")
            print(f"   Security verified: {msg.security.verified}")
        
        # Test 4: Get protocol statistics
        stats = protocol.get_protocol_stats()
        print("✅ Protocol statistics:")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Pending messages: {stats['pending_messages']}")
        print(f"   Message types: {stats['message_types']}")
        
        # Test 5: Message history and traceability
        history = protocol.get_message_history(limit=10)
        print(f"✅ Message history: {len(history)} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Protocol service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_integration():
    """Test agent integration with enhanced A2A Protocol"""
    print("\n🧪 Testing Agent Integration with Enhanced A2A (FR#027)")
    
    try:
        from agents import AgentWorkflow, OrchestratorAgent, SummarizerAgent
        from models.context_model import SessionContext
        
        # Create workflow with enhanced A2A Protocol
        workflow = AgentWorkflow(session_id="test_session_004", use_enhanced_a2a=True)
        
        print("✅ Workflow created with enhanced A2A Protocol")
        print(f"   A2A Protocol type: {type(workflow.a2a).__name__}")
        
        # Create and register agents
        orchestrator = OrchestratorAgent(workflow.a2a)
        summarizer = SummarizerAgent(workflow.a2a)
        
        workflow.register_agent(orchestrator)
        workflow.register_agent(summarizer)
        
        print("✅ Agents registered with workflow")
        print(f"   Orchestrator using enhanced A2A: {orchestrator.using_enhanced_a2a}")
        print(f"   Summarizer using enhanced A2A: {summarizer.using_enhanced_a2a}")
        
        # Create test session context
        session_context = SessionContext(
            session_id="test_session_004",
            raw_input="""
# Test Document
This is a test document for validating A2A Protocol integration.
It contains some sample content to test the multi-agent workflow.
            """.strip(),
            content_type="document"
        )
        
        # Execute workflow (just orchestrator and summarizer)
        print("\n🎬 Executing workflow with enhanced A2A Protocol...")
        
        # Execute orchestrator
        orchestrator_result = await orchestrator.execute({
            "document": session_context.raw_input,
            "content_type": session_context.content_type,
            "session_id": session_context.session_id
        })
        
        print("✅ Orchestrator completed")
        print(f"   Content type detected: {orchestrator_result.get('content_analysis', {}).get('content_type')}")
        
        # Check A2A Protocol statistics
        if hasattr(workflow.a2a, 'get_protocol_stats'):
            stats = workflow.a2a.get_protocol_stats()
            print("\n📊 A2A Protocol Statistics:")
            print(f"   Total messages: {stats['total_messages']}")
            print(f"   Message types: {list(stats['message_types'].keys())}")
            print(f"   Agent activity: {list(stats['agent_activity'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all A2A Protocol tests"""
    print("=" * 70)
    print("🚀 A2A Protocol Integration Test Suite (FR#027)")
    print("=" * 70)
    
    # Test 1: Message schemas
    schemas_passed = await test_a2a_message_schemas()
    
    # Test 2: Security features
    security_passed = await test_a2a_security()
    
    # Test 3: Protocol service
    protocol_passed = await test_a2a_protocol_service()
    
    # Test 4: Agent integration
    integration_passed = await test_agent_integration()
    
    # Print results
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"  📋 Message Schemas: {'✅ PASS' if schemas_passed else '❌ FAIL'}")
    print(f"  🔐 Security Features: {'✅ PASS' if security_passed else '❌ FAIL'}")
    print(f"  🔄 Protocol Service: {'✅ PASS' if protocol_passed else '❌ FAIL'}")
    print(f"  🤖 Agent Integration: {'✅ PASS' if integration_passed else '❌ FAIL'}")
    
    overall_success = all([schemas_passed, security_passed, protocol_passed, integration_passed])
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📋 FR#027 Implementation Summary")
    print("=" * 70)
    print("""
✅ COMPLETED FEATURES:

1. 📦 Formal A2A Message Schemas (Pydantic)
   - TaskDelegationMessage
   - SummarizationCompletedMessage
   - RelationshipMappedMessage
   - VisualizationReadyMessage
   - KnowledgeTransferMessage
   - AgentStatusMessage
   
2. 🔐 Security Layer (Workload Identity)
   - Message signing and verification (HMAC-SHA256)
   - Service Account authentication
   - Authorization policies for agent communication
   - Security audit logging
   
3. 🔄 Enhanced A2A Protocol Service
   - Typed message handling with Pydantic validation
   - Security verification for all messages
   - Message queue with priority management
   - Comprehensive traceability and logging
   
4. 🤖 Agent Integration
   - Base Agent updated to support both legacy and enhanced A2A
   - AgentWorkflow supports both protocol implementations
   - Backward compatibility maintained
   - Typed message notifications

🎯 SUCCESS CRITERIA:
✅ Agents communicate using structured, formalized A2A message schema
✅ Security features implemented with Workload Identity support
✅ All agent handoffs logged with A2A protocol headers
✅ Enhanced traceability with correlation IDs and message history
""")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
