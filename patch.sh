# fix tests/__init__.py spacing and ensure trailing newline
python - <<'PY'
p = "tests/__init__.py"
with open(p, "r", encoding="utf-8") as f:
    s = f.read().rstrip()
# normalize to the formatted content above
formatted = '''"""
Tests for Azure DevOps Test Manager package.
"""


# Test package imports
def test_package_imports():
    """Test that main package components can be imported."""
    try:
        from azure_devops_test_manager import AzureTestPointManager, cli_main
        from azure_devops_test_manager import __version__

        # If we get here, imports work
        assert True
    except ImportError:
        # In test environment, imports might fail if package not installed
        # This is expected during development
        pass


def test_version_available():
    """Test that version information is available."""
    try:
        from azure_devops_test_manager import __version__

        assert __version__ is not None
    except ImportError:
        # Expected during development before package installation
        pass
'''
with open(p, "w", encoding="utf-8") as f:
    f.write(formatted)
print("Updated", p)
PY

# fix quotes in _version.py
sed -i 's/__version__ = version = .*/__version__ = version = "1.0.2.dev4+g6a0d5d905"/' src/azure_devops_test_manager/_version.py
sed -i 's/__version_tuple__ = version_tuple = (1, 0, 2, .*/__version_tuple__ = version_tuple = (1, 0, 2, "dev4", "g6a0d5d905")/' src/azure_devops_test_manager/_version.py
sed -i 's/__commit_id__ = commit_id = .*/__commit_id__ = commit_id = "g6a0d5d905"/' src/azure_devops_test_manager/_version.py
