# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Azure DevOps Test Manager
- Complete test point management functionality
- XML test results integration with fuzzy matching
- Multiple output formats (console, JSON, CSV)
- Comprehensive CLI interface
- Environment variable configuration
- Dry run mode for safe previews
- Bulk update operations
- Detailed test case information retrieval
- Flexible filtering options

### Features
- **Test Point Listing**: Retrieve and display test points from Azure DevOps test plans and suites
- **Test Point Updates**: Update outcomes for individual or bulk test points
- **XML Integration**: Parse JUnit/pytest XML results and automatically update corresponding test points
- **Fuzzy Matching**: Intelligent string matching between XML test names and Azure DevOps test cases
- **Multiple Outputs**: Support for console, JSON, and CSV output formats
- **Advanced Filtering**: Filter test points by outcome, automation status, state, and name patterns
- **Security**: Environment variable-based credential management
- **Reliability**: Comprehensive error handling and validation

## [1.0.0] - 2024-10-28

### Added
- Core `AzureTestPointManager` class for Azure DevOps API interactions
- Command-line interface with `azure-devops-test-manager` and `ado-test-manager` commands
- XML test results parser supporting JUnit and pytest formats
- Fuzzy string matching with configurable similarity thresholds
- Comprehensive documentation and examples
- Type hints throughout the codebase
- Extensive error handling and user feedback
- Environment variable configuration with validation
- Support for Python 3.8+

### Dependencies
- `requests>=2.28.0` for Azure DevOps REST API calls
- `beautifulsoup4>=4.11.0` for HTML test step parsing
- `fuzzywuzzy>=0.18.0` for intelligent name matching
- `python-Levenshtein>=0.12.0` for enhanced fuzzy matching performance

### CLI Features
- List test points with detailed information
- Update test point outcomes individually or in bulk
- Parse XML test results and update test points automatically
- Filter operations by multiple criteria
- Export results to JSON and CSV formats
- Dry run mode to preview changes
- Configuration display and validation

### API Features
- Clean object-oriented design with clear separation of concerns
- Comprehensive type hints for better IDE support
- Detailed docstrings for all public methods
- Flexible configuration options
- Exception handling with custom exception types
- Support for both individual and batch operations

### Documentation
- Comprehensive README with usage examples
- Detailed API documentation
- CLI help system with examples
- Installation instructions for multiple scenarios
- Development setup guide

### Testing
- Unit test structure prepared
- Development dependencies configured
- Code quality tools configured (black, flake8, mypy)
- Coverage reporting setup

### Build System
- Modern Python packaging with `pyproject.toml`
- Setuptools configuration with dynamic versioning
- Entry points for CLI commands
- Proper dependency management
- Development and testing dependency groups

---

## Version History Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements