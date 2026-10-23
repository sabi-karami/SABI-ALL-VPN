# Verification scope

Release: v1.0.0-beta.4

beta.4: `bootstrap.sh` installs missing prerequisites itself (unit-tested with a simulated apt-get on a PATH without python3/curl; idempotent second run). Real package installation on each distribution is not CI-tested. Installer modules are unchanged since beta.2.

Implemented automated checks:
- Bash syntax for all shell files.
- Python parsing for all Python files.
- Core JSON heredoc rendering with synthetic credentials.
- Generated Xray and sing-box server configs were accepted by the installed pinned-version binaries in config-check mode (no listeners started).
- Synthetic catalog rendering verifies every placeholder resolves.
- 30-card template shape and per-card instructions.
- No live-identity/credential material expected in public source.
- No shell xtrace in runtime modules.
- Bootstrap prerequisite auto-install (simulated package manager).
- Panel authentication, unauthorized download rejection, origin/CSRF checks, logout/session invalidation and 7/8-character password boundary.
- JavaScript syntax and source manifest in GitHub Actions.

Not yet verified end-to-end:
- A complete fresh Ubuntu install of this consolidated release.
- Full AWS resource creation plus bootstrap using the new provisioning script.
- Every client/protocol from every ISP and device.
- Rollback/restore of an entire host.

The original deployed panel was browser-tested at desktop and 390px mobile widths; that test does not establish that all future fresh installations work. Status checks only show running services and panel HTTPS. Treat this as a beta and test first on a disposable VM. CI creates no cloud resources and uses no production credentials.
