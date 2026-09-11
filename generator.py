import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from archive import create_zip
from config import SUPPORTED_ORIENTATIONS
from security import (
    safe_filename,
    validate_package_name,
    validate_url,
)
from templates import (
    ANDROID_BUILD_GRADLE,
    ANDROID_MAIN_ACTIVITY,
    ANDROID_MANIFEST,
    GRADLE_PROPERTIES,
    NATIVE_BRIDGE,
    PWA_INDEX,
    PWA_MANIFEST,
    README,
    ROOT_BUILD_GRADLE,
    SERVICE_WORKER,
    SETTINGS_GRADLE,
    STRINGS_XML,
    STYLES_XML,
    render,
)


def generate_project_files(payload):

    project_id = str(uuid.uuid4())

    package_path = payload.package_name.replace(
        ".",
        "/"
    )

    project_name = safe_filename(
        payload.app_name
    )

    fullscreen = ""

    if payload.fullscreen:
        fullscreen = """
        WindowInsetsControllerCompat controller =
                new WindowInsetsControllerCompat(
                        getWindow(),
                        getWindow().getDecorView()
                );

        controller.hide(
                WindowInsetsCompat.Type.systemBars()
        );
""".rstrip()

    bridge = ""

    if payload.native_bridge:
        bridge = render(
            NATIVE_BRIDGE,
            package_name=payload.package_name,
            version=payload.version_name
        )

        bridge = f"""
        webView.addJavascriptInterface(
                new NativeBridge(),
                "Web2AppBridge"
        );
"""

    notification_permission = ""

    if payload.push_notifications:
        notification_permission = """
    <uses-permission
        android:name="android.permission.POST_NOTIFICATIONS" />
""".rstrip()

    files = {}

    files["settings.gradle"] = render(
        SETTINGS_GRADLE,
        project_name=project_name
    )

    files["build.gradle"] = ROOT_BUILD_GRADLE

    files["gradle.properties"] = (
        GRADLE_PROPERTIES
    )

    files["app/build.gradle"] = render(
        ANDROID_BUILD_GRADLE,
        package_name=payload.package_name,
        min_sdk=payload.min_sdk,
        target_sdk=payload.target_sdk,
        version=payload.version_name
    )

    files[
        "app/src/main/AndroidManifest.xml"
    ] = render(
        ANDROID_MANIFEST,
        app_name=payload.app_name,
        orientation=payload.orientation,
        notification_permission=
            notification_permission
    )

    files[
        f"app/src/main/java/"
        f"{package_path}/MainActivity.java"
    ] = render(
        ANDROID_MAIN_ACTIVITY,
        package_name=payload.package_name,
        start_url=payload.start_url,
        bridge=bridge,
        fullscreen=fullscreen
    )

    if payload.native_bridge:

        files[
            f"app/src/main/java/"
            f"{package_path}/NativeBridge.java"
        ] = render(
            NATIVE_BRIDGE,
            package_name=payload.package_name,
            version=payload.version_name
        )

    files[
        "app/src/main/res/values/strings.xml"
    ] = render(
        STRINGS_XML,
        app_name=payload.app_name
    )

    files[
        "app/src/main/res/values/styles.xml"
    ] = STYLES_XML

    files["pwa/manifest.json"] = render(
        PWA_MANIFEST,
        app_name=payload.app_name,
        short_name=payload.app_name[:12],
        start_url=payload.start_url,
        display=(
            "fullscreen"
            if payload.fullscreen
            else "standalone"
        ),
        orientation=payload.orientation
    )

    files["pwa/index.html"] = render(
        PWA_INDEX,
        app_name=payload.app_name,
        start_url=payload.start_url
    )

    if payload.offline_cache:

        files["pwa/sw.js"] = render(
            SERVICE_WORKER,
            project_id=project_id
        )

    web2app_config = {
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
    }

    files["web2app.json"] = json.dumps(
        web2app_config,
        indent=2
    )

    files["README.md"] = render(
        README,
        app_name=payload.app_name,
        start_url=payload.start_url,
        package_name=payload.package_name,
        version=payload.version_name,
        min_sdk=payload.min_sdk,
        target_sdk=payload.target_sdk,
        orientation=payload.orientation,
        fullscreen=payload.fullscreen,
        offline_cache=payload.offline_cache,
        push_notifications=
            payload.push_notifications,
        native_bridge=payload.native_bridge
    )

    return project_id, files


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
            detail=(
                "min_sdk cannot be greater "
                "than target_sdk"
            )
        )

    if payload.orientation not in (
        SUPPORTED_ORIENTATIONS
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid orientation"
        )

    project_id, files = (
        generate_project_files(payload)
    )

    zip_data = create_zip(files)

    return {
        "success": True,

        "project_id": project_id,

        "project": {
            "id": project_id,
            "name": payload.app_name,
            "package_name":
                payload.package_name,
            "start_url":
                payload.start_url,
            "version_name":
                payload.version_name,
            "created_at":
                datetime.now(
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

        "zip_size": len(zip_data),

        "config": payload.model_dump(),

        "message": (
            "Android and PWA templates "
            "generated successfully"
        )
    }