import uuid

import structlog

logger = structlog.get_logger()


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )

        if request.user and hasattr(request.user, "id"):
            structlog.contextvars.bind_contextvars(user_id=request.user.id)

        response = self.get_response(request)
        return response
