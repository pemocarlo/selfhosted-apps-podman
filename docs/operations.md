# Operations

See the root [README](../README.md) for setup and [manual operation](manual.md) for direct commands and lifecycle explanations.

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

Lifecycle commands affect only the selected app:

```sh
scripts/selfhosted add <name>       # first install
scripts/selfhosted disable <name>   # temporary; deploy all keeps skipping it
scripts/selfhosted enable <name>    # restore a disabled or removed app
scripts/selfhosted remove <name>    # uninstall units; keep config and data
scripts/selfhosted restart <name>   # no image pull
```

`remove` is intentionally non-destructive. Delete runtime data only through a deliberate, separately verified manual operation after testing a backup.

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

## Detecting high CPU or memory usage

Start with a short trend rather than a single `top` snapshot. Check the host,
the user-systemd unit, the container, and the processes inside the container:

```sh
APP=grocy
CONTAINER=grocy
nproc
free -h
vmstat 1 5
systemctl --user show "$APP.service" \
  -p CPUAccounting -p CPUUsageNSec -p CPUQuotaPerSecUSec \
  -p MemoryAccounting -p MemoryCurrent -p MemoryPeak \
  -p MemoryHigh -p MemoryMax -p TasksCurrent -p TasksMax
podman stats --no-stream "$CONTAINER"
podman top "$CONTAINER" aux
podman exec "$CONTAINER" ps -eo pid,pcpu,pmem,rss,comm --sort=-pcpu | head -25
```

For a trend, sample at least five times over a minute:

```sh
for sample in 1 2 3 4 5 6; do
  date -Is
  podman stats --no-stream --format \
    'cpu={{.CPUPerc}} mem={{.MemUsage}} pids={{.PIDs}}' "$CONTAINER"
  [ "$sample" = 6 ] || sleep 10
done
```

Interpret the results together:

- A high container CPU percentage with one or two dominant processes points to
  application workload, requests, background jobs, or retries. Inspect request
  logs and recent errors before applying a CPU limit. Container CPU can exceed
  `100%` on a multi-core host.
- Compare container CPU with `vmstat` idle time and `nproc`: a container can
  report substantial CPU while the host still has ample idle capacity.
- Rising `MemoryCurrent`, a high `MemoryPeak`, swap activity, or an
  `OOMKilled` state indicates memory pressure. Check `free -h`,
  `podman inspect "$CONTAINER" --format '{{.State.OOMKilled}}'`, and the
  service journal.
- High host usage with stable container usage points to another service. Use
  `systemd-cgtop --user` or `ps` to find it.
- Repeated readiness checks, expected `404`s for optional UI assets, or routine
  log lines are not automatically faults. Count them over time and correlate
  them with CPU, latency, and user-visible failures.

Do not add `--cpus`, `--memory`, `MemoryHigh`, or `MemoryMax` as a first
response. A hard cap can turn a slow service into an OOM-killed service, and a
CPU quota can hide the workload while increasing request latency. Establish a
baseline, address unnecessary traffic or retries, then apply a tested limit
only when the host's capacity policy requires one. Use `systemctl --user` for
the normal lifecycle; a direct `podman stop` may be undone by `Restart=always`.

See Podman's [`stats` reference](https://docs.podman.io/en/latest/markdown/podman-stats.1.html)
for available metrics and its [`run` resource options](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
before adding a CPU, memory, or PID limit.

## Updates

```sh
scripts/selfhosted update <name>
scripts/selfhosted update all
```

Updates pull registry images and restart only the selected component. Pinned tags change only when the Quadlet changes; floating tags may introduce breaking changes. Back up before upgrades.

To apply repository definition or documentation changes, update the checkout separately and deploy the affected component:

```sh
git pull --ff-only
scripts/selfhosted check
scripts/selfhosted deploy <name>
# Or apply the gateway plus every already-installed app:
scripts/selfhosted deploy all production
```

`update` means “pull container images”; it does not run `git pull`. Deploy records which Quadlet and gateway configuration files it manages, so a later deploy or disable can remove obsolete definitions without touching manually added files or runtime data.

Quadlets contain `AutoUpdate=`, but automatic updates are not enabled by this repository. If you intentionally want unattended updates, enable the user timer with `systemctl --user enable --now podman-auto-update.timer` only after establishing tested backups and rollback procedures.

## Backups

Back up runtime state, not generated containers:

- `~/selfhosted/gateway/{data,config,caddy.env}`
- `~/selfhosted/services/` (env files and every app data directory)

Stop a single app or use its database-native backup tool for a consistent database snapshot. Test restores regularly; a backup that has never been restored is unverified.
Artifactory uses a rootless `:U` volume, so follow its
[detailed operations runbook](../services/artifactory/OPERATIONS.md) for the
required `podman unshare` backup and restore workflow; a plain host `tar` cannot
read that state directory.
