import base64
import hashlib
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from mnemonic import Mnemonic
from modules.helpers import to_b64, from_b64
from modules.config import get_app_secret

class CredentialError(ValueError):
    pass

def generate_password_hash(password, salt=None):
    if salt is None:
        salt = os.urandom(32)  # Remember this
    key = hashlib.pbkdf2_hmac('sha256', (get_app_secret() + password).encode('utf-8'), salt, 1_000_000)
    return key + b'.' + salt


def check_password_hash(password, hashed):
    return hashed == generate_password_hash(password, salt=hashed.split(b'.')[-1])


class Secrets:
    def __init__(self, mnemonic=None, passphrase=None, has_passphrase=False, has_password=False, language='english'):
        self.mnemonic = mnemonic
        self.language = language
        self.passphrase = passphrase
        self.has_passphrase = has_passphrase
        self.has_password = has_password


class CredentialManager:
    secrets_file = Path("data/secrets.dat")

    @classmethod
    def derive_password(cls, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        if isinstance(password, str):
            password = password.encode('utf8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key, salt

    @classmethod
    def write_secrets(cls, mnemonic, passphrase=None, has_passphrase=False,
                      language='english', decryption_key=None, decryption_password=None):
        if decryption_key is None:
            decryption_key = Fernet.generate_key()

        payload = {
            "mnemonic": mnemonic,
            "language": language,
            "has_passphrase": has_passphrase
        }

        if passphrase:
            payload["has_passphrase"] = True
            payload["passphrase"] = passphrase

        raw = f"{to_b64(Fernet(decryption_key).encrypt(json.dumps(payload).encode()))}.{to_b64(decryption_key)}"

        if decryption_password:
            key, salt = cls.derive_password(decryption_password)
            raw = f"{to_b64(Fernet(key).encrypt(raw.encode()))}|{to_b64(salt)}"

        cls.secrets_file.write_text(
            raw
        )

    @classmethod
    def load_secrets(cls, decryption_password=None):
        if not cls.secrets_file.exists():
            return Secrets()

        secrets = cls.secrets_file.read_text()
        if decryption_password:
            secrets, salt = secrets.split('|')
            key, _ = cls.derive_password(decryption_password, from_b64(salt))
            secrets = Fernet(key).decrypt(from_b64(secrets)).decode()
        elif '|' in secrets:
            raise PermissionError("Secrets are password protected")

        raw_data, decryption_key = secrets.split('.')
        payload = Fernet(from_b64(decryption_key)).decrypt(from_b64(raw_data)).decode()
        data = json.loads(payload)
        return Secrets(**data)

    @classmethod
    def get_seed(cls, mnemonic=None, passphrase=None, decryption_password=None):
        try:
            secrets = cls.load_secrets(decryption_password=decryption_password)
        except PermissionError:
            raise ValueError("No decryption key provided")

        mnemonic = mnemonic or secrets.mnemonic
        passphrase = passphrase if passphrase is not None else secrets.passphrase

        if mnemonic is None:
            raise ValueError("No mnemonic provided")
        if secrets.has_passphrase and passphrase is None:
            raise ValueError("No passphrase provided")

        mnemo = Mnemonic(secrets.language)
        return mnemo.to_seed(secrets.mnemonic)

    @classmethod
    def get_required_fields(cls):
        secrets = cls.load_secrets()

        req = []
        if not secrets.mnemonic:
            req.append('mnemonic')
        if secrets.has_passphrase and not secrets.passphrase:
            req.append('passphrase')
        return req
