# Python virtualenv workflow

Recommended workflow after installing Python 3.12 in your WSL distro:

1. Create a project virtual environment in the project root:

```bash
python3.12 -m venv .venv
```

2. Activate the virtual environment:

```bash
# bash/zsh
. .venv/bin/activate

# fish
source .venv/bin/activate.fish
```

3. Upgrade pip and install dev requirements:

```bash
python -m pip install --upgrade pip
python -m pip install -r dev/requirements.txt
```

4. Manage project dependencies

- Add a `requirements.txt` or use `pyproject.toml` + `pip-tools`/`poetry` depending on project policy. For this repo we provide `dev/requirements.txt` for test-time utilities (e.g., `psycopg`).
- To freeze runtime dependencies: `pip freeze > requirements.txt` (only do this for apps; libraries should use a lockfile strategy).

5. Deactivate when done:

```bash
deactivate
```

Security note: Do not commit `.venv/` to source control; add it to `.gitignore` if not already excluded.
