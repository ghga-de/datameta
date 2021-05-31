# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import email
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
import smtplib


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
            # bfname = fname.encode('utf-8')
            part.add_header('Content-Disposition', 'attachment', filename=fname)
            message.attach(part)

        text = message.as_string()

        with smtplib.SMTP(self.hostname, self.port) as server:
            if self.tls:
                server.starttls()
            if self.user:
                server.login(self.user, self.password)
            server.sendmail(sender[1], [ r[1] for r in recipients], text)
