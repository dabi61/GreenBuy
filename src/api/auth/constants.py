"""
Authentication constants
"""
import os

#openssl rand --hex 32
#3f919b7c30efa3a7468bb868190f54376a68b8eb1a014647d50af4cd077b7c76

SECRET_KEY = os.getenv("SECRET_KEY", "3f919b7c30efa3a7468bb868190f54376a68b8eb1a014647d50af4cd077b7c76")
ALGOGRYTHYM = "HS256"
EXPIRE_TIME = 30  # minutes 