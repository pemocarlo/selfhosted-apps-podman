# Artifactory operations

This is the detailed runbook for the deployment described in
[README.md](README.md). Run commands as the deployment user from the
repository checkout unless a command says otherwise. Never commit runtime
environment files, credentials, generated keys, databases, uploads, or
backups.

## Health and startup

Artifactory starts several internal services and the embedded Derby database.
After a first start, restart, or image update, `active` from systemd does not
mean that HTTP is ready. Temporary `502` or `503` responses are expected.

```sh
ARTIFACTORY_HOST=artifactory.example.com
until curl -fsS "https://$ARTIFACTORY_HOST/artifactory/api/system/ping" \
  >/dev/null && \
  curl -fsS "https://$ARTIFACTORY_HOST/router/api/v1/system/health" \
  >/dev/null; do
  sleep 5
done
```

For a one-off check, print the statuses instead of waiting:

```sh
curl -ksS "https://$ARTIFACTORY_HOST/artifactory/api/system/ping"
curl -ksS "https://$ARTIFACTORY_HOST/router/api/v1/system/health"
```

Both endpoints should return `200`. Use `-k` only while diagnosing a
certificate problem; it skips certificate verification.

## JFConnect and optional UI requests

The CE image can try to fetch entitlement data even when it has no JFConnect
process. This produces repeating frontend messages such as:

```text
First-time entitlement fetch failed: 12 UNIMPLEMENTED: Received HTTP status code 404
```

The fresh-install seed disables this integration with
`jfconnect.enabled: false`. Check the runtime setting without replacing the
full generated file:

```sh
podman exec artifactory sh -c \
  'grep -n -A2 "^jfconnect:" /var/opt/jfrog/artifactory/etc/system.yaml'
```

If an existing installation still has it enabled, preserve the runtime file,
change only that setting, and restart Artifactory:

```sh
podman exec artifactory cp -p \
  /var/opt/jfrog/artifactory/etc/system.yaml \
  /var/opt/jfrog/artifactory/etc/system.yaml.before-jfconnect-disable
podman exec artifactory sed -i \
  '/^jfconnect:/{n;s/enabled: true/enabled: false/;}' \
  /var/opt/jfrog/artifactory/etc/system.yaml
scripts/selfhosted restart artifactory
```

Restore the saved file and restart if the setting must be reverted:

```sh
podman exec artifactory cp -p \
  /var/opt/jfrog/artifactory/etc/system.yaml.before-jfconnect-disable \
  /var/opt/jfrog/artifactory/etc/system.yaml
scripts/selfhosted restart artifactory
```

JFrog requires JFConnect for Curation and other entitlement-backed features.
Re-evaluate this setting before enabling one of those features or after an
image change.

The CE frontend also requests the optional ChiliPiper enrichment endpoint.
The tracked route in `gateway/conf.d/artifactory.caddy` answers the external
path with `{}` and `200`, avoiding the CE frontend's `500` popup:

```sh
curl -ksS "https://$ARTIFACTORY_HOST/ui/api/v1/enrichment/lead/chilipiper" \
  -o - -w '\nstatus=%{http_code} content_type=%{content_type}\n'
```

The same route short-circuits an allowlist of CE-missing optional MFE manifest
and app assets with an empty `404`, preserving the browser-visible result
without sending each request through Artifactory. Verify this behavior after
an image update:

```sh
curl -ksS "https://$ARTIFACTORY_HOST/ui/api/v1/onemodel/webapp/manifest.js" \
  -o /dev/null -w 'status=%{http_code} bytes=%{size_download}\n'
```

The response should be `404` with zero bytes. If a future image provides one
of these modules, remove its path from the Caddy allowlist before deploying.
All other UI, Artifactory, and Conan paths continue to use
`reverse_proxy artifactory:8082`.

Deploy and validate gateway-only changes without restarting Artifactory:

```sh
scripts/selfhosted deploy gateway production
scripts/selfhosted status gateway
scripts/selfhosted logs gateway
```

To revert the optional endpoint workarounds, remove the `@chilipiper` and
`@optional_mfe_manifest` matchers and their `handle` blocks from
`gateway/conf.d/artifactory.caddy`, then redeploy the gateway. Do not delete or
replace `services/artifactory/var`.

## Performance and resource troubleshooting

The CE image starts several Java services even for a small Conan installation.
Do not disable `metadata`, `router`, `event`, or readiness checks just to
silence routine log lines. They support normal repository operation; an
internal readiness probe commonly runs every five seconds.

Use the repository's [resource-pressure workflow](../../docs/operations.md#detecting-high-cpu-or-memory-usage)
for the full layered host, systemd, container, process, and log checks. For
Artifactory, capture these additional settings and state alongside that
workflow:

```sh
systemctl --user show artifactory.service \
  -p CPUAccounting -p CPUUsageNSec -p CPUQuotaPerSecUSec \
  -p MemoryAccounting -p MemoryCurrent -p MemoryPeak \
  -p MemoryHigh -p MemoryMax -p TasksCurrent -p TasksMax
podman stats --no-stream artifactory
podman top artifactory aux | head -25
podman exec artifactory ps -eo pid,pcpu,pmem,rss,comm --sort=-pcpu | head -25
free -h
vmstat 1 5
podman inspect artifactory --format \
  'oom_killed={{.State.OOMKilled}} memory={{.HostConfig.Memory}} cpu_quota={{.HostConfig.CpuQuota}} pids_limit={{.HostConfig.PidsLimit}}'
```

