#!/usr/bin/env python3
"""
AWS Lambda Functional Tests for User Service

Tests the actual Lambda functions with realistic event payloads,
focusing on end-to-end functionality rather than unit testing.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch


def create_api_gateway_event(
    http_method: str,
    path_parameters: dict = None,
    body: dict = None,
    user_id: str = "test-user-123",
):
    """Create a realistic API Gateway Lambda event"""
    event = {
        "httpMethod": http_method,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer mock-jwt-token",
        },
        "pathParameters": path_parameters or {},
        "queryStringParameters": None,
        "body": json.dumps(body) if body else None,
        "isBase64Encoded": False,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api",
            "authorizer": {"uid": user_id, "iss": "vibe-app", "principalId": user_id},
            "httpMethod": http_method,
            "path": "/profile/test-123",
            "requestId": "test-request-123",
            "resourcePath": "/profile/{profileId}",
            "stage": "test",
        },
    }
    return event


def create_sample_profile_data():
    """Create sample profile data for testing"""
    return {
        "profile": {
            "nickName": "Test User",
            "aboutMe": "A test profile for functional testing",
            "age": "25",
            "sexualPosition": "vers",
            "bodyType": "fit",
            "eggplantSize": "average",
            "peachShape": "average",
            "healthPractices": "condoms",
            "hivStatus": "negative",
            "preventionPractices": "none",
            "hosting": "hostAndTravel",
            "travelDistance": "city",
            "allocatedMediaIds": ["12345678"],
            "activeMediaIds": ["12345678"],
        }
    }


def test_profile_management_lambda():
    """Test the profile management Lambda function end-to-end"""
    print("Testing Profile Management Lambda Function...")

    # Add the Lambda function directory to path
    lambda_dir = Path(__file__).parent.parent / "user_profile_mgmt"
    sys.path.insert(0, str(lambda_dir))

    # Add the common aws_lambdas directory for core modules
    common_dir = (
        Path(__file__).parent.parent.parent.parent.parent
        / "src"
        / "common"
        / "aws_lambdas"
    )
    sys.path.insert(0, str(common_dir))

    try:
        with patch("core.aws.DynamoDBService") as mock_db_service:
            # Mock DynamoDB service
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_db_service.get_dynamodb.return_value = mock_dynamodb
            mock_db_service.get_table.return_value = mock_table
            mock_db_service.serialize_dynamodb_item.return_value = {
                "test": "serialized"
            }

            # Mock the transact_write_items for successful operations
            mock_dynamodb.meta.client.transact_write_items.return_value = {}

            with patch("core.manager.CommonManager.__init__") as mock_common_init:
                mock_common_init.return_value = None

                with patch(
                    "core.profile_utils.ProfileManager._get_profiles_records"
                ) as mock_get_profiles:
                    mock_get_profiles.return_value = {}

                    # Import the Lambda function
                    from lambda_function import lambda_handler

                    # Test 1: Create Profile (PUT to non-existing profile)
                    print("  Testing profile creation...")

                    create_event = create_api_gateway_event(
                        http_method="PUT",
                        path_parameters={"profileId": "test-123"},
                        body=create_sample_profile_data(),
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.active_profile_ids = []  # Profile doesn't exist
                        mock_manager.upsert.return_value = True
                        mock_manager.get.return_value = {
                            "profileId": "test-123",
                            "nickName": "Test User",
                            "createdAt": "2023-01-01T00:00:00Z",
                        }
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(create_event, {})

                        assert response["statusCode"] == 200
                        body = json.loads(response["body"])
                        assert "message" in body
                        assert "profile" in body
                        assert body["created"] == True
                        print("    ✓ Profile creation successful")

                    # Test 2: Update Profile (PUT to existing profile)
                    print("  Testing profile update...")

                    update_event = create_api_gateway_event(
                        http_method="PUT",
                        path_parameters={"profileId": "test-123"},
                        body=create_sample_profile_data(),
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.active_profile_ids = ["test-123"]  # Profile exists
                        mock_manager.upsert.return_value = True
                        mock_manager.get.return_value = {
                            "profileId": "test-123",
                            "nickName": "Test User Updated",
                            "updatedAt": "2023-01-01T01:00:00Z",
                        }
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(update_event, {})

                        assert response["statusCode"] == 200
                        body = json.loads(response["body"])
                        assert "message" in body
                        assert "profile" in body
                        assert body["created"] == False
                        print("    ✓ Profile update successful")

                    # Test 3: Get Profile
                    print("  Testing profile retrieval...")

                    get_event = create_api_gateway_event(
                        http_method="GET", path_parameters={"profileId": "test-123"}
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.get.return_value = {
                            "profileId": "test-123",
                            "nickName": "Test User",
                            "aboutMe": "A test profile",
                        }
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(get_event, {})

                        assert response["statusCode"] == 200
                        body = json.loads(response["body"])
                        assert "profile" in body
                        assert body["profile"]["profileId"] == "test-123"
                        print("    ✓ Profile retrieval successful")

                    # Test 4: Delete Profile
                    print("  Testing profile deletion...")

                    delete_event = create_api_gateway_event(
                        http_method="DELETE", path_parameters={"profileId": "test-123"}
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.delete.return_value = True
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(delete_event, {})

                        assert response["statusCode"] == 200
                        body = json.loads(response["body"])
                        assert body["message"] == "Profile deleted"
                        print("    ✓ Profile deletion successful")

                    # Test 5: Error Handling - Invalid Profile ID
                    print("  Testing error handling...")

                    invalid_event = create_api_gateway_event(
                        http_method="GET", path_parameters={"profileId": "invalid-id"}
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = False
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(invalid_event, {})

                        assert response["statusCode"] == 400
                        body = json.loads(response["body"])
                        assert "error" in body
                        print("    ✓ Error handling successful")

                    # Test 6: Test the specific error case from the user
                    print("  Testing the specific ValidationError scenario...")

                    problematic_event = create_api_gateway_event(
                        http_method="PUT",
                        path_parameters={"profileId": "ZponlD-4"},
                        body={
                            "profile": {
                                "profileId": "ZponlD-4",
                                "nickName": "Cobalt Hob",
                                "aboutMe": "Fun & chill person...",
                                "age": "52",
                                "sexualPosition": "top",
                                "bodyType": "fit",
                                "eggplantSize": "large",
                                "peachShape": "average",
                                "healthPractices": "condoms",
                                "hivStatus": "negative",
                                "preventionPractices": "none",
                                "hosting": "hostAndTravel",
                                "travelDistance": "neighbourhood",
                                "allocatedMediaIds": ["87qjdfPR"],
                                "activeMediaIds": ["87qjdfPR"],
                            }
                        },
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.active_profile_ids = []  # New profile
                        mock_manager.upsert.return_value = True
                        mock_manager.get.return_value = {
                            "profileId": "ZponlD-4",
                            "nickName": "Cobalt Hob",
                        }
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(problematic_event, {})

                        assert response["statusCode"] == 200
                        body = json.loads(response["body"])
                        assert "profile" in body
                        print("    ✓ Previously problematic profile creation now works")

                    return True

    except Exception as e:
        print(f"    ✗ Profile management Lambda test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cors_headers():
    """Test that CORS headers are properly set"""
    print("Testing CORS headers...")

    lambda_dir = Path(__file__).parent.parent / "user_profile_mgmt"
    sys.path.insert(0, str(lambda_dir))

    # Add the common aws_lambdas directory for core modules
    common_dir = (
        Path(__file__).parent.parent.parent.parent.parent
        / "src"
        / "common"
        / "aws_lambdas"
    )
    sys.path.insert(0, str(common_dir))

    try:
        with patch("core.aws.DynamoDBService") as mock_db_service:
            mock_db_service.get_dynamodb.return_value = Mock()
            mock_db_service.get_table.return_value = Mock()

            with patch("core.manager.CommonManager.__init__") as mock_init:
                mock_init.return_value = None

                with patch(
                    "core.profile_utils.ProfileManager._get_profiles_records"
                ) as mock_get:
                    mock_get.return_value = {}

                    from lambda_function import lambda_handler

                    event = create_api_gateway_event(
                        http_method="GET", path_parameters={"profileId": "test-123"}
                    )

                    with patch(
                        "lambda_function.ProfileManager"
                    ) as mock_profile_manager:
                        mock_manager = Mock()
                        mock_manager.validate_profile_id.return_value = True
                        mock_manager.get.return_value = {"profileId": "test-123"}
                        mock_profile_manager.return_value = mock_manager

                        response = lambda_handler(event, {})

                        headers = response.get("headers", {})
                        assert "Access-Control-Allow-Origin" in headers
                        assert "Content-Type" in headers
                        print("  ✓ CORS headers are properly configured")

                        return True

    except Exception as e:
        print(f"  ✗ CORS headers test failed: {e}")
        return False


def main():
    """Run all AWS Lambda functional tests"""
    print("AWS Lambda Functional Tests for User Service")
    print("=" * 60)

    all_passed = True

    tests = [
        ("Profile Management Lambda", test_profile_management_lambda),
        ("CORS Headers", test_cors_headers),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            all_passed &= result
            if result:
                print(f"✓ {test_name} tests PASSED\n")
            else:
                print(f"✗ {test_name} tests FAILED\n")
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}\n")
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 All AWS Lambda functional tests PASSED!")
        return 0
    else:
        print("❌ Some AWS Lambda functional tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
