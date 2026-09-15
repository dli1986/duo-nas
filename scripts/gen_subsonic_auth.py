import hashlib
import secrets

password = "duo-nas-local-2026"
salt = secrets.token_hex(6)
token = hashlib.md5((password + salt).encode()).hexdigest()
print(f"salt={salt}")
print(f"token={token}")
