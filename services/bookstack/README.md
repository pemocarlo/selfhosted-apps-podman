# BookStack

BookStack wiki plus private MySQL container. Use root [README](../../README.md) and [operations docs](../../docs/operations.md).

## Files

- `quadlet/bookstack.container`: app container.
- `quadlet/bookstack-db.container`: MySQL container.
- `quadlet/bookstack-internal.network`: private app-to-db network.
- `bookstack.example.env`: app settings, URL, and secret placeholders.
- `bookstack-db.example.env`: database name and credentials.
- `mysql/`: persistent database data.
- `public-uploads/`: public uploads.
- `storage-uploads/`: private uploads.
- `../../gateway/conf.d/bookstack.caddy`: public route.

## Example Lines

```sh
APP_URL=https://bookstack.example.com
DB_PASSWORD=CHANGE_ME_DATABASE_PASSWORD
MYSQL_PASSWORD=CHANGE_ME_DATABASE_PASSWORD
BOOKSTACK_SITE_ADDRESS=bookstack.example.com
```

```caddyfile
{$BOOKSTACK_SITE_ADDRESS:http://bookstack.localhost:80} {
	reverse_proxy bookstack:8080
}
```

## Deploy

Before deploy, set matching `DB_PASSWORD` and `MYSQL_PASSWORD`, a unique `APP_KEY`, and the exact public `APP_URL` in generated runtime env files. `scripts/selfhosted deploy bookstack` creates missing env files, then stops if placeholders remain.

```sh
openssl rand -base64 32
nano ~/selfhosted/services/bookstack/bookstack.env
nano ~/selfhosted/services/bookstack/bookstack-db.env
scripts/selfhosted deploy bookstack
```

Set `BOOKSTACK_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`. Change default login `admin@admin.com / password` immediately.

## Notes

- `bookstack.container` depends on `bookstack-db.container`.
- `bookstack-internal.network` keeps database traffic private.
- `bookstack-db.example.env` holds DB name and password vars.
- `bookstack.example.env` holds app URL, app key, and DB host/user vars.
- `mysql/`, `public-uploads/`, and `storage-uploads/` are persistent data paths.
- Back up `mysql/`, `public-uploads/`, and `storage-uploads/` together while the app is stopped, or use a consistent MySQL dump.
