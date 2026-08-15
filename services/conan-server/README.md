# Conan Server

`conan_server` is a small Conan remote without a web UI. Conan documents it
mainly for testing, though it may suit a small trusted team. User passwords
are stored as plaintext in `server.conf`; use Artifactory for a larger or
security-sensitive installation.

## Image

The Quadlet expects `localhost/conan-server:2.30.0`. Build this image in the
separate image/source repository, then confirm it exists locally:

```sh
podman build -t localhost/conan-server:2.30.0 .
podman image exists localhost/conan-server:2.30.0
```

Change `Image=` and `AutoUpdate=` in the Quadlet if the image is published to
a registry.

## Deploy and configure

```sh
scripts/selfhosted deploy conan-server
nano ~/selfhosted/services/conan-server/server.conf
scripts/selfhosted deploy conan-server
```

Replace both generated secrets, set a strong user password, and keep
`ssl_enabled: True` when clients connect through Caddy over HTTPS. Set
`CONAN_SERVER_SITE_ADDRESS` in the gateway env file and redeploy the gateway.

The server does not hot-reload its configuration:

```sh
scripts/selfhosted status conan-server
scripts/selfhosted logs conan-server --follow
scripts/selfhosted restart conan-server
```

Back up `~/selfhosted/services/conan-server/server.conf` and
`~/selfhosted/services/conan-server/data` together. The server data directory
contains the uploaded packages.

## Further reading

- [Official Conan Server documentation](https://docs.conan.io/2/reference/conan_server.html)
- [Conan remote commands](https://docs.conan.io/2/reference/commands/remote.html)
- [Artifactory CE for private development](https://docs.jfrog.com/installation/docs/installing-artifactory)
- [Manual lifecycle commands](../../docs/manual.md)
