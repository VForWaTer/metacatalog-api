#!/usr/bin/env python3
"""
CLI entrypoint for metacatalog-api administration tasks
"""

import sys
import argparse
from metacatalog_api.core import connect
from metacatalog_api.access_control import create_admin_token, validate_token, is_development_mode


def main():
    parser = argparse.ArgumentParser(
        description="Metacatalog API CLI for admin token management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m metacatalog_api.cli --create-admin-token
  python -m metacatalog_api.cli --validate-admin-token your-token-here
        """
    )
    
    parser.add_argument(
        '--create-admin-token',
        action='store_true',
        help='Create a new admin token'
    )
    
    parser.add_argument(
        '--validate-admin-token',
        type=str,
        help='Validate an admin token'
    )
    
    # Add server configuration options
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--environment', default='development', help='Environment')
    parser.add_argument('--admin-token', help='Admin token from environment')
    
    args = parser.parse_args()
    
    # Handle admin token creation
    if args.create_admin_token:
        try:
            with connect() as session:
                token = create_admin_token(session)
                print(f"\n🔑 Admin token created successfully!")
                print(f"📋 Token: {token}")
                print(f"⚠️  Store this token securely - it won't be shown again!\n")
                return 0
        except Exception as e:
            print(f"❌ Failed to create admin token: {e}")
            return 1
    
    # Handle admin token validation
    if args.validate_admin_token:
        try:
            with connect() as session:
                user_token = validate_token(session, args.validate_admin_token)
                if user_token:
                    user_info = f"{user_token.user.first_name} {user_token.user.last_name}" if user_token.user else "No user"
                    print(f"✅ Token is valid! User: {user_info}")
                    return 0
                else:
                    print(f"❌ Token is invalid!")
                    return 1
        except Exception as e:
            print(f"❌ Failed to validate token: {e}")
            return 1
    
    # Default: show help
    print("Metacatalog API Server")
    print(f"Environment: {args.environment}")
    print(f"Host: {args.host}:{args.port}")
    print()
    print("Available CLI options:")
    print("  --create-admin-token     Create a new admin token")
    print("  --validate-admin-token <token>  Validate an admin token")
    print("  --help                   Show full help")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 