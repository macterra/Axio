#!/usr/bin/env python3
"""Test script for Run 1 LLM generator setup

This script verifies:
1. Environment variables are set correctly
2. LLM client libraries are installed
3. LLM generator can initialize
4. Basic generation works (with mock or real API)

Run this before executing run_1.py to verify setup.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_env_vars():
    """Test 1: Check environment variables"""
    print("="*60)
    print("Test 1: Environment Variables")
    print("="*60)

    required = ['LLM_PROVIDER', 'LLM_MODEL']
    optional = ['LLM_API_KEY', 'LLM_BASE_URL']

    all_set = True
    for var in required:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET (required)")
            all_set = False

    for var in optional:
        value = os.getenv(var)
        if value:
            # Mask API key
            if 'KEY' in var and len(value) > 4:
                masked = '***' + value[-4:]
            else:
                masked = value
            print(f"  {var}: {masked}")
        else:
            print(f"  {var}: not set (optional)")

    if not all_set:
        print("\n⚠ Missing required environment variables!")
        print("\nExample setup for Anthropic:")
        print("  export LLM_PROVIDER=anthropic")
        print("  export LLM_MODEL=claude-3-5-sonnet-20241022")
        print("  export LLM_API_KEY=<your-key>")
        print("\nExample setup for OpenAI:")
        print("  export LLM_PROVIDER=openai")
        print("  export LLM_MODEL=gpt-4")
        print("  export LLM_API_KEY=<your-key>")
        return False

    print("\n✓ Environment variables configured")
    return True


def test_imports():
    """Test 2: Check imports and dependencies"""
    print("\n" + "="*60)
    print("Test 2: Imports and Dependencies")
    print("="*60)

    try:
        from rsa_poc.v110.generator.llm import LLMGeneratorV110
        from rsa_poc.v110.state.normative import NormativeStateV110
        print("✓ RSA-PoC modules import successfully")
    except ImportError as e:
        print(f"✗ Failed to import RSA-PoC modules: {e}")
        return False

    # Check LLM client library
    provider = os.getenv('LLM_PROVIDER')
    if provider == 'anthropic':
        try:
            import anthropic
            print(f"✓ anthropic library installed (version: {anthropic.__version__})")
        except ImportError:
            print("✗ anthropic library not installed")
            print("  Install with: pip install anthropic")
            return False
    elif provider == 'openai':
        try:
            import openai
            print(f"✓ openai library installed (version: {openai.__version__})")
        except ImportError:
            print("✗ openai library not installed")
            print("  Install with: pip install openai")
            return False
    else:
        print(f"⚠ Unknown provider: {provider}")
        return False

    return True


def test_generator_init():
    """Test 3: Initialize LLM generator"""
    print("\n" + "="*60)
    print("Test 3: LLM Generator Initialization")
    print("="*60)

    try:
        from rsa_poc.v110.generator.llm import LLMGeneratorV110
        from rsa_poc.v110.state.normative import NormativeStateV110

        state = NormativeStateV110()
        generator = LLMGeneratorV110(state)

        print(f"✓ LLM generator initialized successfully")
        print(f"  Provider: {generator.provider}")
        print(f"  Model: {generator.model}")
        print(f"  Max attempts per step: {generator.MAX_ATTEMPTS_PER_STEP}")

        return True, generator

    except Exception as e:
        print(f"✗ Failed to initialize generator: {e}")
        return False, None


def test_prompt_generation(generator):
    """Test 4: Generate prompt (no API call)"""
    print("\n" + "="*60)
    print("Test 4: Prompt Generation")
    print("="*60)

    try:
        # Create minimal test inputs
        feasible_actions = ["COOPERATE", "EXPLOIT", "WAIT"]
        apcm = {
            "COOPERATE": {"violates": {"P_NO_COOPERATE"}, "satisfies": {"P_FAIRNESS"}},
            "EXPLOIT": {"violates": {"P_NO_EXPLOIT"}, "satisfies": {"P_SELF_INTEREST"}},
            "WAIT": {"violates": set(), "satisfies": {"P_PATIENCE"}}
        }

        prompt = generator._build_prompt(feasible_actions, apcm, None, 1)

        print(f"✓ Prompt generated successfully")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"  Contains compiler pseudocode: {'COMPILER PSEUDOCODE' in prompt}")
        print(f"  Contains examples: {'Example 1' in prompt and 'Example 2' in prompt}")
        print(f"  Contains audit rules: {'Audit A' in prompt and 'Audit B' in prompt}")

        # Show first few lines
        print(f"\n  First 500 characters:")
        print("  " + "-"*56)
        for line in prompt[:500].split('\n'):
            print(f"  {line}")
        print("  " + "-"*56)

        return True

    except Exception as e:
        print(f"✗ Failed to generate prompt: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# RSA-PoC v1.1 Run 1: LLM Generator Setup Test")
    print("#"*60 + "\n")

    results = []

    # Test 1: Environment variables
    results.append(("Environment Variables", test_env_vars()))

    if not results[0][1]:
        print("\n" + "="*60)
        print("SETUP INCOMPLETE: Fix environment variables and try again")
        print("="*60)
        return 1

    # Test 2: Imports
    results.append(("Imports and Dependencies", test_imports()))

    if not results[1][1]:
        print("\n" + "="*60)
        print("SETUP INCOMPLETE: Install required packages and try again")
        print("="*60)
        return 1

    # Test 3: Generator initialization
    init_success, generator = test_generator_init()
    results.append(("Generator Initialization", init_success))

    if not init_success:
        print("\n" + "="*60)
        print("SETUP INCOMPLETE: Generator initialization failed")
        print("="*60)
        return 1

    # Test 4: Prompt generation
    results.append(("Prompt Generation", test_prompt_generation(generator)))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED: Ready to run Run 1")
        print("="*60)
        print("\nNext step:")
        print("  python src/rsa_poc/v110/run_1.py")
        return 0
    else:
        print("✗ SOME TESTS FAILED: Fix issues above")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
