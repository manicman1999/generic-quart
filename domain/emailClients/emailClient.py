import os
import boto3
from typing import Optional

from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

class EmailClient:
    _instance: Optional['EmailClient'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.awsRegion = os.environ.get("AWS_REGION", 'us-west-2')
        self.sesClient = boto3.client('ses', region_name=self.awsRegion)
        self.defaultSender = os.environ.get("EMAIL_SENDER", "noreply@generic.com")

    @serviceErrorHandling
    async def sendEmail(self, subject: str, recipient: str, body: str, isHtml: bool = True) -> Option[bool]:
        body_content = {
            'Html' if isHtml else 'Text': {
                'Data': body,
            }
        }

        response = self.sesClient.send_email(
            Source=self.defaultSender,
            Destination={
                'ToAddresses': [recipient],
            },
            Message={
                'Subject': {
                    'Data': subject,
                },
                'Body': body_content
            }
        )
        return Option(True)

# Instantiate the singleton EmailClient
emailClient = EmailClient()
