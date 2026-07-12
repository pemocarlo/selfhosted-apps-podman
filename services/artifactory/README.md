# Artifactory CE for C/C++

JFrog Artifactory Community Edition provides Conan repositories, a web UI, permissions, and APIs. It is the recommended option for teams. This configuration uses the embedded Derby database for a small single-node installation.

## Deploy

Artifactory is resource-intensive; check JFrog's [current system requirements](https://docs.jfrog.com/installation/docs/artifactory-system-requirements-and-platform-support) before using a small VPS.

```sh
scripts/selfhosted deploy artifactory
```

Set `ARTIFACTORY_SITE_ADDRESS=artifactory.example.com` in `~/selfhosted/gateway/caddy.env`, then deploy the gateway. Open the site, sign in with `admin` / `password`, change the password immediately, set the base URL, and create a local Conan repository such as `conan-local`.

Configure a client:

```sh
conan remote add artifactory https://artifactory.example.com/artifactory/api/conan/conan-local
conan remote login artifactory <user>
```

## Data and updates

All state is under `~/selfhosted/services/artifactory/var`. Back it up before updates. The image uses a floating tag; review release notes and use `scripts/selfhosted update artifactory` only after taking a backup. For larger or critical installations, use PostgreSQL and follow JFrog's single-node installation guide.
