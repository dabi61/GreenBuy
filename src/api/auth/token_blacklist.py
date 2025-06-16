from typing import Set
from datetime import datetime, timezone, timedelta
from jose import jwt
from api.auth.constants import SECRET_KEY, ALGOGRYTHYM
import threading

class TokenBlacklist:
    """
    Quản lý blacklist token để xử lý logout
    Trong production nên dùng Redis hoặc database
    """
    def __init__(self):
        self._blacklisted_tokens: Set[str] = set()
        self._token_expiry: dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def add_token(self, token: str) -> None:
        """Thêm token vào blacklist"""
        with self._lock:
            try:
                # Decode để lấy expiry time
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGOGRYTHYM])
                exp_timestamp = payload.get("exp")
                
                if exp_timestamp:
                    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    self._token_expiry[token] = exp_datetime
                
                self._blacklisted_tokens.add(token)
            except:
                # Nếu token invalid thì vẫn add vào blacklist
                self._blacklisted_tokens.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """Kiểm tra token có trong blacklist không"""
        with self._lock:
            return token in self._blacklisted_tokens
    
    def cleanup_expired_tokens(self) -> None:
        """Dọn dẹp các token đã expired khỏi blacklist"""
        with self._lock:
            current_time = datetime.now(timezone.utc)
            expired_tokens = [
                token for token, exp_time in self._token_expiry.items()
                if exp_time < current_time
            ]
            
            for token in expired_tokens:
                self._blacklisted_tokens.discard(token)
                del self._token_expiry[token]
    
    def get_blacklist_size(self) -> int:
        """Lấy số lượng token trong blacklist"""
        with self._lock:
            return len(self._blacklisted_tokens)

# Singleton instance
token_blacklist = TokenBlacklist()

def add_token_to_blacklist(token: str) -> None:
    """Utility function để add token vào blacklist"""
    token_blacklist.add_token(token)

def is_token_blacklisted(token: str) -> bool:
    """Utility function để kiểm tra token có blacklisted không"""
    return token_blacklist.is_blacklisted(token)

def cleanup_blacklist() -> None:
    """Utility function để cleanup blacklist"""
    token_blacklist.cleanup_expired_tokens() 