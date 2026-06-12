# Client Integration Guide — FCM Token Registration

This guide explains how to obtain an FCM registration token on each platform and register it with the PushNotify backend.

For Firebase project setup (creating an app, downloading credentials), see [docs/firebase-setup.md](firebase-setup.md).

---

## Overview

The registration flow is the same on all platforms:

1. Initialize the Firebase SDK in your app
2. Request notification permission from the user (iOS / Web only)
3. Retrieve the FCM token from the Firebase SDK
4. Call `POST /api/v1/devices/register` with the token

When the OS rotates the token, repeat step 3–4 with the new token.

---

## Android

### Prerequisites

- Firebase project created (see [firebase-setup.md](firebase-setup.md))
- Android app registered in Firebase Console

### Step-by-step

**1. Download `google-services.json`**

Firebase Console → Project Settings → General → **Your apps** → select your Android app → **Download google-services.json**

**2. Place the file in your project**

```
android/app/google-services.json
```

**3. Add the Google Services plugin to root `build.gradle`**

```groovy
// Root-level build.gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

**4. Apply the plugin and add Firebase Messaging to app `build.gradle`**

```groovy
// app/build.gradle
plugins {
    id 'com.google.gms.google-services'
}

dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-messaging'
}
```

**5. Implement `FirebaseMessagingService` to capture new tokens**

Create a service class that extends `FirebaseMessagingService` and override `onNewToken`:

```kotlin
// MyFirebaseMessagingService.kt (snippet — not a deliverable)
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Register with PushNotify backend
        registerTokenWithBackend(token, platform = "android")
    }
}
```

Register the service in `AndroidManifest.xml`:

```xml
<service
    android:name=".MyFirebaseMessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

**6. Call the registration endpoint**

