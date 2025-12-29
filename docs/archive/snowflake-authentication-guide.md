# Snowflake Authentication Guide

This guide explains the different authentication methods available for connecting to Snowflake from the ETL scripts.

## Available Authentication Methods

### 1. Password Authentication (Default)

**When to use**: Local development, CI/CD pipelines, automated scripts

**Configuration**:
```bash
# .env file
SNOWFLAKE_ACCOUNT="your-account.snowflakecomputing.com"
SNOWFLAKE_USER="your-username"
SNOWFLAKE_PASSWORD="your-password"
# SNOWFLAKE_AUTHENTICATOR="snowflake"  # default, can be omitted
SNOWFLAKE_WAREHOUSE="your-warehouse"
SNOWFLAKE_DATABASE="your-database"
SNOWFLAKE_SCHEMA="your-schema"
```

**Pros**:
- Simple to configure
- Works in headless environments
- No user interaction required

**Cons**:
- Requires storing passwords
- Less secure than SSO

### 2. Browser SSO Authentication (authenticator='externalbrowser')

**When to use**: Developer workstations, interactive sessions

**Configuration**:
```bash
# .env file
SNOWFLAKE_ACCOUNT="your-account.snowflakecomputing.com"
SNOWFLAKE_USER="your-username"
SNOWFLAKE_AUTHENTICATOR="externalbrowser"  # enables browser SSO
# No password needed!
SNOWFLAKE_WAREHOUSE="your-warehouse"
SNOWFLAKE_DATABASE="your-database"
SNOWFLAKE_SCHEMA="your-schema"
```

**How it works**:
1. Application initiates connection with `authenticator='externalbrowser'`
2. Snowflake connector opens default web browser
3. User authenticates via Snowflake web interface
4. Authentication token is cached locally
5. Subsequent connections use cached token

**Pros**:
- More secure (no password storage)
- Supports multi-factor authentication
- Uses existing SSO infrastructure
- Tokens are cached for convenience

**Cons**:
- Requires browser access
- Not suitable for headless environments
- Initial setup requires user interaction

### 3. OAuth Authentication (Advanced)

**When to use**: Enterprise integrations, service accounts

**Configuration**:
```bash
# .env file
SNOWFLAKE_ACCOUNT="your-account.snowflakecomputing.com"
SNOWFLAKE_USER="your-username"
SNOWFLAKE_AUTHENTICATOR="oauth"
SNOWFLAKE_TOKEN="your-oauth-token"
SNOWFLAKE_WAREHOUSE="your-warehouse"
SNOWFLAKE_DATABASE="your-database"
SNOWFLAKE_SCHEMA="your-schema"
```

**Pros**:
- Token-based authentication
- Fine-grained access control
- Suitable for service-to-service communication

**Cons**:
- Complex setup
- Requires OAuth infrastructure

## Implementation Examples

### Python Code Example

```python
import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()

# Get configuration from environment
account = os.getenv("SNOWFLAKE_ACCOUNT")
user = os.getenv("SNOWFLAKE_USER")
authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake")
password = os.getenv("SNOWFLAKE_PASSWORD")

# Build connection parameters
conn_params = {
    "account": account,
    "user": user,
    "authenticator": authenticator,
}

# Add password only for password authentication
if authenticator == "snowflake" and password:
    conn_params["password"] = password

# Add optional parameters
for param in ["warehouse", "database", "schema", "role"]:
    value = os.getenv(f"SNOWFLAKE_{param.upper()}")
    if value:
        conn_params[param] = value

# Connect to Snowflake
try:
    conn = snowflake.connector.connect(**conn_params)
    print("Connected successfully!")
    
    # Test connection
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"Test query result: {result[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
```

### Testing Your Connection

Use the provided example script:

```bash
# Set up environment
cp .env.example .env
# Edit .env with your Snowflake credentials

# Test connection
python examples/snowflake_connection_example.py
```

## Troubleshooting

### Browser SSO Issues

**Problem**: Browser doesn't open automatically
**Solution**:
- Ensure you have a default browser set
- Check firewall settings
- Try running in GUI environment (not headless)

**Problem**: Authentication fails in browser
**Solution**:
- Verify SSO configuration in Snowflake
- Check user permissions
- Clear browser cache and cookies

### Password Authentication Issues

**Problem**: "Invalid username or password"
**Solution**:
- Verify password in .env file
- Check if account is locked
- Ensure user has necessary privileges

**Problem**: Connection timeout
**Solution**:
- Check network connectivity
- Verify firewall allows outbound connections
- Test with Snowflake web interface

## Security Best Practices

1. **Never commit .env files** to version control
2. **Use different credentials** for development/production
3. **Rotate passwords/tokens** regularly
4. **Monitor connection logs** for suspicious activity
5. **Use least privilege principle** for database access

## References

- [Snowflake Connector Python Documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [Snowflake Authentication Methods](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth)
- [Browser SSO Configuration](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use#browser-based-sso)
