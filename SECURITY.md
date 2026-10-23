# Security policy / سیاست امنیت

- Never commit `auth.json`, client private keys, `.env`, cloud tokens, access notes or private ZIPs.
- Public releases contain **source only**. The public repository has no live VPN credentials.
- Every fresh install generates random VPN and initial panel credentials. Panel passwords are stored as a scrypt hash; existing sessions are invalidated after a password change.
- The panel allows an 8-character minimum by owner request. A long unique passphrase is safer; the initial password is substantially longer. This release has no MFA.
- Secure/HttpOnly/SameSite session cookies, CSRF checks, same-origin writes, login throttling, private route checks and no-store are included. These do not constitute an independent security audit.
- The panel deliberately exposes server-level VPN secrets to its authenticated owner. Anyone with panel access can download sensitive server configs. Protect the login and administrative network CIDR.
- Root is needed for tunneling and networking; several network daemons run as root in this initial compatibility-focused release. Treat this as a substantial attack surface. Do not co-host unrelated sensitive workloads.
- PPTP and unencrypted SOCKS/HTTP are opt-in and unsafe for sensitive data. No anonymity, leak-free behavior or universal censorship resistance is promised.
- CF API token remains root-only on the server for DNS-01 certificate renewal. API keys are NOT included in exports or panel.
- AWS bootstrap secret is temporarily carried in SSM SecureString, not EC2 user-data; it is deleted after use/failure. Managed resources remain billable on failed provisioning until explicitly removed.
- Dependencies: hashes pinned for major binary assets; source revisions pinned for custom builds; apt and some nested IPsec dependencies can change. Review upstream software and its licenses. SHA checks do not replace code review or signing.
- Report sensitive findings through GitHub private vulnerability reporting if enabled; never post credentials in public issues. Rotate exposed keys immediately.
