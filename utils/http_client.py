"""Shared HTTP request utilities to eliminate duplicated urllib boilerplate."""

import json
import urllib.request
import urllib.error
import urllib.parse
import uuid


def http_json_request(url, method="GET", payload=None, headers=None, timeout=30):
    """Send an HTTP request with JSON body and return parsed JSON response.

    Args:
        url: Full request URL.
        method: HTTP method (GET or POST). POST is used automatically if payload is given.
        payload: Optional dict to send as JSON body.
        headers: Optional dict of additional headers.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response as dict, or {"ok": False, "error": ...} on failure.
    """
    try:
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}: {e.reason}")
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            return error_body
        except Exception:
            return {"ok": False, "error": f"{e.code} {e.reason}"}
    except Exception as e:
        print(f"Request error for {url}: {e}")
        return {"ok": False, "error": str(e)}


def http_multipart_request(url, params=None, files=None, timeout=60):
    """Send a multipart/form-data request (used for file uploads).

    Args:
        url: Full request URL.
        params: Dict of text form fields.
        files: Dict where key is field name and value is
               {"filename": str, "content": bytes, "content_type": str}.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response as dict, or {"ok": False, "error": ...} on failure.
    """
    try:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        body = b""

        for name, value in (params or {}).items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            body += str(value).encode("utf-8") + b"\r\n"

        for name, file_info in (files or {}).items():
            filename = file_info["filename"]
            content = file_info["content"]
            content_type = file_info.get("content_type", "application/octet-stream")
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            body += f"Content-Type: {content_type}\r\n\r\n".encode()
            body += content + b"\r\n"

        body += f"--{boundary}--\r\n".encode()

        req = urllib.request.Request(url, data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}: {e.reason}")
        return {"ok": False, "error": f"{e.code} {e.reason}"}
    except Exception as e:
        print(f"Multipart request error for {url}: {e}")
        return {"ok": False, "error": str(e)}


def download_url(url, timeout=10, headers=None):
    """Download raw bytes from a URL.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.
        headers: Optional dict of request headers.

    Returns:
        Bytes content on success, None on failure.
    """
    try:
        req_headers = {"User-Agent": "Mozilla/5.0"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except Exception as e:
        print(f"Download error for {url}: {e}")
        return None
