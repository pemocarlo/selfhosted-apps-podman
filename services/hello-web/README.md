# Hello Web

Minimal React app that calls the Python API.

In production it is exposed through the shared Caddy gateway at `HELLO_WEB_SITE_ADDRESS`, for example `myapp.myhostname.com`. The Caddy route also proxies `/api/*` to `hello-api`, so the frontend and API share one public origin.

## Files

- `Containerfile`: builds the Vite app and serves static files with internal Caddy on port `8080`.
- `Caddyfile.container`: internal static file server config for the app container.
- `quadlet/hello-web.container`: production Podman Quadlet.
- `../../gateway/conf.d/hello-web.caddy`: public Caddy route for the app and API path.
- `src/`: React source.

## Run With Compose For Development

From the repository root:

```sh
systemctl --user start podman.socket
podman compose -f compose.dev.yml up --build
```

Open:

```text
http://localhost:5173
```

The React app calls `/api/hello`; Vite proxies `/api` to the `hello-api` container.

Test locally:

```sh
curl http://localhost:5173
curl http://localhost:5173/api/hello
curl http://localhost:8000/api/hello
```

Stop:

```sh
podman compose -f compose.dev.yml down
```

## Run Locally Without Containers

Start the API first:

```sh
cd services/hello-api
uv run uvicorn hello_api.main:app --reload
```

Start the web app in another terminal:

```sh
cd services/hello-web
npm install
VITE_API_BASE_URL=http://localhost:8000/api npm run dev
```

The API allows `http://localhost:5173` and `http://127.0.0.1:5173` for this development flow.

## Build Production Image

From the repository root:

```sh
podman build -t localhost/hello-web:latest -f services/hello-web/Containerfile services/hello-web
```

Smoke-test the static container directly:

```sh
podman run --rm -p 127.0.0.1:8081:8080 localhost/hello-web:latest
curl http://localhost:8081
```

## Deploy With Quadlet

Build the image first, and make sure `hello-api` and the gateway are deployed.

Install the web unit:

```sh
mkdir -p ~/.config/containers/systemd
cp services/hello-web/quadlet/hello-web.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start hello-web.service
systemctl --user enable hello-web.service
```

Make sure `gateway/conf.d/hello-web.caddy` is deployed with the gateway and `HELLO_WEB_SITE_ADDRESS` is set in `~/selfhosted/gateway/caddy.env`.

Restart Caddy after adding the route:

```sh
systemctl --user restart caddy-static.service
```

## Test Through Gateway

Local Quadlet gateway:

```sh
curl -i -H 'Host: myapp.localhost' http://127.0.0.1:8080
curl -i -H 'Host: myapp.localhost' http://127.0.0.1:8080/api/hello
```

Production:

```sh
curl -I https://myapp.myhostname.com
curl -i https://myapp.myhostname.com/api/hello
```