Capture at least six samples over a minute while reproducing the slow
operation. The general guide provides the sampling command; this service's
main interpretation is:

- One or two Java processes dominating CPU: correlate request logs, retries,
  background work, and user actions before changing limits.
- High Artifactory CPU while the host still has substantial idle capacity:
  do not throttle solely because the container percentage is high; it can
  exceed `100%` on a multi-core host.
- Rising `MemoryCurrent`, `MemoryPeak`, swap use, or `OOMKilled=true`: treat it
  as memory pressure and inspect logs before changing limits.
- High host usage with stable Artifactory usage: inspect other units with
  `systemd-cgtop --user` or `ps`.

The current Quadlet intentionally sets no CPU or memory cap. Do not add
`--cpus`, `--memory`, `MemoryHigh`, or `MemoryMax` as a first response: a hard
cap can turn a slow operation into an OOM kill, while a CPU quota can increase
latency. Establish a baseline, remove unnecessary traffic or retries, then
apply a tested limit only if the host capacity policy requires one.

Do not add arbitrary JVM heap or `maxOpenConnections` values to this embedded
Derby installation based only on CPU. For substantial workloads, move to
PostgreSQL and tune the Artifactory, Access, and Metadata pools together
against database capacity. See JFrog's [database tuning guidance](https://docs.jfrog.com/installation/docs/database-tuning-for-heavy-loads-in-artifactory)
and [system YAML reference](https://docs.jfrog.com/installation/docs/artifactory-system-yaml).

## Backup and restore

Back up the runtime environment and complete Artifactory state. Stop
Artifactory first so Derby is quiescent. Because the volume uses rootless
Podman's `:U` mapping, the host user may see `var` but cannot read it directly;
plain host `tar` fails with `Permission denied`. Use `podman unshare` for the
archive and extraction sides.

The archive contains credentials. Store it outside the repository with mode
`600`, and keep at least one verified copy off the VPS. This sequence creates a
backup, verifies its required entries, restores it into a temporary directory,
compares the contents, removes the temporary directory, and restarts the
service if it was active before the test:

```sh
set -Eeuo pipefail

backup_dir=~/backups/artifactory
backup_file="$backup_dir/artifactory-$(date +%Y%m%d-%H%M%S).tar.gz"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"

service_was_active=false
if systemctl --user is-active --quiet artifactory.service; then
  service_was_active=true
fi
archive_complete=false
restore_dir=""

cleanup() {
  status=$?
  if [ "$archive_complete" = false ] && [ -e "$backup_file" ]; then
    rm -f -- "$backup_file" || status=$?
  fi
  if [ -n "$restore_dir" ]; then
    podman unshare rm -rf "$restore_dir" || status=$?
  fi
  if [ "$service_was_active" = true ]; then
    systemctl --user start artifactory.service || status=$?
  fi
  exit "$status"
}
trap cleanup EXIT

if [ "$service_was_active" = true ]; then
  systemctl --user stop artifactory.service
fi

podman unshare tar -C ~/selfhosted/services -cf - artifactory | gzip -n > "$backup_file"
chmod 600 "$backup_file"
archive_complete=true

tar -tzf "$backup_file" >/dev/null
tar -tzf "$backup_file" | grep -Fx 'artifactory/artifactory.env' >/dev/null
tar -tzf "$backup_file" | grep -Eq '^artifactory/var(/|$)'

restore_dir=$(mktemp -d "$backup_dir/restore-test.XXXXXX")
podman unshare sh -c \
  'gzip -dc "$1" | tar --no-same-owner -x -C "$2"' \
  sh "$backup_file" "$restore_dir"
podman unshare cmp \
  ~/selfhosted/services/artifactory/artifactory.env \
  "$restore_dir/artifactory/artifactory.env"
podman unshare diff -qr \
  ~/selfhosted/services/artifactory/var \
  "$restore_dir/artifactory/var" >/dev/null

printf 'verified backup: %s\n' "$backup_file"
```

After the cleanup trap starts the service, wait for both HTTP health checks to
return `200`; systemd can report `active` several minutes before Artifactory
is ready.

To perform an actual restore, preserve the current state separately first,
verify the archive listing, stop Artifactory, and extract through the same
rootless namespace:

```sh
backup_file="$HOME/backups/artifactory/verified-archive.tar.gz"
set -Eeuo pipefail
tar -tzf "$backup_file" >/dev/null

restart_needed=false
restart_artifactory() {
  status=$?
  if [ "$restart_needed" = true ]; then
    systemctl --user start artifactory.service || status=$?
  fi
  exit "$status"
}
trap restart_artifactory EXIT
systemctl --user stop artifactory.service
restart_needed=true

gzip -dc "$backup_file" | podman unshare tar \
  --no-same-owner -x -C ~/selfhosted/services

systemctl --user start artifactory.service
restart_needed=false
trap - EXIT
systemctl --user is-active artifactory.service
```

Restoring overwrites the runtime environment file and `var` directory. Run the
health checks above and preserve the current state separately if the restore
may need to be undone.

## Lifecycle and updates

```sh
scripts/selfhosted status artifactory
scripts/selfhosted logs artifactory --follow
scripts/selfhosted restart artifactory
scripts/selfhosted update artifactory
```

The image uses the floating `latest` tag. Review JFrog release notes, take and
verify a backup, then update only Artifactory. Allow several minutes for the
first startup after an update. If it fails, keep `var`, inspect logs, and
restore the last verified backup rather than deleting runtime state.

For a larger or critical installation, use PostgreSQL and JFrog's documented
production architecture rather than this embedded Derby layout.
