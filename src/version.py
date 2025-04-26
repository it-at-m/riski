from typing import Optional

from git import Repo
from git.exc import InvalidGitRepositoryError
from yaml import safe_load

from src.envtools import getenv_with_exception
from src.logtools import getLogger

logger = getLogger()


def get_version() -> str:
    if version := _get_git_version():
        logger.info(f"Version {version} (from git)")
        return version
    elif version := _get_file_version():
        logger.info(f"Version {version} (from .version.yaml)")
        return version
    elif version := getenv_with_exception("APP_VERSION"):
        logger.info(f"Version {version} (from APP_VERSION env var)")
        return version
    else:
        logger.warning("No version found")
        return "Unknown Version"


def _get_git_version() -> Optional[str]:
    version: str = None

    # Try to get the version from the git repository
    try:
        repo = Repo(search_parent_directories=True)
        current_commit_hash = repo.commit("HEAD").hexsha

        # Check if the current commit is tagged
        for tag in repo.tags:
            if tag.commit.hexsha == current_commit_hash:
                return tag.name

        # If the current commit is not tagged, use the commit hash stub
        if version is None:
            return current_commit_hash[:8]

    # Fallback to None if no git repository is found
    except InvalidGitRepositoryError:
        return None


def _get_file_version() -> Optional[str]:
    VERSION_FILE: str = ".version.yaml"
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as file:
            version_dict: dict = safe_load(file)
    except FileNotFoundError:
        return None

    if version := version_dict.get("commit_tag"):
        return str(version)
    elif version := version_dict.get("commit_short_sha"):
        return str(version)
    else:
        return None
