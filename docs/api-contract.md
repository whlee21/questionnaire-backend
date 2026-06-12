# API Contract — PushNotify Backend

This document is the **single source of truth** for the PushNotify REST API.
All backend schemas (T9, T12-T15) and frontend pages (T11, T16-T19) implement against this contract.
Any deviation between this document and the implementation is a bug.

---

## Base URLs

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:8000` |
| Configured via | `VITE_API_BASE_URL` env variable |

## Authentication

Admin-only endpoints require a JWT bearer token:

```
Authorization: Bearer <JWT_TOKEN>
```

Tokens are obtained via `POST /api/v1/auth/login`. Tokens expire after the duration configured in `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Error Format

All errors use one of two formats:

```json
// Application error
{"detail": "human-readable message"}

// FastAPI validation error (422)
{
  "detail": [
    {"loc": ["body", "field_name"], "msg": "error message", "type": "value_error"}
  ]
}
```

## Rate Limits

| Endpoint group | Limit |
|----------------|-------|
| `POST /api/v1/auth/login` | 5 requests / min / IP |
| `POST /api/v1/devices/register` | 10 requests / min / IP |
| `POST /api/v1/messages/send` | 30 requests / min / admin |

Rate limit exceeded → `HTTP 429 Too Many Requests`

---

## Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Health check |
| POST | `/api/v1/auth/login` | Public | Admin login |
| GET | `/api/v1/auth/me` | Admin JWT | Current admin info |
| POST | `/api/v1/devices/register` | Public (constrained) | Register FCM device token |
| GET | `/api/v1/devices` | Admin JWT | List devices (paginated) |
| DELETE | `/api/v1/devices/{id}` | Admin JWT | Delete device record |
| POST | `/api/v1/messages/send` | Admin JWT | Send push notification |
| POST | `/api/v1/topics/subscribe` | Admin JWT | Subscribe tokens to topic |
| POST | `/api/v1/topics/unsubscribe` | Admin JWT | Unsubscribe from topic |
| GET | `/api/v1/topics` | Admin JWT | List topics with subscriber counts |
| GET | `/api/v1/messages/history` | Admin JWT | List send events (paginated + filtered) |
| GET | `/api/v1/messages/history/{id}` | Admin JWT | Send event detail |

---

## Endpoints

### GET /health

Health check. No authentication required.

**Response 200**

```json
{"status": "ok"}
```

---

### POST /api/v1/auth/login

Authenticate as an admin user. Returns a JWT access token.

**Rate limit:** 5 requests / min / IP

**Request body**

