#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

"""Self-hosted Podman/Caddy deployment helper.

Mirrors Bash `scripts/selfhosted` behavior, but runs as standalone Python via
`uv run --script`. Handles gateway and app deploy/update/disable/status flows,
runtime env template creation, Quadlet install, image pulls, and status display.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = Path(os.environ.get("SELFHOSTED_ROOT", Path.home() / "selfhosted"))
QUADLET_DIR = Path(os.environ.get("QUADLET_DIR", Path.home() / ".config/containers/systemd"))
APP_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ScriptError(RuntimeError):
    """User-facing script failure."""

    pass


def die(message: str) -> "None":
    """Abort with user-facing error."""
    raise ScriptError(message)


def usage() -> None:
    """Print supported command syntax."""
    print(
        "Usage:\n"
        "  scripts/selfhosted deploy gateway [local|production]\n"
        "  scripts/selfhosted deploy app <name>\n"
        "  scripts/selfhosted deploy all [local|production]\n"
        "  scripts/selfhosted disable <name>\n"
        "  scripts/selfhosted update <name|gateway|all>\n"
        "  scripts/selfhosted status [name|gateway|all]\n"
        "  scripts/selfhosted list"
    )


def run_command(args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run system command with text output."""
    return subprocess.run(args, check=check, text=True)


def require_app(app: str) -> None:
    """Validate app name and ensure service directory exists."""
    if not APP_NAME_RE.fullmatch(app) or not (ROOT / "services" / app / "quadlet").is_dir():
        die(f"unknown app '{app}'; run 'scripts/selfhosted list'")


def list_apps() -> list[str]:
    """List deployable apps under services/."""
    apps: list[str] = []
    services_dir = ROOT / "services"
    for path in sorted(services_dir.iterdir(), key=lambda item: item.name):
        if path.is_dir() and (path / "quadlet").is_dir():
            apps.append(path.name)
    return apps


def is_disabled(app: str) -> bool:
    """Check runtime disable marker for app."""
    return (RUNTIME_ROOT / "services" / app / ".disabled").exists()


def unit_names(source: Path) -> list[str]:
    """Map Quadlet container files to systemd service names."""
    quadlet_dir = source / "quadlet"
    units = [f"{path.stem}.service" for path in sorted(quadlet_dir.glob("*.container"), key=lambda item: item.name)]
    return units


def unit_names_reverse(source: Path) -> list[str]:
    """Return service names in reverse order for stop operations."""
    return list(reversed(unit_names(source)))


def install_quadlets(source: Path) -> None:
    """Copy Quadlet files into user systemd directory."""
    QUADLET_DIR.mkdir(parents=True, exist_ok=True)
    quadlet_dir = source / "quadlet"
    for path in sorted(quadlet_dir.iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, QUADLET_DIR / path.name)


def template_to_env_name(template: Path) -> str | None:
    """Convert supported env template filename to runtime env filename."""
    name = template.name
    if name.endswith(".example.env"):
        return f"{name.removesuffix('.example.env')}.env"
    if name.endswith(".env.example"):
        return f"{name.removesuffix('.env.example')}.env"
    return None


def install_env_templates(source: Path, target: Path) -> None:
    """Create missing runtime env files from safe templates."""
    candidates = sorted(
        [path for path in source.iterdir() if path.is_file() and template_to_env_name(path)],
        key=lambda item: item.name,
    )
    for template in candidates:
        destination_name = template_to_env_name(template)
        if destination_name is None:
            continue
        destination = target / destination_name
        if not destination.exists():
            shutil.copy2(template, destination)
            destination.chmod(0o600)
            print(f"created {destination}; edit placeholders before production use")


def copy_directory_contents(source: Path, destination: Path) -> None:
    """Copy directory tree contents into destination."""
    shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True, copy_function=shutil.copy2)


def prepare_app_runtime(app: str) -> Path:
    """Ensure app runtime tree exists and copy persistent directories."""
    source = ROOT / "services" / app
    target = RUNTIME_ROOT / "services" / app
    target.mkdir(parents=True, exist_ok=True)
    install_env_templates(source, target)

    for path in sorted(source.iterdir(), key=lambda item: item.name):
        if path.is_dir() and path.name != "quadlet":
            copy_directory_contents(path, target / path.name)

    return target


def check_placeholders(target: Path) -> None:
    """Reject runtime env files that still contain CHANGE_ME."""
    for env_file in target.glob("*.env"):
        try:
            contents = env_file.read_text()
        except OSError as exc:
            die(f"unable to read {env_file}: {exc}")
        if "CHANGE_ME" in contents:
            die(f"edit CHANGE_ME placeholders in {target}/*.env, then deploy again")


def deploy_gateway(profile: str = "production") -> None:
    """Deploy gateway runtime files and restart gateway service."""
    if profile not in {"local", "production"}:
        die("gateway profile must be local or production")

    source = ROOT / "gateway"
    target = RUNTIME_ROOT / "gateway"
    (target / "conf.d").mkdir(parents=True, exist_ok=True)
    (target / "site").mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(parents=True, exist_ok=True)
    (target / "config").mkdir(parents=True, exist_ok=True)
    QUADLET_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source / "Caddyfile", target / "Caddyfile")
    copy_directory_contents(source / "conf.d", target / "conf.d")
    copy_directory_contents(source / "site", target / "site")
    install_env_templates(source, target)
    check_placeholders(target)
    shutil.copy2(source / "quadlet" / "caddy-public.network", QUADLET_DIR / "caddy-public.network")
    shutil.copy2(source / "quadlet" / f"caddy-{profile}.container", QUADLET_DIR / "caddy-static.container")
    run_command(["systemctl", "--user", "daemon-reload"])
    run_command(["systemctl", "--user", "restart", "caddy-static.service"])
    print(f"deployed gateway ({profile})")


