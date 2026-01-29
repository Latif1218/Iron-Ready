from pwdlib import PasswordHash
from ..schemas import user_schema


password_hash = PasswordHash.recommended()

def hash_password(password: str):
    return password_hash.hash(password)   




def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)