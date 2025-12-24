"""S3 storage management for slidemaker API."""

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aiobotocore.session
from botocore.exceptions import ClientError

from slidemaker.utils.logger import get_logger

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

logger = get_logger(__name__)


class S3Storage:
    """Manages file upload, download, and signed URL generation for AWS S3.

    This class provides asynchronous methods for interacting with AWS S3, including:
    - File upload/download (binary and JSON)
    - Presigned URL generation
    - File deletion

    All operations use SSE-S3 encryption for data at rest.

    Example:
        async with S3Storage(bucket_name="my-bucket") as storage:
            await storage.upload_file(data, "outputs/presentation.pptx")
            url = await storage.generate_presigned_url("outputs/presentation.pptx")
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1") -> None:
        """
        Initialize S3Storage.

        Args:
            bucket_name: S3 bucket name (from environment variable S3_BUCKET_NAME)
            region: AWS region (from environment variable AWS_REGION, defaults to "us-east-1")
        """
        self.bucket_name = bucket_name
        self.region = region
        self.session = aiobotocore.session.get_session()
        self._client: S3Client | None = None

        logger.info(
            "S3Storage initialized",
            bucket_name=bucket_name,
            region=region,
        )

    async def __aenter__(self) -> "S3Storage":
        """Async context manager entry."""
        self._client = await self.session.create_client(
            "s3", region_name=self.region
        ).__aenter__()
        logger.debug("S3 client created")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            logger.debug("S3 client closed")

    async def upload_file(
        self, file_data: bytes, key: str, content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to S3.

        Args:
            file_data: Binary data to upload
            key: S3 object key (e.g., "outputs/presentation.pptx")
            content_type: Content-Type header (default: "application/octet-stream")

        Returns:
            S3 object key

        Raises:
            RuntimeError: If S3 client is not initialized
            ClientError: If S3 upload fails
        """
        if not self._client:
            raise RuntimeError("S3Storage not initialized. Use 'async with' context manager.")

        try:
            await self._client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
            logger.info(
                "File uploaded to S3",
                bucket=self.bucket_name,
                key=key,
                size_bytes=len(file_data),
            )
            return key

        except ClientError as e:
            logger.error(
                "S3 upload failed",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
            )
            raise

    async def download_file(self, key: str) -> bytes:
        """
        Download file from S3.

        Args:
            key: S3 object key

        Returns:
            File binary data

        Raises:
            RuntimeError: If S3 client is not initialized
            FileNotFoundError: If object does not exist
            ClientError: If S3 download fails
        """
        if not self._client:
            raise RuntimeError("S3Storage not initialized. Use 'async with' context manager.")

        try:
            response = await self._client.get_object(Bucket=self.bucket_name, Key=key)
            body = response["Body"]
            data: bytes = await body.read()
            logger.debug(
                "File downloaded from S3",
                bucket=self.bucket_name,
                key=key,
                size_bytes=len(data),
            )
            return data

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                logger.error(
                    "S3 object not found",
                    bucket=self.bucket_name,
                    key=key,
                )
                raise FileNotFoundError(f"S3 object not found: {key}") from e

            logger.error(
                "S3 download failed",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
            )
            raise

    async def upload_json(self, key: str, data: dict[str, Any]) -> None:
        """
        Upload JSON data to S3.

        Args:
            key: S3 object key
            data: Dictionary to upload (datetime values are converted to ISO 8601)

        Raises:
            RuntimeError: If S3 client is not initialized
            ClientError: If S3 upload fails
        """
        # Convert datetime to ISO 8601 format
        json_str = json.dumps(data, default=self._json_serializer, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode("utf-8")

        await self.upload_file(json_bytes, key, content_type="application/json")
        logger.debug("JSON uploaded to S3", bucket=self.bucket_name, key=key)

    async def download_json(self, key: str) -> dict[str, Any]:
        """
        Download JSON data from S3.

        Args:
            key: S3 object key

        Returns:
            Parsed dictionary

        Raises:
            RuntimeError: If S3 client is not initialized
            FileNotFoundError: If object does not exist
            ValueError: If JSON parsing fails
            ClientError: If S3 download fails
        """
        data = await self.download_file(key)

        try:
            json_data: dict[str, Any] = json.loads(data.decode("utf-8"))
            logger.debug("JSON downloaded from S3", bucket=self.bucket_name, key=key)
            return json_data

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON from S3",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
            )
            raise ValueError(f"Invalid JSON in S3 object {key}: {e}") from e

    async def generate_presigned_url(self, key: str, expiration: int = 604800) -> str:
        """
        Generate presigned URL for S3 object (valid for 7 days by default).

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 7 days = 604800)

        Returns:
            Presigned URL (HTTPS)

        Raises:
            RuntimeError: If S3 client is not initialized
            ClientError: If URL generation fails
        """
        if not self._client:
            raise RuntimeError("S3Storage not initialized. Use 'async with' context manager.")

        try:
            url: str = await self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            logger.info(
                "Presigned URL generated",
                bucket=self.bucket_name,
                key=key,
                expiration_seconds=expiration,
            )
            return url

        except ClientError as e:
            logger.error(
                "Failed to generate presigned URL",
                bucket=self.bucket_name,
                key=key,
                error=str(e),
            )
            raise

    async def delete_file(self, key: str) -> None:
        """
        Delete file from S3.

        This operation is idempotent - deleting a non-existent object is considered success.

        Args:
            key: S3 object key

        Raises:
            RuntimeError: If S3 client is not initialized
            ClientError: If S3 deletion fails (excluding NoSuchKey)
        """
        if not self._client:
            raise RuntimeError("S3Storage not initialized. Use 'async with' context manager.")

        try:
            await self._client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info("File deleted from S3", bucket=self.bucket_name, key=key)

        except ClientError as e:
            # Ignore NoSuchKey errors (idempotent operation)
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code != "NoSuchKey":
                logger.error(
                    "S3 deletion failed",
                    bucket=self.bucket_name,
                    key=key,
                    error=str(e),
                )
                raise

    @staticmethod
    def _json_serializer(obj: Any) -> str:
        """
        JSON serializer for objects not serializable by default json module.

        Args:
            obj: Object to serialize

        Returns:
            ISO 8601 formatted string for datetime objects

        Raises:
            TypeError: If object type is not supported
        """
        if isinstance(obj, datetime):
            # Ensure timezone-aware datetime
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=UTC)
            iso_string: str = obj.isoformat()
            return iso_string

        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
