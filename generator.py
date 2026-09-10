import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from config import SUPPORTED_ORIENTATIONS
from security import (
    safe_filename,
    validate_package_name,
    validate_url,
)


def generate_android_files(config):
    app_name = config.app_name
    package_name = config.package_name
    package_path = package_name.replace(".", "/")

    fullscreen = config.fullscreen
    native_bridge = config.native_bridge

    fullscreen_code = ""

    if fullscreen:
        fullscreen_code = """
        WindowInsetsControllerCompat controller =
                new WindowInsetsControllerCompat(
                        getWindow(),
                        getWindow().getDecorView()
                );

        controller.hide(
                WindowInsetsCompat.Type.systemBars()
        );
"""

    bridge_code = ""

    if native_bridge:
        bridge_code = """
        webView.addJavascriptInterface(
                new NativeBridge(),
                "Web2AppBridge"
        );
"""

    notification_permission = ""

    if config.push_notifications:
        notification_permission = """
    <uses-permission
        android:name="android.permission.POST_NOTIFICATIONS" />
"""

    files = {}

    files["settings.gradle"] = f"""
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(
        RepositoriesMode.FAIL_ON_PROJECT_REPOS
    )

    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{safe_filename(app_name)}"

include(":app")
""".strip()

    files["build.gradle"] = """
plugins {
    id 'com.android.application'
        version '8.7.3'
        apply false
}
""".strip()

    files["gradle.properties"] = """
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
android.nonTransitiveRClass=true
""".strip()

    files["app/build.gradle"] = f"""
plugins {{
    id 'com.android.application'
}}

android {{
    namespace '{package_name}'
    compileSdk 35

    defaultConfig {{
        applicationId '{package_name}'
        minSdk {config.min_sdk}
        targetSdk {config.target_sdk}

        versionCode 1
        versionName '{config.version_name}'
    }}
}}

dependencies {{
    implementation 'androidx.appcompat:appcompat:1.7.0'
    implementation 'androidx.core:core:1.15.0'
    implementation 'androidx.webkit:webkit:1.12.1'
}}
""".strip()

    files[
        "app/src/main/AndroidManifest.xml"
    ] = f"""
<?xml version="1.0" encoding="utf-8"?>

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
            android:screenOrientation="{config.orientation}"
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
""".strip()

    files[
        f"app/src/main/java/{package_path}/MainActivity.java"
    ] = f"""
package {package_name};

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

public class MainActivity extends AppCompatActivity {{

    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {{

        super.onCreate(savedInstanceState);

        webView = new WebView(this);

        WebSettings settings =
                webView.getSettings();

        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);

        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        settings.setSupportZoom(false);

        webView.setWebViewClient(
                new WebViewClient()
        );

{bridge_code}

        webView.loadUrl(
                "{config.start_url}"
        );

        setContentView(webView);

{fullscreen_code}
    }}

    @Override
    public void onBackPressed() {{

        if (
            webView != null
            && webView.canGoBack()
        ) {{
            webView.goBack();
        }} else {{
            super.onBackPressed();
        }}
    }}
}}
""".strip()

    if native_bridge:

        files[
            f"app/src/main/java/{package_path}/NativeBridge.java"
        ] = f"""
package {package_name};

import android.webkit.JavascriptInterface;

public class NativeBridge {{

    @JavascriptInterface
    public String getPlatform() {{
        return "Android";
    }}

    @JavascriptInterface
    public String getVersion() {{
        return "{config.version_name}";
    }}
}}
""".strip()

    files[
        "app/src/main/res/values/strings.xml"
    ] = f"""
<?xml version="1.0" encoding="utf-8"?>

<resources>

    <string name="app_name">
        {app_name}
    </string>

</resources>
""".strip()

    files[
        "app/src/main/res/values/styles.xml"
    ] = """
<?xml version="1.0" encoding="utf-8"?>

<resources>

    <style
        name="Theme.Web2App"
        parent="Theme.AppCompat.DayNight.NoActionBar">

        <item name="android:fontFamily">
            sans
        </item>

        <item name="android:statusBarColor">
            #080b10
        </item>

        <item name="android:navigationBarColor">
            #080b10
        </item>

    </style>

</resources>
""".strip()

    return files


def generate_pwa_files(config):

    manifest = {
        "name": config.app_name,
        "short_name": config.app_name[:12],
        "start_url": config.start_url,
        "display": (
            "fullscreen"
            if config.fullscreen
            else "standalone"
        ),
        "orientation": config.orientation,
        "background_color": "#080b10",
        "theme_color": "#6d63ff",
        "icons": []
    }

    files = {
        "pwa/manifest.json": json.dumps(
            manifest,
            indent=2
        )
    }

    if config.offline_cache:

        files["pwa/sw.js"] = """
const CACHE_NAME = "web2app-lab-v1";

self.addEventListener(
    "install",
    event => {

        event.waitUntil(
            caches.open(CACHE_NAME)
                .then(cache => {
                    return cache.addAll([
                        "./"
                    ]);
                })
        );
    }
);

self.addEventListener(
    "fetch",
    event => {

        event.respondWith(
            caches.match(event.request)
                .then(cached => {

                    if (cached) {
                        return cached;
                    }

                    return fetch(event.request);
                })
        );
    }
);
""".strip()

    return files


def generate_project(payload):

    validate_url(
        payload.start_url
    )

    if not validate_package_name(
        payload.package_name
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Android package name"
        )

    if payload.min_sdk > payload.target_sdk:
        raise HTTPException(
            status_code=400,
            detail="min_sdk cannot be greater than target_sdk"
        )

    if payload.orientation not in SUPPORTED_ORIENTATIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid orientation"
        )

    project_id = str(uuid.uuid4())

    android_files = generate_android_files(
        payload
    )

    pwa_files = generate_pwa_files(
        payload
    )

    files = {}

    files.update(android_files)
    files.update(pwa_files)

    files["web2app.json"] = json.dumps(
        {
            "project_id": project_id,
            "name": payload.app_name,
            "package_name": payload.package_name,
            "start_url": payload.start_url,
            "version": payload.version_name,

            "features": {
                "fullscreen": payload.fullscreen,
                "offline_cache": payload.offline_cache,
                "push_notifications":
                    payload.push_notifications,
                "native_bridge":
                    payload.native_bridge
            },

            "sdk": {
                "min": payload.min_sdk,
                "target": payload.target_sdk
            },

            "orientation": payload.orientation
        },
        indent=2
    )

    files["README.md"] = f"""# {payload.app_name}

Generated by Web2App LAB.

## Website

{payload.start_url}

## Android

Package: `{payload.package_name}`

Version: `{payload.version_name}`

Min SDK: `{payload.min_sdk}`

Target SDK: `{payload.target_sdk}`

Orientation: `{payload.orientation}`

## Features

Fullscreen: `{payload.fullscreen}`

Offline Cache: `{payload.offline_cache}`

Push Notifications: `{payload.push_notifications}`

Native Bridge: `{payload.native_bridge}`

## Project

Project ID:

`{project_id}`

This project contains the generated Android and PWA project structure.
""".strip()

    return {
        "success": True,

        "project_id": project_id,

        "project": {
            "id": project_id,
            "name": payload.app_name,
            "package_name": payload.package_name,
            "start_url": payload.start_url,
            "version_name": payload.version_name,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        },

        "file_count": len(files),

        "files": [
            {
                "path": path,
                "size": len(
                    content.encode("utf-8")
                )
            }
            for path, content in files.items()
        ],

        "config": payload.model_dump(),

        "message": (
            "Android and PWA project "
            "structure generated successfully"
        )
    }