"""Small Angelcam HTTP adapter; no tokens or upstream response bodies are logged."""

import requests

API_ROOT = "https://api.angelcam.com/v1"
REQUEST_TIMEOUT = (3.05, 15)


class APIError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def fetch_angelcam(path, token, params=None):
    try:
        response = requests.get(
            f"{API_ROOT}/{path}",
            headers={"Authorization": f"PersonalAccessToken {token}"},
            params=params,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.Timeout as error:
        raise APIError("Angelcam did not respond in time.", 504) from error
    except requests.RequestException as error:
        raise APIError("Could not reach Angelcam.", 502) from error

    if response.status_code != 200:
        messages = {
            400: "Angelcam rejected the request.",
            401: "Angelcam rejected the access token.",
            403: "Access to this Angelcam resource is denied.",
            404: "The Angelcam resource was not found.",
            429: "Angelcam rate limit reached. Try again later.",
        }
        status = response.status_code if response.status_code in messages else 502
        raise APIError(messages.get(status, "Angelcam is unavailable."), status)

    try:
        data = response.json()
    except ValueError as error:
        raise APIError("Angelcam returned an invalid JSON response.", 502) from error
    if not isinstance(data, dict):
        raise APIError("Angelcam returned an unexpected response.", 502)
    return data
