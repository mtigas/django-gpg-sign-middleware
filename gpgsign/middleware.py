#!/usr/bin/env python
#coding=utf-8
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


import gnupg
import os
import re
import subprocess
from django.conf import settings
#from traceback import format_exc


class GpgSignHtmlMiddleware(object):
    HTMLSTART = re.compile('\<html[^>]*\>')
    HTMLEND = re.compile('\</html[^>]*\>')
    _charset_from_content_type_re = re.compile(r';\s*charset=([^\s;]+)', re.I)
    LINEDASH = re.compile('^-', re.MULTILINE)

    """
    For text/html responses, PGP-signs the page content (hiding the header and
    PGP signature in HTML comments).
    """
    def process_response(self, request, response):
        is_html = response.get('Content-Type', '').lower().strip().startswith('text/html')

        # You can restrict to specific URL roots, blacklist, or do other
        # logic regarding what pages to sign here.
        if is_html and (
            not (request.path.startswith('/blog/exclude-this/'))
        ):
            try:
                response.content = self.gpg_signed_html(response.content, content_type=response.get('Content-Type', '').lower().strip())
            except:
                #with open('/tmp/django.log', 'a+b') as f:
                #    f.write(request.path + "\n")
                #    f.write(format_exc())
                raise
        return response



    @private
    def gpg_binary(self):
        """
        If there is a `GNUPG_BINARY` setting, tries to use that as the
        path to the `gpg` or `gpg2` executable. If not, ask the system
        where it is and try to dereference symlinks along the way.
        """
        gpgbin = getattr(settings, "GNUPG_BINARY", None)
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
            raise Exception("Could not find the `gpg` or `gpg2` executable. Please set GNUPG_BINARY in your local_settings.py file.")

        return gpgbin

    @private
    def get_gpg(self):
        gpgbin = self.gpg_binary()
        gpghome = getattr(settings, "GNUPG_HOME",
            os.environ.get('GNUPGHOME',
                os.path.join(os.environ['HOME'], '.gnupg')
            )
        )
        pubring = os.path.join(gpghome, 'pubring.gpg')
        secring = os.path.join(gpghome, 'secring.gpg')

        if not getattr(settings, "GNUPG_IDENTITY", None):
            raise Exception("Authentication key not yet configured. Please run 'manage.py gpginit' first.")
        elif not os.path.exists(secring) or not os.path.exists(pubring):
            raise Exception("The GnuPG public and secret keyrings do not exist.")

        return gnupg.GPG(gpgbin, homedir=gpghome)

    @private
    def gpg_signed_str(self, data):
        """
        Given a file handle or a string, returns the PGP SIGNATURE for the data,
        as signed by the identity configured in `settings.GNUPG_*`.
        """
        gpg = self.get_gpg()
        return unicode(gpg.sign(
            data,
            default_key=getattr(settings, "GNUPG_IDENTITY", None),
            clearsign=True,
            detach=False,
            binary=False,
            digest_algo="SHA512"
        ))

    @private
    def gpg_signed_html(self.content, content_type=None):
        """
        Given a rendered HTML file in a string, this injects an HTML comment
        immediately after <html> that starts the embedded "clearsign" PGP
        signature, and an HTML comment immediately before </html> that ends
        that signature. Returns that clearsigned HTML string
        """
        if not content_type:
            content_type = "text/html; charset=utf-8"

        charset = self._charset_from_content_type_re.search(content_type)
        if not charset:
            charset = 'utf-8'
        else:
            charset = charset.group(1)

        content = content.decode(charset)

        c = self.HTMLSTART.split(content, 1)[1]
        pre_content = self.HTMLSTART.split(content, 1)[0].strip()
        starttag = self.HTMLSTART.search(content).group(0).strip()
        inside_content = self.HTMLEND.split(c, 1)[0].strip()
        post_content = self.HTMLEND.split(c, 1)[1].strip()
        endtag = htmltag = self.HTMLEND.search(c).group(0).strip()

        inside_content = self.LINEDASH.sub('&#x2D;', inside_content)

        new_inside_content = u"%s<!--\n" % starttag
        new_inside_content += self.gpg_signed_str(u"""This page content is PGP-signed until the final \"END PGP SIGNATURE\" line.

    You can verify this page by running `curl $THIS_URL | gpg`
    or by copying-and-pasting this entire source into PGP or something similar.
    This page is signed with the following PGP key:
    %s

    -->\n%s\n<!--""" % (getattr(settings, "GNUPG_IDENTITY", None), inside_content))
        new_inside_content += u"-->%s" % endtag
        return pre_content + new_inside_content + post_content
