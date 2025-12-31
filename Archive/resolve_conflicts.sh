#!/bin/bash
set -e

echo "=== Resolving conflicts for PR #2 and #3 ==="

# Create backup of current files
cp .gitignore .gitignore.backup
cp requirements.txt requirements.txt.backup

# For .gitignore: merge both versions
echo "# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg
*.egg-info/
dist/
build/
*.log

# Jupyter Notebook
.ipynb_checkpoints/

# Virtual environments
venv/
env/
.venv/
.env/

# From PR #2/#3
Github-branch.md
.env" > .gitignore

# For requirements.txt: merge both versions
echo "# Core dependencies
snowflake-connector-python>=3.0.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Development dependencies
pytest>=7.0.0
pytest-mock>=3.10.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0

# Optional/AI dependencies (for future stories)
openai>=1.0.0
spacy>=3.7.0

# From PR #2/#3 (already included above)
# psycopg2-binary>=2.9" > requirements.txt

echo "=== Conflict resolution complete ==="
