import time
import datetime
import logging
from django.http import JsonResponse


logger = logging.getLogger('request_logger')

class PerformanceMiddleware:
    # This middleware logs request info on every request
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record start time
        start_time = time.perf_counter()

        # Pass to the rest of the stack
        response = self.get_response(request)

        # Calculate latency and get current timestamp
        duration = time.perf_counter() - start_time
        finished_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(
            f"TIME: {finished_at} | "
            f"METHOD: {request.method} | "
            f"URL: {request.path} | "
            f"STATUS: {response.status_code} | "
            f"LATENCY: {duration:.4f}s"
        )

        return response




class APIVersionMiddleware:

    # This middleware enforces versioning on endpoints
    # checks for X-API-Version header
    
    REQUIRED_VERSION = "1"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Only profile-related endpoints
        if path.startswith("/api/profiles"):
            version = request.headers.get("X-API-Version")

            if version != self.REQUIRED_VERSION:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "API version header required"
                    },
                    status=400
                )

        return self.get_response(request)