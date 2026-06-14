#!/usr/bin/env python
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_password():
    """Test password hashing and validation"""

    print("=" * 50)
    print("Password Hash Testing")
    print("=" * 50)

    # Test 1: Generate hash for admin123
    password = "admin123"
    generated_hash = generate_password_hash(password)
    print(f"\n1. Generated hash for '{password}':")
    print(f"   {generated_hash}")

    # Test 2: Verify the hash
    is_valid = check_password_hash(generated_hash, password)
    print(f"\n2. Hash validation test:")
    print(f"   Password '{password}' matches its hash: {is_valid}")

    # Test 3: Test wrong password
    is_valid_wrong = check_password_hash(generated_hash, "wrongpassword")
    print(f"   Wrong password 'wrongpassword' matches hash: {is_valid_wrong}")

    # Test 4: Load hash from environment
    env_hash = os.getenv('ADMIN_PASSWORD_HASH')
    if env_hash:
        print(f"\n3. Testing hash from .env file:")
        print(f"   Hash: {env_hash[:50]}...")
        is_valid_env = check_password_hash(env_hash, password)
        print(f"   Password '{password}' matches env hash: {is_valid_env}")

        if not is_valid_env:
            print(f"\n   ⚠️  WARNING: The hash in .env doesn't match '{password}'!")
            print(f"   Please update your .env file with this hash:")
            print(f"   ADMIN_PASSWORD_HASH={generated_hash}")
    else:
        print(f"\n3. No ADMIN_PASSWORD_HASH found in .env file")
        print(f"   Add this to your .env file:")
        print(f"   ADMIN_PASSWORD_HASH={generated_hash}")

    # Test 5: Check admin username
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    print(f"\n4. Admin username from .env: {admin_user}")

    print("\n" + "=" * 50)
    print("Recommendations:")
    print("=" * 50)

    if not env_hash or not is_valid_env:
        print(f"✓ Update your .env file with:")
        print(f"  ADMIN_USERNAME=admin")
        print(f"  ADMIN_PASSWORD_HASH={generated_hash}")
        print(f"  ADMIN_PASSWORD=admin123  # Optional fallback")
    else:
        print("✓ Your password hash is correct!")

    print("\nTo test login, run:")
    print("  docker-compose logs -f web")
    print("  # Then try logging in with username 'admin' and password 'admin123'")


if __name__ == "__main__":
    test_password()