#!/usr/bin/env python
"""Test script to verify token fallback mechanism."""

import os
import sys
from unittest.mock import Mock, patch
from clickup_framework.client import ClickUpClient
from clickup_framework.exceptions import ClickUpAuthError

def test_token_source_tracking():
    """Test that token source is correctly tracked."""
    print("Test 1: Token source tracking")

    # Test with environment variable
    with patch.dict(os.environ, {'CLICKUP_API_TOKEN': 'env_token'}):
        with patch('clickup_framework.client.get_context_manager') as mock_context:
            mock_context.return_value.get_api_token.return_value = 'context_token'

            client = ClickUpClient()
            assert client.token_source == "environment", f"Expected 'environment', got {client.token_source}"
            assert client.api_token == 'env_token', f"Expected 'env_token', got {client.api_token}"
            print("  ✓ Environment token correctly prioritized")

    # Test with only context token
    with patch.dict(os.environ, {}, clear=True):
        with patch('clickup_framework.client.get_context_manager') as mock_context:
            mock_context.return_value.get_api_token.return_value = 'context_token'

            client = ClickUpClient()
            assert client.token_source == "context", f"Expected 'context', got {client.token_source}"
            assert client.api_token == 'context_token', f"Expected 'context_token', got {client.api_token}"
            print("  ✓ Context token used when env var not set")

    # Test with parameter
    with patch('clickup_framework.client.get_context_manager') as mock_context:
        mock_context.return_value.get_api_token.return_value = None

        client = ClickUpClient(api_token='param_token')
        assert client.token_source == "parameter", f"Expected 'parameter', got {client.token_source}"
        assert client.api_token == 'param_token', f"Expected 'param_token', got {client.api_token}"
        print("  ✓ Parameter token has highest priority")

    print("✓ Token source tracking works correctly\n")


def test_fallback_switching():
    """Test that fallback token switching works."""
    print("Test 2: Fallback token switching")

    with patch.dict(os.environ, {'CLICKUP_API_TOKEN': 'env_token'}):
        with patch('clickup_framework.client.get_context_manager') as mock_context:
            mock_context.return_value.get_api_token.return_value = 'context_token'

            client = ClickUpClient()

            # Initially using environment token
            assert client.token_source == "environment"
            print(f"  Initial source: {client.token_source}")

            # Switch to fallback
            switched = client._switch_to_fallback_token()
            assert switched == True, "Should have found fallback token"
            assert client.token_source == "context", f"Expected 'context', got {client.token_source}"
            assert client.api_token == 'context_token', f"Expected 'context_token', got {client.api_token}"
            print(f"  ✓ Switched to fallback: {client.token_source}")

            # Try switching again (should fail - no more fallbacks)
            switched = client._switch_to_fallback_token()
            assert switched == False, "Should not have found another fallback"
            print("  ✓ No infinite switching (correctly detects no more fallbacks)")

    print("✓ Fallback switching works correctly\n")


def test_401_triggers_fallback():
    """Test that 401 error triggers fallback attempt."""
    print("Test 3: 401 error triggers fallback")

    with patch.dict(os.environ, {'CLICKUP_API_TOKEN': 'env_token'}):
        with patch('clickup_framework.client.get_context_manager') as mock_context:
            mock_context.return_value.get_api_token.return_value = 'context_token'

            client = ClickUpClient()

            # Mock the session.request method
            mock_response = Mock()

            # First call returns 401 (env token fails)
            # Second call returns 200 (context token succeeds)
            call_count = [0]
            def mock_request(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    mock_response.status_code = 401
                    return mock_response
                else:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"success": True}
                    return mock_response

            with patch.object(client.session, 'request', side_effect=mock_request):
                try:
                    result = client._request('GET', '/test')

                    # Should have switched to context token
                    assert client.token_source == "context", f"Expected 'context', got {client.token_source}"
                    assert call_count[0] == 2, f"Expected 2 calls, got {call_count[0]}"
                    assert result == {"success": True}
                    print("  ✓ 401 triggered fallback and retry succeeded")
                except Exception as e:
                    print(f"  ✗ Unexpected error: {e}")
                    raise

    print("✓ 401 error handling with fallback works correctly\n")


def test_401_fails_when_no_fallback():
    """Test that 401 raises error when no fallback available."""
    print("Test 4: 401 error with no fallback")

    with patch.dict(os.environ, {'CLICKUP_API_TOKEN': 'env_token'}):
        with patch('clickup_framework.client.get_context_manager') as mock_context:
            # No context token available
            mock_context.return_value.get_api_token.return_value = None

            client = ClickUpClient()

            # Mock the session.request method to always return 401
            mock_response = Mock()
            mock_response.status_code = 401

            with patch.object(client.session, 'request', return_value=mock_response):
                try:
                    client._request('GET', '/test')
                    print("  ✗ Should have raised ClickUpAuthError")
                    assert False, "Should have raised ClickUpAuthError"
                except ClickUpAuthError:
                    print("  ✓ Correctly raised ClickUpAuthError when no fallback")

    print("✓ 401 error without fallback works correctly\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Token Fallback Mechanism")
    print("=" * 60 + "\n")

    try:
        test_token_source_tracking()
        test_fallback_switching()
        test_401_triggers_fallback()
        test_401_fails_when_no_fallback()

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
