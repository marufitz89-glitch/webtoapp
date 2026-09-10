APP_NAME = "Web2App LAB"
APP_VERSION = "2.0.0"

HOST = "0.0.0.0"
PORT = 8000

REQUEST_TIMEOUT = 15.0
CONNECT_TIMEOUT = 8.0

MAX_HTML_SIZE = 5 * 1024 * 1024
MAX_REDIRECTS = 5

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; Web2App-LAB/2.0; "
    "+https://web2app.local)"
)

SUPPORTED_SCHEMES = {
    "http",
    "https"
}

SUPPORTED_ORIENTATIONS = {
    "portrait",
    "landscape",
    "unspecified"
}