# Network / port inventory

IPv4 dedicated VM. No TCP/UDP wildcard range is opened by the AWS helper. Outbound traffic follows the default SG egress policy. Host rules are additive, not a firewall reset.

| Service | Transport / port | Path |
|---|---|---|
| ACME HTTP-01 (manual DNS) | TCP 80 | Direct |
| Xray REALITY | TCP 443 | Direct |
| Hysteria2 | UDP 443 | Direct |
| VLESS WS | TCP 2053 | CDN |
| VLESS XHTTP | TCP 2083 | CDN |
| VMess WS | TCP 2087 | CDN |
| Trojan WS | TCP 2096 | CDN |
| sing-box REALITY | TCP 3443 | Direct |
| MTProto | TCP 4433 | Direct |
| OpenConnect | TCP/UDP 4443 | Direct |
| SoftEther / SSTP | TCP 5555, TCP 992 | Direct |
| Tor obfs4 | TCP 7443 | Direct |
| Shadowsocks 2022 | TCP/UDP 8388 | Direct |
| Trojan TLS | TCP 8443 | Direct |
| TUIC | UDP 8443 | Direct |
| ShadowTLS | TCP 9443 | Direct |
| Private panel | TCP 9444 | Direct; authenticated |
| Naive | TCP/UDP 10443 | Direct |
| AnyTLS | TCP 11443 | Direct |
| OpenVPN | TCP/UDP 1194 | Direct |
| IPsec | UDP 500/4500 | NAT-T |
| WireGuard | UDP 51820 | Direct |
| AmneziaWG | UDP 51821 | Direct |
| dnstt | UDP 53 redirected to 5300 | Authoritative delegated DNS |
| SSH SOCKS tunnel | TCP 22 | Key-only tunnel user; no shell |
| Optional PPTP | TCP 1723 + GRE protocol 47 | Legacy, unsafe |
| Optional SOCKS/HTTP | TCP 1080 | Unencrypted transport |

Never expose loopback-only ports 19771 (panel backend), 18388, 1081, 2001, 9050/9001. Do not expose plain L2TP UDP 1701 without IPsec. WireGuard/AWG/OpenVPN client files target IPv4; IPv6 routing/leak prevention must be handled on clients. Other cloud providers require their own firewall/security-group configuration in addition to host iptables.
