from datetime import datetime
from io import BytesIO
import os
import random
from typing import Optional

import httpx
import aioboto3
from PIL import Image

from domain.domainError.domainError import DomainError
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling


class S3Client:
    _instance = None
    _session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._session = aioboto3.Session()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "aws_access_key_id"):  # Only set these once
            self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.region_name = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
            self.bucket = os.getenv("S3_BUCKET", "matchue-assets")
            self.serveRegion = os.getenv("S3_SERVE_REGION", "us-east-2")

    async def _get_client(self):
        if self._session is None:
            raise Exception("Session not initialized")
        client = await self._session.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        ).__aenter__()
        return client

    @serviceErrorHandling
    async def uploadResponseImage(
        self, bytes: BytesIO, s3ImageKey: Optional[str] = None
    ):
        # The folder should be a date, and remain in chronological order, but still look obfuscated to the naked eye.
        now = datetime.utcnow()
        dateInt = int(now.isoformat()[:10].replace("-", ""))
        obfuscatedDate = (dateInt - 12345678) * 283 + ((dateInt * 229) % 283)

        if s3ImageKey is None:
            s3ImageKey = f"image-pool/{obfuscatedDate}/{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}.webp"

        client = await self._get_client()
        try:
            with Image.open(bytes) as image:
                image = image.convert("RGBA")

                # Convert the image to WebP
                with BytesIO() as webp_image_io:
                    image.save(webp_image_io, format="WEBP", quality=80)
                    webp_image_io.seek(0)

                    contentType = "image/webp"

                    await client.upload_fileobj(
                        webp_image_io,
                        self.bucket,
                        s3ImageKey,
                        ExtraArgs={"ContentType": contentType},
                    )
        finally:
            await client.__aexit__(None, None, None)

        return Option(
            f"https://{self.bucket}.s3.{self.serveRegion}.amazonaws.com/{s3ImageKey}"
        )

    @serviceErrorHandling
    async def uploadResponseVideo(
        self, bytes: BytesIO, s3ImageKey: Optional[str] = None
    ):
        # The folder should be a date, and remain in chronological order, but still look obfuscated to the naked eye.
        now = datetime.utcnow()
        dateInt = int(now.isoformat()[:10].replace("-", ""))
        obfuscatedDate = (dateInt - 12345678) * 283 + ((dateInt * 229) % 283)

        if s3ImageKey is None:
            s3ImageKey = f"video-pool/{obfuscatedDate}/{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}.mp4"

        client = await self._get_client()
        try:
            await client.upload_fileobj(
                bytes,
                self.bucket,
                s3ImageKey,
                ExtraArgs={"ContentType": "video/mp4"},
            )
        finally:
            await client.__aexit__(None, None, None)

        return Option(
            f"https://{self.bucket}.s3.{self.serveRegion}.amazonaws.com/{s3ImageKey}"
        )

    @serviceErrorHandling
    async def reuploadImage(self, imageUrl, s3ImageKey: Optional[str] = None):
        async with httpx.AsyncClient() as httpClient:
            response = await httpClient.get(imageUrl)
            response.raise_for_status()

        # The folder should be a date, and remain in chronological order, but still look obfuscated to the naked eye.
        now = datetime.utcnow()
        dateInt = int(now.isoformat()[:10].replace("-", ""))
        obfuscatedDate = (dateInt - 12345678) * 283 + ((dateInt * 229) % 283)

        if s3ImageKey is None:
            s3ImageKey = f"image-pool/{obfuscatedDate}/{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}.webp"

        with Image.open(BytesIO(response.content)) as image:
            image = image.convert("RGBA")

            # Convert the image to WebP
            with BytesIO() as webp_image_io:
                image.save(webp_image_io, format="WEBP", quality=80)
                webp_image_io.seek(0)

                contentType = "image/webp"

                client = await self._get_client()
                try:
                    await client.upload_fileobj(
                        webp_image_io,
                        self.bucket,
                        s3ImageKey,
                        ExtraArgs={"ContentType": contentType},
                    )
                finally:
                    await client.__aexit__(None, None, None)

        return Option(
            f"https://{self.bucket}.s3.{self.serveRegion}.amazonaws.com/{s3ImageKey}"
        )

    @serviceErrorHandling
    async def uploadImage(self, image: Image.Image, s3ImageKey: Optional[str] = None):
        # The folder should be a date, and remain in chronological order, but still look obfuscated to the naked eye.
        now = datetime.utcnow()
        dateInt = int(now.isoformat()[:10].replace("-", ""))
        obfuscatedDate = (dateInt - 12345678) * 283 + ((dateInt * 229) % 283)

        if s3ImageKey is None:
            s3ImageKey = f"image-pool/{obfuscatedDate}/{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}.webp"

        # Convert the image to WebP
        webp_image_io = BytesIO()
        image = image.convert("RGBA")
        image.save(webp_image_io, format="WEBP", quality=80)
        webp_image_io.seek(0)

        contentType = "image/webp"

        client = await self._get_client()
        try:
            await client.upload_fileobj(
                webp_image_io,
                self.bucket,
                s3ImageKey,
                ExtraArgs={"ContentType": contentType},
            )
        finally:
            await client.__aexit__(None, None, None)

        image.close()
        webp_image_io.close()

        return Option(
            f"https://{self.bucket}.s3.{self.serveRegion}.amazonaws.com/{s3ImageKey}"
        )

    @serviceErrorHandling
    async def convertToPNG(self, imageUrl: str) -> Option[str]:
        async with httpx.AsyncClient() as httpClient:
            response = await httpClient.get(imageUrl)
            response.raise_for_status()

        # The folder should be a date, and remain in chronological order, but still look obfuscated to the naked eye.
        now = datetime.utcnow()
        dateInt = int(now.isoformat()[:10].replace("-", ""))
        obfuscatedDate = (dateInt - 12345678) * 283 + ((dateInt * 229) % 283)

        s3ImageKey = f"image-pool/{obfuscatedDate}/{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}.png"

        with BytesIO(response.content) as content_io:
            with Image.open(content_io) as image:
                with BytesIO() as png_image_io:
                    image = image.convert("RGBA")
                    image.save(png_image_io, format="PNG", quality=80)
                    png_image_io.seek(0)

                    contentType = "image/png"

                    client = await self._get_client()
                    try:
                        await client.upload_fileobj(
                            png_image_io,
                            self.bucket,
                            s3ImageKey,
                            ExtraArgs={"ContentType": contentType},
                        )
                    finally:
                        await client.__aexit__(None, None, None)

        return Option(
            f"https://{self.bucket}.s3.{self.serveRegion}.amazonaws.com/{s3ImageKey}"
        )
