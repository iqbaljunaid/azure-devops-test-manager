"""
Unit tests for Azure DevOps Test Manager CLI functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO
import json
import tempfile
import os


class TestCLI:
    """Test cases for CLI functionality."""

    @patch("azure_devops_test_manager.cli.AzureTestPointManager")
    def test_show_config_command(self, mock_manager_class):
        """Test --show-config command."""
        # Mock manager instance
        mock_manager = Mock()
        mock_manager.organization_url = "https://test.visualstudio.com"
        mock_manager.project_name = "Test Project"
        mock_manager.personal_access_token = "test_token_12345"
        mock_manager_class.return_value = mock_manager

        # Import and test CLI
        from azure_devops_test_manager.cli import main

        with patch("sys.argv", ["azure-devops-test-manager", "--show-config"]):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                # Verify configuration was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                config_output = "\n".join(print_calls)
                assert "https://test.visualstudio.com" in config_output
                assert "Test Project" in config_output

    @patch("azure_devops_test_manager.cli.AzureTestPointManager")
    def test_list_command_success(self, mock_manager_class):
        """Test successful list command."""
        # Mock manager and its methods
        mock_manager = Mock()
        mock_manager.organization_url = "https://test.visualstudio.com"
        mock_manager.project_name = "Test Project"
        mock_manager.list_test_points_for_plan.return_value = {
            123: {
                "suite_info": {"id": 123, "name": "Test Suite", "type": "Static"},
                "test_points": [
                    {
                        "point_id": 456,
                        "test_case_id": 789,
                        "test_case_name": "Sample Test",
                        "outcome": "Passed",
                        "state": "Completed",
                        "configuration_name": "Default",
                        "automated": False,
                        "assigned_to": "Unassigned",
                    }
                ],
            }
        }
        mock_manager_class.return_value = mock_manager

        from azure_devops_test_manager.cli import main

        with patch("sys.argv", ["azure-devops-test-manager", "12345"]):
            with patch("builtins.print"):
                result = main()

                assert result == 0
                mock_manager.list_test_points_for_plan.assert_called_once_with(
                    plan_id=12345, suite_id=None, detailed=False
                )

    @patch("azure_devops_test_manager.cli.AzureTestPointManager")
    def test_update_command_dry_run(self, mock_manager_class):
        """Test update command with dry run."""
        mock_manager = Mock()
        mock_manager.organization_url = "https://test.visualstudio.com"
        mock_manager.project_name = "Test Project"
        mock_manager.list_test_points_for_plan.return_value = {
            123: {
                "suite_info": {"id": 123, "name": "Test Suite", "type": "Static"},
                "test_points": [
                    {
                        "point_id": 456,
                        "test_case_name": "Sample Test",
                        "outcome": "Failed",
                        "state": "Completed",
                        "automated": False,
                    }
                ],
            }
        }
        mock_manager_class.return_value = mock_manager

        from azure_devops_test_manager.cli import main

        with patch(
            "sys.argv",
            [
                "azure-devops-test-manager",
                "12345",
                "--update-outcome",
                "Passed",
                "--dry-run",
            ],
        ):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                # Verify dry run was indicated in output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                output = "\n".join(print_calls)
                assert "DRY RUN" in output

    def test_missing_plan_id_error(self):
        """Test error when plan_id is not provided."""
        from azure_devops_test_manager.cli import main

        with patch("sys.argv", ["azure-devops-test-manager"]):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 1
                # Verify error message was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                error_output = "\n".join(print_calls)
                assert "plan_id is required" in error_output

    @patch("azure_devops_test_manager.cli.AzureTestPointManager")
    def test_configuration_error_handling(self, mock_manager_class):
        """Test handling of configuration errors."""
        from azure_devops_test_manager.core import ConfigurationError
        from azure_devops_test_manager.cli import main

        mock_manager_class.side_effect = ConfigurationError("Missing AZURE_DEVOPS_PAT")

        with patch("sys.argv", ["azure-devops-test-manager", "12345"]):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 1
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                error_output = "\n".join(print_calls)
                assert "Configuration Error" in error_output

    @patch("azure_devops_test_manager.cli.AzureTestPointManager")
    def test_xml_update_command(self, mock_manager_class):
        """Test XML-based update command."""
        mock_manager = Mock()
        mock_manager.organization_url = "https://test.visualstudio.com"
        mock_manager.project_name = "Test Project"
        mock_manager.update_from_test_results.return_value = {
            "total_matches": 5,
            "total_updated": 5,
            "by_outcome": {"Passed": 3, "Failed": 2},
        }
        mock_manager_class.return_value = mock_manager

        from azure_devops_test_manager.cli import main

        # Create a temporary XML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write('<?xml version="1.0"?><testsuites></testsuites>')
            xml_path = f.name

        try:
            with patch(
                "sys.argv",
                ["azure-devops-test-manager", "12345", "--from-xml", xml_path],
            ):
                with patch("builtins.print") as mock_print:
                    result = main()

                    assert result == 0
                    mock_manager.update_from_test_results.assert_called_once()

                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    output = "\n".join(print_calls)
                    assert "XML-based update completed" in output
        finally:
            os.unlink(xml_path)

    def test_help_command(self):
        """Test help command displays usage information."""
        from azure_devops_test_manager.cli import main

        with patch("sys.argv", ["azure-devops-test-manager", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with code 0 for help
            assert exc_info.value.code == 0


class TestOutputFormats:
    """Test different output format functions."""

    def test_print_console_output(self):
        """Test console output formatting."""
        from azure_devops_test_manager.cli import print_console_output

        test_points = {
            123: {
                "suite_info": {"id": 123, "name": "Test Suite", "type": "Static"},
                "test_points": [
                    {
                        "point_id": 456,
                        "test_case_id": 789,
                        "test_case_name": "Sample Test",
                        "outcome": "Passed",
                        "state": "Completed",
                        "configuration_name": "Default",
                        "automated": False,
                        "assigned_to": "Unassigned",
                    }
                ],
            }
        }

        with patch("builtins.print") as mock_print:
            print_console_output(test_points, detailed=False)

            # Verify output was generated
            assert mock_print.called
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = "\n".join(print_calls)
            assert "TEST POINTS SUMMARY" in output
            assert "Test Suite" in output

    def test_save_json_output(self):
        """Test JSON output saving."""
        from azure_devops_test_manager.cli import save_json_output

        test_points = {
            123: {
                "suite_info": {"id": 123, "name": "Test Suite"},
                "test_points": [{"point_id": 456, "test_case_name": "Sample Test"}],
            }
        }

        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("builtins.print"):
                    save_json_output(test_points, 12345)

                    mock_open.assert_called_once()
                    mock_json_dump.assert_called_once()

    def test_save_csv_output(self):
        """Test CSV output saving."""
        from azure_devops_test_manager.cli import save_csv_output

        test_points = {
            123: {
                "suite_info": {"id": 123, "name": "Test Suite", "type": "Static"},
                "test_points": [
                    {
                        "point_id": 456,
                        "test_case_id": 789,
                        "test_case_name": "Sample Test",
                        "outcome": "Passed",
                        "state": "Completed",
                        "configuration_name": "Default",
                        "automated": False,
                        "assigned_to": "Unassigned",
                    }
                ],
            }
        }

        with patch("builtins.open", create=True) as mock_open:
            with patch("csv.writer") as mock_csv_writer:
                mock_writer_instance = Mock()
                mock_csv_writer.return_value = mock_writer_instance

                with patch("builtins.print"):
                    save_csv_output(test_points, 12345)

                    mock_open.assert_called_once()
                    mock_writer_instance.writerow.assert_called()  # Header and data rows


# Test fixtures
@pytest.fixture
def sample_test_points():
    """Sample test points data for testing."""
    return {
        123: {
            "suite_info": {"id": 123, "name": "Auth Tests", "type": "Static"},
            "test_points": [
                {
                    "point_id": 456,
                    "test_case_id": 789,
                    "test_case_name": "Login Test",
                    "outcome": "Passed",
                    "state": "Completed",
                    "configuration_name": "Chrome",
                    "automated": True,
                    "assigned_to": "Test User",
                },
                {
                    "point_id": 457,
                    "test_case_id": 790,
                    "test_case_name": "Logout Test",
                    "outcome": "Failed",
                    "state": "Completed",
                    "configuration_name": "Firefox",
                    "automated": False,
                    "assigned_to": "Unassigned",
                },
            ],
        }
    }


class TestArgumentParsing:
    """Test command line argument parsing."""

    def test_basic_arguments(self):
        """Test parsing of basic arguments."""
        from azure_devops_test_manager.cli import main
        import argparse

        # We can't easily test argparse without running main,
        # so we'll test the parser configuration indirectly
        # by checking that main() handles different argument combinations

        # This is more of a smoke test to ensure the parser is configured correctly
        with patch(
            "azure_devops_test_manager.cli.AzureTestPointManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager.organization_url = "https://test.visualstudio.com"
            mock_manager.project_name = "Test Project"
            mock_manager_class.return_value = mock_manager

            # Test plan_id only
            with patch("sys.argv", ["azure-devops-test-manager", "12345"]):
                with patch("builtins.print"):
                    mock_manager.list_test_points_for_plan.return_value = {}
                    result = main()
                    assert result in [0, 1]  # Should not crash

            # Test plan_id and suite_id
            with patch("sys.argv", ["azure-devops-test-manager", "12345", "67890"]):
                with patch("builtins.print"):
                    mock_manager.list_test_points_for_plan.return_value = {}
                    result = main()
                    assert result in [0, 1]  # Should not crash
