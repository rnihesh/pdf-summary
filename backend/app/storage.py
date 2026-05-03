import boto3
from botocore.config import Config
from .config import settings

_s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
    endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com",
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)


def s3_key_for(user_id: int, doc_id: int, filename: str) -> str:
    safe = filename.replace("/", "_")
    return f"users/{user_id}/{doc_id}/{safe}"


def upload_bytes(key: str, data: bytes, content_type: str = "application/pdf") -> None:
    _s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def delete_key(key: str) -> None:
    try:
        _s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except Exception:
        pass


def presigned_get(key: str, expires: int = 600) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
