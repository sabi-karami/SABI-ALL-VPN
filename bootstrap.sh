#!/usr/bin/env bash
set -Eeuo pipefail
VERSION=v1.0.0-beta.2
REPOSITORY=sabi-karami/SABI-ALL-VPN
if [[ ${1:-} == --help ]]; then echo 'bootstrap.sh [--aws [AWS OPTIONS] | --resume | --noninteractive]'; exit; fi
command -v curl >/dev/null || { echo 'Install curl first.'; exit 1; }
command -v python3 >/dev/null || { echo 'Install Python 3 first.'; exit 1; }
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
curl -fLsS --retry 3 "https://github.com/$REPOSITORY/archive/refs/tags/$VERSION.tar.gz" -o "$WORK/source.tgz"
tar -xzf "$WORK/source.tgz" -C "$WORK"
SRC="$WORK/${REPOSITORY##*/}-${VERSION#v}"
cd "$SRC"
sha256sum --check MANIFEST.sha256 >/dev/null
if [[ ${1:-} == --aws ]]; then
 shift
 VENV="$HOME/.local/share/sabi-allvpn/venv"
 if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv "$VENV" || { echo 'Install python3-venv, then retry.'; exit 1; }; fi
 "$VENV/bin/pip" install --disable-pip-version-check -q -r scripts/aws-requirements.txt
 "$VENV/bin/python" scripts/aws_provision.py "$@"
else
 if [[ $EUID == 0 ]]; then bash install.sh "$@"; else sudo bash install.sh "$@"; fi
fi
