import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".config"))
load_dotenv(ROOT.parents[1] / ".env")
DATA_DIR = Path(os.getenv("VISION_DATA_DIR", str(ROOT / "data"))).resolve()
MODEL_PATH = Path(os.getenv("VISION_MODEL_PATH", str(ROOT / "models" / "yolo11n.pt"))).resolve()
API_KEY = os.getenv("VISION_API_KEY", "")
PERSON_CLASSES = [s.strip() for s in os.getenv("VISION_PERSON_CLASSES", "person").split(",")]
SEAT_CLASSES = [s.strip() for s in os.getenv("VISION_SEAT_CLASSES", "tv").split(",")]
SEAT_SEMANTICS = os.getenv("VISION_SEAT_SEMANTICS", "monitors")
MAX_BYTES = 250 * 1024 * 1024
MAX_SECONDS = 600
SAMPLE_FPS = 2
