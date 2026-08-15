# Artifactory CE for C/C++

JFrog Artifactory Community Edition for C/C++ provides a Conan repository,
web UI, permissions, and APIs. It is the team-oriented option in this
repository. The image uses the embedded Derby database for a small, single-node
installation.

## Before deployment

- Check JFrog's [system requirements](https://docs.jfrog.com/installation/docs/artifactory-system-requirements-and-platform-support); Artifactory is resource-intensive.
- Decide the public hostname and set `ARTIFACTORY_SITE_ADDRESS` in the gateway env file.
- Plan a backup of `~/selfhosted/services/artifactory/var` before the first update.

## Deploy and configure

Set the production hostname in `~/selfhosted/gateway/caddy.env`, deploy the
gateway first so that the shared network exists, and then deploy Artifactory:

```sh
sed -i 's/^ARTIFACTORY_SITE_ADDRESS=.*/ARTIFACTORY_SITE_ADDRESS=artifactory.example.com/' \
  ~/selfhosted/gateway/caddy.env
scripts/selfhosted deploy gateway production
scripts/selfhosted deploy artifactory
```

On the first login, complete the onboarding wizard: change the default
`admin` / `password` credentials and set the base URL to the public HTTPS
hostname. In the CE image, create the local Conan repository from the UI:
Administration → Repositories → Add Repository → Local → Conan. The generic
repository REST API is Pro-only in this edition. The password can be changed
later in the Administration UI, but the default password must not be left in
use.

Configure a Conan client using the repository URL shown by Artifactory:

```sh
conan remote add artifactory https://artifactory.example.com/artifactory/api/conan/conan-local
conan remote login artifactory <user>
```

## This installation

The VPS is configured with:

- runtime state: `~/selfhosted/services/artifactory/var`
- gateway route: `artifactory:8082` on the shared `caddy-public` network
- image: `releases-docker.jfrog.io/jfrog/artifactory-cpp-ce:latest`

The working deployment order is:

```sh
scripts/selfhosted deploy gateway production
scripts/selfhosted deploy artifactory
```

The Artifactory env file is generated from
`services/artifactory/artifactory.example.env` and remains mode `0600`. The
initial installation currently retains JFrog's default `admin` / `password`
login until it is changed through the UI.

Fresh installs also seed `var/etc/system.yaml` with the root-level setting
`jfconnect.enabled: false`. `scripts/selfhosted` copies this seed only when
the runtime file does not already exist, so it does not overwrite generated
keys, database settings, or an administrator's later configuration changes.
Re-enable JFConnect manually in that file, then restart Artifactory, if a
future installation needs Curation or another entitlement-backed feature.

### Configuration ownership

The tracked `services/artifactory/var/etc/system.yaml` is intentionally only
a small, non-secret bootstrap seed. The complete runtime file at
`~/selfhosted/services/artifactory/var/etc/system.yaml` belongs to the
installation: JFrog may add generated settings and it is covered by the
private state backup. Do not replace the runtime file with a repository copy,
and do not commit the full runtime `var` directory. This keeps generated keys,
installation-specific settings, and future JFrog changes out of Git while
still making the fresh-install JFConnect default reproducible.

## Troubleshooting

### Slow first screen

The first startup or restart can take several minutes while Artifactory
initializes its services and embedded Derby database. Temporary `502` or `503`
responses are expected during that window. Wait until both checks return `200`:

```sh
curl -fsS https://<artifactory-host>/artifactory/api/system/ping
curl -fsS https://<artifactory-host>/router/api/v1/system/health
```

Once those checks pass, the login page should load quickly. If the JFrog logo
still spins, look for this repeating frontend error:

```text
First-time entitlement fetch failed: 12 UNIMPLEMENTED: Received HTTP status code 404
```

This indicates that the CE image has JFConnect enabled but does not have a
JFConnect process available. The frontend retries the missing entitlement
endpoint, causing the spinner and extra CPU; this is inside Artifactory, not
Caddy or DNS.

For this image, disable that integration and restart Artifactory:

```sh
podman exec artifactory cp -p \
  /var/opt/jfrog/artifactory/etc/system.yaml \
  /var/opt/jfrog/artifactory/etc/system.yaml.before-jfconnect-disable
podman exec artifactory sed -i \
  '/^jfconnect:/{n;s/enabled: true/enabled: false/;}' \
  /var/opt/jfrog/artifactory/etc/system.yaml
scripts/selfhosted restart artifactory
```

Verify the `jfconnect` section contains `enabled: false`, health checks pass,
and the frontend log is quiet. This preserves the data directory and is
reversible by restoring the saved file:

```sh
podman exec artifactory cp -p \
  /var/opt/jfrog/artifactory/etc/system.yaml.before-jfconnect-disable \
  /var/opt/jfrog/artifactory/etc/system.yaml
scripts/selfhosted restart artifactory
```

JFrog documents JFConnect as required for Curation, so re-evaluate this
setting before enabling Curation or other entitlement-backed features, and
after changing the image version.

### Login popup from optional lead enrichment

The CE frontend may request the following optional endpoint after login even
when JFConnect is intentionally disabled:

```text
/ui/api/v1/enrichment/lead/chilipiper
```

