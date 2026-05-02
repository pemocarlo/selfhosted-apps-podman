# Hello API

Small FastAPI backend managed with `uv` and exposed by the shared Caddy gateway.

## Files

- `pyproject.toml`: Python project metadata and dependencies.
- `uv.lock`: locked Python dependencies.
- `src/hello_api/`: FastAPI package.
- `tests/`: API tests.
- `Containerfile`: production image build.
- `quadlet/hello-api.container`: production Podman Quadlet.
- `../../gateway/conf.d/hello-api.caddy`: Caddy reverse-proxy route.

## Develop Locally

```sh
uv sync
uv run uvicorn hello_api.main:app --reload
```

Test directly:

```sh
curl http://localhost:8000/api/hello
curl http://localhost:8000/api/health
```

Run tests:

```sh
uv run pytest
```

## Build Image

From the repository root:

```sh
podman build -t localhost/hello-api:latest -f services/hello-api/Containerfile services/hello-api
```

## Deploy With Quadlet

Install the shared gateway network first from `gateway/`.

Then install the API unit:

```sh
mkdir -p ~/.config/containers/systemd
cp services/hello-api/quadlet/hello-api.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start hello-api.service
systemctl --user enable hello-api.service
```

Make sure `gateway/conf.d/hello-api.caddy` is deployed with the gateway and `HELLO_API_SITE_ADDRESS` is set in `~/selfhosted/gateway/caddy.env`.

Restart Caddy after adding the route:

```sh
systemctl --user restart caddy-static.service
```

## Test Through Gateway

Local Quadlet gateway:

```sh
curl -i -H 'Host: api.localhost' http://127.0.0.1:8080/api/hello
```

Production:

```sh
curl -i https://api.myhostname.com/api/hello
```
