# Windows Host Postgres Configuration

This document provides step-by-step instructions for configuring PostgreSQL on a Windows host to accept connections from WSL and other network clients.

## Prerequisites

- PostgreSQL installed on Windows (version 12 or later recommended)
- Administrative access to modify configuration files and firewall rules
- WSL 2 installed and configured (see [WSL Setup](wsl-setup.md))

## 1. PostgreSQL Configuration Files

### 1.1 Locate Configuration Files

PostgreSQL configuration files are typically located in:
- `C:\Program Files\PostgreSQL\<version>\data\` (default installation)
- Or check the data directory in `pgAdmin` or via `SHOW data_directory;` in `psql`

Key files:
- `postgresql.conf` - Main configuration file
- `pg_hba.conf` - Host-based authentication file

### 1.2 Configure `postgresql.conf`

Edit `postgresql.conf` to allow network connections:

```ini
# Listen on all interfaces (or specific IPs)
listen_addresses = '*'  # or 'localhost,192.168.1.100'

# Port configuration (default is 5432)
port = 5432

# Connection settings
max_connections = 100
```

**Important**: After changing `postgresql.conf`, restart the PostgreSQL service:
```powershell
# Restart PostgreSQL service
Restart-Service postgresql-x64-<version>
# Or using Services GUI
```

### 1.3 Configure `pg_hba.conf`

Edit `pg_hba.conf` to allow connections from WSL and other authorized hosts:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Allow local connections
local   all             all                                     peer

# Allow connections from WSL subnet (typical WSL2 subnet)
host    all             all             172.22.0.0/16           scram-sha-256

# Allow connections from specific developer IPs
host    all             all             203.0.113.45/32         md5

# Allow connections from localhost (IPv4 and IPv6)
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

**Notes**:
- WSL2 typically uses IPs in the `172.22.0.0/16` range, but this may vary
- Use `scram-sha-256` for secure password authentication (PostgreSQL 10+)
- For older PostgreSQL versions, use `md5`

## 2. Windows Firewall Configuration

### 2.1 Add Firewall Rule via PowerShell

```powershell
# Add inbound rule to allow PostgreSQL on port 5432
New-NetFirewallRule `
    -DisplayName "PostgreSQL Server" `
    -Direction Inbound `
    -LocalPort 5432 `
    -Protocol TCP `
    -Action Allow `
    -Description "Allow PostgreSQL database connections"

# Verify the rule was created
Get-NetFirewallRule -DisplayName "PostgreSQL Server"
```

### 2.2 Alternative: Using Windows Defender Firewall GUI

1. Open "Windows Defender Firewall with Advanced Security"
2. Click "Inbound Rules" → "New Rule..."
3. Select "Port" → "TCP" → "Specific local ports: 5432"
4. Select "Allow the connection"
5. Select when the rule applies (Domain, Private, Public)
6. Name: "PostgreSQL Server"

### 2.3 Rollback/Removal

```powershell
# Remove the firewall rule
Remove-NetFirewallRule -DisplayName "PostgreSQL Server"

# Or disable it temporarily
Disable-NetFirewallRule -DisplayName "PostgreSQL Server"
```

## 3. Security Best Practices

### 3.1 Credential Handling

**Never commit credentials to version control!**

Use `.env` file (added to `.gitignore`):
```bash
# .env file
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://postgres:password@localhost:5432/datalab
```

### 3.2 TLS/SSL Configuration (Recommended for Production)

In `postgresql.conf`:
```ini
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'root.crt'
```

### 3.3 Network Security

- Use specific IP ranges instead of `*` in `listen_addresses` when possible
- Consider using VPN for remote access
- Regularly update PostgreSQL and Windows security patches

## 4. Verification

### 4.1 From Windows (Local Verification)

```powershell
# Test local connection
psql -h localhost -p 5432 -U postgres -c "SELECT version();"
```

### 4.2 From WSL (Cross-System Verification)

```bash
# Set environment variables
export POSTGRES_HOST=host.docker.internal  # or Windows host IP
export POSTGRES_PORT=5432

# Run verification script
./dev/verify_env.sh

# Or directly test with psql
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U postgres -c "SELECT 1;"
```

### 4.3 Using Project Verification Script

The project includes `dev/verify_postgres_connection.py` for automated verification:

```bash
# Install dependencies
pip install psycopg2-binary

# Run verification
python dev/verify_postgres_connection.py --database-url "postgresql://user:pass@host:5432/db"
```

## 5. Troubleshooting

### 5.1 Common Issues

1. **Connection refused**: Check if PostgreSQL service is running
2. **Authentication failed**: Verify `pg_hba.conf` entries and credentials
3. **Firewall blocking**: Temporarily disable firewall to test
4. **WSL network issues**: Use `host.docker.internal` or Windows host IP

### 5.2 Diagnostic Commands

```powershell
# Check PostgreSQL service status
Get-Service postgresql*

# Check listening ports
netstat -an | findstr :5432

# Test connectivity from Windows
Test-NetConnection -ComputerName localhost -Port 5432
```

## 6. References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Story 1.1: WSL Python & Node Setup](../stories/1.1.WSL-Python-Node-Setup.md)
- [Story 1.2: Windows Host Postgres Configuration](../stories/1.2.Windows-Host-Postgres-Configuration.md)
- [Project Security Guidelines](../../docs/prd_shards/12-security.md)

## 7. Support

For corporate-managed machines with restricted firewall policies, contact your IT department for assistance with firewall rule exceptions.