On this CE image, the request reaches the frontend service, which tries to
initialize JFConnect and returns `500` because `jfconnect.enabled` is `false`.
The result is a browser popup such as `Server Error — Request failed with
status code 500`. The `frontend.featureToggler.commonShouldEnableChiliPiper`
setting is not accepted by this CE build, so do not add it to `system.yaml`.

The tracked Caddy route in `gateway/conf.d/artifactory.caddy` handles only this
optional endpoint and returns an empty JSON success response. All other
Artifactory and Conan paths continue to use `reverse_proxy artifactory:8082`.
This keeps JFConnect disabled and avoids changing Artifactory data or
authentication behavior.

Deploy and validate the workaround with:

```sh
scripts/selfhosted deploy gateway production

curl -ksS https://<artifactory-host>/ui/api/v1/enrichment/lead/chilipiper \
  -o - -w '\nstatus=%{http_code} content_type=%{content_type}\n'
curl -fsS https://<artifactory-host>/artifactory/api/system/ping
curl -fsS https://<artifactory-host>/router/api/v1/system/health
```

The first command should return `{}` with status `200` and content type
`application/json`; the health checks should also return `200`. A normal
Artifactory login may still cause the browser to issue the optional request,
but Caddy answers it locally so it does not reach Artifactory or produce a
popup.

To revert the workaround, remove the `@chilipiper` matcher and its `handle`
block from `gateway/conf.d/artifactory.caddy`, restore the direct proxy:

```caddyfile
{$ARTIFACTORY_SITE_ADDRESS:http://artifactory.localhost:80} {
    encode zstd gzip
    reverse_proxy artifactory:8082
}
```

Then redeploy and validate the gateway again:

```sh
scripts/selfhosted deploy gateway production
scripts/selfhosted status gateway
scripts/selfhosted logs gateway
```

Do not delete or replace `services/artifactory/var`; this workaround only
changes the gateway route. Keep `jfconnect.enabled: false` unless a future
installation also provides the JFConnect service and needs an entitlement-
backed feature such as Curation.

Inspect the condition with:

```sh
scripts/selfhosted status artifactory
scripts/selfhosted logs artifactory
podman stats --no-stream artifactory
podman exec artifactory sh -c \
  'grep -n -A2 "^jfconnect:" /var/opt/jfrog/artifactory/etc/system.yaml; \
   ps -ef | grep -i jfconnect | grep -v grep || true'
```

If the checks still fail, inspect the service logs and container status before
restarting again. Never delete the `var` directory: it contains the Derby
database, keys, and repository data.

## Backup and restore

Back up the runtime env file and the complete Artifactory state directory.
Stop Artifactory first so the Derby database is quiescent. The archive contains
credentials, so store it outside the repository with restrictive permissions:

```sh
backup_dir=~/backups/artifactory
backup_file="$backup_dir/artifactory-$(date +%Y%m%d-%H%M%S).tar.gz"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"

systemctl --user stop artifactory.service
if ! tar -C ~/selfhosted/services -czf "$backup_file" artifactory; then
  systemctl --user start artifactory.service
  exit 1
fi
systemctl --user start artifactory.service
chmod 600 "$backup_file"
tar -tzf "$backup_file" >/dev/null
systemctl --user is-active artifactory.service
```

Keep at least one backup off the VPS and test a restore before relying on it.
To restore, stop Artifactory, verify the archive path, extract it over the
runtime state, and start the service again:

```sh
backup_file=~/backups/artifactory/<verified-archive>.tar.gz
systemctl --user stop artifactory.service
tar -C ~/selfhosted/services --no-same-owner -xzf "$backup_file"
systemctl --user start artifactory.service
systemctl --user is-active artifactory.service
```

Restoring overwrites the current Artifactory env file and data directory.
Preserve the current state separately if you may need to undo the restore.

## Lifecycle and updates

```sh
scripts/selfhosted status artifactory
scripts/selfhosted logs artifactory --follow
scripts/selfhosted restart artifactory
scripts/selfhosted update artifactory
```

All persistent state is under `~/selfhosted/services/artifactory/var`; the
env file is `~/selfhosted/services/artifactory/artifactory.env`. Restarting,
disabling, or removing the service definition does not intentionally delete
these paths.

The image uses a floating `latest` tag. Review JFrog release notes, take and
verify a backup, then update only Artifactory:

```sh
scripts/selfhosted update artifactory
scripts/selfhosted status artifactory
scripts/selfhosted logs artifactory --follow
```

Allow several minutes for the first startup after an update. Automatic image
updates are not enabled by this repository. If an update fails, keep the data
directory, inspect the logs, and restore the last verified backup rather than
deleting runtime state.

For larger or critical installations, use PostgreSQL and follow JFrog's
documented production architecture rather than this small embedded database
layout.

## Further reading

- [Artifactory installation](https://docs.jfrog.com/installation/docs/installing-artifactory)
- [JFConnect microservice](https://docs.jfrog.com/installation/docs/jfconnect-microservice)
- [Onboarding wizard](https://docs.jfrog.com/installation/docs/onboarding-wizard)
- [Conan repositories in Artifactory](https://docs.jfrog.com/artifactory/docs/conan-repositories)
- [Repository operations](../../docs/operations.md)
