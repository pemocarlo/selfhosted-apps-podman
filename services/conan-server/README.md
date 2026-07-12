# Conan Server

`conan_server` is a basic Conan remote without a web UI. Conan documents it mainly for testing, though it may suit a small trusted team. Users and passwords are stored as plaintext in `server.conf`.

## Image

The Quadlet expects `localhost/conan-server:2.30.0`. Build and publish this image from a separate image repository using:

```dockerfile
FROM docker.io/library/python:3.13-slim
RUN pip install --no-cache-dir conan-server==2.30.0
EXPOSE 9300
ENTRYPOINT ["conan_server"]
```

Change `Image=` and `AutoUpdate=` if using a registry image.

```sh
podman build -t localhost/conan-server:2.30.0 .
```

## Deploy

```sh
podman image exists localhost/conan-server:2.30.0
scripts/selfhosted deploy conan-server
nano ~/selfhosted/services/conan-server/server.conf
scripts/selfhosted deploy conan-server
```

The first deploy creates `server.conf` and stops at its placeholders. Generate two different secrets with `openssl rand -hex 32`, set a strong password, and rerun deployment. Set `CONAN_SERVER_SITE_ADDRESS=conan.example.com` in the gateway env and redeploy the gateway.

Configure a client:

```sh
conan remote add private https://conan.example.com
conan remote login private conan
```

Back up `~/selfhosted/services/conan-server/data` and `server.conf` together. Restart the service after configuration changes; it does not hot-reload.
