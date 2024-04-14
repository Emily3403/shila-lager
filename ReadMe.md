# Shila Lager

This is the software we use to run the Shila Lager website. 

## Installation

### Native
This is the only option for now. Once this app is production ready, it will be available as a docker image.

1. Install the app with `pip install shila_lager`
2. Setup environment variables:
   - `SECRET_KEY={64 random characters}`
   - `SERVER_NAMES={whitespace separated list of domain names}`
3. Setup the database: `shila-manage init-db`
4. Create an admin user: `shila-manage createsuperuser`
5. Run the app: `shila-manage runserver` or with a systemd service: `shila-manage init-systemd && systemctl start shila-lager`
6. Setup SSL with a reverse proxy like nginx or apache.

#### Bonus
- Setup serving static files with a web server like nginx or apache.
- Setup an Email provider with the following environment variables:
  - `MAIL_SERVER={smtp server}`
  - `MAIL_PORT={smtp port}`
  - `MAIL_USE_TLS={True or False}`
  - `MAIL_USERNAME={smtp username}`
  - `MAIL_PASSWORD={smtp password}`
- Setup OpenID Connect with the following environment variables:
  - `OIDC_CLIENT_ID={client id}`
  - `OIDC_CLIENT_SECRET={client secret}`
  - `OIDC_ISSUER={issuer}`
  - `OIDC_REDIRECT_URI={redirect uri}`
  - `OIDC_LOGOUT_REDIRECT_URI={logout redirect uri}`