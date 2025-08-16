#!/usr/bin/env python3
# Filename: open_in_safari_server.py
# Version: 1.0.0
#
# What it does:
# - Runs a small HTTP server on macOS that accepts requests from your Windows VM (Parallels)
#   to open a URL in Safari.
# - Secured by:
#   * Allowed subnets (Parallels vnic ranges by default)
#   * Shared token (HTTP header)
#   * CORS enabled for extension use
#
# Prerequisites:
# - macOS (Apple Silicon recommended), Python 3 (/usr/bin/python3)
# - Parallels Desktop with Parallels Tools installed
#
# How to use:
# - Double-click mac/open_in_safari.command to install and start this server as a LaunchAgent.
# - In Edge (Windows), load the extension and set options to match PORT/TOKEN and your Mac host IP.
#
# Dependencies:
# - Python standard library only (http.server, socketserver, ipaddress, json, subprocess)
#
# Pip (not needed for stdlib-only script):
# 1) cd ~/Documents && source myenv/bin/activate && pip install (none required)
# 2) pip install (none required)

import http.server
import socketserver
import socket
import json
import subprocess
import sys
import os
import ipaddress
from urllib.parse import parse_qs

# =========================
# CONFIG (overridden by env)
# =========================
CONFIG = {
    "PORT": 51888,
    "BIND_ADDRESS": "0.0.0.0",
    "ALLOWED_SUBNETS": ["10.211.55.0/24", "10.37.129.0/24"],
    "SHARED_TOKEN": "changeme123456",
    "DRY_RUN": False,
    "VERBOSE": True,
}

# Environment overrides (set by LaunchAgent)
def load_env_overrides():
    port = os.environ.get("OIS_PORT")
    bind = os.environ.get("OIS_BIND")
    token = os.environ.get("OIS_TOKEN")
    subnets = os.environ.get("OIS_ALLOWED_SUBNETS")
    if port:
        try:
            CONFIG["PORT"] = int(port)
        except ValueError:
            pass
    if bind:
        CONFIG["BIND_ADDRESS"] = bind
    if token:
        CONFIG["SHARED_TOKEN"] = token
    if subnets:
        CONFIG["ALLOWED_SUBNETS"] = [s.strip() for s in subnets.split(",") if s.strip()]
    CONFIG["DRY_RUN"] = os.environ.get("OIS_DRY_RUN", "false").lower() == "true"
    CONFIG["VERBOSE"] = os.environ.get("OIS_VERBOSE", "true").lower() == "true"

load_env_overrides()

VERSION = "1.0.0"

def log(msg):
    if CONFIG["VERBOSE"]:
        print(msg, flush=True)

def redacted_token():
    t = CONFIG["SHARED_TOKEN"]
    if not t:
        return "<empty>"
    if len(t) <= 4:
        return "***"
    return t[:2] + "***" + t[-2:]

def client_allowed(client_ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for cidr in CONFIG["ALLOWED_SUBNETS"]:
        try:
            if ip_obj in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False

def open_in_safari(url: str) -> (bool, str):
    # Validate scheme
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "Only http/https URLs are permitted."
    if CONFIG["DRY_RUN"]:
        log(f"[DRY_RUN] Would open in Safari: {url}")
        return True, "DRY_RUN: OK"
    try:
        # Use the 'open' tool to send URL to Safari
        # 'open -a Safari <url>' opens in a new tab/window as configured
        res = subprocess.run(
            ["/usr/bin/open", "-a", "Safari", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if res.returncode != 0:
            return False, res.stderr.strip() or "Unknown error from 'open'"
        return True, "Opened in Safari"
    except Exception as e:
        return False, str(e)

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = f"OpenInSafariServer/{VERSION}"

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-OpenInSafari-Token")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            # try form-encoded
            try:
                data = parse_qs(raw.decode("utf-8"))
                return {k: v[0] for k, v in data.items()}
            except Exception:
                return {}

    def _reject(self, code: int, msg: str):
        try:
            self.send_response(code)
            self._set_cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": msg}).encode("utf-8"))
        except BrokenPipeError:
            pass

    def _ok(self, payload: dict):
        try:
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        except BrokenPipeError:
            pass

    def _extract_token(self) -> str:
        return self.headers.get("X-OpenInSafari-Token", "")

    def _client_ip(self) -> str:
        return self.client_address[0]

    def do_GET(self):
        if self.path.startswith("/ping"):
            client_ip = self._client_ip()
            token_ok = (self._extract_token() == CONFIG["SHARED_TOKEN"]) if CONFIG["SHARED_TOKEN"] else True
            allowed = client_allowed(client_ip)
            payload = {
                "ok": bool(token_ok and allowed),
                "version": VERSION,
                "client_ip": client_ip,
                "allowed": allowed,
                "token_ok": bool(token_ok)
            }
            self._ok(payload)
            return
        self._reject(404, "Not Found")

    def do_POST(self):
        client_ip = self._client_ip()
        if not client_allowed(client_ip):
            log(f"DENY: client {client_ip} not in allowed subnets {CONFIG['ALLOWED_SUBNETS']}")
            return self._reject(403, "Forbidden: Client IP not allowed")
        if CONFIG["SHARED_TOKEN"]:
            token = self._extract_token()
            if token != CONFIG["SHARED_TOKEN"]:
                log("DENY: token mismatch [redacted]")
                return self._reject(401, "Unauthorized: Bad token")
        if self.path.startswith("/open"):
            data = self._read_json()
            url = (data.get("url") or "").strip()
            if not url:
                return self._reject(400, "Missing 'url'")
            ok, msg = open_in_safari(url)
            if ok:
                log(f"OK: {client_ip} -> {url}")
                return self._ok({"ok": True, "message": msg})
            else:
                log(f"ERR: {client_ip} -> {url}: {msg}")
                return self._reject(500, msg)
        return self._reject(404, "Not Found")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def main():
    bind = CONFIG["BIND_ADDRESS"]
    port = CONFIG["PORT"]
    try:
        httpd = ThreadingHTTPServer((bind, port), Handler)
    except OSError as e:
        print(f"Failed to bind {bind}:{port}: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    # Determine server addresses
    try:
        host_name = socket.gethostname()
    except Exception:
        host_name = "unknown"

    print("Open in Safari Server", flush=True)
    print(f"Version: {VERSION}", flush=True)
    print(f"Listening on {bind}:{port}", flush=True)
    print(f"Allowed subnets: {', '.join(CONFIG['ALLOWED_SUBNETS'])}", flush=True)
    print(f"Token: {redacted_token()}", flush=True)
    print(f"Hostname: {host_name}", flush=True)
    print("Endpoints: POST /open, GET /ping", flush=True)

    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    main()