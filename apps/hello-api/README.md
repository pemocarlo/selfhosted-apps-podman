# Hello API

Small FastAPI backend managed with `uv`.

Run locally:

```sh
uv sync
uv run uvicorn hello_api.main:app --reload
```

Test directly:

```sh
curl http://localhost:8000/api/hello
```

Run tests:

```sh
uv run pytest
```
