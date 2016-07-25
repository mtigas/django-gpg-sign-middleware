# django gpg sign middleware

A Django middleware that GPG signs entire HTML pages, hidden from most users
by stashing the PGP "clearsign" header/footer bits
(`BEGIN PGP SIGNED MESSAGE` and `BEGIN PGP SIGNATURE` and etc) in HTML comments.

© 2016 Mike Tigas. Licensed under the [GNU Affero General Public License v3 or later](LICENSE.md).

---

Very roughly extracted from some of the stuff that powers
[my site](https://mike.tig.as/). (See also: [site colophon](https://mike.tig.as/colophon/),
[django-medusa](https://github.com/mtigas/django-medusa/))

Requires an installation of [GnuPG](https://www.gnupg.org/); uses
isislovecruft's [python-gnupg fork](https://github.com/isislovecruft/python-gnupg).
Has only been tested with Django 1.4.

---

There is a non-zero chance that this is a pointless or bad idea,
but it was a fun random thing to throw together over a few days. If you worry
that you can't trust the hosting or transmission of my website (even over
HTTPS or strongly-authenticated [Tor onion services](http://tigas3l7uusztiqu.onion/)),
and after all of that you still trust my PGP key, then you can be certain
that my HTML pages are still legit. Or something like that.

**Important**: This is also essentially useless in a normal server-side Django
installation; to ensure safety of your PGP key, minimize CPU load (and denial
of service risk), and the ability to actually serve pages if you have a key
passphrase, **you probably need to couple this with something that "bakes" your
site into a static HTML form** -- like
[django-medusa](https://github.com/mtigas/django-medusa/).
Generating your site statically ahead of time doesn't expose your PGP key
to would-be server attackers, and allows you to verify page integrity across
mirrors or other distribution mechanisms (like local area meshnets or
content distributed via sneakernet or etc).

**Why not detached signatures or something in HTTP headers or etc?** Mostly out
of laziness: doing it this way allows a simple `curl $URL | gpg` to verify a
page. It also keeps things simple when serving on a basic static-only web
server. We also avoid thinking about what to do about things like variant URLs
where the canonical URL is not a literal _filename_ (i.e. `/blog/` +
`/blog/index.html`). HTTP headers were avoided, because I wanted this to work
without a dynamic server-side component for extra metadata like that and
utilizing HTTP headers would involve more steps for a user to verify page data.
(Also: questions regarding what format to use, the fact that HTTP headers are
uncompressed, etc.)

In short: this little experiment might not be for you, use it at your own risk.

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

## Configuration

In your `settings.py` file, this middleware uses the following options:

    # You should set these.
    GNUPG_HOME = '/home/mtigas/.gnupg'
    GNUPG_BINARY = '/usr/local/bin/gpg2'
    GNUPG_IDENTITY = '4034E60AA7827C5DF21A89AAA993E7156E0E9923'

    # These are essentially optional
    GNUPG_HEADER_MESSAGE = None
    GNUPG_PATH_FILTER = lambda path: True

* **GNUPG_HOME** is akin to the `$GNUPGHOME` environment variable; it is the
  full path to your user `.gnupg` directory. If `GNUPG_HOME` is not set, the
  middleware will first fall back to the `$GNUPGHOME` environment variable; if
  the environment variable is not set, it will fall back to `$HOME/.gnupg`.

* **GNUPG_BINARY** is the full path to the gpg binary you wish to use.

* **GNUPG_IDENTITY** is the ID of the key you wish to use for signing. The
  secret key listed here must already exist in the GNUPG_HOME keychain. This
  value may be any keyid format that GPG accepts (`0x6E0E9923`, `6E0E9923`,
  `A993E7156E0E9923`, etc).

* **GNUPG_HEADER_MESSAGE** changes the HTML comment that is displayed at the
  top of your file, explaining that the page is PGP-signed. See *Example*
  section below. If `None`, the default is:

  ```
  u"""This page content is PGP-signed until the final \"END PGP SIGNATURE\" line.

  You can verify this page by running `curl $THIS_URL | gpg`
  or by copying-and-pasting this entire source into PGP or something similar.
  This page is signed with the following PGP key:
  {identity}"""
  ```

  If you use the `{identity}` variable in your message, it is expanded into the
  value of `GNUPG_IDENTITY`, using `str.format()`.

* **GNUPG_PATH_FILTER**: A function that receives one argument, representing
  `request.path` inside the middleware `process_response()` method. The function
  defined here must return `True` or `False`; paths returning `False` will not
  be signed by this middleware. This allows you to write whitelists/blacklists
  if you do not want to sign every `text/html` response. The default
  GNUPG_PATH_FILTER always returns `True`.

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
* If you run this on a server and the PGP key has a passphrase, you're gonna
  have a bad time.
