import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORTS_DIR = os.path.join(ROOT_DIR, "exports")
PRODUCTION_DIR = os.path.join(ROOT_DIR, "content", "production")

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(PRODUCTION_DIR, exist_ok=True)
