"""System Bridge: System"""
from __future__ import annotations

import asyncio
import os
import platform
import re
import socket
import sys
import uuid
from json import dumps
from typing import Any, Optional

from aiogithubapi import (
    GitHubAPI,
    GitHubConnectionException,
    GitHubException,
    GitHubRatelimitException,
)
from pkg_resources import parse_version
from plyer import uniqueid
from psutil import boot_time, users
from psutil._common import suser
from systembridgeshared.base import Base
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import System as DatabaseModel

from .._version import __version__
from .base import ModuleUpdateBase


class System(Base):
    """System"""

    def active_user_id(self) -> int:
        """Get active user ID"""
        return os.getpid()

    def active_user_name(self) -> str:
        """Get active user"""
        return os.getlogin()

    def boot_time(self) -> float:
        """Get boot time"""
        return boot_time()

    def camera_usage(self) -> list[str]:
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

    def fqdn(self) -> str:
        """Get FQDN"""
        return socket.getfqdn()

    def hostname(self) -> str:
        """Get hostname"""
        return socket.gethostname()

    def ip_address_4(self) -> str:
        """Get IPv4 address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    def ip_address_6(self) -> str:
        """Get IPv6 address"""
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect(("2001:4860:4860::8888", 80))
            return sock.getsockname()[0]
        except OSError:
            return ""

    def mac_address(self) -> str:
        """Get MAC address"""
        # pylint: disable=consider-using-f-string
        return ":".join(re.findall("..", "%012x" % uuid.getnode()))

    def pending_reboot(self) -> bool:
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

    def platform(self) -> str:
        """Get platform"""
        return platform.system()

    def platform_version(self) -> str:
        """Get platform version"""
        return platform.version()

    def uptime(self) -> float:
        """Get uptime"""
        return os.times().system

    def users(self) -> list[suser]:  # pylint: disable=unsubscriptable-object
        """Get users"""
        return users()

    def uuid(self) -> str:
        """Get UUID"""
        return uniqueid.id or self.mac_address()

    def version(self) -> str:
        """Get version"""
        return __version__.public()

    async def version_latest(self) -> Optional[Any]:
        """Get latest version from GitHub"""
        self._logger.info("Get latest version from GitHub")

        try:
            async with GitHubAPI() as github:
                releases = await github.repos.releases.list("timmo001/system-bridge")
            return releases.data[0] if releases.data else None
        except (
            GitHubConnectionException,
            GitHubRatelimitException,
        ) as error:
            self._logger.error("Error getting data from GitHub: %s", error)
        except GitHubException as error:
            self._logger.exception(
                "Unexpected error getting data from GitHub: %s", error
            )
        return None

    def version_newer_available(
        self,
        database: Database,
    ) -> Optional[bool]:
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


class SystemUpdate(ModuleUpdateBase):
    """System Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._system = System()

    async def update_active_user_id(self) -> None:
        """Update active user ID"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="active_user_id",
                value=str(self._system.active_user_id()),
            ),
        )

    async def update_active_user_name(self) -> None:
        """Update active user name"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="active_user_name",
                value=self._system.active_user_name(),
            ),
        )

    async def update_boot_time(self) -> None:
        """Update boot time"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="boot_time",
                value=str(self._system.boot_time()),
            ),
        )

    async def update_camera_usage(self) -> None:
        """Update camera usage"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="camera_usage",
                value=dumps(self._system.camera_usage()),
            ),
        )

    async def update_fqdn(self) -> None:
        """Update FQDN"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="fqdn",
                value=self._system.fqdn(),
            ),
        )

    async def update_hostname(self) -> None:
        """Update hostname"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="hostname",
                value=self._system.hostname(),
            ),
        )

    async def update_ip_address_4(self) -> None:
        """Update IP address 4"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="ip_address_4",
                value=self._system.ip_address_4(),
            ),
        )

    async def update_ip_address_6(self) -> None:
        """Update IP address 6"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="ip_address_6",
                value=self._system.ip_address_6(),
            ),
        )

    async def update_mac_address(self) -> None:
        """Update MAC address"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="mac_address",
                value=self._system.mac_address(),
            ),
        )

    async def update_pending_reboot(self) -> None:
        """Update pending reboot"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="pending_reboot",
                value=str(self._system.pending_reboot()),
            ),
        )

    async def update_platform(self) -> None:
        """Update platform"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="platform",
                value=self._system.platform(),
            ),
        )

    async def update_platform_version(self) -> None:
        """Update platform version"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="platform_version",
                value=self._system.platform_version(),
            ),
        )

    async def update_uptime(self) -> None:
        """Update uptime"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="uptime",
                value=str(self._system.uptime()),
            ),
        )

    async def update_users(self) -> None:
        """Update users"""
        for user in self._system.users():
            for key, value in user._asdict().items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"user_{user.name.replace(' ','_').lower()}_{key}",
                        value=value,
                    ),
                )

    async def update_uuid(self) -> None:
        """Update UUID"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="uuid",
                value=self._system.uuid(),
            ),
        )

    async def update_version(self) -> None:
        """Update version"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="version",
                value=self._system.version(),
            ),
        )

    async def update_version_latest(self) -> None:
        """Update latest version"""
        release = await self._system.version_latest()
        if release and release.tag_name:
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key="version_latest",
                    value=release.tag_name.replace("v", "")
                    if release is not None
                    else None,
                ),
            )

    async def update_version_newer_available(self) -> None:
        """Update newer version available"""
        value = self._system.version_newer_available(self._database)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="version_newer_available",
                value=str(value) if value else str(False),
            ),
        )

    async def update_all_data(self) -> None:
        """Update data"""
        await asyncio.gather(
            *[
                self.update_active_user_id(),
                self.update_active_user_name(),
                self.update_boot_time(),
                self.update_camera_usage(),
                self.update_fqdn(),
                self.update_hostname(),
                self.update_ip_address_4(),
                self.update_ip_address_6(),
                self.update_mac_address(),
                self.update_pending_reboot(),
                self.update_platform(),
                self.update_platform_version(),
                self.update_uptime(),
                self.update_users(),
                self.update_uuid(),
                self.update_version(),
                self.update_version_latest(),
            ]
        )
        # Run after other version updates
        await self.update_version_newer_available()
