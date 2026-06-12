# Firebase Project Setup Guide

## 1. Overview

Firebase Cloud Messaging (FCM) is Google's cross-platform messaging solution for sending push notifications to Android, iOS, and web clients. This guide covers creating a Firebase project, configuring credentials for the backend, and setting up clients (web, iOS, Android).

> **🟢 FCM_FAKE=1 mode (default in Docker) requires NO Firebase setup.**
> All local development and automated QA uses `FCM_FAKE=1`, which runs a `FakeFcmClient` that records send requests in memory without contacting Firebase. **You only need to follow this guide if you intend to deliver real push notifications to real devices.**

For the API reference, see [`docs/api-contract.md`](api-contract.md).

---

## 2. Prerequisites

| Requirement | Details |
|---|---|
| Firebase account | https://console.firebase.google.com (Google account required) |
| Node.js 18+ | Only if you want to use Firebase CLI (optional) |
| `FCM_FAKE=1` | **No Firebase account needed for local dev or CI** |

> For local development, set `FCM_FAKE=1` in `backend/.env` (this is already the default in `docker-compose.yml`) and skip to [Section 9](#9-local-development-with-fcm_fake-no-firebase-required).

---

## 3. Create a Firebase Project

1. Go to https://console.firebase.google.com
2. Click **"Add project"**
3. Enter a project name, click **Continue**
4. Configure Google Analytics (optional — you may disable it)
5. Click **"Create project"**
6. Wait for provisioning, then click **Continue**
7. Note your **Project ID** — this becomes the `FIREBASE_PROJECT_ID` environment variable

---

## 4. Enable Cloud Messaging

1. In Firebase Console, click the gear icon → **Project Settings**
2. Click the **Cloud Messaging** tab
3. FCM is enabled by default for all new projects — no additional action is needed
4. **Important**: The "Server key" displayed on this page is the deprecated legacy FCM API.
   Do **not** use it. This project uses the FCM HTTP v1 API exclusively via the
   `firebase-admin` Python SDK with service account credentials.

---

## 5. Service Account Key (Backend Credentials)

> ```
> ⚠️  SECURITY WARNING
> NEVER commit the service account JSON file to version control.
> The .gitignore in this project already blocks **/serviceAccount*.json.
> Verify before downloading: git check-ignore /path/to/serviceAccount.json
> ```

### Steps

1. Firebase Console → gear icon → **Project Settings** → **Service accounts** tab
2. Click **"Generate new private key"**
3. Click **"Generate key"** in the confirmation dialog
4. Save the downloaded JSON file **securely outside your repository** (e.g., `~/.secrets/` or a secrets vault)
5. Set the environment variable:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/serviceAccount.json"
   ```

   Or add to `backend/.env`:

   ```dotenv
   GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/serviceAccount.json
   FIREBASE_PROJECT_ID=your-actual-project-id
   FCM_FAKE=0
   ```

6. The Python `firebase-admin` SDK reads credentials via ADC (Application Default Credentials) automatically — no additional code changes are needed.

### Role Requirements

Grant the service account the **Firebase Cloud Messaging Sender** role (IAM & Admin → Service accounts → your account → Permissions). Avoid granting Owner or Editor for least-privilege.

---

## 6. Web Push Certificate (VAPID Key)

1. Firebase Console → **Project Settings** → **Cloud Messaging** tab
2. Scroll to **"Web configuration"**
3. Under **"Web Push certificates"**, click **"Generate key pair"**
4. Copy the generated public key (this is your VAPID key)
5. Use the VAPID key in frontend web push initialization:

   ```javascript
   import { getToken } from 'firebase/messaging'

   const token = await getToken(messaging, {
     vapidKey: 'YOUR_VAPID_PUBLIC_KEY'
   })
   ```

   Store the VAPID public key in a frontend environment variable (e.g., `VITE_FIREBASE_VAPID_KEY`). The public key is safe to expose in client-side code but keeping it in env vars makes rotation easier.

---

## 7. iOS — APNs Auth Key

iOS push notifications require Apple Push Notification service (APNs) credentials uploaded to Firebase. Without this, Firebase will silently fail to deliver notifications to iOS devices.

1. Go to [Apple Developer Console](https://developer.apple.com) → **Certificates, Identifiers & Profiles** → **Keys**
2. Click **"+"** to create a new key
3. Enter a descriptive name, check **"Apple Push Notifications service (APNs)"**
4. Click **Continue**, then **Register**
5. **Download the `.p8` key file** — this can only be downloaded once; store it immediately in a secure location
6. Note the **Key ID** (shown in the developer console) and your **Team ID** (top-right of developer console)
7. Firebase Console → **Project Settings** → **Cloud Messaging** → your iOS app → **Upload APNs Auth Key**:
   - Upload the `.p8` file
   - Enter the **Key ID** and **Team ID**
8. In Xcode: **Signing & Capabilities** → **"+"** → **Push Notifications**

> **Note**: APNs Auth Keys (`.p8`) are preferred over APNs Certificates (`.p12`) — they don't expire annually and support all APNs features.

---

## 8. Android — google-services.json

1. Firebase Console → **Project Settings** → **General** tab
2. Under **"Your apps"**, click **"Add app"** → select **Android**
3. Enter your Android package name — this must exactly match the `applicationId` in your app's `build.gradle`
4. Click **"Register app"**
5. Download **`google-services.json`**
6. Place the file in your Android project's `app/` directory:

   ```
   android/app/google-services.json
   ```

7. Add the Google Services plugin to your root `build.gradle`:

   ```groovy
   // root build.gradle
   buildscript {
     dependencies {
       classpath 'com.google.gms:google-services:4.4.0'
     }
   }
   ```

8. Apply the plugin and add the Firebase Messaging dependency in your app's `build.gradle`:

   ```groovy
   // app/build.gradle
   apply plugin: 'com.google.gms.google-services'

   dependencies {
     implementation 'com.google.firebase:firebase-messaging:23.4.0'
   }
   ```

---

## 9. Local Development with FCM_FAKE (No Firebase Required)

```
FCM_FAKE=1 is the DEFAULT in docker-compose.yml.
The entire stack runs without Firebase credentials using FakeFcmClient.
ALL automated QA scenarios use this mode.
```

To activate:

```bash
# In backend/.env (already set to 1 in docker-compose.yml):
FCM_FAKE=1
```

### How FakeFcmClient Works

The `FakeFcmClient`:

- Records all send requests in memory
- Returns configurable responses (success / `UNREGISTERED` / `INVALID_ARGUMENT` per token)
- Enables full end-to-end testing without a real device or Firebase project
- Produces identical API responses to the real FCM client from the caller's perspective

This means:

- No `GOOGLE_APPLICATION_CREDENTIALS` required
- No `FIREBASE_PROJECT_ID` required
- All API endpoints behave identically to production
- Batch sends, broadcasts, and per-token results all work correctly

---

## 10. Validate-Only Dry Run (with real Firebase)

When real Firebase credentials are configured, you can validate a message structure without actually delivering it using `dry_run: true`.

**Environment setup:**

```dotenv
# backend/.env
FCM_FAKE=0
GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccount.json
FIREBASE_PROJECT_ID=your-project-id
```

**Request body with dry_run:**

```json
{
  "target": { "type": "broadcast" },
  "notification": { "title": "Test", "body": "Validation only" },
  "dry_run": true
}
```

Firebase will:
- Validate the message structure and credentials
- Return a message ID if the message would be accepted
- **Not** deliver the notification to any device

This is useful for verifying credentials and message formats in staging before enabling real delivery.

---

## 11. Security Checklist

```
[ ] serviceAccount*.json added to .gitignore BEFORE downloading key
    (verify: git check-ignore /path/to/serviceAccount.json)
[ ] Service account has only necessary permissions
    (Firebase Cloud Messaging Sender role — not Owner/Editor)
[ ] Rotate service account keys periodically
    (IAM & Admin → Service accounts → your account → Keys)
[ ] Never log or print the service account JSON content
[ ] VAPID public key is safe to expose in frontend — keep in env vars for easy rotation
[ ] APNs .p8 key downloaded only once — store in a password manager or secrets vault immediately
[ ] FCM_FAKE=0 only in environments with real credentials (never in CI without secrets configured)
[ ] google-services.json excluded from version control if it contains sensitive project details
```

---

## 12. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `Could not load the default credentials` | `GOOGLE_APPLICATION_CREDENTIALS` not set or path incorrect | Verify env var is exported and file exists at the path |
| `File not found: serviceAccount.json` | Relative path used instead of absolute | Use an absolute path in `GOOGLE_APPLICATION_CREDENTIALS` |
| iOS notifications not delivered | APNs `.p8` key not uploaded to Firebase | Follow [Section 7](#7-ios--apns-auth-key) |
| iOS notifications silently fail | Bundle ID mismatch between Firebase app and Xcode | Verify Firebase iOS app bundle ID matches Xcode target |
| Web push not working in production | HTTPS not configured | Web push requires HTTPS; `localhost` is exempt in development |
| Web push: `VAPID key mismatch` | Different VAPID key used between token registration and send | Ensure the same VAPID key is used for `getToken()` and stored in backend env |
| Android notifications not delivered | `google-services.json` package name doesn't match `applicationId` | Re-download `google-services.json` after correcting package name in Firebase Console |
| All issues in local dev | Firebase credentials not set up | Use `FCM_FAKE=1` to bypass Firebase entirely for local development |
| `Permission denied` on Firebase send | Service account lacks Messaging Sender role | IAM & Admin → Service accounts → grant FCM Sender role |
