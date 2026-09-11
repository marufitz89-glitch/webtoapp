ANDROID_MAIN_ACTIVITY = r'''package {package_name};

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

public class MainActivity extends AppCompatActivity {

    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);

        WebSettings settings = webView.getSettings();

        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);

        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        settings.setSupportZoom(false);

        webView.setWebViewClient(
                new WebViewClient()
        );

{bridge}

        webView.loadUrl(
                "{start_url}"
        );

        setContentView(webView);

{fullscreen}
    }

    @Override
    public void onBackPressed() {

        if (
            webView != null &&
            webView.canGoBack()
        ) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
'''


NATIVE_BRIDGE = r'''package {package_name};

import android.webkit.JavascriptInterface;

public class NativeBridge {

    @JavascriptInterface
    public String getPlatform() {
        return "Android";
    }

    @JavascriptInterface
    public String getVersion() {
        return "{version}";
    }

    @JavascriptInterface
    public String getPackageName() {
        return "{package_name}";
    }
}
'''


ANDROID_BUILD_GRADLE = r'''plugins {
    id 'com.android.application'
}

android {
    namespace '{package_name}'
    compileSdk 35

    defaultConfig {
        applicationId '{package_name}'
        minSdk {min_sdk}
        targetSdk {target_sdk}

        versionCode 1
        versionName '{version}'
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.7.0'
    implementation 'androidx.core:core:1.15.0'
    implementation 'androidx.webkit:webkit:1.12.1'
}
'''


ROOT_BUILD_GRADLE = r'''plugins {
    id 'com.android.application' version '8.7.3' apply false
}
'''


SETTINGS_GRADLE = r'''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(
        RepositoriesMode.FAIL_ON_PROJECT_REPOS
    )

    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "{project_name}"

include(":app")
'''


GRADLE_PROPERTIES = r'''org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
android.nonTransitiveRClass=true
'''


ANDROID_MANIFEST = r'''<?xml version="1.0" encoding="utf-8"?>

<manifest
    xmlns:android="http://schemas.android.com/apk/res/android">

{notification_permission}

    <uses-permission
        android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:label="{app_name}"
        android:usesCleartextTraffic="false"
        android:theme="@style/Theme.Web2App">

        <activity
            android:name=".MainActivity"
            android:screenOrientation="{orientation}"
            android:exported="true">

            <intent-filter>

                <action
                    android:name="android.intent.action.MAIN" />

                <category
                    android:name="android.intent.category.LAUNCHER" />

            </intent-filter>

        </activity>

    </application>

</manifest>
'''


STRINGS_XML = r'''<?xml version="1.0" encoding="utf-8"?>

<resources>

    <string name="app_name">{app_name}</string>

</resources>
'''


STYLES_XML = r'''<?xml version="1.0" encoding="utf-8"?>

<resources>

    <style
        name="Theme.Web2App"
        parent="Theme.AppCompat.DayNight.NoActionBar">

        <item name="android:fontFamily">sans</item>

        <item name="android:statusBarColor">
            #080b10
        </item>

        <item name="android:navigationBarColor">
            #080b10
        </item>

    </style>

</resources>
'''


PWA_MANIFEST = r'''{
    "name": "{app_name}",
    "short_name": "{short_name}",
    "start_url": "{start_url}",
    "display": "{display}",
    "orientation": "{orientation}",
    "background_color": "#080b10",
    "theme_color": "#6d63ff",
    "icons": []
}
'''


SERVICE_WORKER = r'''const CACHE_NAME = "web2app-{project_id}-v1";

const APP_SHELL = [
    "./",
    "./index.html"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(APP_SHELL))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        )
    );

    self.clients.claim();
});

self.addEventListener("fetch", event => {

    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {

                const copy = response.clone();

                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(
                            event.request,
                            copy
                        );
                    });

                return response;
            })
            .catch(() => {
                return caches.match(event.request);
            })
    );
});
'''


PWA_INDEX = r'''<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width,initial-scale=1.0">

    <meta
        name="theme-color"
        content="#6d63ff">

    <link
        rel="manifest"
        href="manifest.json">

    <title>{app_name}</title>

</head>

<body>

    <main>

        <h1>{app_name}</h1>

        <p>
            Web2App LAB generated PWA.
        </p>

        <p>
            <a href="{start_url}">
                Open Website
            </a>
        </p>

    </main>

    <script>

        if ("serviceWorker" in navigator) {

            window.addEventListener(
                "load",
                () => {

                    navigator.serviceWorker.register(
                        "./sw.js"
                    );

                }
            );

        }

    </script>

</body>

</html>
'''


README = r'''# {app_name}

Generated by Web2App LAB.

## Website

{start_url}

## Android

Package: `{package_name}`

Version: `{version}`

Minimum SDK: `{min_sdk}`

Target SDK: `{target_sdk}`

Orientation: `{orientation}`

## Features

- Fullscreen: {fullscreen}
- Offline Cache: {offline_cache}
- Push Notifications: {push_notifications}
- Native Bridge: {native_bridge}

## Generated Components

- Android WebView
- Android Manifest
- Gradle configuration
- PWA Manifest
- Service Worker
- Native Bridge
- Project configuration

## Build

Open the Android project in a compatible Android Studio environment and build the application.
'''


def render(template: str, **values) -> str:
    return template.format(**values)