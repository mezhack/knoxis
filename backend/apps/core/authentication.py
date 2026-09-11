from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    # DRF's SessionAuthentication.authenticate_header() returns None on purpose,
    # to stop browsers popping a basic-auth dialog when a session check fails.
    # The side effect: with no auth header to send back, APIView.handle_exception
    # downgrades every unauthenticated request from 401 to 403, for every view
    # that relies on the default IsAuthenticated permission. A JSON API has no
    # dialog to avoid, so it can return a real header and keep the real 401.
    def authenticate_header(self, request):
        return "Session"
