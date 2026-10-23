# Changelog

## v1.0.0-beta.2

- Rename repository to `SABI-ALL-VPN` at the owner's request.
- Update public URLs and bootstrap source-directory handling for the new repository name.
- Use beta.2 commands in the README; beta.1 is retained as historical source.
- Installation features, secret handling and validation limitations are unchanged.

## v1.0.0-beta.1

- Two bootstraps: existing dedicated Ubuntu host, or AWS provisioning followed by the same installation.
- Parameterized domain, IP, Cloudflare records and independent per-install secrets.
- Consolidated original setup corrections: sing-box REALITY listener on 3443; VMess AES-128-GCM; correct XHTTP client separation; optional Naive client configuration; SoftEther RSA certificate and ADMINHUB; no vpncmd symlink; Telegram fronting on 4443; DNS delegation; renewal hooks.
- Authenticated Persian panel, click-to-copy, per-protocol guides, private files, safe default secret hiding, username sabi, minimum password length 8.
- Root-only logs/ZIP, public-source secret exclusion, checkpoints and background service install.
- PPTP and raw SOCKS/HTTP optional and off by default.
- Unit/CI validation; fresh-host/AWS integrated testing remains pending.
