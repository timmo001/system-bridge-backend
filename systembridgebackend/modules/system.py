"""System Bridge: System"""
from __future__ import annotations

import asyncio
import os
import platform
import re
import socket
import sys
import uuid
from typing import Any

import aiohttp
from pkg_resources import parse_version
from plyer import uniqueid
from psutil import boot_time, users
from psutil._common import suser
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import System as DatabaseModel

from .._version import __version__
from .base import ModuleUpdateBase


class SystemUpdate(ModuleUpdateBase):
    """System Update"""

    def _active_user_id(self) -> int:
        """Get active user ID"""
        return os.getpid()

    def _active_user_name(self) -> str:
        """Get active user"""
        return os.getlogin()

    def _boot_time(self) -> float:
        """Get boot time"""
        return boot_time()

    def _camera_usage(self) -> list[str]:
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

    def _fqdn(self) -> str:
        """Get FQDN"""
        return socket.getfqdn()

    def _hostname(self) -> str:
        """Get hostname"""
        return socket.gethostname()

    def _ip_address_4(self) -> str:
        """Get IPv4 address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    def _ip_address_6(self) -> str:
        """Get IPv6 address"""
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect(("2001:4860:4860::8888", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    def _mac_address(self) -> str:
        """Get MAC address"""
        # pylint: disable=consider-using-f-string
        return ":".join(re.findall("..", "%012x" % uuid.getnode()))

    def _pending_reboot(self) -> bool:
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

    def _platform(self) -> str:
        """Get platform"""
        return platform.system()

    def _platform_version(self) -> str:
        """Get platform version"""
        return platform.version()

    def _uptime(self) -> float:
        """Get uptime"""
        return os.times().system

    def _users(self) -> list[suser]:  # pylint: disable=unsubscriptable-object
        """Get users"""
        return users()

    def _uuid(self) -> str:
        """Get UUID"""
        return uniqueid.id or self._mac_address()

    def _version(self) -> str:
        """Get version"""
        return __version__.public()

    async def _version_latest(self) -> Any | None:
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

    def _version_newer_available(
        self,
        database: Database,
    ) -> bool | None:
        """Check if newer version is available"""
        version_record = database.get_data_item_by_key(DatabaseModel, "version")
        if version_record is None:
            return None
        version = version_record.value
        latest_version_record = database.get_data_item_by_key(
            DatabaseModel, "version_latest"
        )
        if latest_version_record is None:
            return None
        latest_version = latest_version_record.value
        if version is not None and latest_version is not None:
            return parse_version(latest_version) > parse_version(version)
        return None

    async def update_all_data(self) -> System:
        """Update data"""
        data = await asyncio.gather(
            *[
                self._active_user_id(),
                self._active_user_name(),
                self._boot_time(),
                self._camera_usage(),
                self._fqdn(),
                self._hostname(),
                self._ip_address_4(),
                self._ip_address_6(),
                self._mac_address(),
                self._pending_reboot(),
                self._platform(),
                self._platform_version(),
                self._uptime(),
                self._users(),
                self._uuid(),
                self._version(),
                self._version_latest(),
            ]
        )
        # Run after other version updates
        return await self._version_newer_available()
