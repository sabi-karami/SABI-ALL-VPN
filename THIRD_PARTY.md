# Third-party attribution

This orchestrator integrates upstream software without claiming authorship or security audit of those projects. Upstream licenses apply to their binaries, scripts and dependencies:

- Xray / XTLS: https://github.com/XTLS/Xray-core
- sing-box / SagerNet: https://github.com/SagerNet/sing-box
- WireGuard: https://www.wireguard.com/
- AmneziaWG Go and tools: https://github.com/amnezia-vpn
- OpenVPN: https://github.com/OpenVPN/openvpn
- IPsec installation: Lin Song (hwdsl2), https://github.com/hwdsl2/setup-ipsec-vpn — CC BY-SA 3.0; downloaded at install time, attribution retained. The orchestrator selects a pinned Ubuntu script and pins its extras URLs; downstream packages/downloads may not all be pinned.
- Libreswan: https://github.com/libreswan/libreswan
- OpenConnect / ocserv: https://gitlab.com/openconnect/ocserv
- SoftEther VPN Stable: https://github.com/SoftEtherVPN/SoftEtherVPN_Stable
- accel-ppp: https://github.com/accel-ppp/accel-ppp
- mtg / 9seconds: https://github.com/9seconds/mtg
- Tor / obfs4: https://www.torproject.org/
- dnstt / David Fifield: https://www.bamsoftware.com/software/dnstt/
- Nginx, Certbot, OpenSSH and Ubuntu distribution packages retain their respective licenses.
- Vazirmatn Persian font by Saber Rastikerdar and contributors: https://github.com/rastikerdar/vazirmatn — SIL Open Font License 1.1, see `panel/static/OFL.txt`.
- Flask / Werkzeug and Gunicorn retain their respective licenses.

Review `versions.lock.json` and upstream licensing before redistribution. Public release archives contain the custom orchestration and panel, not private deployment configs.
