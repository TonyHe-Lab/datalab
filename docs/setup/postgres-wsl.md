# Postgres Reachability from WSL

This document explains how to verify TCP reachability from WSL to a Postgres server running on the Windows host or elsewhere.

1. On Windows host (Story 1.2 covers full host-side setup):
- Ensure Postgres is listening on 0.0.0.0 or the host IP and firewall allows incoming connections on the Postgres port (default 5432).
- Edit `postgresql.conf` to set `listen_addresses = '*'` and adjust `pg_hba.conf` to allow the WSL user's IP/range.

2. From WSL, a simple tcp check:

```sh
# using netcat
nc -zv <POSTGRES_HOST> <POSTGRES_PORT>

# or using python
python - <<PY
import socket
s=socket.socket(); s.settimeout(3)
try:
  s.connect(("<POSTGRES_HOST>", <POSTGRES_PORT>))
  print('ok')
except Exception as e:
  print('failed', e)
finally:
  s.close()
PY
```

3. Notes:
- WSL2 runs in a lightweight VM, so connecting to services on Windows host usually requires using the host IP (e.g., `host.docker.internal` or the Windows host IP). Story 1.2 will provide recommended host-side config and troubleshooting steps.

4. Optional: Authentication check from WSL

If you want to verify that credentials also work (not just TCP), you can enable an auth check using the project's verification script.

Example (local):

```bash
export POSTGRES_HOST=host.docker.internal
export POSTGRES_PORT=5432
export POSTGRES_USER=devuser
export POSTGRES_PASSWORD=devpass
export POSTGRES_DB=mydb
export VERIFY_PG_AUTH=1
python -m pip install -r dev/requirements.txt
./dev/verify_env.sh
```

In CI, set `VERIFY_PG_AUTH=1` and add the POSTGRES_* values to repository Secrets. Be careful not to commit credentials.
