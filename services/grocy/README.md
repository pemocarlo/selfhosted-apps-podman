# Grocy

Grocy is a household inventory and organization app using the LinuxServer.io
container image.

## Before deployment

Review the generated `~/selfhosted/services/grocy/grocy.env`:

```sh
id -u
id -g
nano ~/selfhosted/services/grocy/grocy.env
```

Set `PUID`, `PGID`, and `TZ` to suitable values for the deployment user. Set
`GROCY_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env` before exposing it
publicly.

## Deploy and lifecycle

```sh
scripts/selfhosted deploy grocy
scripts/selfhosted status grocy
scripts/selfhosted logs grocy --follow
scripts/selfhosted restart grocy
scripts/selfhosted update grocy
```

Sign in with the image's initial administrator credentials and change the
password immediately. After an image update, open Grocy's root page once so pending
database migrations can run.

Persistent application data is under
`~/selfhosted/services/grocy/config`. Back up that directory; disabling or
removing the service definition does not remove it.

## Further reading

- [Grocy project site](https://grocy.info/)
- [Grocy source and documentation](https://github.com/grocy/grocy)
- [LinuxServer.io Grocy image documentation](https://docs.linuxserver.io/images/docker-grocy/)
- [Manual lifecycle commands](../../docs/manual.md)
