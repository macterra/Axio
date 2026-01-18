"""
RSA-PoC v4.1 — LLM Integration Test
Verifies Claude API connectivity with frozen parameters.

Run: python -m src.rsa_poc.v410.test_llm_integration
"""

import os
import sys


def test_llm_integration():
    """Test LLM API connectivity with a minimal call."""

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return False

    print(f"✓ ANTHROPIC_API_KEY present ({len(api_key)} chars)")

    # Import anthropic
    try:
        import anthropic
        print(f"✓ anthropic package installed (version: {anthropic.__version__})")
    except ImportError:
        print("❌ anthropic package not installed")
        print("   Install with: pip install anthropic")
        return False

    # Import our deliberator
    try:
        from src.rsa_poc.v410.deliberator import (
            LLMDeliberator,
            LLMDeliberatorConfig,
            SYSTEM_PROMPT_V410,
        )
        print("✓ v410 deliberator imports successful")
    except ImportError as e:
        print(f"❌ Failed to import v410 deliberator: {e}")
        return False

    # Verify frozen parameters
    config = LLMDeliberatorConfig()
    print(f"\nFrozen LLM Parameters:")
    print(f"  model: {config.model}")
    print(f"  temperature: {config.temperature}")
    print(f"  max_tokens: {config.max_tokens}")

    expected_model = "claude-sonnet-4-20250514"
    expected_temp = 0.0
    expected_tokens = 4096

    if config.model != expected_model:
        print(f"❌ Model mismatch: expected {expected_model}, got {config.model}")
        return False
    if config.temperature != expected_temp:
        print(f"❌ Temperature mismatch: expected {expected_temp}, got {config.temperature}")
        return False
    if config.max_tokens != expected_tokens:
        print(f"❌ Max tokens mismatch: expected {expected_tokens}, got {config.max_tokens}")
        return False

    print("✓ All frozen parameters match spec")

    # Test minimal API call
    print("\n--- Testing API connectivity ---")
    print("Sending minimal test prompt...")

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=50,
            temperature=config.temperature,
            messages=[
                {"role": "user", "content": "Reply with exactly: API_OK"}
            ]
        )

        reply = response.content[0].text.strip()
        print(f"Response: {reply}")

        if "API_OK" in reply or "OK" in reply:
            print("✓ API connectivity verified")
        else:
            print(f"⚠ Unexpected response (API works but format different)")

        # Show usage
        print(f"\nUsage: {response.usage.input_tokens} in, {response.usage.output_tokens} out")

        return True

    except anthropic.AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your ANTHROPIC_API_KEY")
        return False
    except anthropic.RateLimitError as e:
        print(f"❌ Rate limited: {e}")
        return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False


def test_deliberation_round():
    """Test a full deliberation round with mock observation."""

    print("\n--- Testing Full Deliberation Round ---")

    try:
        from src.rsa_poc.v410.deliberator import LLMDeliberator, LLMDeliberatorConfig
        from src.rsa_poc.v410.core import NormStateV410
        from src.rsa_poc.v410.core.norm_state import create_initial_norm_state
        from src.rsa_poc.v410.env import TriDemandV410

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Create environment
    env = TriDemandV410(seed=42)
    obs, info = env.reset()

    # Create norm state with initial rules
    norm_state = create_initial_norm_state()

    print(f"Observation: agent_pos={obs.agent_pos}, inventory={obs.inventory}")
    print(f"NormState: {len(norm_state.rules)} rules, hash={norm_state.norm_hash[:16]}...")

    # Create deliberator
    config = LLMDeliberatorConfig()
    deliberator = LLMDeliberator(config)

    print("\nCalling LLM deliberator...")
    output = deliberator.deliberate(obs, norm_state, episode=1, step=0)

    if output.error:
        print(f"❌ Deliberation error: {output.error}")
        return False

    print(f"✓ Deliberation completed in {output.deliberation_time_ms:.1f}ms")
    print(f"  Generated {len(output.justifications)} justifications")

    if output.justifications:
        print("\nSample justification:")
        j = output.justifications[0]
        print(f"  action_id: {j.action_id}")
        print(f"  rule_refs: {j.rule_refs}")
        print(f"  claims: {len(j.claims)} predicates")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("RSA-PoC v4.1 — LLM Integration Test")
    print("=" * 60)
    print()

    if not test_llm_integration():
        print("\n⛔ Integration test FAILED")
        sys.exit(1)

    if not test_deliberation_round():
        print("\n⛔ Deliberation test FAILED")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
