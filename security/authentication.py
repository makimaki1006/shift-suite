# 認証・認可モジュール
import hashlib
import secrets
import time
from datetime import datetime, timedelta

class AuthenticationManager:
    """認証管理クラス"""
    
    def __init__(self):
        self.sessions = {}
        self.session_timeout = 3600  # 1時間
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """パスワードのハッシュ化"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.pbkdf2_hmac('sha256', 
                                   password.encode(), 
                                   salt.encode(), 
                                   100000)
        return hashed.hex(), salt
    
    def create_session(self, user_id: str) -> str:
        """セッション作成"""
        session_id = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(seconds=self.session_timeout)
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "expires": expiry.isoformat()
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """セッション検証"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        expiry = datetime.fromisoformat(session["expires"])
        
        if datetime.now() > expiry:
            del self.sessions[session_id]
            return False
        
        return True

# 認証インスタンス
auth_manager = AuthenticationManager()
