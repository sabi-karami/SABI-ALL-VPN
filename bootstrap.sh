#!/usr/bin/env bash
# SABI ALL VPN bootstrap.
# Installs its own prerequisites (curl, Python 3, venv, CA certificates) when missing,
# downloads the pinned release, verifies MANIFEST.sha256 and starts the installer.
set -Eeuo pipefail
VERSION=v1.0.0-beta.4
REPOSITORY=sabi-karami/SABI-ALL-VPN
MODE=server
DEPS_ONLY=no
case "${1:-}" in
 --help) echo 'bootstrap.sh [--aws [AWS OPTIONS] | --resume | --noninteractive | --deps-only [--aws]]'; exit;;
 --deps-only) DEPS_ONLY=yes; shift; if [[ ${1:-} == --aws ]]; then MODE=aws; fi;;
 --aws) MODE=aws;;
esac
say(){ printf '[SABI] %s\n' "$*" >&2; }
die(){ printf '[SABI] ERROR: %s\n' "$*" >&2; exit 1; }
as_root(){
 if [[ $EUID -eq 0 ]]; then "$@"
 elif command -v sudo >/dev/null 2>&1; then sudo "$@"
 else die "Root or sudo is needed to install: $*"; fi
}
have_fetch(){ command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1; }
venv_ok(){
 command -v python3 >/dev/null 2>&1 || return 1
 local t; t=$(mktemp -d)
 if python3 -m venv "$t/v" >/dev/null 2>&1 && [[ -x "$t/v/bin/pip" ]]; then rm -rf "$t"; return 0; fi
 rm -rf "$t"; return 1
}
missing(){
 local m=""
 have_fetch || m="$m curl"
 command -v python3 >/dev/null 2>&1 || m="$m python"
 if [[ $MODE == aws ]] && ! venv_ok; then m="$m venv"; fi
 echo "$m"
}
install_prereqs(){
 local need; need=$(missing)
 [[ -n "$need" ]] || return 0
 say "Installing missing prerequisites:$need"
 if command -v apt-get >/dev/null 2>&1; then
  local p="ca-certificates"
  case "$need" in *curl*) p="$p curl";; esac
  case "$need" in *python*|*venv*) p="$p python3 python3-venv";; esac
  as_root env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=300 update -qq
  # shellcheck disable=SC2086
  as_root env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=300 install -y -qq --no-install-recommends $p
 elif command -v dnf >/dev/null 2>&1; then as_root dnf install -y ca-certificates curl python3
 elif command -v yum >/dev/null 2>&1; then as_root yum install -y ca-certificates curl python3
 elif command -v zypper >/dev/null 2>&1; then as_root zypper -n install ca-certificates curl python3
 elif command -v apk >/dev/null 2>&1; then as_root apk add --no-cache ca-certificates curl python3
 elif command -v pacman >/dev/null 2>&1; then as_root pacman -Sy --noconfirm --needed ca-certificates curl python
 elif command -v brew >/dev/null 2>&1; then brew install python curl
 else die "No supported package manager found. Install curl and python3 (with venv) manually, then retry."
 fi
 hash -r
 need=$(missing)
 [[ -z "$need" ]] || die "Prerequisites still missing:$need"
 say "Prerequisites ready."
}
fetch(){
 if command -v curl >/dev/null 2>&1; then curl -fLsS --retry 3 "$1" -o "$2"
 else wget -q --tries=3 -O "$2" "$1"; fi
}
check_manifest(){
 if command -v sha256sum >/dev/null 2>&1; then sha256sum --check MANIFEST.sha256 >/dev/null
 else shasum -a 256 -c MANIFEST.sha256 >/dev/null; fi
}
install_prereqs
if [[ $DEPS_ONLY == yes ]]; then exit 0; fi
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
fetch "https://github.com/$REPOSITORY/archive/refs/tags/$VERSION.tar.gz" "$WORK/source.tgz"
tar -xzf "$WORK/source.tgz" -C "$WORK"
SRC="$WORK/${REPOSITORY##*/}-${VERSION#v}"
cd "$SRC"
check_manifest
if [[ $MODE == aws ]]; then
 shift
 VENV="$HOME/.local/share/sabi-allvpn/venv"
 if [[ ! -x "$VENV/bin/pip" ]]; then rm -rf "$VENV"; python3 -m venv "$VENV"; fi
 "$VENV/bin/pip" install --disable-pip-version-check -q -r scripts/aws-requirements.txt
 "$VENV/bin/python" scripts/aws_provision.py "$@"
else
 if [[ $EUID == 0 ]]; then bash install.sh "$@"; else sudo bash install.sh "$@"; fi
fi
