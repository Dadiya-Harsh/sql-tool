from setuptools import setup, find_packages

setup(
    name="sql-agent-tool",          # Package name (must be unique if publishing to PyPI)
    version="0.1.8",                # Version number
    description="A Python tool for interacting with PostgreSQL databases",
    long_description=open("README.md").read(),  # Use README as description
    long_description_content_type="text/markdown",
    author="Harsh Dadiya",
    author_email="harshdadiya@gmail.com",
    url="https://github.com/Dadiya-Harsh/sql-tool",  # Replace with your GitHub URL
    packages=find_packages(),       # Automatically find packages (e.g., sql_agent_tool)
    install_requires=[              # List dependencies
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "groq>=0.1",
    "pydantic>=2.0",
    "sqlparse>=0.4",
    "python-dotenv>=0.20",
    "openai>=1.0",
    "google-generativeai>=0.3"
    ],
    python_requires=">=3.10",       # Specify minimum Python version
    classifiers=[                   # Metadata for PyPI (optional)
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)