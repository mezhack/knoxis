from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        data = response.data
        if isinstance(data, dict) and "detail" not in data:
            response.data = {
                "type": "validation_error",
                "title": "Dados inválidos",
                "status": response.status_code,
                "fields": data,
            }
        elif isinstance(data, dict) and "detail" in data:
            response.data = {
                "type": "error",
                "title": str(data["detail"]),
                "status": response.status_code,
                "detail": str(data["detail"]),
            }
    return response
