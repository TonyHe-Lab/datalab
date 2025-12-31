feat(epic1): add WSL/local dev docs and verification scripts — clean branch

Changes introduced
- Adds Epic1 documentation and developer verification scripts:
  - `docs/` WSL/local dev guides and story documentation
  - `dev/verify_db_schema.py`
  - `dev/verify_postgres_connection.py`
  - `dev/verify_env.sh` (made executable)
  - `requirements.txt` updates

Why this branch exists
- The original branch `feat/epic1-complete-20251227-1810` accidentally included virtual environment contents and compiled artifacts (venv, site-packages, `__pycache__`, `*.pyc`). To avoid polluting `main`, this PR is created from a clean branch `feat/epic1-clean-20251228` based on `main` and contains only the intended files.

Cleanup already performed
- Updated `.gitignore` to include `venv/`, `__pycache__/`, `*.py[cod]`, `site-packages/`.
- Removed tracked `dev/__pycache__/*.pyc` from original feature branch and pushed.
- Created `feat/epic1-clean-20251228` from `main`, checked out only required files, removed accidental tracked `venv/` and other build artifacts from the index (`git rm -r --cached venv`) and pushed.

Review checklist
- Verify each file under `docs/` is strictly Epic1-related (no unrelated files).
- Inspect `dev/verify_*` scripts for correctness and shebang/executable bit.
- Validate `requirements.txt` changes align with project policy (dev vs prod deps).
- Confirm no sensitive data (keys, secrets) are present.

Testing guidance
- Run focused tests locally or in CI before merging:
  ```bash
  git checkout feat/epic1-clean-20251228
  pytest tests/ai/test_pii_detector.py -q
  # or run full test-suite
  pytest -q
  ```
- Note: previous runs showed `pytest tests/ai/test_pii_detector.py` had exit code 5 — investigate logs if failures appear.

Suggested merge & post-merge steps
- Create PR from `feat/epic1-clean-20251228` into `main` and run CI.
- After merge, delete the old dirty branch to avoid confusion:
  ```bash
  git push origin --delete feat/epic1-complete-20251227-1810
  git branch -d feat/epic1-complete-20251227-1810
  ```

Suggested reviewers and labels
- Reviewers: repo maintainers and docs owner (replace with team handles)
- Labels: docs, infra, chore

If you want me to create the PR automatically, confirm and ensure `gh` CLI is available and authenticated on this machine, or provide a temporary token.