See [Sample Registration Call](#sample-registration-call) below.

---

## iOS

### Prerequisites

- Firebase project created (see [firebase-setup.md](firebase-setup.md))
- iOS app registered in Firebase Console
- Paid Apple Developer account

### Step-by-step

**1. Create an APNs Auth Key (.p8) in Apple Developer Console**

Apple Developer Portal → **Certificates, Identifiers & Profiles** → **Keys** → **+** →
- Enable **Apple Push Notifications service (APNs)**
- Download the `.p8` file (save it — it can only be downloaded once)
- Note the **Key ID** and your **Team ID**

**2. Upload the .p8 key to Firebase Console**

Firebase Console → Project Settings → **Cloud Messaging** → iOS app configuration →
**APNs Authentication Key** → Upload → provide Key ID and Team ID

**3. Enable Push Notifications capability in Xcode**

Xcode → Project → Target → **Signing & Capabilities** → **+ Capability** →
**Push Notifications**

Also add **Background Modes** → enable **Remote notifications**

**4. Configure Firebase and APNs in app delegate**

```swift
// AppDelegate.swift (snippet — integration reference only)
import FirebaseCore
import FirebaseMessaging
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate,
                   UNUserNotificationCenterDelegate, MessagingDelegate {

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        FirebaseApp.configure()

        // Request permission
        UNUserNotificationCenter.current().delegate = self
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { _, _ in }
        application.registerForRemoteNotifications()

        Messaging.messaging().delegate = self
        return true
    }
}
```

**5. Retrieve the FCM token via the Messaging delegate**

```swift
// MessagingDelegate callback (snippet)
func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
    guard let token = fcmToken else { return }
    // Register with PushNotify backend
    registerTokenWithBackend(token, platform: "ios")
}
```

Alternatively, fetch the token on demand:

```swift
Messaging.messaging().token { token, error in
    guard let token = token else { return }
    registerTokenWithBackend(token, platform: "ios")
}
```

**6. Call the registration endpoint**

See [Sample Registration Call](#sample-registration-call) below.

---

## Web

### Prerequisites

- Firebase project created (see [firebase-setup.md](firebase-setup.md))
- Web app registered in Firebase Console
- **HTTPS required in production** (localhost is exempt for development)

### Step-by-step

**1. Get the VAPID key**

Firebase Console → Project Settings → **Cloud Messaging** → **Web configuration** →
**Web Push certificates** → **Generate key pair** (or use existing) → copy the **Key pair** value

**2. Create `firebase-messaging-sw.js` at your web root**

This service worker handles background messages:

```javascript
// public/firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification;
  self.registration.showNotification(title, { body });
});
```

**3. Initialize Firebase Messaging in your app**

```javascript
// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getMessaging } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const app = initializeApp(firebaseConfig);
export const messaging = getMessaging(app);
```

**4. Request notification permission and get the FCM token**

```javascript
import { getToken, onMessage } from 'firebase/messaging';
import { messaging } from './firebase';

async function requestPermissionAndGetToken() {
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    console.warn('Notification permission denied');
    return;
  }

  const token = await getToken(messaging, {
    vapidKey: import.meta.env.VITE_FIREBASE_VAPID_KEY,
    serviceWorkerRegistration: await navigator.serviceWorker.register('/firebase-messaging-sw.js'),
  });

  return token;
}
```

**5. Call the registration endpoint**

See [Sample Registration Call](#sample-registration-call) below.

---

## Sample Registration Call

The registration call is identical across all platforms. Use your platform's HTTP client to call:

```
POST /api/v1/devices/register
Content-Type: application/json
```

### JavaScript / TypeScript (Fetch API)

```javascript
// Example registration call (all platforms)
async function registerFcmToken(token, platform, appVersion, deviceId) {
  const response = await fetch('/api/v1/devices/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fcm_token: token,
      platform: platform,       // 'android' | 'ios' | 'web'
      app_version: appVersion,  // e.g. '1.0.0'
      installation_id: deviceId, // optional stable device ID
    }),
  });

  if (!response.ok) {
    throw new Error(`Registration failed: ${response.status}`);
  }

  const { id, registered } = await response.json();
  // id: server-side UUID for this device record
  // registered: true
  return id;
}
```

### Request body reference

```json
{
  "fcm_token": "fxWjKdQ5R4...",
  "platform": "web",
  "app_version": "1.0.0",
  "installation_id": "browser-fingerprint-or-uuid",
  "external_user_id": "your-system-user-id"
}
```

Full schema: see [api-contract.md → POST /api/v1/devices/register](api-contract.md#post-apiv1devicesregister)

### Successful response

```json
HTTP 201 Created

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "registered": true
}
```

---

## Token Rotation

FCM tokens can be invalidated or rotated at any time. Handle token changes:

| Platform | Trigger |
|----------|---------|
| Android | `FirebaseMessagingService.onNewToken()` |
| iOS | `MessagingDelegate.messaging(_:didReceiveRegistrationToken:)` |
| Web | `onTokenRefresh` callback or call `getToken()` on each app start |

Always call `POST /api/v1/devices/register` with the new token. The backend will upsert the record (update if the `installation_id` matches an existing record, otherwise create).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Token is `null` on iOS | APNs Auth Key not uploaded, or Push Notifications capability missing | Re-check steps 1–3 in the iOS section |
| `getToken()` fails on Web | VAPID key mismatch or service worker not found at `/firebase-messaging-sw.js` | Verify VAPID key and service worker URL |
| Registration returns 422 | Missing required field or wrong `platform` value | Check request body against schema |
| Registration returns 429 | Rate limit (10/min/IP) exceeded | Implement exponential backoff |
| Notifications not received on Web | Not HTTPS in production | Serve over HTTPS; localhost is exempt |
| Background messages not shown on Web | Service worker not registered | Ensure `firebase-messaging-sw.js` is at web root and registered before calling `getToken()` |

---

## See Also

- [Firebase project setup](firebase-setup.md) — creating the Firebase project, registering apps, downloading credentials
- [API contract](api-contract.md) — complete endpoint reference
