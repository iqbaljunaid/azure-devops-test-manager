"""
Azure DevOps Test Manager

A comprehensive tool for managing Azure DevOps test points with XML integration and fuzzy matching.

This package provides functionality to:
- List test points from Azure DevOps test plans and suites
- Update test point outcomes using PATCH API
- Filter test points by various criteria
- Output results in multiple formats (console, JSON, CSV)
- Parse XML test results and automatically update test points using fuzzy matching

Example Usage:
    from azure_devops_test_manager import AzureTestPointManager

    # Create manager instance
    manager = AzureTestPointManager()

    # List test points
    points = manager.list_test_points_for_plan(plan_id=12345)

    # Update from XML results
    manager.update_from_test_results(
        plan_id=12345,
        xml_file_path="test-results.xml"
    )

Environment Variables:
    AZURE_DEVOPS_PAT: Your Azure DevOps Personal Access Token (required)
    AZURE_DEVOPS_ORG: Organization URL (default: https://azure-devops.visualstudio.com)
    AZURE_DEVOPS_PROJECT: Project name (default: Project_NAME)
"""

try:
    from ._version import version as __version__
except ImportError:
    # Fallback for development/editable installs
    __version__ = "unknown"

from .core import AzureTestPointManager
from .cli import main as cli_main

__all__ = ["__version__", "AzureTestPointManager", "cli_main"]

