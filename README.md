# PushNotify — Firebase Push Notification Sender Console

React admin console + FastAPI backend for sending FCM push notifications.

## Prerequisites

- Docker + Docker Compose
- Python 3.12
- Node 20

## Quick start

```bash
cp backend/.env.example backend/.env
make up
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## FCM_FAKE mode

`FCM_FAKE=1` (default in Docker) runs the entire stack without real Firebase credentials. All QA uses this mode.

## Running tests

```bash
cd backend && pytest
cd frontend && npm run test -- --run
```

## Docs

- [Firebase setup](docs/firebase-setup.md)
- [API reference](docs/api-contract.md)
