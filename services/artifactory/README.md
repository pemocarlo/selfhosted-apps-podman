# Artifactory CE for C/C++

JFrog Artifactory Community Edition for C/C++ provides a team-facing Conan
repository, web UI, permissions, and APIs. This repository runs the small
single-node image with its embedded Derby database. It is resource-intensive;
use PostgreSQL and JFrog's production architecture for larger installations.

## Before deployment

- Review JFrog's [system requirements](https://docs.jfrog.com/installation/docs/artifactory-system-requirements-and-platform-support).
- Choose the public hostname and set `ARTIFACTORY_SITE_ADDRESS` in the gateway
  environment file.
- Plan a verified backup of the complete Artifactory state before updates.

## Deploy and configure

Set the production hostname, deploy the gateway so that the shared network
exists, and then deploy Artifactory:

```sh
ARTIFACTORY_HOST=artifactory.example.com
sed -i "s#^ARTIFACTORY_SITE_ADDRESS=.*#ARTIFACTORY_SITE_ADDRESS=$ARTIFACTORY_HOST#" \
  ~/selfhosted/gateway/caddy.env
scripts/selfhosted deploy gateway production
scripts/selfhosted deploy artifactory
```

On first login, complete the onboarding wizard, replace the image's factory
administrator credentials, and set the base URL to the public HTTPS hostname.
In the CE image, create a local Conan repository from the UI:
Administration → Repositories → Add Repository → Local → Conan. The generic
repository REST API is Pro-only in this edition.

Configure a Conan client using the repository URL shown by Artifactory:

```sh
conan remote add artifactory \
  "https://$ARTIFACTORY_HOST/artifactory/api/conan/conan-local"
CONAN_USER=your-username
conan remote login artifactory "$CONAN_USER"
```

## Runtime layout

- Persistent state: `~/selfhosted/services/artifactory/var`
- Runtime environment: `~/selfhosted/services/artifactory/artifactory.env`
- Gateway upstream: `artifactory:8082` on `caddy-public`
- Image: `releases-docker.jfrog.io/jfrog/artifactory-cpp-ce:latest`

The environment file is generated from
`services/artifactory/artifactory.example.env` and remains mode `0600`.
The tracked `services/artifactory/var/etc/system.yaml` is only a small,
non-secret bootstrap seed. The runtime file gains generated keys and settings;
never replace it with the repository seed or commit the runtime `var` tree.

Fresh installs seed `jfconnect.enabled: false` because this CE image does not
provide the JFConnect process. Re-enable it only when the installation also
needs an entitlement-backed feature such as Curation and has the required
JFrog service available.

## Operations

See [Artifactory operations](OPERATIONS.md) for startup health checks, optional
CE integrations, performance/resource troubleshooting, backups and restores,
updates, and rollback guidance.

The root [operations guide](../../docs/operations.md) contains the general
resource-pressure workflow for every service.

## Further reading

- [Artifactory installation](https://docs.jfrog.com/installation/docs/installing-artifactory)
- [JFConnect microservice](https://docs.jfrog.com/installation/docs/jfconnect-microservice)
- [Onboarding wizard](https://docs.jfrog.com/installation/docs/onboarding-wizard)
- [Conan repositories](https://docs.jfrog.com/artifactory/docs/conan-repositories)
