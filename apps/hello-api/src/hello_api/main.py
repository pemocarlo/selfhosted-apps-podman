from fastapi import FastAPI

app = FastAPI(title="Hello API", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI behind Caddy"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "hello-api", "docs": "/docs", "health": "/api/health"}
