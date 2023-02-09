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

from .smtp import SMTPClient

from pyramid import threadlocal

from email.utils import parseaddr

import logging
log = logging.getLogger(__name__)


__smtp = SMTPClient(
    hostname  = threadlocal.get_current_registry().settings['datameta.smtp_host'],
    port      = threadlocal.get_current_registry().settings['datameta.smtp_port'],
    user      = threadlocal.get_current_registry().settings['datameta.smtp_user'],
    password  = threadlocal.get_current_registry().settings['datameta.smtp_pass'],
    tls       = threadlocal.get_current_registry().settings['datameta.smtp_tls']
)

__smtp_from = parseaddr(threadlocal.get_current_registry().settings['datameta.smtp_from'])


def send(recipients, subject, template, values, bcc=None, rec_header_only=False):
    """Sends an email message to the specified recipients using the provided template and values.

    Keyword arguments:
    recipients - str or list to specify a single or multiple recipients
    subject - the subject of the message
    template - str that specifies the body of the message
    values - dict that is used to apply format() on the template before sending"""

    # Format the message
    message = template.format(**values)

    # Send the message
    try:
        __smtp.sendMessage(__smtp_from, recipients, subject, message, bcc=bcc, rec_header_only=rec_header_only)
    except Exception as e:
        log.error("SMTP error.", extra={"error": e})
