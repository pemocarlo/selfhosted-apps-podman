# BookStack

BookStack is a documentation/wiki application. This service uses the community `solidnerd/bookstack` image with a MySQL container and exposes BookStack through the shared Caddy gateway.

## Files

- `quadlet/bookstack.container`: BookStack application container.
- `quadlet/bookstack-db.container`: MySQL database container.
- `quadlet/bookstack-internal.network`: private app-to-database network.
- `bookstack.env.example`: BookStack environment template.
- `bookstack-db.env.example`: database environment template.
- `mysql/`: persistent MySQL data.
- `public-uploads/`: persistent public uploads.
- `storage-uploads/`: persistent private uploads.
- `../../gateway/conf.d/bookstack.caddy`: public Caddy route.

## Prepare Runtime Files

From the infrastructure repo root:

```sh
mkdir -p ~/selfhosted/services/bookstack
cp -a services/bookstack/mysql services/bookstack/public-uploads services/bookstack/storage-uploads ~/selfhosted/services/bookstack/
cp services/bookstack/bookstack.env.example ~/selfhosted/services/bookstack/bookstack.env
cp services/bookstack/bookstack-db.env.example ~/selfhosted/services/bookstack/bookstack-db.env
```

Edit secrets and the public URL:

```sh
nano ~/selfhosted/services/bookstack/bookstack.env
nano ~/selfhosted/services/bookstack/bookstack-db.env
```

Use the same database password in `DB_PASSWORD` and `MYSQL_PASSWORD`.

Generate a unique `APP_KEY` before production use:

```sh
openssl rand -base64 32
```

Set `APP_URL` to the URL users will open, without a trailing slash:

```sh
APP_URL=https://bookstack.myhostname.com
```

## Gateway

Set `BOOKSTACK_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`:

```sh
BOOKSTACK_SITE_ADDRESS=bookstack.myhostname.com
```

For local gateway testing:

```sh
BOOKSTACK_SITE_ADDRESS=http://bookstack.localhost:80
```

## Deploy

Install the Quadlets:

```sh
mkdir -p ~/.config/containers/systemd
cp services/bookstack/quadlet/bookstack-internal.network ~/.config/containers/systemd/
cp services/bookstack/quadlet/bookstack-db.container ~/.config/containers/systemd/
cp services/bookstack/quadlet/bookstack.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start bookstack-db.service bookstack.service
systemctl --user restart caddy-static.service
```

Do not run `systemctl --user enable bookstack.service`. Quadlet services are generated; autostart is controlled by the `[Install]` section in the `.container` files and applied by the generator.

## Test

Local gateway:

```sh
curl -I -H 'Host: bookstack.localhost' http://127.0.0.1:8080
```

Production:

```sh
curl -I https://bookstack.myhostname.com
```

Default initial login is usually:

```text
admin@admin.com / password
```

Change it immediately after first login.

## Logs

```sh
journalctl --user -u bookstack.service -f
journalctl --user -u bookstack-db.service -f
podman logs bookstack
podman logs bookstack-db
```

## Backup

Back up these runtime paths:

- `~/selfhosted/services/bookstack/mysql`
- `~/selfhosted/services/bookstack/public-uploads`
- `~/selfhosted/services/bookstack/storage-uploads`
- `~/selfhosted/services/bookstack/bookstack.env`
- `~/selfhosted/services/bookstack/bookstack-db.env`

Take database backups before upgrades or migrations.
