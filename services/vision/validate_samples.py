"""Local HTTP smoke check on the supplied videos; no ground-truth accuracy claim."""
import json
import argparse
import time
import uuid
from pathlib import Path
import httpx
from app import settings

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--output", default="docs/vision-validation.json")
args = parser.parse_args()
videos = json.loads((root / "docs/referencias/videos-inventario.json").read_text(encoding="utf-8"))
records = []
with httpx.Client(base_url="http://127.0.0.1:8002", headers={"X-Vision-Key": settings.API_KEY},
                  timeout=120, trust_env=False) as client:
    for video in videos:
        path = Path(video["path"])
        job_id = str(uuid.uuid4())
        with path.open("rb") as stream:
            response = client.post("/v1/jobs", data={"job_id": job_id, "confidence": ".5"},
                                   files={"video": (path.name, stream, "video/mp4")})
        response.raise_for_status()
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            response = client.get(f"/v1/jobs/{job_id}")
            response.raise_for_status()
            job = response.json()
            if job["status"] in ("completed", "failed", "cancelled"):
                break
            time.sleep(2)
        if job["status"] != "completed":
            raise RuntimeError(f'{path.name}: {job["status"]} {job["error"]}')
        result = job["result"]
        record = {"file": path.name, "job_id": job_id, "status": job["status"], **result}
        records.append(record)
        preview = client.get(f"/v1/jobs/{job_id}/preview")
        preview.raise_for_status()
        output = root / "tmp/vision-validation"
        output.mkdir(parents=True, exist_ok=True)
        (output / f"{path.stem}.jpg").write_bytes(preview.content)
        print(json.dumps({k: record[k] for k in ("file", "status", "people_max", "seats_max", "sampled_frames", "processing_seconds")}), flush=True)
(root / args.output).write_text(
    json.dumps({"note": "Baseline detections; no annotated ground truth; accuracy not validated.", "videos": records}, indent=2),
    encoding="utf-8")
