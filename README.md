# Angelcam API adapter

Django backend built for a **technical assessment for a job application**. It belongs to the same project as the [React frontend](https://github.com/YadiraAllauca/angelcam).

The backend forwards authorized requests to Angelcam for a user profile, shared cameras, stream URLs, and recording metadata. Video playback and seeking happen in the frontend; this server does not relay video or store recordings.

## Local setup

Tested with Python 3.12. Runtime dependencies are pinned in `requirements.txt`; development tools are in `requirements-dev.txt`.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

On Windows, activate the environment with `.venv\Scripts\activate`. Put the generated key in `DJANGO_SECRET_KEY` in `.env`, then run:

```sh
python manage.py check
python manage.py migrate
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`. Configure the frontend's `VITE_API_URL` accordingly. Django's built-in admin uses SQLite; the camera endpoints do not store account or camera data in that database.

## Configuration

Settings load `.env` through `python-dotenv`. Existing process environment variables take precedence.

| Variable | Behavior |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required; generate your own key. Never commit it. |
| `DJANGO_DEBUG` | Defaults to `false`; the example enables it for local development. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames; defaults to `localhost,127.0.0.1`. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins; defaults to the frontend on localhost or 127.0.0.1, port 5173. Add your actual frontend origin, including its port. |

CORS is limited to `/api/` and is not an authorization mechanism. A public deployment still needs appropriate HTTPS, server and Django deployment settings; `runserver` is for development. The old development key was removed from current source files, but remains in Git history. If it was ever used in a deployment, replace that deployment's key.

## API contract

All protected endpoints accept `Authorization: Bearer <token>` or `Authorization: PersonalAccessToken <token>` for compatibility with the frontend. Requests to Angelcam always use `PersonalAccessToken`. Missing or malformed authorization returns `401` before any external request.

| Method | Route | Successful response |
| --- | --- | --- |
| POST | `/api/login/` | `{ "message": "Login successful", "data": { ... } }` |
| GET | `/api/cameras/` | `{ "cameras": { "results": [ ... ], ... } }` |
| GET | `/api/stream/:id/` | `{ "stream_details": [{ "url": "...", "format": "..." }] }` |
| GET | `/api/recording-info/:id/` | `{ "recording_info": { ... } }` |
| GET | `/api/recording-timeline/:id/?start=...&end=...` | `{ "timeline": { "segments": [ ... ], ... } }` |
| GET | `/api/recording-stream/:id/?start=...&end=...` | `{ "stream": { "url": "...", ... } }` |

Login accepts an URL-encoded form field named `token`. It checks the token against Angelcam's profile endpoint; it does not create a session, issue a token, or revoke one. All subsequent requests supply the token again. Angelcam enforces resource permissions.

Recording dates must be ISO datetimes with a timezone, for example `2026-09-29T00:00:00Z`. The timeline requires both dates. A recording stream requires `start`; `end` is optional, preserving the original contract. When both are provided, `start` must be earlier than `end`. Encode query parameters normally, including `+` in timezone offsets.

An empty stream list returns `200` with `stream_details: []`, allowing the frontend to display its empty state. Camera listing uses the **shared cameras** endpoint. The adapter does not aggregate pages or combine shared and owned cameras.

## External failures

All Angelcam calls have a 3.05-second connection timeout and a 15-second read timeout. These are socket timeouts, not a total request deadline. Redirects are not followed.

- Angelcam `400`, `401`, `403`, `404`, and `429` responses retain their status with a generic message.
- Timeouts return `504`.
- Connection failures, other unexpected statuses, and malformed JSON return `502`.
- Unsupported HTTP methods return `405` with an `Allow` header.

Errors do not expose upstream response bodies. API responses use `Cache-Control: no-store`. Tokens are forwarded for each request and are not written to application storage or logs. There are no automatic retries, local rate limiting, or token refresh.

## Verification

```sh
python manage.py check
python manage.py test
black --check cameras/client.py cameras/views.py cameras/tests.py angelcam_back/settings.py
```

The 11 tests use Django's test client and mocked HTTP calls. They cover profile and stream response shapes, both authorization schemes, method restrictions, date validation, timeout and error mapping, stream handling, cache headers, and CORS preflight/error responses. They do not require cameras, real access tokens, or database writes.

These tests verify local behavior, not current Angelcam API availability, account permissions, real video playback, or end-to-end integration. This repository is a technical assessment, not a production surveillance backend.

## Permissions

No license has been granted to use, modify, or redistribute this repository. It is not presented as an official Angelcam application.
