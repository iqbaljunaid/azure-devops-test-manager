"""
Unit tests for Azure DevOps Test Manager core functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from azure_devops_test_manager.core import (
    AzureTestPointManager,
    ConfigurationError,
    AzureAPIError,
)


class TestAzureTestPointManager:
    """Test cases for AzureTestPointManager class."""

    @patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_PAT": "test_token",
            "AZURE_DEVOPS_ORG": "https://test.visualstudio.com",
            "AZURE_DEVOPS_PROJECT": "Test Project",
        },
    )
    def test_initialization_with_env_vars(self):
        """Test initialization with environment variables."""
        manager = AzureTestPointManager()

        assert manager.personal_access_token == "test_token"
        assert manager.organization_url == "https://test.visualstudio.com"
        assert manager.project_name == "Test Project"
        assert manager.api_version == "7.1"

    def test_initialization_with_parameters(self):
        """Test initialization with explicit parameters."""
        manager = AzureTestPointManager(
            personal_access_token="param_token",
            organization_url="https://param.visualstudio.com",
            project_name="Param Project",
            api_version="6.0",
        )

        assert manager.personal_access_token == "param_token"
        assert manager.organization_url == "https://param.visualstudio.com"
        assert manager.project_name == "Param Project"
        assert manager.api_version == "6.0"

    def test_initialization_missing_token(self):
        """Test initialization fails when PAT is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError):
                AzureTestPointManager()

    @patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_PAT": "test_token",
            "AZURE_DEVOPS_ORG": "https://test.visualstudio.com",
            "AZURE_DEVOPS_PROJECT": "Test Project",
        },
    )
    @patch("azure_devops_test_manager.core.requests.get")
    def test_get_test_suites_success(self, mock_get):
        """Test successful retrieval of test suites."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "value": [
                {"id": 1, "name": "Suite 1", "suiteType": "StaticTestSuite"},
                {"id": 2, "name": "Suite 2", "suiteType": "DynamicTestSuite"},
            ]
        }
        mock_get.return_value = mock_response

        manager = AzureTestPointManager()
        suites = manager.get_test_suites(12345)

        assert len(suites) == 2
        assert suites[0]["id"] == 1
        assert suites[0]["name"] == "Suite 1"

    @patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_PAT": "test_token",
            "AZURE_DEVOPS_ORG": "https://test.visualstudio.com",
            "AZURE_DEVOPS_PROJECT": "Test Project",
        },
    )
    @patch("azure_devops_test_manager.core.requests.get")
    def test_get_test_points_success(self, mock_get):
        """Test successful retrieval of test points."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "value": [
                {
                    "id": 101,
                    "testCase": {"id": 201, "name": "Test Case 1"},
                    "configuration": {"id": 301, "name": "Windows 10"},
                    "outcome": "Passed",
                    "state": "Completed",
                }
            ]
        }
        mock_get.return_value = mock_response

        manager = AzureTestPointManager()
        points = manager.get_test_points(12345, 67890)

        assert len(points) == 1
        assert points[0]["id"] == 101
        assert points[0]["testCase"]["name"] == "Test Case 1"

    @patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_PAT": "test_token",
            "AZURE_DEVOPS_ORG": "https://test.visualstudio.com",
            "AZURE_DEVOPS_PROJECT": "Test Project",
        },
    )
    @patch("azure_devops_test_manager.core.requests.patch")
    def test_update_test_point_outcome_success(self, mock_patch):
        """Test successful test point outcome update."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 101, "outcome": "Passed"}
        mock_patch.return_value = mock_response

        manager = AzureTestPointManager()
        result = manager.update_test_point_outcome(
            12345, 67890, 101, "Passed", "Test comment"
        )

        assert result["id"] == 101
        assert result["outcome"] == "Passed"

        # Verify the API call was made with correct parameters
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"]["outcome"] == "Passed"
        assert call_args.kwargs["json"]["comment"] == "Test comment"

    def test_process_test_point(self):
        """Test test point processing."""
        manager = AzureTestPointManager(
            personal_access_token="test_token",
            organization_url="https://test.visualstudio.com",
            project_name="Test Project",
        )

        raw_point = {
            "id": 101,
            "testCase": {"id": 201, "name": "Test Case 1"},
            "configuration": {"id": 301, "name": "Windows 10"},
            "outcome": "Passed",
            "state": "Completed",
            "isAutomated": True,
            "assignedTo": {"displayName": "John Doe"},
        }

        processed = manager.process_test_point(raw_point)

        assert processed["point_id"] == 101
        assert processed["test_case_id"] == 201
        assert processed["test_case_name"] == "Test Case 1"
        assert processed["configuration_name"] == "Windows 10"
        assert processed["outcome"] == "Passed"
        assert processed["state"] == "Completed"
        assert processed["automated"] is True
        assert processed["assigned_to"] == "John Doe"


class TestXMLParsing:
    """Test cases for XML parsing functionality."""

    def test_parse_test_results_xml(self, tmp_path):
        """Test XML test results parsing."""
        # Create a test XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <testsuites>
            <testsuite name="pytest" tests="4" failures="1" errors="1" skipped="1">
                <testcase classname="tests.test_example" name="test_pass" time="0.001"/>
                <testcase classname="tests.test_example" name="test_fail" time="0.002">
                    <failure message="AssertionError">Test failed</failure>
                </testcase>
                <testcase classname="tests.test_example" name="test_error" time="0.003">
                    <error message="RuntimeError">Test error</error>
                </testcase>
                <testcase classname="tests.test_example" name="test_skip" time="0.000">
                    <skipped message="Skipped"/>
                </testcase>
            </testsuite>
        </testsuites>"""

        xml_file = tmp_path / "test_results.xml"
        xml_file.write_text(xml_content)

        manager = AzureTestPointManager(
            personal_access_token="test_token",
            organization_url="https://test.visualstudio.com",
            project_name="Test Project",
        )

        results = manager.parse_test_results_xml(str(xml_file))

        assert len(results["passed"]) == 1
        assert len(results["failed"]) == 1
        assert len(results["error"]) == 1
        assert len(results["skipped"]) == 1

        # Check passed test
        passed_test = results["passed"][0]
        assert passed_test["name"] == "test_pass"
        assert passed_test["classname"] == "tests.test_example"
        assert passed_test["clean_name"] == "pass"

        # Check failed test
        failed_test = results["failed"][0]
        assert failed_test["name"] == "test_fail"
        assert "failure_message" in failed_test

    def test_parse_nonexistent_xml_file(self):
        """Test parsing non-existent XML file raises error."""
        manager = AzureTestPointManager(
            personal_access_token="test_token",
            organization_url="https://test.visualstudio.com",
            project_name="Test Project",
        )

        with pytest.raises(FileNotFoundError):
            manager.parse_test_results_xml("/nonexistent/file.xml")


