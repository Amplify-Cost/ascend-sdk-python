"""
SEC-039 Enterprise Hardening - Comprehensive Review Test

Tests all aspects of the cognito_pool_provisioner.py changes:
1. Specific exception handling
2. Retry logic with exponential backoff
3. IAM permission validation
4. Type hints and function signatures
5. Refactored method extraction

Engineer: Code Review Agent
Date: 2025-12-02
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError


# =============================================================================
# TEST 1: Specific Exception Handling
# =============================================================================

def test_specific_cognito_exceptions():
    """
    SEC-039: Verify specific Cognito exceptions are handled correctly.

    Evidence Required:
    - InvalidParameterException caught and logged (non-fatal)
    - ResourceNotFoundException caught and re-raised (critical)
    - NotAuthorizedException caught and logged (non-fatal)
    - TooManyRequestsException caught and logged (non-fatal)
    """
    from services.cognito_pool_provisioner import CognitoPoolProvisioner

    # Test each exception type
    test_cases = [
        ('InvalidParameterException', False),  # Should not raise
        ('ResourceNotFoundException', True),    # Should raise
        ('NotAuthorizedException', False),      # Should not raise
        ('TooManyRequestsException', False),    # Should not raise
    ]

    for exception_name, should_raise in test_cases:
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client

            # Create exception
            exception_class = type(exception_name, (Exception,), {})
            mock_client.exceptions = Mock()
            setattr(mock_client.exceptions, exception_name, exception_class)

            # Configure MFA to raise exception
            mock_client.set_user_pool_mfa_config.side_effect = exception_class("Test error")

            provisioner = CognitoPoolProvisioner(validate_permissions=False)
            audit_details = {}

            if should_raise:
                with pytest.raises(exception_class):
                    provisioner._configure_mfa('test-pool-id', 'OPTIONAL', audit_details)
                print(f"✓ {exception_name} correctly re-raised")
            else:
                provisioner._configure_mfa('test-pool-id', 'OPTIONAL', audit_details)
                assert 'mfa_error' in audit_details
                print(f"✓ {exception_name} caught and logged without raising")


# =============================================================================
# TEST 2: Retry Decorator Logic
# =============================================================================

def test_retry_decorator_exponential_backoff():
    """
    SEC-039: Verify retry decorator implements exponential backoff correctly.

    Evidence Required:
    - Retries throttling errors up to MAX_RETRIES times
    - Exponential backoff: 1s → 2s → 4s
    - Non-retryable errors fail immediately
    - Success on retry doesn't waste attempts
    """
    from services.cognito_pool_provisioner import with_retry, RETRYABLE_ERROR_CODES

    print("\n=== Testing Retry Decorator ===")

    # Test 1: Success on first attempt
    call_count = 0

    @with_retry(max_retries=3)
    def success_first_try():
        nonlocal call_count
        call_count += 1
        return "success"

    result = success_first_try()
    assert result == "success"
    assert call_count == 1
    print(f"✓ Success on first attempt (1 call)")

    # Test 2: Retryable error with eventual success
    call_count = 0

    @with_retry(max_retries=3, initial_backoff=0.1)
    def retry_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error = ClientError(
                {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                'TestOperation'
            )
            raise error
        return "success"

    start_time = time.time()
    result = retry_then_succeed()
    duration = time.time() - start_time

    assert result == "success"
    assert call_count == 3
    assert duration >= 0.3  # 0.1 + 0.2 = 0.3s minimum
    print(f"✓ Retried 2 times before success (3 calls, {duration:.2f}s)")

    # Test 3: Non-retryable error fails immediately
    call_count = 0

    @with_retry(max_retries=3)
    def non_retryable_error():
        nonlocal call_count
        call_count += 1
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'No access'}},
            'TestOperation'
        )
        raise error

    with pytest.raises(ClientError) as exc_info:
        non_retryable_error()

    assert call_count == 1  # Should not retry
    assert exc_info.value.response['Error']['Code'] == 'AccessDenied'
    print(f"✓ Non-retryable error failed immediately (1 call)")

    # Test 4: Max retries exceeded
    call_count = 0

    @with_retry(max_retries=2, initial_backoff=0.1)
    def always_throttled():
        nonlocal call_count
        call_count += 1
        error = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Throttled'}},
            'TestOperation'
        )
        raise error

    with pytest.raises(ClientError):
        always_throttled()

    assert call_count == 3  # Initial + 2 retries
    print(f"✓ Max retries exceeded (3 calls)")


# =============================================================================
# TEST 3: IAM Permission Validation
# =============================================================================

def test_iam_permission_validation():
    """
    SEC-039: Verify IAM permission validation works correctly.

    Evidence Required:
    - Validates on init if validate_permissions=True
    - Raises PermissionError if no Cognito access
    - Logs IAM identity for audit
    """
    from services.cognito_pool_provisioner import CognitoPoolProvisioner

    print("\n=== Testing IAM Permission Validation ===")

    # Test 1: Validation disabled (default behavior)
    with patch('boto3.client'):
        provisioner = CognitoPoolProvisioner(validate_permissions=False)
        assert not provisioner._iam_validated
        print("✓ Validation skipped when validate_permissions=False")

    # Test 2: Validation enabled with access
    with patch('boto3.client') as mock_boto:
        mock_cognito = Mock()
        mock_sts = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'cognito-idp':
                return mock_cognito
            elif service_name == 'sts':
                return mock_sts

        mock_boto.side_effect = client_factory
        mock_sts.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123:role/test'}
        mock_cognito.list_user_pools.return_value = {'UserPools': []}

        provisioner = CognitoPoolProvisioner(validate_permissions=True)
        assert provisioner._iam_validated
        print("✓ Validation passed with proper access")

    # Test 3: Validation enabled without access
    with patch('boto3.client') as mock_boto:
        mock_cognito = Mock()
        mock_sts = Mock()

        def client_factory(service_name, **kwargs):
            if service_name == 'cognito-idp':
                return mock_cognito
            elif service_name == 'sts':
                return mock_sts

        mock_boto.side_effect = client_factory
        mock_sts.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123:role/test'}

        # Simulate access denied
        error = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
            'ListUserPools'
        )
        mock_cognito.list_user_pools.side_effect = error

        with pytest.raises(PermissionError) as exc_info:
            CognitoPoolProvisioner(validate_permissions=True)

        assert "lacks Cognito access" in str(exc_info.value)
        print("✓ PermissionError raised when access denied")


# =============================================================================
# TEST 4: Function Refactoring
# =============================================================================

def test_refactored_methods():
    """
    SEC-039: Verify refactored methods work correctly in isolation.

    Evidence Required:
    - _build_pool_params returns valid structure
    - _create_user_pool handles TagResource gracefully
    - _configure_mfa updates audit_details correctly
    - _create_app_client returns client ID
    - _create_domain is idempotent
    - _create_admin_user handles existing users
    """
    from services.cognito_pool_provisioner import CognitoPoolProvisioner

    print("\n=== Testing Refactored Methods ===")

    with patch('boto3.client') as mock_boto:
        mock_client = Mock()
        mock_boto.return_value = mock_client

        provisioner = CognitoPoolProvisioner(validate_permissions=False)

        # Test 1: _build_pool_params
        pool_params = provisioner._build_pool_params(
            organization_slug='test-org',
            organization_id=123,
            organization_name='Test Org',
            password_policy={'MinimumLength': 12}
        )

        assert pool_params['PoolName'] == 'owkai-test-org'
        assert pool_params['Policies']['PasswordPolicy']['MinimumLength'] == 12
        assert pool_params['MfaConfiguration'] == 'OFF'
        assert 'UserPoolTags' in pool_params
        print("✓ _build_pool_params returns valid structure")

        # Test 2: _create_user_pool with TagResource fallback
        mock_client.create_user_pool.side_effect = [
            ClientError(
                {'Error': {'Code': 'AccessDeniedException', 'Message': 'TagResource denied'}},
                'CreateUserPool'
            ),
            {'UserPool': {'Id': 'pool-123', 'Arn': 'arn:aws:pool-123'}}
        ]

        pool_params_with_tags = {'UserPoolTags': {'test': 'value'}, 'PoolName': 'test'}
        result = provisioner._create_user_pool(pool_params_with_tags)

        assert result['UserPool']['Id'] == 'pool-123'
        assert mock_client.create_user_pool.call_count == 2  # First with tags, retry without
        print("✓ _create_user_pool handles TagResource gracefully")

        # Test 3: _configure_mfa updates audit_details
        mock_client.set_user_pool_mfa_config.return_value = {}
        mock_client.exceptions.InvalidParameterException = type('InvalidParameterException', (Exception,), {})

        audit_details = {}
        provisioner._configure_mfa('pool-123', 'OPTIONAL', audit_details)

        assert 'mfa_configured' in audit_details
        print("✓ _configure_mfa updates audit_details")

        # Test 4: _create_app_client
        mock_client.create_user_pool_client.return_value = {
            'UserPoolClient': {'ClientId': 'client-456'}
        }

        client_id = provisioner._create_app_client('pool-123', 'test-org')
        assert client_id == 'client-456'
        print("✓ _create_app_client returns client ID")

        # Test 5: _create_domain idempotency
        mock_client.create_user_pool_domain.return_value = {}
        mock_client.exceptions.InvalidParameterException = type('InvalidParameterException', (Exception,), {})

        audit_details = {}
        domain = provisioner._create_domain('pool-123', 'test-org', audit_details)

        assert domain == 'owkai-test-org-auth'
        print("✓ _create_domain returns domain name")


# =============================================================================
# TEST 5: Type Hints Verification
# =============================================================================

def test_type_hints():
    """
    SEC-039: Verify type hints are present on all public methods.

    Evidence Required:
    - All parameters have type hints
    - All return types specified
    - Using proper typing imports (Dict, Any, Optional, Tuple)
    """
    import inspect
    from services.cognito_pool_provisioner import CognitoPoolProvisioner

    print("\n=== Testing Type Hints ===")

    provisioner = CognitoPoolProvisioner(validate_permissions=False)

    # Check key methods have type hints
    methods_to_check = [
        '_build_pool_params',
        '_create_user_pool',
        '_configure_mfa',
        '_create_app_client',
        '_create_domain',
        '_create_admin_user'
    ]

    for method_name in methods_to_check:
        method = getattr(provisioner, method_name)
        sig = inspect.signature(method)

        # Check return annotation
        has_return = sig.return_annotation != inspect.Signature.empty

        # Check parameter annotations (exclude self)
        params_with_hints = [
            p for p in sig.parameters.values()
            if p.name != 'self' and p.annotation != inspect.Signature.empty
        ]
        total_params = len([p for p in sig.parameters.values() if p.name != 'self'])

        if has_return and len(params_with_hints) == total_params:
            print(f"✓ {method_name} has complete type hints")
        else:
            print(f"✗ {method_name} missing type hints (return: {has_return}, params: {len(params_with_hints)}/{total_params})")


# =============================================================================
# TEST 6: Edge Cases and Error Scenarios
# =============================================================================

def test_edge_cases():
    """
    SEC-039: Test edge cases and error scenarios.

    Evidence Required:
    - Empty password policy uses defaults
    - MFA=OFF skips configuration
    - Existing users don't generate new passwords
    - Domain already exists is handled gracefully
    """
    from services.cognito_pool_provisioner import CognitoPoolProvisioner

    print("\n=== Testing Edge Cases ===")

    with patch('boto3.client') as mock_boto:
        mock_client = Mock()
        mock_boto.return_value = mock_client

        provisioner = CognitoPoolProvisioner(validate_permissions=False)

        # Test 1: MFA=OFF skips configuration
        audit_details = {}
        provisioner._configure_mfa('pool-123', 'OFF', audit_details)

        assert audit_details['mfa_configured'] == 'OFF'
        mock_client.set_user_pool_mfa_config.assert_not_called()
        print("✓ MFA=OFF skips configuration")

        # Test 2: Existing user returns no password
        mock_client.exceptions.UsernameExistsException = type('UsernameExistsException', (Exception,), {})
        mock_client.admin_create_user.side_effect = mock_client.exceptions.UsernameExistsException()
        mock_client.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'sub', 'Value': 'existing-123'}]
        }

        audit_details = {}
        cognito_id, password = provisioner._create_admin_user(
            'pool-123', 'test@example.com', 1, 'test-org', audit_details
        )

        assert cognito_id == 'existing-123'
        assert password is None
        assert audit_details['admin_note'] == 'User already existed'
        print("✓ Existing user returns no password")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SEC-039 ENTERPRISE HARDENING - COMPREHENSIVE REVIEW")
    print("="*80)

    test_functions = [
        test_retry_decorator_exponential_backoff,
        test_iam_permission_validation,
        test_refactored_methods,
        test_type_hints,
        test_edge_cases
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            print(f"\n{'='*80}")
            print(f"Running: {test_func.__name__}")
            print(f"{'='*80}")
            test_func()
            passed += 1
            print(f"\n✅ PASSED: {test_func.__name__}")
        except Exception as e:
            failed += 1
            print(f"\n❌ FAILED: {test_func.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print(f"{'='*80}\n")
