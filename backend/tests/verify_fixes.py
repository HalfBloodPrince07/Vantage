import asyncio
import json
from backend.streaming_steps import ensure_step_queue, get_step_queue
from backend.utils.llm_utils import sanitize_llm_response

async def test_streaming_fix():
    print("Testing Streaming Fix...")
    session_id = "test_session_123"
    
    # 1. Ensure queue creates it
    queue = ensure_step_queue(session_id)
    assert queue is not None, "Queue should be created"
    
    # 2. Ensure calling it again returns the SAME queue
    queue2 = ensure_step_queue(session_id)
    assert queue is queue2, "Should return the same queue instance"
    
    # 3. Verify get_step_queue works
    queue3 = get_step_queue(session_id)
    assert queue is queue3, "get_step_queue should return the same queue"
    
    print("✅ Streaming fix verified!")

def test_validation_fix():
    print("\nTesting Validation Fix...")
    
    # 1. Test sanitize_llm_response
    markdown_json = "```json\n{\"key\": \"value\"}\n```"
    cleaned = sanitize_llm_response(markdown_json)
    assert cleaned == '{"key": "value"}', f"Failed to clean markdown: {cleaned}"
    
    # 2. Test validate_json logic (simulated)
    def validate_json(text: str) -> bool:
        try:
            cleaned = sanitize_llm_response(text)
            json.loads(cleaned)
            return True
        except json.JSONDecodeError:
            return False
            
    assert validate_json(markdown_json) is True, "Should validate markdown-wrapped JSON"
    assert validate_json('{"key": "value"}') is True, "Should validate raw JSON"
    assert validate_json("invalid json") is False, "Should reject invalid JSON"
    
    print("✅ Validation fix verified!")

async def main():
    await test_streaming_fix()
    test_validation_fix()

if __name__ == "__main__":
    asyncio.run(main())
