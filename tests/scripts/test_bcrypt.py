"""Test bcrypt password hashing and verification."""
from passlib.context import CryptContext

# Configure password context (same as in the app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test password
test_password = "Welcome123!"

# Hash the password
hashed = pwd_context.hash(test_password)
print(f"Generated hash: {hashed}")

# Verify the password
is_valid = pwd_context.verify(test_password, hashed)
print(f"Verification result: {is_valid}")

# Now test with the actual hash from the database (from logs)
# User's hash: $2b$12$B5rugGt7SJ87AFNwCYrp9O9hXfcY82Cr8w7Q89qireleNFo4CgKwm
actual_hash = "$2b$12$B5rugGt7SJ87AFNwCYrp9O9hXfcY82Cr8w7Q89qireleNFo4CgKwm"
print(f"\nTesting against actual hash from database:")
print(f"Hash: {actual_hash}")

try:
    is_valid_actual = pwd_context.verify(test_password, actual_hash)
    print(f"Verification result: {is_valid_actual}")
except Exception as e:
    print(f"Error during verification: {e}")
    import traceback
    traceback.print_exc()
