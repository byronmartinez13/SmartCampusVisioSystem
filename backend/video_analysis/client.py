import httpx
from django.conf import settings


class VisionClient:
    """Server-side adapter; service credentials never reach the browser."""
    def __init__(self):
        self.http = httpx.Client(base_url=settings.VISION_SERVICE_URL,
                                 headers={"X-Vision-Key": settings.VISION_API_KEY},
                                 timeout=httpx.Timeout(120, connect=5), trust_env=False)

    def close(self):
        self.http.close()

    def frame(self, content, confidence):
        response = self.http.post('/v1/frame', data={'confidence': str(confidence)},
                                  files={'image': ('frame.jpg', content, 'image/jpeg')}, timeout=120)
        response.raise_for_status()
        return response.json()

    def submit(self, job):
        with job.video.open("rb") as video:
            response = self.http.post("/v1/jobs", data={"job_id": str(job.remote_id),
                                      "confidence": str(job.confidence)},
                                      files={"video": (job.original_name, video, "application/octet-stream")})
        response.raise_for_status()

    def status(self, job):
        response = self.http.get(f"/v1/jobs/{job.remote_id}")
        response.raise_for_status()
        return response.json()

    def cancel(self, job):
        response = self.http.post(f"/v1/jobs/{job.remote_id}/cancel")
        if response.status_code != 404:
            response.raise_for_status()

    def preview(self, job):
        response = self.http.get(f"/v1/jobs/{job.remote_id}/preview", timeout=10)
        response.raise_for_status()
        return response.content
