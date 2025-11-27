"""Security helpers for configuring Kafka TLS/mTLS."""

from base64 import b64decode
from logging import Logger, getLogger
from pathlib import Path
from ssl import SSLContext, create_default_context
from tempfile import TemporaryDirectory

from config.config import Config, get_config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from faststream.security import BaseSecurity

logger: Logger = getLogger(__name__)
config: Config = get_config()


def setup_security() -> BaseSecurity:
    """Set up Kafka security configuration based on application settings.

    Returns:
        BaseSecurity: The configured security object for Kafka.

    Raises:
        ValueError: If required environment variables are not set or if there are issues
            loading the PKCS#12 file.
    """
    with TemporaryDirectory() as tempdir:
        tempdir_path: Path = Path(tempdir)
        logger.debug("Setting up Kafka mTLS security using environment variables.")
        # Unpack CA file
        ca_data: str | None = config.kafka_ca_b64
        ca_data = b64decode(s=ca_data).decode(encoding="utf-8")

        # Unpack PKCS#12 file
        pkcs12_data: str | None = config.kafka_pkcs12_data
        pkcs12_bytes = b64decode(s=pkcs12_data)

        # Unpack PKCS#12 password
        pkcs12_pw: str | None = config.kafka_pkcs12_pw
        pkcs12_pw_bytes: bytes = b64decode(s=pkcs12_pw)

        # Extract the private key and certificate from the PKCS#12 file
        try:
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                data=pkcs12_bytes,
                password=pkcs12_pw_bytes,
            )
        except Exception as e:
            raise ValueError(f"Failed to load PKCS#12 file: {e}")

        if private_key is None or certificate is None:
            raise ValueError("PKCS#12 file does not contain a private key and certificate.")

        # Write cert and key to temporary files
        cert_file: Path = tempdir_path / "kafka.cert"
        key_file: Path = tempdir_path / "kafka.key"
        with open(file=cert_file, mode="wb") as f:
            f.write(certificate.public_bytes(encoding=serialization.Encoding.PEM))
        with open(file=key_file, mode="wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Create SSL context
        ssl_context: SSLContext = create_default_context(
            cadata=ca_data,
        )

        # Load client cert and key
        ssl_context.load_cert_chain(
            certfile=cert_file,
            keyfile=key_file,
        )

    return BaseSecurity(ssl_context=ssl_context, use_ssl=True)
