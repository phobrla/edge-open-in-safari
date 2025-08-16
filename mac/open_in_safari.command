#!/bin/zsh
# Filename: open_in_safari.command
# Version: 1.0.0
# set -x for verbose tracing if needed
set -euo pipefail
IFS=$'\n\t'

# What it does:
# - Installs and starts a user LaunchAgent that runs open_in_safari_server.py
# - Detects Parallels vnic IPs and shows you the host IP(s), port, and token
# - Double-click friendly: no arguments required
#
# Prerequisites:
# - macOS (Apple Silicon recommended)
# - Python 3 at /usr/bin/python3 (macOS default)
# - Parallels Desktop with Parallels Tools installed
#
# How to use:
# - Double-click this .command file.
# - Follow the dialog to configure the Edge extension with Host IP / Port / Token.
#
# References:
# - LaunchAgents: https://www.launchd.info
# - Python http.server: https://docs.python.org/3/library/http.server.html

################################
# CONFIG (edit as desired)
################################
PORT=51888
BIND_ADDRESS="0.0.0.0"
# Common Parallels subnets. Keep both for vnic0/vnic1 by default.
ALLOWED_SUBNETS=("10.211.55.0/24" "10.37.129.0/24")
SHARED_TOKEN="changeme123456"

# Install a LaunchAgent to run at login
INSTALL_LAUNCH_AGENT=true

# Safety and verbosity
DRY_RUN=false
VERBOSE=true

################################
# Internals
################################
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_PY="${SCRIPT_DIR}/open_in_safari_server.py"
LAUNCH_NAME="com.phobrla.open-in-safari"
LAUNCH_PLIST="${HOME}/Library/LaunchAgents/${LAUNCH_NAME}.plist"
PYTHON_BIN="/usr/bin/python3"

log() { if [[ "${VERBOSE}" == "true" ]]; then echo "$@"; fi }
run() { if [[ "${DRY_RUN}" == "true" ]]; then echo "[DRY_RUN] $@"; else eval "$@"; fi }

ensure_python() {
  if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "Python 3 not found at ${PYTHON_BIN}. Please install Command Line Tools or Python 3." >&2
    exit 1
  fi
}

detect_vnic_ips() {
  local ips=()
  # vnic interfaces are used by Parallels
  for nic in $(ifconfig -l | tr ' ' '\n' | grep -E '^vnic[0-9]+$' || true); do
    local ip
    ip=$(ifconfig "${nic}" 2>/dev/null | awk '/inet /{print $2}')
    if [[ -n "${ip}" ]]; then
      ips+=("${ip}")
    fi
  done
  # Fallback to primary en interface if nothing found
  if [[ ${#ips[@]} -eq 0 ]]; then
    local primary
    primary=$(route -n get default 2>/dev/null | awk '/interface:/{print $2}' || true)
    if [[ -n "${primary}" ]]; then
      local ip
      ip=$(ipconfig getifaddr "${primary}" 2>/dev/null || true)
      if [[ -n "${ip}" ]]; then
        ips+=("${ip}")
      fi
    fi
  fi
  echo "${ips[@]}"
}

write_launch_agent() {
  log "Writing LaunchAgent to ${LAUNCH_PLIST}"
  local allowed_subnets_csv
  allowed_subnets_csv="$(printf "%s," "${ALLOWED_SUBNETS[@]}")"
  allowed_subnets_csv="${allowed_subnets_csv%,}"

  local stdout_log="${SCRIPT_DIR}/open_in_safari_server.out.log"
  local stderr_log="${SCRIPT_DIR}/open_in_safari_server.err.log"

  /usr/bin/tee "${LAUNCH_PLIST}" >/dev/null <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LAUNCH_NAME}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>${SERVER_PY}</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>${stdout_log}</string>
  <key>StandardErrorPath</key><string>${stderr_log}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>OIS_PORT</key><string>${PORT}</string>
    <key>OIS_BIND</key><string>${BIND_ADDRESS}</string>
    <key>OIS_TOKEN</key><string>${SHARED_TOKEN}</string>
    <key>OIS_ALLOWED_SUBNETS</key><string>${allowed_subnets_csv}</string>
    <key>OIS_VERBOSE</key><string>${VERBOSE}</string>
    <key>OIS_DRY_RUN</key><string>${DRY_RUN}</string>
  </dict>
</dict>
</plist>
PLIST
}

reload_launch_agent() {
  # Unload if exists, then load
  if launchctl print "gui/$(id -u)/${LAUNCH_NAME}" >/dev/null 2>&1; then
    log "Unloading existing LaunchAgent..."
    run launchctl bootout "gui/$(id -u)/${LAUNCH_NAME}" || true
  fi
  log "Loading LaunchAgent..."
  run launchctl bootstrap "gui/$(id -u)" "${LAUNCH_PLIST}"
  log "Kickstarting..."
  run launchctl kickstart -k "gui/$(id -u)/${LAUNCH_NAME}"
}

show_info_dialog() {
  local host_ips=("$@")
  local ips_text
  if [[ ${#host_ips[@]} -gt 0 ]]; then
    ips_text=$(printf "* %s\n" "${host_ips[@]}")
  else
    ips_text="(none detected)"
  fi

  local msg="Open in Safari helper is running.

Detected Mac host IP(s) for Parallels:
${ips_text}

Configure the Edge extension Options:
- Host: one of the IPs above (commonly 10.211.55.2)
- Port: ${PORT}
- Token: ${SHARED_TOKEN}

Then click the toolbar button or use Alt+Shift+S."
  /usr/bin/osascript <<OSA
display dialog "${msg}" with title "Open in Safari (Mac helper)" buttons {"OK"} default button "OK"
OSA
}

main() {
  ensure_python

  if [[ ! -f "${SERVER_PY}" ]]; then
    echo "Server script not found at ${SERVER_PY}" >&2
    exit 1
  fi

  mkdir -p "${HOME}/Library/LaunchAgents"

  if [[ "${INSTALL_LAUNCH_AGENT}" == "true" ]]; then
    write_launch_agent
    reload_launch_agent
  else
    log "INSTALL_LAUNCH_AGENT=false; starting server in foreground..."
    if [[ "${DRY_RUN}" == "true" ]]; then
      log "[DRY_RUN] Would run: ${PYTHON_BIN} ${SERVER_PY}"
    else
      "${PYTHON_BIN}" "${SERVER_PY}" &
      disown
    fi
  fi

  local ips
  ips=($(detect_vnic_ips))
  show_info_dialog "${ips[@]}"
}

main "$@"