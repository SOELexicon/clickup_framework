"""Extract ClickUp session token from Chrome browser."""

import sys
from clickup_framework import get_context_manager
from clickup_framework.utils.chrome_session import (
    get_clickup_session_token,
    extract_clickup_session_token,
    extract_from_network_request,
)


def extract_session_token_command(args):
    """Extract and optionally save ClickUp session token from Chrome."""
    context = get_context_manager()
    
    if args.manual:
        # Show manual extraction instructions
        instructions = extract_from_network_request()
        print(instructions)
        return
    
    # Try to extract from Chrome
    profile = args.profile or "Default"
    print(f"Attempting to extract session token from Chrome profile: {profile}...")
    
    try:
        session_data = extract_clickup_session_token(profile)
        
        if not session_data or 'session_token' not in session_data:
            print("\n❌ Could not automatically extract session token from Chrome.", file=sys.stderr)
            print("\nThis may be because:", file=sys.stderr)
            print("  - Chrome is currently running (close it first)", file=sys.stderr)
            print("  - Cookies are encrypted (Windows credential protection)", file=sys.stderr)
            print("  - Different Chrome profile is in use", file=sys.stderr)
            print("\nTry manual extraction:", file=sys.stderr)
            print("  cum extract_session_token --manual", file=sys.stderr)
            print("\nOr set it directly:", file=sys.stderr)
            print("  cum set_current session_token <token>", file=sys.stderr)
            sys.exit(1)
        
        session_token = session_data.get('session_token')
        
        if not session_token:
            print("\n❌ Session token not found in Chrome cookies.", file=sys.stderr)
            print("\nTry manual extraction:", file=sys.stderr)
            print("  cum extract_session_token --manual", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ {error_msg}", file=sys.stderr)
        
        # If it's a known issue, provide helpful guidance
        if "Chrome is currently running" in error_msg or "encrypted" in error_msg.lower():
            print("\n💡 Solution: Use manual extraction", file=sys.stderr)
            print("  cum extract_session_token --manual", file=sys.stderr)
        else:
            print("\nTry manual extraction:", file=sys.stderr)
            print("  cum extract_session_token --manual", file=sys.stderr)
        
        sys.exit(1)
    
    # Show token (masked)
    masked_token = f"{session_token[:20]}...{session_token[-10:]}" if len(session_token) > 30 else "********"
    print(f"\n✓ Found session token: {masked_token}")
    
    # Save if requested
    if args.save:
        try:
            context.set_session_token(session_token)
            print("✓ Session token saved to context")
        except Exception as e:
            print(f"\n❌ Error saving session token: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("\nTo save this token, run:")
        print(f"  cum set_current session_token {session_token}")
        print("\nOr use --save flag:")
        print("  cum extract_session_token --save")


def register_command(subparsers, add_common_args=None):
    """Register the extract_session_token command with argparse."""
    parser = subparsers.add_parser(
        'extract_session_token',
        aliases=['extract-token', 'get-session'],
        help='Extract ClickUp session token from Chrome browser',
        description='Extract ClickUp session token from Chrome cookies for use with v1 API endpoints'
    )
    parser.add_argument(
        '--profile',
        default='Default',
        help='Chrome profile to extract from (default: Default)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Automatically save the extracted token to context'
    )
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Show manual extraction instructions'
    )
    parser.set_defaults(func=extract_session_token_command)

