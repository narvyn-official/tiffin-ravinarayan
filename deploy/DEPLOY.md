# Deployment guide — tiffin.ravinarayan.in

Deploys this Django app to an Ubuntu 24.04 VPS, fronted by nginx + gunicorn,
with TLS via Let's Encrypt. Static files served by WhiteNoise.

## DNS first

Add an A record at your DNS provider:

```
Host:  tiffin.ravinarayan.in
Type:  A
Value: <YOUR_VPS_IP>
TTL:   3600
```

(Optional) `www.tiffin.ravinarayan.in` → same IP.

Wait for propagation: `dig tiffin.ravinarayan.in +short` → must show your VPS IP.

## On the VPS

> Set the variables once at the top, then copy/paste blocks below.

```bash
APP=tiffin_ravinarayan
DOMAIN=tiffin.ravinarayan.in
REPO=https://github.com/<your-user>/<repo>.git
APP_DIR=/var/www/$APP
```

### 1. System deps (once per server)

```bash
apt update && apt install -y \
    python3-venv python3-pip nginx git certbot python3-certbot-nginx
```

### 2. Clone the app

```bash
mkdir -p /var/www && cd /var/www
git clone "$REPO" "$APP"
cd "$APP_DIR"
```

### 3. Virtualenv + dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 4. Environment file

```bash
cp deploy/.env.example .env
# Generate a real secret key
python3 -c "import secrets; print('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(64))" >> /tmp/sk
nano .env   # paste the new key, set ALLOWED_HOSTS + CSRF_TRUSTED_ORIGINS
chmod 600 .env
```

Required variables in `.env`:

```
DJANGO_SECRET_KEY=<long random string>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=tiffin.ravinarayan.in,www.tiffin.ravinarayan.in
DJANGO_CSRF_TRUSTED_ORIGINS=https://tiffin.ravinarayan.in,https://www.tiffin.ravinarayan.in
```

### 5. Database + collected static + superuser

```bash
set -a && . .env && set +a
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
```

### 6. Permissions

```bash
chown -R root:www-data "$APP_DIR"
chmod -R g+rX "$APP_DIR"
chmod 660 "$APP_DIR/db.sqlite3" 2>/dev/null || true
chmod 770 "$APP_DIR" 2>/dev/null || true
```

### 7. Gunicorn (systemd unit)

```bash
cp deploy/tiffin_ravinarayan_gunicorn.service \
   /etc/systemd/system/tiffin_ravinarayan_gunicorn.service
systemctl daemon-reload
systemctl enable --now tiffin_ravinarayan_gunicorn
systemctl status tiffin_ravinarayan_gunicorn --no-pager
```

The socket should appear at `$APP_DIR/tiffin.sock`.

### 8. Nginx

```bash
cp deploy/nginx.conf /etc/nginx/sites-available/$APP
ln -sf /etc/nginx/sites-available/$APP /etc/nginx/sites-enabled/$APP
nginx -t && systemctl reload nginx
```

Test plain HTTP first:

```bash
curl -H "Host: $DOMAIN" -i http://127.0.0.1/ | head -5
```

### 9. TLS via certbot

```bash
certbot --nginx -d $DOMAIN -d www.$DOMAIN \
        --non-interactive --agree-tos -m admin@$DOMAIN --redirect
```

Certbot edits the nginx config to add the SSL block and an HTTP→HTTPS redirect.
Cert auto-renews via the system certbot timer; check it:

```bash
systemctl list-timers | grep certbot
```

### 10. Smoke test

```bash
curl -I https://$DOMAIN/
curl -s https://$DOMAIN/ | grep -oE '<title>[^<]+</title>'
```

Expect `200 OK` and the brand title.

## Updating the app later

```bash
cd "$APP_DIR"
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
systemctl restart tiffin_ravinarayan_gunicorn
```

## Troubleshooting

- **502 Bad Gateway** from nginx: gunicorn isn't running or socket perms wrong.
  `journalctl -u tiffin_ravinarayan_gunicorn -n 50 --no-pager` shows why.
- **CSRF "origin not trusted"** on form POST: update `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env` then `systemctl restart tiffin_ravinarayan_gunicorn`.
- **Static files 404**: run `collectstatic` and restart gunicorn (WhiteNoise serves from `STATIC_ROOT`).
- **Backups**: `cp db.sqlite3 db.sqlite3.$(date +%F).bak` (cron daily; sync off-server weekly).
