#!/usr/bin/env python
from werkzeug.security import generate_password_hash
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_password_hash.py <password>")
        sys.exit(1)

    password = sys.argv[1]
    password_hash = generate_password_hash(password)
    print(f"Password hash: {password_hash}")
    print("\nAdd this to your .env file as:")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")


if __name__ == "__main__":
    main()