```json
{
  "email": "admin@example.com",
  "password": "string"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string | ✅ | Admin email address |
| `password` | string | ✅ | Admin password |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success — token returned |
| 401 | Invalid credentials |
| 422 | Validation error (missing fields) |
| 429 | Rate limit exceeded |

---

### GET /api/v1/auth/me

Return the currently authenticated admin's info.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Response 200**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "created_at": "2026-06-12T00:00:00Z"
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing or invalid token |

---

### POST /api/v1/devices/register

Register a client FCM token. Called from mobile/web apps when the OS assigns a new FCM token.
Raw FCM tokens are stored server-side and **never returned** in API responses.

**Rate limit:** 10 requests / min / IP

**Request body — `RegisterDeviceIn`**

```json
{
  "fcm_token": "fxWjKdQ5R4...",
  "platform": "android",
  "app_version": "1.0.0",
  "installation_id": "550e8400-...",
  "external_user_id": "user-42"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `fcm_token` | string | ✅ | Unique FCM registration token from the OS |
| `platform` | `"ios"` \| `"android"` \| `"web"` | ✅ | Client platform |
| `app_version` | string | ✅ | App semver string, e.g. `"1.2.3"` |
| `installation_id` | string | ❌ | Stable device identifier (optional) |
| `external_user_id` | string | ❌ | Your system's user ID (optional) |

**Response 201**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "registered": true
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| 201 | Token registered (new or updated) |
| 422 | Validation error |
| 429 | Rate limit exceeded |

---

### GET /api/v1/devices

List registered devices with pagination. Raw FCM tokens are masked.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Query parameters**

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `page` | integer | `1` | 1-based page number |
| `size` | integer | `20` | Items per page (max 100) |
| `platform` | string | — | Filter by platform: `ios`, `android`, `web` |
| `push_enabled` | boolean | — | Filter by push-enabled status |

**Response 200 — paginated `DeviceOut`**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "android",
      "app_version": "1.0.0",
      "fcm_token_masked": "fxW...kQ5R",
      "push_enabled": true,
      "external_user_id": "user-42",
      "last_seen_at": "2026-06-12T00:00:00Z",
      "created_at": "2026-06-12T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

**`DeviceOut` field reference**

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID string | Device record ID |
| `platform` | `"ios"` \| `"android"` \| `"web"` | |
| `app_version` | string | |
| `fcm_token_masked` | string | Format: `tok-...XXXX` (never full token) |
| `push_enabled` | boolean | False when FCM reports token invalid |
| `external_user_id` | string \| null | |
| `last_seen_at` | ISO 8601 datetime | Last successful delivery or re-registration |
| `created_at` | ISO 8601 datetime | |

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing or invalid token |
| 422 | Invalid query parameters |

---

### DELETE /api/v1/devices/{id}

Delete a device record by its UUID.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Path parameter:** `id` — UUID of the device record

**Response 204** — No content

**Status codes**

| Code | Meaning |
|------|---------|
| 204 | Deleted successfully |
| 401 | Missing or invalid token |
| 404 | Device not found |

---

### POST /api/v1/messages/send

Send a push notification. Supports four target types.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Rate limit:** 30 requests / min / admin

**Request body — `SendRequest`**

The `target` field is a discriminated union on `type`:

#### Target type 1: single token

```json
{
  "target": {
    "type": "token",
    "token": "fxWjKdQ5R4..."
  },
  "notification": {
    "title": "Hello",
    "body": "World",
    "image_url": "https://example.com/img.png"
  },
  "data": {
    "screen": "home",
    "badge_count": "3"
  },
  "dry_run": false,
  "idempotency_key": "req-abc123"
}
```

#### Target type 2: multiple tokens (max 500 per request)

```json
{
  "target": {
    "type": "tokens",
    "tokens": ["tok1", "tok2", "tok3"]
  },
  "notification": {
    "title": "Announcement",
    "body": "Check this out!"
  }
}
```

#### Target type 3: FCM topic

```json
{
  "target": {
    "type": "topic",
    "topic": "news"
  },
  "notification": {
    "title": "Breaking news",
    "body": "Something happened."
  }
}
```

#### Target type 4: broadcast (all registered devices)

```json
{
  "target": {
    "type": "broadcast"
  },
  "notification": {
    "title": "System update",
    "body": "Please restart your app."
  }
}
```

> **Note:** Broadcast sends to the reserved FCM topic `all`. Devices must be subscribed to `all` to receive it.

**`SendRequest` field reference**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `target` | object | ✅ | See target variants above |
| `notification.title` | string | ✅ | Notification title |
| `notification.body` | string | ✅ | Notification body text |
| `notification.image_url` | string | ❌ | URL of image to display |
| `data` | object | ❌ | Arbitrary key-value pairs — **ALL values MUST be strings** |
| `dry_run` | boolean | ❌ | Default `false`. If `true`, validates without sending |
| `idempotency_key` | string | ❌ | Deduplication key; same key within 24h returns cached result |

**⚠️ CRITICAL:** The `data` field values **MUST be strings**. FCM rejects non-string values at the protocol level. Convert numbers/booleans to strings before sending (e.g., `"badge_count": "3"`, not `"badge_count": 3`).

**Response 200 — `SendResultOut`**

```json
{
  "success_count": 10,
  "failure_count": 2,
  "invalidated_tokens": ["tok-dead-1", "tok-dead-2"],
  "dry_run": false
}
```

| Field | Type | Notes |
|-------|------|-------|
| `success_count` | integer | Number of tokens/devices that accepted the message |
| `failure_count` | integer | Number of tokens/devices that rejected the message |
| `invalidated_tokens` | string[] | Masked tokens that FCM reported as invalid (auto-deregistered) |
| `dry_run` | boolean | Mirrors the request's `dry_run` flag |

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Request processed (check `failure_count` for partial failures) |
| 400 | Invalid target (e.g., empty token list) |
| 401 | Missing or invalid token |
| 422 | Validation error (e.g., non-string data values) |
| 429 | Rate limit exceeded |

---

### POST /api/v1/topics/subscribe

Subscribe one or more FCM tokens (or registered device records) to a topic.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Request body — `TopicSubscribeIn`**

```json
{
  "topic": "news",
  "tokens": ["tok1", "tok2"],
  "device_ids": ["550e8400-...", "661f9500-..."]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `topic` | string | ✅ | Topic name (alphanumeric + hyphens/underscores) |
| `tokens` | string[] | ❌ | Raw FCM tokens to subscribe (max 1000 per request) |
| `device_ids` | UUID[] | ❌ | Device record IDs to subscribe (max 1000 per request) |

At least one of `tokens` or `device_ids` must be provided.

**Response 200**

```json
{
  "success_count": 2,
  "failure_count": 0
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Operation complete |
| 400 | Neither `tokens` nor `device_ids` provided |
| 401 | Missing or invalid token |
| 422 | Validation error |

---

### POST /api/v1/topics/unsubscribe

Unsubscribe one or more tokens from a topic.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Request body** — same schema as `TopicSubscribeIn`:

```json
{
  "topic": "news",
  "tokens": ["tok1"],
  "device_ids": []
}
```

**Response 200**

```json
{
  "success_count": 1,
  "failure_count": 0
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Operation complete |
| 400 | Neither `tokens` nor `device_ids` provided |
| 401 | Missing or invalid token |
| 422 | Validation error |

---

### GET /api/v1/topics

List all topics with subscriber counts.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Response 200**

```json
[
  {
    "name": "news",
    "subscriber_count": 1042,
    "created_at": "2026-06-12T00:00:00Z"
  },
  {
    "name": "all",
    "subscriber_count": 5000,
    "created_at": "2026-06-01T00:00:00Z"
  }
]
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing or invalid token |

---

### GET /api/v1/messages/history

List past send events with pagination and optional filtering.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Query parameters**

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `page` | integer | `1` | 1-based page number |
| `size` | integer | `20` | Items per page (max 100) |
| `target_type` | string | — | Filter by `token`, `tokens`, `topic`, `broadcast` |
| `actor` | string | — | Filter by admin email |
| `from` | ISO 8601 date | — | Filter events on or after this date |
| `to` | ISO 8601 date | — | Filter events before or on this date |
| `dry_run` | boolean | — | Filter by dry-run flag |

**Response 200 — paginated `SendEventOut`**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "actor": "admin@example.com",
      "target_type": "topic",
      "target_summary": "news",
      "payload_summary": {
        "title": "Breaking news",
        "body": "Something happened."
      },
      "dry_run": false,
      "success_count": 1042,
      "failure_count": 3,
      "created_at": "2026-06-12T00:00:00Z"
    }
  ],
  "total": 250,
  "page": 1,
  "size": 20
}
```

**`SendEventOut` field reference**

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID string | Send event record ID |
| `actor` | string | Email of the admin who triggered the send |
| `target_type` | `"token"` \| `"tokens"` \| `"topic"` \| `"broadcast"` | |
| `target_summary` | string | Masked token, topic name, `"N tokens"`, or `"broadcast"` |
| `payload_summary` | object | `{"title": "...", "body": "..."}` — image_url omitted |
| `dry_run` | boolean | |
| `success_count` | integer | |
| `failure_count` | integer | |
| `created_at` | ISO 8601 datetime | |

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing or invalid token |
| 422 | Invalid query parameters |

---

### GET /api/v1/messages/history/{id}

Retrieve full detail of a single send event.

**Auth:** `Authorization: Bearer <JWT_TOKEN>`

**Path parameter:** `id` — UUID of the send event

**Response 200 — `SendEventDetailOut`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "admin@example.com",
  "target_type": "tokens",
  "target_summary": "10 tokens",
  "payload_summary": {
    "title": "Flash sale",
    "body": "50% off today only!"
  },
  "dry_run": false,
  "success_count": 8,
  "failure_count": 2,
  "invalidated_tokens": ["tok-...XXXX"],
  "created_at": "2026-06-12T00:00:00Z"
}
```

