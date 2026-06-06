# Contributing

Keep changes small and service-independent.

Before opening a change:

```sh
bash -n scripts/selfhosted
git diff --check
```

For a new app, add `services/<name>/quadlet/`, safe `*.example.env` templates if needed, persistent-directory `.gitkeep` files, a Caddy route, and a concise service README. Never commit runtime secrets or data.
