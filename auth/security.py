import re
import bcrypt

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against its hashed version.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def is_valid_email(email: str) -> bool:
    """
    Simple email validation using regular expressions.
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def is_valid_username(username: str) -> bool:
    """
    Validates username (letters, numbers, underscores, between 3-20 chars).
    """
    pattern = r'^[\w]{3,20}$'
    return bool(re.match(pattern, username))
