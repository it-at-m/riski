from src.logtools import getLogger
from src.version import get_version


def main():
    logger = getLogger()
    version = get_version()
    logger.info(f"Hello from the app! Version: {version}")


if __name__ == "__main__":
    main()
