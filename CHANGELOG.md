# Changelog

## v1.0.0-beta.4

- `bootstrap.sh` now installs its own prerequisites automatically: curl, Python 3, python3-venv and CA certificates (apt with lock wait, dnf, yum, zypper, apk, pacman or Homebrew). No manual step is needed before the one-line command.
- Download falls back to `wget` when `curl` is absent; a `wget` variant of the one-liner is documented. Manifest check falls back to `shasum -a 256`.
- New `--deps-only [--aws]` option; broken AWS helper venvs are recreated.
- New unit test with a simulated package manager. Installer modules unchanged.

## v1.0.0-beta.3

- Visual redesign of the README: animated SVG banner, protocol map (30 cards, 5 groups, default ports), install-flow diagram, illustrative panel mockup with **synthetic data only**, badges, GitHub alerts and a Mermaid traffic diagram.
- New GitHub Pages landing page (`docs/index.html`, Persian RTL, Vazirmatn) and docs index (`docs/README.md`).
- Community health files: issue forms with a secret-redaction warning, private security-report link, PR template, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- Reproducible artwork generator `docs/assets/build_assets.py` (embeds an OFL Vazirmatn subset).
- Install commands now reference beta.3. Installer behaviour is unchanged; fresh-host/AWS end-to-end testing is still pending.

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
