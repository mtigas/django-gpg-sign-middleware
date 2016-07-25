#!/usr/bin/env python
#coding=utf-8
#
# Requires "gnupg>=2.0.2". Use `pip install "gnupg>=2.0.2"`. Outputs to STDOUT.
#
# Usage: cli.py [-h] filename
#     i.e.: ./cli.py index.html > index.signed.html
#
# django-gpg-sign-middleware - https://github.com/mtigas/django-gpg-sign-middleware
# Copyright © 2016, Mike Tigas.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import gnupg
import os
import re
import subprocess

# Optional (I think). Full path to GnuPG binary. By default, tries `gpg2` on
# $PATH and then tries `gpg` on $PATH.
GNUPG_BINARY = "/usr/local/bin/gpg2"

# Optional. By default tries $GNUPGHOME env var and then falls back to
# $HOME/.gnupg
GNUPG_HOME = None

# Required. The GPG key ID that you want to sign stuff with.
GNUPG_IDENTITY = "0x6E0E9923"

# Optional. See `comment_msg()` below.`
GNUPG_HEADER_MESSAGE = None

##########

HTMLSTART = re.compile('\<html[^>]*\>')
HTMLEND = re.compile('\</html[^>]*\>')
_charset_from_content_type_re = re.compile(r';\s*charset=([^\s;]+)', re.I)
LINEDASH = re.compile('^-', re.MULTILINE)

def gpg_binary():
    """
    If there is a `GNUPG_BINARY` setting, tries to use that as the
    path to the `gpg` or `gpg2` executable. If not, ask the system
    where it is and try to dereference symlinks along the way.
    """
    gpgbin = GNUPG_BINARY
    try:
        if not gpgbin:
            gpgbin = subprocess.Popen(
                ['which', 'gpg2'],
                stdout=subprocess.PIPE
            ).stdout.read().strip("\n")
        if not gpgbin:
            gpgbin = subprocess.Popen(
                ['which', 'gpg'],
                stdout=subprocess.PIPE
            ).stdout.read().strip("\n")
    except OSError:
        # Don't have "which" command, so can't ask the OS for the path
        # to the gpg or gpg2 binary
        pass

    if gpgbin:
        # dereference symlinks, since `python-gnupg` can't cope with 'em.
        gpgbin = os.path.realpath(gpgbin)

    if not gpgbin:
        raise Exception("Could not find the `gpg` or `gpg2` executable. Please set GNUPG_BINARY.")

    return gpgbin

def get_gpg():
    gpgbin = gpg_binary()
    gpghome = GNUPG_HOME
    if not gpghome:
        gpghome = os.environ.get('GNUPGHOME',
            os.path.join(os.environ['HOME'], '.gnupg')
        )
    pubring = os.path.join(gpghome, 'pubring.gpg')
    secring = os.path.join(gpghome, 'secring.gpg')

    if not GNUPG_IDENTITY:
        raise Exception("Authentication key not yet configured. Please run 'manage.py gpginit' first.")
    elif not os.path.exists(secring) or not os.path.exists(pubring):
        raise Exception("The GnuPG public and secret keyrings do not exist.")

    return gnupg.GPG(gpgbin, homedir=gpghome)

def gpg_signed_str(data):
    """
    Given a file handle or a string, returns the PGP SIGNATURE for the data,
    as signed by the identity configured in `GNUPG_IDENTITY`.
    """
    gpg = get_gpg()
    return unicode(gpg.sign(
        data,
        default_key=GNUPG_IDENTITY,
        clearsign=True,
        detach=False,
        binary=False,
        digest_algo="SHA512"
    ))

def gpg_signed_html(content, content_type=None):
    """
    Given a rendered HTML file in a string, this injects an HTML comment
    immediately after <html> that starts the embedded "clearsign" PGP
    signature, and an HTML comment immediately before </html> that ends
    that signature. Returns that clearsigned HTML string
    """
    if not content_type:
        content_type = "text/html; charset=utf-8"

    charset = _charset_from_content_type_re.search(content_type)
    if not charset:
        charset = 'utf-8'
    else:
        charset = charset.group(1)

    content = content.decode(charset)

    c = HTMLSTART.split(content, 1)[1]
    pre_content = HTMLSTART.split(content, 1)[0].strip()
    starttag = HTMLSTART.search(content).group(0).strip()
    inside_content = HTMLEND.split(c, 1)[0].strip()
    post_content = HTMLEND.split(c, 1)[1].strip()
    endtag = htmltag = HTMLEND.search(c).group(0).strip()

    inside_content = LINEDASH.sub('&#x2D;', inside_content)

    new_inside_content = u"%s<!--\n" % starttag
    new_inside_content += gpg_signed_str(u"{header_msg}\n-->\n{inside_content}\n<!--".format(
        header_msg=comment_msg(),
        inside_content=inside_content
    ))
    new_inside_content += u"-->%s" % endtag
    return pre_content + new_inside_content + post_content

def comment_msg():
    msg = GNUPG_HEADER_MESSAGE
    if not msg:
        msg = u"""This page content is PGP-signed until the final \"END PGP SIGNATURE\" line.

You can verify this page by running `curl $THIS_URL | gpg`
or by copying-and-pasting this entire source into PGP or something similar.
This page is signed with the following PGP key:
{identity}"""
    return msg.format(identity=GNUPG_IDENTITY)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add PGP clearsign signature to a static HTML page.')
    parser.add_argument('filename', metavar='filename',
                        help='path to an HTML file')
    args = parser.parse_args()
    with open(args.filename, 'rb') as f:
        print gpg_signed_html(f.read())
