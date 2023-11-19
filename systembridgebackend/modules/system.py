"""System Bridge: System"""
from __future__ import annotations

import asyncio
import os
import platform
import re
import socket
import sys
import uuid
from typing import Any, override

import aiohttp
from pkg_resources import parse_version
from plyer import uniqueid
from psutil import boot_time, users
from psutil._common import suser
from systembridgemodels.system import System, SystemUser

from .._version import __version__
from .base import ModuleUpdateBase


class SystemUpdate(ModuleUpdateBase):
    """System Update"""

    def __init__(self) -> None:
        """Initialise"""
        super().__init__()
        self._mac_address: str = self._get_mac_address()
        self._version: str = __version__.public()
        self._version_latest: str | None = None

    async def _get_active_user_id(self) -> int:
        """Get active user ID"""
        return os.getpid()

    async def _get_active_user_name(self) -> str:
        """Get active user"""
        return os.getlogin()

    async def _get_boot_time(self) -> float:
        """Get boot time"""
        return boot_time()

    async def _get_camera_usage(self) -> list[str]:
        """Returns a list of apps that are currently using the webcam."""
        active_apps = []
        if sys.platform == "win32":
            # Read from registry for camera usage
            import winreg  # pylint: disable=import-error,import-outside-toplevel

            subkey_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"

            def get_subkey_timestamp(subkey) -> int | None:
                """Returns the timestamp of the subkey"""
                try:
                    value, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                    return value
                except OSError:
                    pass
                return None

            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey_path)
                # Enumerate over the subkeys of the webcam key
                subkey_count, _, _ = winreg.QueryInfoKey(key)
                # Recursively open each subkey and check the "LastUsedTimeStop" value.
                # A value of 0 means the camera is currently in use.
                for idx in range(subkey_count):
                    subkey_name = winreg.EnumKey(key, idx)
                    subkey_name_full = f"{subkey_path}\\{subkey_name}"
                    subkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey_name_full)
                    if subkey_name == "NonPackaged":
                        # Enumerate over the subkeys of the "NonPackaged" key
                        subkey_count, _, _ = winreg.QueryInfoKey(subkey)
                        for np_idx in range(subkey_count):
                            subkey_name_np = winreg.EnumKey(subkey, np_idx)
                            subkey_name_full_np = (
                                f"{subkey_path}\\NonPackaged\\{subkey_name_np}"
                            )
                            subkey_np = winreg.OpenKey(
                                winreg.HKEY_CURRENT_USER, subkey_name_full_np
                            )
                            if get_subkey_timestamp(subkey_np) == 0:
                                active_apps.append(subkey_name_np)
                    else:
                        if get_subkey_timestamp(subkey) == 0:
                            active_apps.append(subkey_name)
                    winreg.CloseKey(subkey)
                winreg.CloseKey(key)
            except OSError:
                pass
        elif sys.platform in ["darwin", "linux"]:
            # Unknown, please open an issue or PR if you know how to do this
            pass
        return active_apps

    async def _get_fqdn(self) -> str:
        """Get FQDN"""
        return socket.getfqdn()

    async def _get_hostname(self) -> str:
        """Get hostname"""
        return socket.gethostname()

    async def _get_ip_address_4(self) -> str:
        """Get IPv4 address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    async def _get_ip_address_6(self) -> str:
        """Get IPv6 address"""
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect(("2001:4860:4860::8888", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    def _get_mac_address(self) -> str:
        """Get MAC address"""
        # pylint: disable=consider-using-f-string
        return ":".join(re.findall("..", "%012x" % uuid.getnode()))

    async def _get_pending_reboot(self) -> bool:
        """Check if there is a pending reboot"""
        if sys.platform == "win32":
            # Read from registry for pending reboot
            import winreg  # pylint: disable=import-error,import-outside-toplevel

            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            # Check for "Reboot Required" keys
            try:
                key = winreg.OpenKey(
                    reg,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
                )
                winreg.CloseKey(key)
                return True
            except OSError:
                pass
            try:
                key = winreg.OpenKey(
                    reg,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
                )
                winreg.CloseKey(key)
                return True
            except OSError:
                pass
            # Check for recent installation requiring reboot
            try:
                key = winreg.OpenKey(
                    reg,
                    r"SOFTWARE\Microsoft\Updates\UpdateExeVolatile",
                )
                winreg.CloseKey(key)
                return True
            except OSError:
                pass
            # Check for System Center Configuration Manager
            try:
                key = winreg.OpenKey(
                    reg,
                    r"SOFTWARE\Microsoft\SMS\Mobile Client\Reboot Management\RebootData",
                )
                winreg.CloseKey(key)
                return True
            except OSError:
                pass
            # Check for pending file rename operations
            try:
                key = winreg.OpenKey(
                    reg,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager",
                )
                value, _ = winreg.QueryValueEx(key, "PendingFileRenameOperations")
                winreg.CloseKey(key)
                if value:
                    return True
            except OSError:
                pass
        elif sys.platform in ["darwin", "linux"]:
            if os.path.exists("/var/run/reboot-required"):
                return True
            if os.path.exists("/var/run/reboot-required.pkgs"):
                return True
        return False

    async def _get_platform(self) -> str:
        """Get platform"""
        return platform.system()

    async def _get_platform_version(self) -> str:
        """Get platform version"""
        return platform.version()

    async def _get_uptime(self) -> float:
        """Get uptime"""
        return os.times().system

    async def _get_users(self) -> list[suser]:  # pylint: disable=unsubscriptable-object
        """Get users"""
        return users()

    @property
    def _uuid(self) -> str:
        """Get UUID"""
        return uniqueid.id or self._mac_address

    async def _get_version_latest(self) -> Any | None:
        """Get latest version from GitHub"""
        self._logger.info("Get latest version from GitHub")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/repos/timmo001/system-bridge/releases/latest"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if (
                        data is not None
                        and (tag_name := data.get("tag_name")) is not None
                    ):
                        return tag_name.replace("v", "")

        return None

    async def _get_version_newer_available(self) -> bool | None:
        """Check if newer version is available"""
        if self._version_latest is not None:
            return parse_version(self._version_latest) > parse_version(self._version)
        return None

    @override
    async def update_all_data(self) -> System:
        """Update all data"""
        self._logger.debug("Update all data")

        (
            active_user_name,
            boot_time_result,
            camera_usage,
            fqdn,
            hostname,
            ip_address_4,
            ip_address_6,
            pending_reboot,
            platform_result,
            platform_version,
            uptime,
            users_result,
            version_latest,
        ) = await asyncio.gather(
            *[
                self._get_active_user_name(),
                self._get_boot_time(),
                self._get_camera_usage(),
                self._get_fqdn(),
                self._get_hostname(),
                self._get_ip_address_4(),
                self._get_ip_address_6(),
                self._get_pending_reboot(),
                self._get_platform(),
                self._get_platform_version(),
                self._get_uptime(),
                self._get_users(),
                self._get_version_latest(),
            ]
        )

        return System(
            boot_time=boot_time_result,
            fqdn=fqdn,
            hostname=hostname,
            ip_address_4=ip_address_4,
            mac_address=self._mac_address,
            platform_version=platform_version,
            platform=platform_result,
            uptime=uptime,
            users=[
                SystemUser(
                    name=user.name,
                    active=user.name == active_user_name,
                    terminal=user.terminal,
                    host=user.host,
                    started=user.started,
                    pid=user.pid,
                )
                for user in users_result
            ],
            uuid=self._uuid,
            version=self._version,
            camera_usage=camera_usage,
            ip_address_6=ip_address_6,
            pending_reboot=pending_reboot,
            version_latest=version_latest,
            version_newer_available=await self._get_version_newer_available(),
        )
