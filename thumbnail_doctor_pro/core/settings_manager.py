"""
Settings Manager for Thumbnail Doctor Pro Ultimate
Handles application settings with encryption support
"""
import json
from typing import Any, Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib

class SettingsManager:
    _instance = None
    
    def __init__(self, db_manager=None):
        from core.database import DatabaseManager
        self.db = db_manager or DatabaseManager.get_instance()
        self._cipher = None
        self._init_settings()
    
    @classmethod
    def get_instance(cls, db_manager=None) -> 'SettingsManager':
        if cls._instance is None:
            cls._instance = cls(db_manager)
        return cls._instance
    
    def _get_cipher_key(self) -> bytes:
        machine_id = str(os.getpid()) + str(os.uname().nodename if hasattr(os, 'uname') else "default")
        key_material = hashlib.sha256(machine_id.encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'thumbnail_doctor_salt_v1',
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(key_material))
    
    def _get_cipher(self) -> Fernet:
        if self._cipher is None:
            self._cipher = Fernet(self._get_cipher_key())
        return self._cipher
    
    def encrypt_value(self, value: str) -> str:
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        cipher = self._get_cipher()
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    
    def _init_settings(self):
        defaults = {
            'theme': 'dark',
            'gemini_model': 'auto',
            'auto_capture_hotkey': 'Ctrl+Shift+A',
            'export_format': 'pdf',
            'enable_notifications': 'true',
            'language': 'en'
        }
        
        for key, value in defaults.items():
            if self.db.get_setting(key) is None:
                self.db.save_setting(key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        value = self.db.get_setting(key)
        if value is None:
            return default
        
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def set(self, key: str, value: Any):
        if isinstance(value, (bool, dict, list)):
            str_value = json.dumps(value)
        else:
            str_value = str(value)
        self.db.save_setting(key, str_value)
    
    def save_api_key(self, service: str, api_key: str):
        encrypted = self.encrypt_value(api_key)
        self.db.save_api_key(service, encrypted)
    
    def get_api_key(self, service: str) -> Optional[str]:
        encrypted = self.db.get_api_key(service)
        if encrypted:
            try:
                return self.decrypt_value(encrypted)
            except Exception:
                return None
        return None
    
    def get_all_settings(self) -> Dict[str, Any]:
        keys = ['theme', 'gemini_model', 'auto_capture_hotkey', 'export_format',
                'enable_notifications', 'language']
        return {key: self.get(key) for key in keys}
    
    def reset_to_defaults(self):
        defaults = {
            'theme': 'dark',
            'gemini_model': 'auto',
            'auto_capture_hotkey': 'Ctrl+Shift+A',
            'export_format': 'pdf',
            'enable_notifications': 'true',
            'language': 'en'
        }
        for key, value in defaults.items():
            self.set(key, value)
