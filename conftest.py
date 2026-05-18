import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_magnews.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-prod")
os.environ.setdefault("UPLOAD_ROOT", "./test_uploads")

sys.path.insert(0, str(Path(__file__).parent))
