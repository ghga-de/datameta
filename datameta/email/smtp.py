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

import email
from email.mime.base import MIMEBase
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr, formatdate
import smtplib
import ssl

class SMTPClient:

    def __init__(self,
            hostname = 'localhost',
            port = '587',
            user = None,
            password = None,
            tls = False,
            rec_header_only=False):
        self.hostname = hostname
        self.port     = port
        self.user     = user
        self.password = password
        self.tls      = tls

    def sendMessage(self,
            sender,
            recipients,
            subject,
            message_text,
            attachments = {},
            bcc = None,
            rec_header_only=False):

        if not isinstance(recipients, list):
            recipients = [ recipients ]

        message = MIMEMultipart()

        # Header
        message["Date"] = formatdate(localtime=True)
        message["From"] = formataddr(sender)
        message["To"] = ', '.join([formataddr(recipient) for recipient in recipients])
        message["Subject"] = subject

        # Remove the recipients from the recipients if they are to be used only for the header
        if rec_header_only:
            recipients = []

        # Add BCC recipients after building the 'To' header
        if bcc:
            if isinstance(bcc, list):
                recipients += [ (None, elem) for elem in bcc ]
            else:
                recipients.append((None, bcc))

        # If we have no recpients here, there is an error
        if not recipients:
            raise RuntimeError("No recipients specified.")

        message.attach(MIMEText(message_text, 'plain'))
        for fname, data in attachments.items():
            app_type = 'pdf' if fname[-4:].lower() == '.pdf' else 'octet-stream'
            part = MIMEBase("application", app_type)
            part.set_payload(data)
            email.encoders.encode_base64(part)
            bfname = fname.encode('utf-8')
            part.add_header('Content-Disposition', 'attachment', filename=fname)
            message.attach(part)

        text = message.as_string()

        with smtplib.SMTP(self.hostname, self.port) as server:
            if self.tls:
                server.starttls()
            if self.user:
                server.login(self.user, self.password)
            server.sendmail(sender[1], [ r[1] for r in recipients], text)
