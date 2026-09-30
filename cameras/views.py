from functools import wraps

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from django.views.decorators.csrf import csrf_exempt

from .client import APIError, fetch_angelcam


def access_token(request):
    parts = request.headers.get("Authorization", "").split()
    if len(parts) != 2 or parts[0].lower() not in {"bearer", "personalaccesstoken"}:
        raise APIError("A Bearer or PersonalAccessToken header is required.", 401)
    return parts[1]


def endpoint(method, authenticated=True):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method != method:
                response = JsonResponse(
                    {"error": f"Only {method} requests are allowed."}, status=405
                )
                response["Allow"] = method
            else:
                try:
                    token = access_token(request) if authenticated else None
                    response = view(request, token, *args, **kwargs)
                except APIError as error:
                    response = JsonResponse({"error": str(error)}, status=error.status)
                    if error.status == 401:
                        response["WWW-Authenticate"] = "PersonalAccessToken"
            response["Cache-Control"] = "no-store"
            return response

        return wrapped

    return decorate


def recording_range(request, end_required=True):
    values = {}
    parsed = {}
    for name in ("start", "end"):
        value = request.GET.get(name)
        if not value:
            if name == "start" or end_required:
                raise APIError(f"{name.capitalize()} time is required.")
            continue
        try:
            date = parse_datetime(value)
        except (ValueError, OverflowError):
            date = None
        if date is None or not is_aware(date):
            raise APIError(
                f"{name.capitalize()} must be an ISO datetime with a timezone."
            )
        values[name] = value
        parsed[name] = date
    if "end" in parsed and parsed["start"] >= parsed["end"]:
        raise APIError("Start time must be earlier than end time.")
    return values


@endpoint("GET", authenticated=False)
def home(request, token):
    return JsonResponse({"message": "Welcome to API!"})


@csrf_exempt
@endpoint("POST", authenticated=False)
def login(request, token):
    token = request.POST.get("token", "").strip()
    if not token or any(character.isspace() for character in token):
        raise APIError("A non-empty access token without whitespace is required.")
    data = fetch_angelcam("me", token)
    return JsonResponse({"message": "Login successful", "data": data})


@endpoint("GET")
def get_cameras(request, token):
    data = fetch_angelcam("shared-cameras", token)
    return JsonResponse({"cameras": data})


@endpoint("GET")
def get_camera_stream(request, token, camera_id):
    data = fetch_angelcam(f"shared-cameras/{camera_id}/", token)
    streams = data.get("streams", [])
    if not isinstance(streams, list):
        raise APIError("Angelcam returned an invalid stream list.", 502)
    stream_details = [
        {"url": stream["url"], "format": stream["format"]}
        for stream in streams
        if isinstance(stream, dict)
        and isinstance(stream.get("url"), str)
        and isinstance(stream.get("format"), str)
    ]
    return JsonResponse({"stream_details": stream_details})


@endpoint("GET")
def get_recording_info(request, token, camera_id):
    data = fetch_angelcam(f"shared-cameras/{camera_id}/recording/", token)
    return JsonResponse({"recording_info": data})


@endpoint("GET")
def get_recording_stream(request, token, camera_id):
    params = recording_range(request, end_required=False)
    data = fetch_angelcam(
        f"shared-cameras/{camera_id}/recording/stream/", token, params
    )
    return JsonResponse({"stream": data})


@endpoint("GET")
def get_recording_timeline(request, token, camera_id):
    params = recording_range(request)
    data = fetch_angelcam(
        f"shared-cameras/{camera_id}/recording/timeline/", token, params
    )
    return JsonResponse({"timeline": data})
