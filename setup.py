"""
Azure DevOps Test Manager

A comprehensive tool for managing Azure DevOps test points with XML integration and fuzzy matching.
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="azure-devops-test-manager",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Azure DevOps Test Manager Team",
    author_email="junaid.iqbal74@gmail.com",
    description="A comprehensive tool for managing Azure DevOps test points with XML integration and fuzzy matching",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iqbaljunaid/azure-devops-test-manager",
    project_urls={
        "Bug Tracker": "https://github.com/iqbaljunaid/azure-devops-test-manager/issues",
        "Documentation": "https://azure-devops-test-manager.readthedocs.io/",
        "Source Code": "https://github.com/iqbaljunaid/azure-devops-test-manager",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "fuzzywuzzy>=0.18.0",
        "python-Levenshtein>=0.12.0",
        "azure-devops>=7.1.0b4",
        "azure-core==1.36.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "responses>=0.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "azure-devops-test-manager=azure_devops_test_manager.cli:main"
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
