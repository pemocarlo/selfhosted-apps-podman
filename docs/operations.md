# Operations

See the root [README](../README.md) for setup and [manual installation](manual.md) for direct commands.

## Quadlet operation

After changing a Quadlet:

```sh
systemctl --user daemon-reload
systemctl --user restart <name>.service
```

To inspect generated units or generator errors:

```sh
systemd-analyze --user --generators=true verify <name>.service
/usr/lib/systemd/system-generators/podman-system-generator --user --dryrun
systemctl --user cat <name>.service
```

Do not enable generated Quadlet services with `systemctl`; the generator applies their `[Install]` sections. `scripts/selfhosted disable <name>` removes definitions but preserves application data.

## Checks and troubleshooting

```sh
bash -n scripts/selfhosted
git diff --check
scripts/selfhosted check
scripts/selfhosted status all
journalctl --user -u <name>.service -f
podman logs <container>
podman network inspect caddy-public
```

For a missing unit, inspect generator output. For an unreachable site, check DNS, firewall rules, ports 80/443, the hostname in `~/selfhosted/gateway/caddy.env`, container status, and the Caddy upstream name. Caddy stores certificates under `~/selfhosted/gateway/data`; keep the server clock correct.

## Updates

```sh
scripts/selfhosted update <name>
scripts/selfhosted update all
```

Updates pull registry images and restart only the selected component. Pinned tags change only when the Quadlet changes; floating tags may introduce breaking changes. Back up before upgrades.

Quadlets contain `AutoUpdate=`, but automatic updates are not enabled by this repository. If you intentionally want unattended updates, enable the user timer with `systemctl --user enable --now podman-auto-update.timer` only after establishing tested backups and rollback procedures.

## Backups

Back up runtime state, not generated containers:

- `~/selfhosted/gateway/{data,config,caddy.env}`
- `~/selfhosted/services/` (env files and every app data directory)

Stop a single app or use its database-native backup tool for a consistent database snapshot. Test restores regularly; a backup that has never been restored is unverified.
