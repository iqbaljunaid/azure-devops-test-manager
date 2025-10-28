# Azure DevOps Test Manager

[![CI](https://github.com/iqbaljunaid/azure-devops-test-manager/workflows/CI/badge.svg)](https://github.com/iqbaljunaid/azure-devops-test-manager/actions/workflows/ci.yml)
[![Build and Publish](https://github.com/iqbaljunaid/azure-devops-test-manager/workflows/Build%20and%20Publish%20to%20PyPI/badge.svg)](https://github.com/iqbaljunaid/azure-devops-test-manager/actions/workflows/publish.yml)
[![PyPI version](https://badge.fury.io/py/azure-devops-test-manager.svg)](https://badge.fury.io/py/azure-devops-test-manager)
[![Python Support](https://img.shields.io/pypi/pyversions/azure-devops-test-manager.svg)](https://pypi.org/project/azure-devops-test-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive tool for managing Azure DevOps test points with XML integration and fuzzy matching capabilities.

## Features

- **Test Point Management**: List, filter, and update test points from Azure DevOps test plans and suites
- **XML Integration**: Parse JUnit/pytest XML test results and automatically update test points
- **Fuzzy Matching**: Intelligent matching between XML test names and Azure DevOps test case names
- **Multiple Output Formats**: Console, JSON, and CSV output support
- **Flexible Filtering**: Filter test points by outcome, automation status, state, and name patterns
- **Bulk Operations**: Update multiple test points efficiently with batch operations
- **Dry Run Mode**: Preview changes before applying them
- **Environment Configuration**: Secure credential management through environment variables

## Installation

### From PyPI (Recommended)

```bash
pip install azure-devops-test-manager
```

### From Source

```bash
git clone https://github.com/iqbaljunaid/azure-devops-test-manager.git
cd azure-devops-test-manager
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/iqbaljunaid/azure-devops-test-manager.git
cd azure-devops-test-manager
pip install -e ".[dev]"
```

## Quick Start

### 1. Configuration

Set up your Azure DevOps credentials as environment variables:

```bash
export AZURE_DEVOPS_PAT="your_personal_access_token"
export AZURE_DEVOPS_ORG="https://dev.azure.com/yourorg"
export AZURE_DEVOPS_PROJECT="Your Project Name"
```

### 2. Basic Usage

```bash
# List all test points in a test plan
azure-devops-test-manager 12345

# List test points for a specific suite with details
azure-devops-test-manager 12345 67890 --detailed

# Update test points from XML results
azure-devops-test-manager 12345 --from-xml test-results.xml

# Preview updates without applying them
azure-devops-test-manager 12345 --update-outcome Passed --dry-run
```

## Command Line Usage

### Listing Test Points

```bash
# List all test points in a test plan
azure-devops-test-manager 679333

# List test points for a specific suite
azure-devops-test-manager 679333 679334

# Get detailed test case information (slower)
azure-devops-test-manager 679333 --detailed

# Export results to different formats
azure-devops-test-manager 679333 --output json
azure-devops-test-manager 679333 --output csv
```

### Updating Test Points

```bash
# Update all test points to "Passed"
azure-devops-test-manager 679333 --update-outcome Passed

# Update only specific outcomes
azure-devops-test-manager 679333 --update-outcome Passed --filter-outcome Failed

# Update only automated tests
azure-devops-test-manager 679333 --update-outcome Passed --filter-automated true

# Add comments to updates
azure-devops-test-manager 679333 --update-outcome Passed --comment "Fixed in latest build"

# Preview changes before applying
azure-devops-test-manager 679333 --update-outcome Passed --dry-run
```

### XML-Based Updates

The tool can parse JUnit/pytest XML test results and automatically update test points:

```bash
# Update test points based on XML results
azure-devops-test-manager 679333 --from-xml test-results.xml

# Preview XML-based updates
azure-devops-test-manager 679333 --from-xml test-results.xml --dry-run

# Update specific suite with higher matching threshold
azure-devops-test-manager 679333 679334 --from-xml test-results.xml --min-score 90

# Add comment to XML-based updates
azure-devops-test-manager 679333 --from-xml test-results.xml --comment "Updated from CI pipeline"
```

### Configuration

```bash
# Check current configuration
azure-devops-test-manager --show-config

# Get help
azure-devops-test-manager --help
```

## Python API Usage

You can also use the tool programmatically:

```python
from azure_devops_test_manager import AzureTestPointManager

# Initialize manager
manager = AzureTestPointManager()

# List test points
test_points = manager.list_test_points_for_plan(plan_id=12345)

# Update from XML results
results = manager.update_from_test_results(
    plan_id=12345,
    xml_file_path="test-results.xml",
    comment="Updated from automated tests"
)

print(f"Updated {results['total_updated']} test points")

# Update specific test point
manager.update_test_point_outcome(
    plan_id=12345,
    suite_id=67890,
    point_id=123,
    outcome="Passed",
    comment="Manual verification complete"
)
```

## Configuration

The tool supports configuration through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_DEVOPS_PAT` | Personal Access Token (Required) | None |
| `AZURE_DEVOPS_ORG` | Organization URL | `https://azure-devops.visualstudio.com` |
| `AZURE_DEVOPS_PROJECT` | Project Name | `Project_NAME` |

### Required Permissions

Your Azure DevOps Personal Access Token needs the following permissions:
- **Test Management**: Read & Write
- **Work Items**: Read (for detailed test case information)

## XML Test Results Format

The tool supports standard JUnit/pytest XML formats. Example:

```xml
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="3" failures="1" skipped="1">
    <testcase classname="tests.test_example" name="test_success" time="0.001"/>
    <testcase classname="tests.test_example" name="test_failure" time="0.002">
      <failure message="AssertionError">Test failed</failure>
    </testcase>
    <testcase classname="tests.test_example" name="test_skip" time="0.000">
      <skipped message="Skipped test"/>
    </testcase>
  </testsuite>
</testsuites>
```

## Outcome Mapping

XML test results are mapped to Azure DevOps outcomes as follows:

| XML Result | Azure DevOps Outcome |
|------------|----------------------|
| `passed` | `Passed` |
| `failed` | `Failed` |
| `error` | `Failed` |
| `skipped` | `Blocked` |

## Fuzzy Matching

The tool uses fuzzy string matching to correlate XML test names with Azure DevOps test case names:

- **Clean Name Matching**: Removes common prefixes like `test_`
- **Partial Matching**: Handles partial name matches
- **Token Sort Matching**: Flexible word order matching
- **Configurable Threshold**: Minimum similarity score (default: 80%)

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/azure-devops-test-manager.git
cd azure-devops-test-manager
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src tests
```

### Type Checking

```bash
mypy src
```

### Building Package

```bash
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/azure-devops-test-manager/issues)
- **Documentation**: [Read the Docs](https://azure-devops-test-manager.readthedocs.io/)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/azure-devops-test-manager/discussions)

## Acknowledgments

- Built with [requests](https://requests.readthedocs.io/) for HTTP API calls
- Uses [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for intelligent name matching
- XML parsing with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- Inspired by the need for better integration between test automation and Azure DevOps test management