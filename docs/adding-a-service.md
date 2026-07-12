# Adding a service

Keep each service independent and use the smallest layout it needs:

```text
services/example/
  quadlet/example.container
  example.example.env       # only when needed
  data/.gitkeep             # only for persistent data
  README.md
gateway/conf.d/example.caddy
```

## Quadlet

Start with:

```ini
[Unit]
Description=Example service

[Container]
Image=registry.example.com/example:1.2.3
ContainerName=example
Network=caddy-public.network
Volume=%h/selfhosted/services/example/data:/data:Z
AutoUpdate=registry
NoNewPrivileges=true

[Service]
Restart=always
TimeoutStartSec=900

[Install]
WantedBy=default.target
```

- Use a fully qualified, pinned image when practical.
- Mount persistent paths under `%h/selfhosted/services/<name>`.
- Use `:Z` for private SELinux labeling. Add `:U` only when the image requires ownership adjustment; it changes host ownership.
- Connect only HTTP-facing containers to `caddy-public.network`.
- Put databases on a service-specific `.network` and add Quadlet dependencies with `Requires=` and `After=`.
- Do not publish application ports; Caddy reaches them over the shared network.
- Add resource or health settings only when the image documents suitable values and commands.

## Configuration and route

Commit safe environment templates as `*.example.env` and other safe configuration templates as `*.example.conf`. Use `CHANGE_ME` for required secrets; deployment creates mode-`0600` runtime files and stops until placeholders are replaced.

```caddyfile
{$EXAMPLE_SITE_ADDRESS:http://example.localhost:80} {
	encode zstd gzip
	reverse_proxy example:8080
}
```

Add the local and production examples to `gateway/caddy.example.env`. Keep credentials out of Caddy configuration.

## README and verification

Document only service-specific settings, initialization, client checks, update risks, and backup paths. Then verify:

```sh
bash -n scripts/selfhosted
scripts/selfhosted check
scripts/selfhosted deploy example
scripts/selfhosted status example
curl -I http://example.localhost:8080
git diff --check
```

Confirm that disabling preserves data and that the service can be restored from backup. Application source and image builds stay in their own repositories.
