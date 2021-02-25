# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .smtp import SMTPClient

from pyramid import threadlocal

from email.utils import parseaddr

__smtp = SMTPClient(
        hostname  =threadlocal.get_current_registry().settings['datameta.smtp_host'],
        port      =threadlocal.get_current_registry().settings['datameta.smtp_port'],
        user      =threadlocal.get_current_registry().settings['datameta.smtp_user'],
        password  =threadlocal.get_current_registry().settings['datameta.smtp_pass'],
        tls       =threadlocal.get_current_registry().settings['datameta.smtp_tls']
        )

__smtp_from = parseaddr(threadlocal.get_current_registry().settings['datameta.smtp_from'])

def send(recipients, subject, template, values, bcc=None):
    """Sends an email message to the specified recipients using the provided template and values.

    Keyword arguments:
    recipients - str or list to specify a single or multiple recipients
    subject - the subject of the message
    template - str that specifies the body of the message
    values - dict that is used to apply format() on the template before sending"""

    # Format the message
    message = template.format(**values)

    # Send the message
    __smtp.sendMessage(__smtp_from, recipients, subject, message, bcc=bcc)
