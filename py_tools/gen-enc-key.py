
from cryptography.fernet import Fernet
import os


def generate_key():
# Generate a key
    key = Fernet.generate_key()
    return key

if __name__ == "__main__":
    key = generate_key()
    key_decoded = key.decode()
    print(key_decoded)
    