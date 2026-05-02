# Hello Web

Minimal React app that calls the Python API.

This is included for development only. Production deployment for this repository stays focused on Podman Quadlets for long-running services.

## Run With Compose

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