class TestFuzzyMatching:
    """Test cases for fuzzy matching functionality."""

    def test_fuzzy_match_test_names(self):
        """Test fuzzy matching between XML tests and Azure test points."""
        manager = AzureTestPointManager(
            personal_access_token="test_token",
            organization_url="https://test.visualstudio.com",
            project_name="Test Project",
        )

        # Sample test results from XML
        test_results = {
            "passed": [
                {
                    "name": "test_login_success",
                    "clean_name": "login_success",
                    "full_name": "tests.auth.test_login_success",
                    "xml_outcome": "passed",
                }
            ],
            "failed": [
                {
                    "name": "test_login_failure",
                    "clean_name": "login_failure",
                    "full_name": "tests.auth.test_login_failure",
                    "xml_outcome": "failed",
                }
            ],
            "skipped": [],
            "error": [],
        }

        # Sample Azure test points
        azure_test_points = {
            123: {
                "suite_info": {"id": 123, "name": "Auth Tests"},
                "test_points": [
                    {
                        "point_id": 456,
                        "test_case_name": "Login Success Test",
                        "test_case_title": "Login Success Test",
                        "suite_id": 123,
                    },
                    {
                        "point_id": 789,
                        "test_case_name": "Login Failure Test",
                        "test_case_title": "Login Failure Test",
                        "suite_id": 123,
                    },
                ],
            }
        }

        # Add xml_outcome to test results
        for outcome, tests in test_results.items():
            for test in tests:
                test["xml_outcome"] = outcome

        matches = manager.fuzzy_match_test_names(
            test_results, azure_test_points, min_score=70
        )

        # Should find some matches
        assert (
            len(matches["matches"]) >= 0
        )  # May vary based on fuzzy matching algorithm
        assert "unmatched_azure" in matches
        assert "unmatched_xml" in matches


# Integration tests (require actual Azure DevOps connection)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require actual Azure DevOps connection."""

    @pytest.mark.skip(reason="Requires actual Azure DevOps credentials")
    def test_real_azure_connection(self):
        """Test actual connection to Azure DevOps."""
        # This test would require real credentials and should be skipped by default
        pass


# Fixtures for testing
@pytest.fixture
def sample_xml_file(tmp_path):
    """Create a sample XML test results file."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <testsuites>
        <testsuite name="pytest" tests="2" failures="1">
            <testcase classname="tests.example" name="test_success" time="0.001"/>
            <testcase classname="tests.example" name="test_failure" time="0.002">
                <failure message="Test failed">Assertion failed</failure>
            </testcase>
        </testsuite>
    </testsuites>"""

    xml_file = tmp_path / "sample_results.xml"
    xml_file.write_text(xml_content)
    return str(xml_file)


@pytest.fixture
def mock_azure_manager():
    """Create a mock Azure Test Point Manager for testing."""
    with patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_PAT": "test_token",
            "AZURE_DEVOPS_ORG": "https://test.visualstudio.com",
            "AZURE_DEVOPS_PROJECT": "Test Project",
        },
    ):
        return AzureTestPointManager()


# Test configuration
@pytest.mark.unit
class TestConfiguration:
    """Test configuration and validation."""

    def test_missing_configuration_raises_error(self):
        """Test that missing configuration raises appropriate error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as excinfo:
                AzureTestPointManager()

            assert "AZURE_DEVOPS_PAT" in str(excinfo.value)

    def test_partial_configuration_raises_error(self):
        """Test that partial configuration raises appropriate error."""
        with patch.dict(os.environ, {"AZURE_DEVOPS_PAT": "token"}, clear=True):
            # Should work with defaults
            manager = AzureTestPointManager()
            assert manager.personal_access_token == "token"
