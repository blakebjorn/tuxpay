import os
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from modules import config
from modules.logging import logger
from modules.pdf import get_invoice_pdf_data, build_invoice_pdf


async def email_invoice(invoice):
    pdf_data = await get_invoice_pdf_data(invoice['id'])
    pdf_file = await build_invoice_pdf(pdf_data)

    recipients = [invoice['customer_email'] or ""] + \
                 re.split("[;,\\s]", config.get("email_recipients",
                                                namespace="EMAIL",
                                                default=""))
    recipients = [x for x in set(recipients) if x]

    e = Email(to=recipients,
              bcc=recipients,
              subject=f"TuxPay Payment for Invoice {invoice['name']}",
              content=f"<div>Payment has been confirmed. Invoice is attached</div>",
              attachments=[(pdf_file.read_bytes(), f"Invoice {invoice['name']}.pdf")])
    try:
        e.send()
    except smtplib.SMTPException as e:
        logger.warning("Could not send email", exc_info=e)


class Email:
    def __init__(self, to=None, cc=None, bcc=None,
                 subject="No Subject", content=("No Content",),
                 from_address=None, attachments=None):
        self.username = config.get("smtp_username", namespace="EMAIL")
        self.password = config.get("smtp_password", namespace="EMAIL")
        self.smtp = None

        from_name = config.get("smtp_from_name", namespace="EMAIL") or "TuxPay"
        from_address = from_address or self.username

        self.message = MIMEMultipart()
        self.build_recipients(to, cc, bcc)
        self.message['From'] = f"{from_name} <{from_address}>"
        self.message['Subject'] = subject

        self.message.attach(MIMEText(str(content), 'html'))

        if attachments:
            if not isinstance(attachments, list):
                attachments = [attachments]
            for att in attachments:
                if isinstance(att, str):
                    with open(att, "rb") as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.split(att)[-1])
                        self.message.attach(attachment)
                elif isinstance(att, tuple):
                    content, filename = att
                    if isinstance(content, bytes):
                        attachment = MIMEApplication(content)
                    else:
                        attachment = MIMEApplication(content.read())
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    self.message.attach(attachment)

    def build_recipients(self, to, cc, bcc):
        if isinstance(to, str):
            to = [to]
        if isinstance(cc, str):
            cc = [cc]
        if isinstance(bcc, str):
            bcc = [bcc]
        if cc:
            self.message['CC'] = "; ".join([x.strip() for x in cc])
        if bcc:
            self.message['BCC'] = "; ".join([x.strip() for x in bcc])
        self.message['To'] = "; ".join([x.strip() for x in to])

    def send(self):
        self.smtp = smtplib.SMTP(config.get("smtp_host", namespace="EMAIL"),
                                 int(config.get("smtp_port", namespace="EMAIL")))
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(self.username, self.password)
        from_addr = re.search("(.*?)(<)(.*?)(>)", self.message['From']).group(3)
        recipients = self.message['To'].split(";")
        if self.message['CC'] is not None:
            recipients += self.message['CC'].split(";")
        if self.message['BCC'] is not None:
            recipients += self.message['BCC'].split(";")
        recipients = [str(x).strip() for x in recipients]

        return self.smtp.sendmail(from_addr, recipients, self.message.as_string())
