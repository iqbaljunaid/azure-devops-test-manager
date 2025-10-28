"""
Core functionality for Azure DevOps test point management.

This module contains the main AzureTestPointManager class that provides
all the functionality for interacting with Azure DevOps test management APIs.
"""

import requests
import json
import csv
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz, process


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class AzureAPIError(Exception):
    """Raised when Azure DevOps API calls fail."""

    pass


class AzureTestPointManager:
    """
    Main class for managing Azure DevOps test points.

    This class provides functionality to list, filter, and update test points
    in Azure DevOps, as well as integrate with XML test results.
    """

    def __init__(
        self,
        personal_access_token: Optional[str] = None,
        organization_url: Optional[str] = None,
        project_name: Optional[str] = None,
        api_version: str = "7.1",
    ):
        """
        Initialize the Azure Test Point Manager.

        Args:
            personal_access_token: Azure DevOps PAT (defaults to AZURE_DEVOPS_PAT env var)
            organization_url: Organization URL (defaults to AZURE_DEVOPS_ORG env var)
            project_name: Project name (defaults to AZURE_DEVOPS_PROJECT env var)
            api_version: API version to use (defaults to "7.1")

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Load configuration from parameters or environment variables
        self.personal_access_token = personal_access_token or os.getenv(
            "AZURE_DEVOPS_PAT"
        )
        self.organization_url = organization_url or os.getenv(
            "AZURE_DEVOPS_ORG", "https://azure-devops.visualstudio.com"
        )
        self.project_name = project_name or os.getenv(
            "AZURE_DEVOPS_PROJECT", "Project_NAME"
        )
        self.api_version = api_version

        # Validate configuration
        self._validate_configuration()

        # Set up authentication and headers
        self.auth = ("", self.personal_access_token)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.base_url = f"{self.organization_url}/{self.project_name}/_apis"

    def _validate_configuration(self) -> None:
        """Validate that all required configuration is present."""
        missing_vars = []

        if not self.personal_access_token:
            missing_vars.append("AZURE_DEVOPS_PAT")

        if not self.organization_url:
            missing_vars.append("AZURE_DEVOPS_ORG")

        if not self.project_name:
            missing_vars.append("AZURE_DEVOPS_PROJECT")

        if missing_vars:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing_vars)}. "
                "Please set the required environment variables or pass them as parameters."
            )

    def get_test_suites(self, plan_id: int) -> List[Dict[str, Any]]:
        """
        Get all test suites for a test plan.

        Args:
            plan_id: The ID of the test plan

        Returns:
            List of test suites

        Raises:
            AzureAPIError: If the API call fails
        """
        try:
            url = f"{self.base_url}/testplan/Plans/{plan_id}/suites?api-version={self.api_version}"

            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return data.get("value", [])

        except requests.exceptions.HTTPError as e:
            raise AzureAPIError(f"HTTP Error fetching test suites: {e}")
        except Exception as e:
            raise AzureAPIError(f"Error fetching test suites: {e}")

    def get_test_points(self, plan_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """
        Get test points for a specific suite.

        Args:
            plan_id: The ID of the test plan
            suite_id: The ID of the test suite

        Returns:
            List of test points

        Raises:
            AzureAPIError: If the API call fails
        """
        try:
            url = f"{self.base_url}/test/Plans/{plan_id}/Suites/{suite_id}/points?api-version={self.api_version}"

            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return data.get("value", [])

        except requests.exceptions.HTTPError as e:
            raise AzureAPIError(
                f"HTTP Error fetching test points for suite {suite_id}: {e}"
            )
        except Exception as e:
            raise AzureAPIError(f"Error fetching test points for suite {suite_id}: {e}")

    def get_test_case_details(self, test_case_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a test case.

        Args:
            test_case_id: The ID of the test case

        Returns:
            Test case details dictionary
        """
        try:
            url = f"{self.base_url}/wit/workitems/{test_case_id}?$expand=all&api-version={self.api_version}"

            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()

            work_item = response.json()
            fields = work_item.get("fields", {})

            # Parse test steps if available
            steps_field = fields.get("Microsoft.VSTS.TCM.Steps", "")
            steps = []

            if steps_field:
                soup = BeautifulSoup(steps_field, "html.parser")
                for step in soup.find_all("step"):
                    parameterized_strings = step.find_all("parameterizedstring")
                    if not parameterized_strings:
                        parameterized_strings = step.find_all("parameterizedString")

                    action = (
                        parameterized_strings[0].text
                        if len(parameterized_strings) > 0
                        else ""
                    )
                    expected = (
                        parameterized_strings[1].text
                        if len(parameterized_strings) > 1
                        else ""
                    )

                    steps.append(
                        {
                            "id": step.get("id"),
                            "type": step.get("type"),
                            "action": action.strip(),
                            "expected": expected.strip(),
                        }
                    )

            return {
                "id": work_item.get("id"),
                "title": fields.get("System.Title", "Unknown"),
                "state": fields.get("System.State", "Unknown"),
                "assigned_to": fields.get("System.AssignedTo", {}).get(
                    "displayName", "Unassigned"
                ),
                "created_by": fields.get("System.CreatedBy", {}).get(
                    "displayName", "Unknown"
                ),
                "created_date": fields.get("System.CreatedDate"),
                "priority": fields.get("Microsoft.VSTS.Common.Priority", "Unknown"),
                "automation_status": fields.get(
                    "Microsoft.VSTS.TCM.AutomationStatus", "Not Automated"
                ),
                "steps": steps,
                "url": work_item.get("_links", {}).get("html", {}).get("href"),
            }

        except Exception as e:
            # Return basic info if detailed fetch fails
            return {
                "id": test_case_id,
                "title": "Unable to fetch details",
                "state": "Unknown",
                "steps": [],
            }

    def process_test_point(
        self, point: Dict[str, Any], detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Process and format a test point for display.

        Args:
            point: Raw test point data from API
            detailed: Whether to fetch detailed test case information

        Returns:
            Processed test point data dictionary
        """
        test_case = point.get("testCase", {})
        configuration = point.get("configuration", {})

        processed_point = {
            "point_id": point.get("id"),
            "test_case_id": test_case.get("id"),
            "test_case_name": test_case.get("name", "Unknown"),
            "test_case_url": test_case.get("url"),
            "configuration_id": configuration.get("id"),
            "configuration_name": configuration.get("name", "Default"),
            "state": point.get("state", "Unknown"),
            "outcome": point.get("outcome", "Unknown"),
            "last_test_run_id": point.get("lastTestRun", {}).get("id"),
            "last_result_id": point.get("lastResult", {}).get("id"),
            "assigned_to": point.get("assignedTo", {}).get("displayName", "Unassigned"),
            "automated": point.get("isAutomated", False),
            "suite_id": point.get("suiteId"),
            "plan_id": point.get("testPlan", {}).get("id"),
        }

        # Fetch detailed test case information if requested
        if detailed and processed_point["test_case_id"]:
            test_case_details = self.get_test_case_details(
                processed_point["test_case_id"]
            )
            processed_point.update(
                {
                    "test_case_details": test_case_details,
                    "test_case_title": test_case_details.get(
                        "title", processed_point["test_case_name"]
                    ),
                    "test_case_state": test_case_details.get("state", "Unknown"),
                    "test_case_priority": test_case_details.get("priority", "Unknown"),
                    "automation_status": test_case_details.get(
                        "automation_status", "Not Automated"
                    ),
                    "steps_count": len(test_case_details.get("steps", [])),
                }
            )

        return processed_point

    def list_test_points_for_plan(
        self, plan_id: int, suite_id: Optional[int] = None, detailed: bool = False
    ) -> Dict[str, Any]:
        """
        List all test points for a test plan.

        Args:
            plan_id: The ID of the test plan
            suite_id: The ID of a specific test suite (optional)
            detailed: Whether to fetch detailed test case information

        Returns:
            Dictionary containing test points organized by suite
        """
        all_test_points = {}

        if suite_id:
            # Process specific suite
            test_points = self.get_test_points(plan_id, suite_id)

            if test_points:
                processed_points = [
                    self.process_test_point(point, detailed) for point in test_points
                ]
                all_test_points[suite_id] = {
                    "suite_info": {
                        "id": suite_id,
                        "name": f"Suite {suite_id}",
                        "type": "Unknown",
                    },
                    "test_points": processed_points,
                }
        else:
            # Process all suites
            suites = self.get_test_suites(plan_id)

            for suite in suites:
                suite_id = suite["id"]
                suite_name = suite["name"]
                suite_type = suite.get("suiteType", "Unknown")

                test_points = self.get_test_points(plan_id, suite_id)

                if test_points:
                    processed_points = [
                        self.process_test_point(point, detailed)
                        for point in test_points
                    ]

                    all_test_points[suite_id] = {
                        "suite_info": {
                            "id": suite_id,
                            "name": suite_name,
                            "type": suite_type,
                            "parent_suite_id": suite.get("parentSuite", {}).get("id"),
                            "plan_id": suite.get("plan", {}).get("id"),
                        },
                        "test_points": processed_points,
                    }

        return all_test_points

    def update_test_point_outcome(
        self,
        plan_id: int,
        suite_id: int,
        point_id: int,
        outcome: str,
        comment: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update test point outcome using PATCH API.

        Args:
            plan_id: The ID of the test plan
            suite_id: The ID of the test suite
            point_id: The ID of the test point
            outcome: New outcome ('Passed', 'Failed', 'Blocked', etc.)
            comment: Optional comment for the update

        Returns:
            Updated test point data or None if failed

        Raises:
            AzureAPIError: If the API call fails
        """
        try:
            url = f"{self.base_url}/test/Plans/{plan_id}/Suites/{suite_id}/points/{point_id}?api-version={self.api_version}"

            payload = {"outcome": outcome}

            if comment:
                payload["comment"] = comment

            response = requests.patch(
                url, auth=self.auth, headers=self.headers, json=payload
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            raise AzureAPIError(f"HTTP Error updating point {point_id}: {e}")
        except Exception as e:
            raise AzureAPIError(f"Error updating point {point_id}: {e}")

    def parse_test_results_xml(
        self, xml_file_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse test results from XML file (JUnit/pytest format).

        Args:
            xml_file_path: Path to the XML test results file

        Returns:
            Dictionary containing test results categorized by outcome
        """
        if not os.path.exists(xml_file_path):
            raise FileNotFoundError(f"XML file not found: {xml_file_path}")

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            test_results = {"passed": [], "failed": [], "skipped": [], "error": []}

            # Find all testcase elements
            for testcase in root.iter("testcase"):
                classname = testcase.get("classname", "")
                name = testcase.get("name", "")
                time = testcase.get("time", "0")

                # Construct full test name for matching
                full_name = f"{classname}.{name}" if classname else name

                # Clean up the test name for better matching
                clean_name = name
                if clean_name.startswith("test_"):
                    clean_name = clean_name[5:]  # Remove "test_" prefix

                test_info = {
                    "classname": classname,
                    "name": name,
                    "full_name": full_name,
                    "clean_name": clean_name,
                    "time": float(time),
                    "raw_element": testcase,
                }

                # Check for failure, error, or skipped elements
                if testcase.find("failure") is not None:
                    failure_elem = testcase.find("failure")
                    test_info["failure_message"] = failure_elem.get("message", "")
                    test_info["failure_text"] = failure_elem.text or ""
                    test_results["failed"].append(test_info)

                elif testcase.find("error") is not None:
                    error_elem = testcase.find("error")
                    test_info["error_message"] = error_elem.get("message", "")
                    test_info["error_text"] = error_elem.text or ""
                    test_results["error"].append(test_info)

                elif testcase.find("skipped") is not None:
                    skipped_elem = testcase.find("skipped")
                    test_info["skip_message"] = skipped_elem.get("message", "")
                    test_info["skip_text"] = skipped_elem.text or ""
                    test_results["skipped"].append(test_info)

                else:
                    # No failure, error, or skipped -> passed
                    test_results["passed"].append(test_info)

            return test_results

        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error parsing XML file: {e}")

    def fuzzy_match_test_names(
        self,
        test_results: Dict[str, List[Dict[str, Any]]],
        azure_test_points: Dict[str, Any],
        min_score: int = 80,
    ) -> Dict[str, Any]:
        """
        Match test results with Azure DevOps test points using fuzzy matching.

        Args:
            test_results: Parsed test results from XML
            azure_test_points: Azure DevOps test points
            min_score: Minimum fuzzy matching score (0-100)

        Returns:
            Dictionary with matching results
        """
        # Create a flat list of all test results with their outcomes
        all_test_results = []
        for outcome, tests in test_results.items():
            for test in tests:
                test["xml_outcome"] = outcome
                all_test_results.append(test)

        # Create a flat list of all Azure test points
        all_azure_points = []
        for suite_id, suite_data in azure_test_points.items():
            for point in suite_data["test_points"]:
                point["suite_id"] = suite_id
                all_azure_points.append(point)

        # Create name lists for fuzzy matching
        xml_test_names = [test["clean_name"] for test in all_test_results]
        xml_full_names = [test["full_name"] for test in all_test_results]

        matches = []
        unmatched_azure = []

        for azure_point in all_azure_points:
            azure_name = azure_point.get(
                "test_case_title", azure_point["test_case_name"]
            )
            azure_clean_name = azure_name.lower().replace("_", " ").replace("-", " ")

            # Try different matching strategies
            best_match = None
            best_score = 0
            match_strategy = ""

            # Strategy 1: Match against clean names
            match_result = process.extractOne(
                azure_clean_name, xml_test_names, scorer=fuzz.ratio
            )
            if match_result and match_result[1] > best_score:
                best_match = match_result
                best_score = match_result[1]
                match_strategy = "clean_name"

            # Strategy 2: Match against full names
            match_result = process.extractOne(
                azure_clean_name, xml_full_names, scorer=fuzz.partial_ratio
            )
            if match_result and match_result[1] > best_score:
                best_match = match_result
                best_score = match_result[1]
                match_strategy = "full_name"

            # Strategy 3: Token sort ratio for more flexible matching
            for xml_test in all_test_results:
                xml_name = xml_test["clean_name"]
                score = fuzz.token_sort_ratio(
                    azure_clean_name.lower(), xml_name.lower()
                )
                if score > best_score:
                    best_match = (xml_name, score)
                    best_score = score
                    match_strategy = "token_sort"

            if best_score >= min_score:
                # Find the matching XML test
                matched_xml_test = None
                if match_strategy == "clean_name":
                    matched_xml_test = next(
                        (
                            t
                            for t in all_test_results
                            if t["clean_name"] == best_match[0]
                        ),
                        None,
                    )
                elif match_strategy == "full_name":
                    matched_xml_test = next(
                        (
                            t
                            for t in all_test_results
                            if t["full_name"] == best_match[0]
                        ),
                        None,
                    )
                else:  # token_sort
                    matched_xml_test = next(
                        (
                            t
                            for t in all_test_results
                            if t["clean_name"] == best_match[0]
                        ),
                        None,
                    )

                if matched_xml_test:
                    match_info = {
                        "azure_point": azure_point,
                        "xml_test": matched_xml_test,
                        "match_score": best_score,
                        "match_strategy": match_strategy,
                        "azure_name": azure_name,
                        "xml_name": matched_xml_test["name"],
                    }
                    matches.append(match_info)
                else:
                    unmatched_azure.append(azure_point)
            else:
                unmatched_azure.append(azure_point)

        # Find unmatched XML tests
        matched_xml_names = {match["xml_test"]["name"] for match in matches}
        unmatched_xml = [
            test for test in all_test_results if test["name"] not in matched_xml_names
        ]

        return {
            "matches": matches,
            "unmatched_azure": unmatched_azure,
            "unmatched_xml": unmatched_xml,
        }

    def update_from_test_results(
        self,
        plan_id: int,
        xml_file_path: str,
        suite_id: Optional[int] = None,
        min_score: int = 80,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update Azure DevOps test points based on test results from XML file.

        Args:
            plan_id: The ID of the test plan
            xml_file_path: Path to the XML test results file
            suite_id: The ID of a specific test suite (optional)
            min_score: Minimum fuzzy matching score (0-100)
            comment: Optional comment for the updates

        Returns:
            Dictionary with update summary
        """
        # Parse XML test results
        test_results = self.parse_test_results_xml(xml_file_path)

        # Get Azure DevOps test points
        azure_test_points = self.list_test_points_for_plan(plan_id, suite_id)

        # Perform fuzzy matching
        matching_results = self.fuzzy_match_test_names(
            test_results, azure_test_points, min_score
        )
        matches = matching_results["matches"]

        if not matches:
            return {"total_matches": 0, "total_updated": 0, "error": "No matches found"}

        # Map XML outcomes to Azure outcomes
        outcome_mapping = {
            "failed": "Failed",
            "error": "Failed",
            "skipped": "Blocked",
            "passed": "Passed",
        }

        update_summary = {
            "total_matches": len(matches),
            "total_updated": 0,
            "by_outcome": {},
            "errors": [],
        }

        # Update test points
        for match in matches:
            xml_outcome = match["xml_test"]["xml_outcome"]
            azure_outcome = outcome_mapping.get(xml_outcome, "None")
            azure_point = match["azure_point"]

            try:
                self.update_test_point_outcome(
                    plan_id=plan_id,
                    suite_id=azure_point["suite_id"],
                    point_id=azure_point["point_id"],
                    outcome=azure_outcome,
                    comment=comment,
                )

                update_summary["total_updated"] += 1

                # Track by outcome
                if azure_outcome not in update_summary["by_outcome"]:
                    update_summary["by_outcome"][azure_outcome] = 0
                update_summary["by_outcome"][azure_outcome] += 1

            except AzureAPIError as e:
                update_summary["errors"].append(str(e))

        return update_summary
