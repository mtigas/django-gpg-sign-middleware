# django gpg sign middleware

A Django middleware that GPG signs entire HTML pages, hidden from most users
by stashing the PGP "clearsign" header/footer bits
(`BEGIN PGP SIGNED MESSAGE` and `BEGIN PGP SIGNATURE` and etc) in HTML comments.

Requires an installation of [GnuPG](https://www.gnupg.org/); uses
isislovecruft's [python-gnupg fork](https://github.com/isislovecruft/python-gnupg).

Very roughly extracted from some of the stuff that powers
[my site](https://mike.tig.as/). (See also: [site colophon](https://mike.tig.as/colophon/),
[django-medusa](https://github.com/mtigas/django-medusa/))


© 2016 Mike Tigas. Licensed under the [GNU Affero General Public License v3 or later](LICENSE.md).


# Installation

Install the package:

    pip install -e https://github.com/mtigas/django-gpg-sign-middleware.git#egg=django-gpg-sign-middleware

Add this to Django application's `settings.py` file:

    INSTALLED_APPS = (
        ...
        'gpgsign',
        ...
        )

---

The middleware should be added to the appropriate level of `MIDDLEWARE_CLASSES`
in your settings file:

    MIDDLEWARE_CLASSES = (
    ...
    'gpgsign.middleware.GpgSignHtmlMiddleware',
    )

It can safely go at the end (becoming the first middleware that has the
opportunity); to rewrite the response body. If you have other middlewares that
rewrite the HTML *response body* and you wish to GPG sign the HTML *after* the
effects of the other middleware, then place the `GpgSignHtmlMiddleware` line
above the other middleware.

---

The following values should also exist in your settings:

    GNUPG_HOME = '/home/mtigas/.gnupg'
    GNUPG_BINARY = '/usr/local/bin/gpg2'
    GNUPG_IDENTITY = '4034E60AA7827C5DF21A89AAA993E7156E0E9923'

* **GNUPG_HOME** is akin to the `$GNUPGHOME` environment variable; it is the
  full path to your user `.gnupg` directory. If `GNUPG_HOME` is not set, the
  middleware will first fall back to the `$GNUPGHOME` environment variable; if
  the environment variable is not set, it will fall back to `$HOME/.gnupg`.

* **GNUPG_BINARY** is the full path to the gpg binary you wish to use.

* **GNUPG_IDENTITY** is the ID of the key you wish to use for signing. The
  secret key listed here must already exist in the GNUPG_HOME keychain. This
  value may be any keyid format that GPG accepts (`0x6E0E9923`, `6E0E9923`,
  `A993E7156E0E9923`, etc).

## Example

Given a homepage (`/`) that responds with the following response body:

```html
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Hi!</title>
</head>
<body>
<h1>Hello world!</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
</html>
```

Navigating to the page _should_ result in something not unlike the following
(but signed with _your_ GPG key).

```html
<html><!--
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

This page content is PGP-signed until the final "END PGP SIGNATURE" line.

You can verify this page by running `curl $THIS_URL | gpg`
or by copying-and-pasting this entire source into PGP or something similar.
This page is signed with the following PGP key:
4034E60AA7827C5DF21A89AAA993E7156E0E9923

- -->
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Hi!</title>
</head>
<body>
<h1>Hello world!</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
<!--
-----BEGIN PGP SIGNATURE-----

iQIcBAEBCgAGBQJXlkXyAAoJEBS4eLqV2mhKpBMQAI00ZRnn3dvA8/9jbGKcTS5d
hYhudz0oGiTOz3+7fy2QGBS2vbz0z496pQQKFPE8P9+mRBr/ZOfV/UYUG4Qxk8kI
McdUGP++FjO1bx5zQ/FpxkJW7rwTnhkGKiazp+6qXtxDGxP+aSV1QG+R+4PrTMzY
3hRdJqsFM9j6ozSz7vCcP2AUYum4wi14jPbWcZWbLgMqFjThDKVjAiptmazyf/Sd
fHFKUnnFEaWqCofMR4TWj/H6netR2sZ7SzGC3dogDKMMQT2bxHS4Z9V/geY/GctK
FsaL2thnuNOwLxqZZjIJAJfEsAZeZUzDA4l8zdx/LwEDwfBssSeSQuOzcdlX79/8
Tlmgwd26ZCcteFkyMz4Gj6wm/wV+5wKS+TDdIt0wXEEGH17D/QfWz9X851UukaaU
W8Ln8ZybwFRe7/M1oTCeI74GvxotV6wXa9pUy4f74o5gDREjCfgkrMtY+PdrPHjk
MkTbeBvj9hEOhm+GJeKWoQZH3PcHJBLgjJjipMBgrNccuqheowDfvkNraWwtGyGQ
nd5ZOOdUVJ+Vx285Zbg0W+06hbg5a6Kao1j4ebT7fHCdC5MQSILjP9hrXn3P6M5W
eS+QuWWb7zHH8jUH3m/89OpP0WWyXHsxYzejyUKdxVeqdKJQ7L7/ZPAIyFL8Trgc
5lhCS5rX3TbYvDiG5AoV
=T8eW
-----END PGP SIGNATURE-----
--></html>
```

# Caveats

* You may have some issues with passphrase prompts if `gpg-agent` is set to
  immediately forget your secret key passphrase.