Same as `SendEventOut` plus `invalidated_tokens` (masked).

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing or invalid token |
| 404 | Event not found |

---

## Shared Schemas

### Pagination envelope

All list endpoints return:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20
}
```

### `DeviceOut`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "ios",
  "app_version": "1.0.0",
  "fcm_token_masked": "tok-...XXXX",
  "push_enabled": true,
  "external_user_id": null,
  "last_seen_at": "2026-06-12T00:00:00Z",
  "created_at": "2026-06-12T00:00:00Z"
}
```

### `SendResultOut`

```json
{
  "success_count": 10,
  "failure_count": 2,
  "invalidated_tokens": ["tok-...XXXX"],
  "dry_run": false
}
```

### `SendEventOut`

```json
{
  "id": "uuid",
  "actor": "admin@example.com",
  "target_type": "token | tokens | topic | broadcast",
  "target_summary": "tok-...XXXX or 'news' or '10 tokens' or 'broadcast'",
  "payload_summary": {"title": "...", "body": "..."},
  "dry_run": false,
  "success_count": 10,
  "failure_count": 0,
  "created_at": "2026-06-12T00:00:00Z"
}
```

---

## Important Constraints

### FCM Protocol Requirements

1. **`data` values MUST be strings.** FCM rejects any non-string value at the protocol level.
   - ✅ `"badge_count": "3"`
   - ❌ `"badge_count": 3`

2. **Multicast limit: 500 tokens per `send` request.** If you provide more than 500 tokens in `target.tokens`, the backend will chunk the request internally into batches of ≤500.

3. **Topic subscribe/unsubscribe: 1000 tokens per request.** Batch client calls if you have more.

4. **"Broadcast" uses the reserved `all` topic.** FCM has no native global-send feature. Broadcast is implemented by sending to the `all` topic — devices must be subscribed to receive it. The backend auto-subscribes devices to `all` on registration.

### Security Constraints

5. **Raw FCM tokens are NEVER returned in API responses.** All API responses use masked tokens in the format `tok-...XXXX`. The full token is stored server-side only.

6. **Admin JWT tokens are short-lived.** Check the `exp` claim and re-authenticate when expired.

### Deprecated APIs

7. **Do NOT use the legacy FCM server-key (HTTP v1) API.** The legacy server-key API was deprecated in June 2024 and is not used by this backend. The backend uses the Firebase Admin SDK (OAuth 2.0 service account credentials).
