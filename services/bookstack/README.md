# BookStack

BookStack is a wiki backed by a private MySQL container. The app is exposed
through Caddy; MySQL is available only on `bookstack-internal.network`.

## Before deployment

Set these values in the generated runtime env files:

- `APP_URL`: the exact public URL, without a trailing slash.
- `APP_KEY`: a new unique application key.
- Matching `DB_PASSWORD` and `MYSQL_PASSWORD` values.
- A strong `MYSQL_ROOT_PASSWORD`.

The first deploy creates the env files and stops while `CHANGE_ME` placeholders
remain:

```sh
scripts/selfhosted deploy bookstack
openssl rand -base64 32
nano ~/selfhosted/services/bookstack/bookstack.env
nano ~/selfhosted/services/bookstack/bookstack-db.env
scripts/selfhosted deploy bookstack
```

Set `BOOKSTACK_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env` and redeploy
the gateway. Change the image's initial administrator credentials immediately.

## Lifecycle and data

`bookstack.service` requires `bookstack-db.service`; restarting the app does
not remove or recreate the database data.

```sh
scripts/selfhosted status bookstack
scripts/selfhosted logs bookstack --follow
scripts/selfhosted restart bookstack
scripts/selfhosted update bookstack
```

Back up these paths together:

- `~/selfhosted/services/bookstack/mysql/`
- `~/selfhosted/services/bookstack/public-uploads/`
- `~/selfhosted/services/bookstack/storage-uploads/`

For a consistent backup, stop the app or use a database-native MySQL dump.
Test the restore before upgrading the image.

## Further reading

- [BookStack documentation](https://www.bookstackapp.com/docs/)
- [BookStack installation](https://www.bookstackapp.com/docs/admin/installation/)
- [BookStack backup and restore](https://www.bookstackapp.com/docs/admin/backup-restore/)
- [BookStack system CLI](https://www.bookstackapp.com/docs/admin/system-cli/)
- [Manual lifecycle commands](../../docs/manual.md)
