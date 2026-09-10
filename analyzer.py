from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from config import (
    CONNECT_TIMEOUT,
    MAX_HTML_SIZE,
    MAX_REDIRECTS,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from security import validate_url


def absolute_url(base_url: str, value: str | None):
    if not value:
        return None

    return urljoin(base_url, value.strip())


def find_manifest(
    soup: BeautifulSoup,
    base_url: str
):
    for tag in soup.find_all("link"):
        rel = tag.get("rel", [])

        if isinstance(rel, str):
            rel = [rel]

        rel = [
            str(item).lower()
            for item in rel
        ]

        if "manifest" in rel:
            href = tag.get("href")

            if href:
                return absolute_url(
                    base_url,
                    href
                )

    return None


def find_favicon(
    soup: BeautifulSoup,
    base_url: str
):
    preferred = [
        "icon",
        "shortcut icon",
        "apple-touch-icon"
    ]

    for wanted in preferred:
        for tag in soup.find_all("link"):
            rel = tag.get("rel", [])

            if isinstance(rel, str):
                rel = [rel]

            rel = [
                str(item).lower()
                for item in rel
            ]

            if wanted in rel:
                href = tag.get("href")

                if href:
                    return absolute_url(
                        base_url,
                        href
                    )

    return urljoin(base_url, "/favicon.ico")


def find_service_worker(
    soup: BeautifulSoup
):
    for script in soup.find_all("script"):
        content = script.get_text(
            " ",
            strip=True
        )

        if (
            "serviceWorker" in content
            and "register" in content
        ):
            return True

    for script in soup.find_all(
        "script",
        src=True
    ):
        source = script.get("src", "").lower()

        if (
            "service-worker" in source
            or source.endswith("/sw.js")
            or source.endswith("sw.js")
        ):
            return True

    return False


def find_viewport(
    soup: BeautifulSoup
):
    return soup.find(
        "meta",
        attrs={
            "name": "viewport"
        }
    ) is not None


def find_theme_color(
    soup: BeautifulSoup
):
    tag = soup.find(
        "meta",
        attrs={
            "name": "theme-color"
        }
    )

    if tag:
        return tag.get("content")

    return None


async def inspect_manifest(
    manifest_url: str | None
):
    if not manifest_url:
        return None

    try:
        validate_url(manifest_url)

        timeout = httpx.Timeout(
            REQUEST_TIMEOUT,
            connect=CONNECT_TIMEOUT
        )

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={
                "User-Agent": USER_AGENT
            }
        ) as client:

            response = await client.get(
                manifest_url
            )

        if response.status_code >= 400:
            return None

        data = response.json()

        return {
            "name": data.get("name"),
            "short_name": data.get("short_name"),
            "display": data.get("display"),
            "start_url": data.get("start_url"),
            "theme_color": data.get(
                "theme_color"
            ),
            "background_color": data.get(
                "background_color"
            ),
            "icons": len(
                data.get("icons", [])
            )
        }

    except Exception:
        return None


async def fetch_website(
    url: str
):
    current_url = validate_url(url)

    timeout = httpx.Timeout(
        REQUEST_TIMEOUT,
        connect=CONNECT_TIMEOUT
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        headers={
            "User-Agent": USER_AGENT
        }
    ) as client:

        for _ in range(MAX_REDIRECTS + 1):

            current_url = validate_url(
                current_url
            )

            response = await client.get(
                current_url
            )

            if response.status_code in {
                301,
                302,
                303,
                307,
                308
            }:

                location = response.headers.get(
                    "location"
                )

                if not location:
                    break

                current_url = urljoin(
                    str(response.url),
                    location
                )

                continue

            return response, current_url

    raise HTTPException(
        status_code=400,
        detail="Too many redirects"
    )


async def analyze_website(
    url: str
):
    response, final_url = await fetch_website(
        url
    )

    content_type = response.headers.get(
        "content-type",
        ""
    ).lower()

    if "text/html" not in content_type:
        raise HTTPException(
            status_code=400,
            detail="The URL does not return an HTML page"
        )

    html = response.text

    if len(html.encode("utf-8")) > MAX_HTML_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Website HTML is too large"
        )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    parsed = urlparse(final_url)

    title = ""

    if soup.title:
        title = soup.title.get_text(
            strip=True
        )

    description_tag = soup.find(
        "meta",
        attrs={
            "name": "description"
        }
    )

    description = ""

    if description_tag:
        description = (
            description_tag.get("content")
            or ""
        )

    manifest_url = find_manifest(
        soup,
        final_url
    )

    service_worker = find_service_worker(
        soup
    )

    favicon = find_favicon(
        soup,
        final_url
    )

    viewport = find_viewport(
        soup
    )

    theme_color = find_theme_color(
        soup
    )

    manifest_data = await inspect_manifest(
        manifest_url
    )

    pwa = bool(
        manifest_url
        and service_worker
    )

    recommendations = []

    if parsed.scheme != "https":
        recommendations.append(
            "Enable HTTPS for production"
        )

    if not manifest_url:
        recommendations.append(
            "Add a Web App Manifest"
        )

    if not service_worker:
        recommendations.append(
            "Add a Service Worker"
        )

    if not viewport:
        recommendations.append(
            "Add a mobile viewport meta tag"
        )

    if not recommendations:
        recommendations.append(
            "Website is ready for Web2App conversion"
        )

    return {
        "success": True,

        "analyzed_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "url": final_url,
        "original_url": url,

        "protocol": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,

        "secure": parsed.scheme == "https",

        "status_code": response.status_code,
        "content_type": content_type,

        "title": title,
        "description": description,

        "pwa": pwa,

        "manifest": bool(manifest_url),
        "manifest_url": manifest_url,
        "manifest_data": manifest_data,

        "service_worker": service_worker,

        "favicon": favicon,

        "viewport": viewport,
        "theme_color": theme_color,

        "stats": {
            "images": len(
                soup.find_all("img")
            ),
            "links": len(
                soup.find_all("a")
            ),
            "scripts": len(
                soup.find_all("script")
            ),
            "stylesheets": len(
                soup.find_all(
                    "link",
                    attrs={
                        "rel": "stylesheet"
                    }
                )
            ),
            "html_size": len(
                html.encode("utf-8")
            )
        },

        "recommendations": recommendations
    }