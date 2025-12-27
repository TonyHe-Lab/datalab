#!/usr/bin/env python3
"""
Snowflake Connection Example
===========================

This example demonstrates different authentication methods for Snowflake connection,
including browser SSO authentication (authenticator='externalbrowser').

Usage:
  python snowflake_connection_example.py

Environment variables required:
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and either:
    - SNOWFLAKE_PASSWORD (for password auth)
    - SNOWFLAKE_AUTHENTICATOR='externalbrowser' (for browser SSO)
    - SNOWFLAKE_TOKEN (for OAuth)
"""

import os
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class AuthMethod(Enum):
    """Snowflake authentication methods"""

    PASSWORD = "password"
    BROWSER_SSO = "browser_sso"
    OAUTH = "oauth"


@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration"""

    account: str
    user: str
    password: Optional[str] = None
    authenticator: str = "snowflake"  # default
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        """Create config from environment variables"""
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake")
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        database = os.getenv("SNOWFLAKE_DATABASE")
        schema = os.getenv("SNOWFLAKE_SCHEMA")
        role = os.getenv("SNOWFLAKE_ROLE")

        if not account or not user:
            raise ValueError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER are required")

        return cls(
            account=account,
            user=user,
            password=password,
            authenticator=authenticator,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role,
        )

    def get_auth_method(self) -> AuthMethod:
        """Determine authentication method from configuration"""
        if self.authenticator == "externalbrowser":
            return AuthMethod.BROWSER_SSO
        elif self.authenticator == "oauth":
            return AuthMethod.OAUTH
        else:
            return AuthMethod.PASSWORD

    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for snowflake-connector-python"""
        params = {
            "account": self.account,
            "user": self.user,
            "authenticator": self.authenticator,
        }

        # Add password if using password auth
        if self.authenticator == "snowflake" and self.password:
            params["password"] = self.password

        # Add optional parameters
        if self.warehouse:
            params["warehouse"] = self.warehouse
        if self.database:
            params["database"] = self.database
        if self.schema:
            params["schema"] = self.schema
        if self.role:
            params["role"] = self.role

        return params


def test_snowflake_connection():
    """Test Snowflake connection with current configuration"""
    try:
        import snowflake.connector
    except ImportError:
        print("ERROR: snowflake-connector-python not installed")
        print("Install with: pip install snowflake-connector-python")
        return False

    try:
        config = SnowflakeConfig.from_env()
        auth_method = config.get_auth_method()

        print(f"Snowflake Configuration:")
        print(f"  Account: {config.account}")
        print(f"  User: {config.user}")
        print(f"  Authentication: {auth_method.value}")

        if auth_method == AuthMethod.BROWSER_SSO:
            print("\nNOTE: Browser SSO authentication selected")
            print("A browser window will open for authentication...")
        elif auth_method == AuthMethod.PASSWORD and not config.password:
            print("ERROR: Password authentication requires SNOWFLAKE_PASSWORD")
            return False

        # Create connection
        print("\nConnecting to Snowflake...")
        conn = snowflake.connector.connect(**config.get_connection_params())

        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]

        print(f"✓ Connected successfully!")
        print(f"  Snowflake version: {version}")

        # Show current context
        cursor.execute(
            "SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        )
        warehouse, database, schema = cursor.fetchone()
        print(f"  Warehouse: {warehouse or 'Not set'}")
        print(f"  Database: {database or 'Not set'}")
        print(f"  Schema: {schema or 'Not set'}")

        cursor.close()
        conn.close()
        return True

    except snowflake.connector.errors.Error as e:
        print(f"ERROR: Snowflake connection failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Main function"""
    print("Snowflake Connection Example")
    print("=" * 30)

    # Check environment
    required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set these variables in your .env file:")
        print("  SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com")
        print("  SNOWFLAKE_USER=your-username")
        print("\nFor password authentication add:")
        print("  SNOWFLAKE_PASSWORD=your-password")
        print("\nFor browser SSO authentication add:")
        print("  SNOWFLAKE_AUTHENTICATOR=externalbrowser")
        return 1

    # Test connection
    success = test_snowflake_connection()

    if success:
        print("\n✓ Connection test passed!")
        return 0
    else:
        print("\n✗ Connection test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