def deploy_app(app: str) -> None:
    """Deploy one app, enabling it if previously disabled."""
    require_app(app)
    source = ROOT / "services" / app
    runtime_target = prepare_app_runtime(app)
    check_placeholders(runtime_target)
    disabled_marker = runtime_target / ".disabled"
    if disabled_marker.exists():
        disabled_marker.unlink()
    install_quadlets(source)
    run_command(["systemctl", "--user", "daemon-reload"])
    units = unit_names(source)
    if units:
        run_command(["systemctl", "--user", "restart", *units])
    run_command(["systemctl", "--user", "try-restart", "caddy-static.service"])
    print(f"deployed app {app}")


def deploy_all(profile: str = "production") -> None:
    """Deploy gateway and every enabled app."""
    deploy_gateway(profile)
    for app in list_apps():
        if is_disabled(app):
            print(f"skip disabled app {app}")
        else:
            deploy_app(app)


def disable_app(app: str) -> None:
    """Disable one app without deleting runtime data."""
    require_app(app)
    source = ROOT / "services" / app
    runtime_target = RUNTIME_ROOT / "services" / app
    runtime_target.mkdir(parents=True, exist_ok=True)
    (runtime_target / ".disabled").touch()

    units = unit_names_reverse(source)
    if units:
        run_command(["systemctl", "--user", "stop", *units], check=False)

    for path in sorted((source / "quadlet").iterdir(), key=lambda item: item.name):
        if path.is_file():
            try:
                (QUADLET_DIR / path.name).unlink()
            except FileNotFoundError:
                pass

    run_command(["systemctl", "--user", "daemon-reload"])
    run_command(["systemctl", "--user", "try-restart", "caddy-static.service"])
    print(f"disabled app {app}; runtime data preserved")


def pull_images(source: Path) -> None:
    """Pull non-local images referenced by Quadlets."""
    images: set[str] = set()
    for quadlet in sorted((source / "quadlet").glob("*.container"), key=lambda item: item.name):
        try:
            contents = quadlet.read_text()
        except OSError as exc:
            die(f"unable to read {quadlet}: {exc}")
        for line in contents.splitlines():
            if line.startswith("Image="):
                images.add(line.removeprefix("Image=").strip())

    for image in sorted(image for image in images if image):
        if image.startswith("localhost/"):
            print(f"skip local image {image}")
        else:
            run_command(["podman", "pull", image])


def update_component(component: str) -> None:
    """Refresh images and restart one component."""
    if component == "gateway":
        source = ROOT / "gateway"
        pull_images(source)
        run_command(["systemctl", "--user", "restart", "caddy-static.service"])
        print("updated gateway")
        return

    require_app(component)
    if is_disabled(component):
        die(f"{component} is disabled; use 'scripts/selfhosted deploy app {component}' to enable it")

    source = ROOT / "services" / component
    runtime_target = prepare_app_runtime(component)
    check_placeholders(runtime_target)
    install_quadlets(source)
    run_command(["systemctl", "--user", "daemon-reload"])
    pull_images(source)
    units = unit_names(source)
    if units:
        run_command(["systemctl", "--user", "restart", *units])
    print(f"updated {component}")


def update_all() -> None:
    """Refresh gateway and every enabled app."""
    update_component("gateway")
    for app in list_apps():
        if is_disabled(app):
            print(f"skip disabled app {app}")
        else:
            update_component(app)


def show_status(component: str = "all") -> None:
    """Print systemd status for gateway, app, or all."""
    if component == "all":
        show_status("gateway")
        for app in list_apps():
            show_status(app)
        return

    if component == "gateway":
        run_command(["systemctl", "--user", "--no-pager", "--full", "status", "caddy-static.service"], check=False)
        return

    require_app(component)
    if is_disabled(component):
        print(f"{component}: disabled")
        return

    source = ROOT / "services" / component
    units = unit_names(source)
    if units:
        run_command(["systemctl", "--user", "--no-pager", "--full", "status", *units], check=False)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch CLI and return process exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        usage()
        return 0

    try:
        command = args[0]
        if command == "deploy":
            if len(args) < 2:
                usage()
                return 1
            target = args[1]
            if target == "gateway":
                deploy_gateway(args[2] if len(args) > 2 else "production")
            elif target == "app":
                if len(args) < 3:
                    usage()
                    return 1
                deploy_app(args[2])
            elif target == "all":
                deploy_all(args[2] if len(args) > 2 else "production")
            else:
                usage()
                return 1
        elif command == "disable":
            if len(args) < 2:
                usage()
                return 1
            disable_app(args[1])
        elif command == "update":
            if len(args) < 2:
                usage()
                return 1
            if args[1] == "all":
                update_all()
            else:
                update_component(args[1])
        elif command == "status":
            show_status(args[1] if len(args) > 1 else "all")
        elif command == "list":
            for app in list_apps():
                print(app)
        else:
            usage()
            return 1
    except ScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: missing command or file: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        cmd = " ".join(exc.cmd) if isinstance(exc.cmd, Sequence) and not isinstance(exc.cmd, str) else str(exc.cmd)
        print(f"error: command failed with exit code {exc.returncode}: {cmd}", file=sys.stderr)
        return exc.returncode or 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
