#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export DEBIAN_FRONTEND=noninteractive
ROOT=/root/allvpn
STATE=/var/lib/sabi-allvpn
source /etc/sabi-allvpn/install.env
export PATH=/usr/local/go/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
if [[ -f "$ROOT/secrets.env" ]]; then set -a; source "$ROOT/secrets.env"; set +a; fi
fail(){ printf '%s\n' "ERROR: $*" >&2; exit 1; }
clone_pinned(){
 local url=$1 dir=$2 sha=$3
 if [[ ! -d "$dir/.git" ]]; then mkdir -p "$dir"; git -C "$dir" init -q; git -C "$dir" remote add origin "$url"; fi
 git -C "$dir" fetch -q --depth 1 origin "$sha"
 git -C "$dir" checkout -q --detach "$sha"
 test "$(git -C "$dir" rev-parse HEAD)" = "$sha"
}
require_service(){ systemctl is-active --quiet "$1" || fail "Service is not active: $1 (journalctl -u $1)"; }
