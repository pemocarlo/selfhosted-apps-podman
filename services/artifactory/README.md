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

```sh
scripts/selfhosted deploy artifactory
```

Then deploy the gateway with the hostname configured. On the first login,
change the default `admin` / `password` credentials, set the base URL, and
create a local Conan repository such as `conan-local`.

Configure a Conan client using the repository URL shown by Artifactory:

```sh
conan remote add artifactory https://artifactory.example.com/artifactory/api/conan/conan-local
conan remote login artifactory <user>
```

## Lifecycle and data

```sh
scripts/selfhosted status artifactory
scripts/selfhosted logs artifactory --follow
scripts/selfhosted restart artifactory
scripts/selfhosted update artifactory
```

The image uses a floating `latest` tag. Review release notes and take a
verified backup before updating. All persistent state is under
`~/selfhosted/services/artifactory/var`.

For larger or critical installations, use PostgreSQL and follow JFrog's
documented production architecture rather than this small embedded database
layout.

## Further reading

- [Artifactory installation](https://docs.jfrog.com/installation/docs/installing-artifactory)
- [Conan repositories in Artifactory](https://docs.jfrog.com/artifactory/docs/conan-repositories)
- [Repository operations](../../docs/operations.md)
