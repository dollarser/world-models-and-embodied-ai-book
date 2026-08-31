#!/usr/bin/env python3
"""Run Docker Compose without mutating a broken global credential config.

Some Docker Desktop installations keep `credsStore: desktop` after the
credential helper disappears from PATH. For public base images this wrapper
creates a task-specific anonymous Docker config in the temporary directory and
reuses the existing context and CLI plugins. It never copies credentials.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def docker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    user_docker = Path.home() / ".docker"
    config_path = user_docker / "config.json"

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return environment

    helper = config.get("credsStore")
    if not helper or shutil.which(f"docker-credential-{helper}"):
        return environment

    temporary = Path(tempfile.gettempdir()) / "cv2embodied-docker-config"
    temporary.mkdir(mode=0o700, parents=True, exist_ok=True)
    anonymous = {
        "auths": {},
        "currentContext": config.get("currentContext", "default"),
    }
    (temporary / "config.json").write_text(
        json.dumps(anonymous, indent=2) + "\n", encoding="utf-8"
    )

    for name in ("cli-plugins", "contexts"):
        source = user_docker / name
        target = temporary / name
        if source.exists() and not target.exists():
            target.symlink_to(source, target_is_directory=True)

    environment["DOCKER_CONFIG"] = str(temporary)
    return environment


def main() -> int:
    if not sys.argv[1:]:
        print("usage: docker_compose.py COMPOSE_ARGS...", file=sys.stderr)
        return 2
    command = ["docker", "compose", *sys.argv[1:]]
    os.execvpe(command[0], command, docker_environment())
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
