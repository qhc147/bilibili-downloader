"""yt-dlp 版本检查模块

提供版本检查、对比和更新信息获取功能。
"""

from dataclasses import dataclass
from typing import Optional
import requests
from packaging.version import Version, InvalidVersion
import yt_dlp.version


class NetworkError(Exception):
    """网络连接异常"""
    pass


class ParseError(Exception):
    """API 响应解析异常"""
    pass


@dataclass
class VersionInfo:
    """版本信息数据类"""
    current: str
    latest: str
    has_update: bool
    changelog: str
    release_date: str


class VersionChecker:
    """yt-dlp 版本检查器"""

    PYPI_API_URL = "https://pypi.org/pypi/yt-dlp/json"
    TIMEOUT = 10

    def get_current_version(self) -> str:
        """获取本地已安装的 yt-dlp 版本

        Returns:
            str: 当前版本号，例如 "2024.04.09"
        """
        return yt_dlp.version.__version__

    def get_latest_version(self) -> VersionInfo:
        """从 PyPI API 获取最新版本信息

        Returns:
            VersionInfo: 包含最新版本的完整信息

        Raises:
            NetworkError: 网络连接失败或 API 返回错误
            ParseError: API 响应格式错误
        """
        try:
            response = requests.get(self.PYPI_API_URL, timeout=self.TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError("连接超时，请检查网络")
        except requests.exceptions.ConnectionError:
            raise NetworkError("无法连接到 PyPI，请检查网络代理")
        except requests.exceptions.ProxyError:
            raise NetworkError("代理配置错误，请检查代理设置")
        except requests.exceptions.SSLError:
            raise NetworkError("SSL 证书验证失败，请检查系统时间")
        except requests.exceptions.HTTPError as e:
            raise NetworkError(f"PyPI 服务器返回错误: {e.response.status_code if e.response else '未知'}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络请求失败: {str(e)}")

        if response.status_code != 200:
            raise NetworkError(f"PyPI 服务器返回错误: {response.status_code}")

        # 检查响应体大小，防止恶意 API 返回超大响应
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > 10:
                    raise ParseError(f"响应体过大 ({size_mb:.1f} MB)，拒绝解析")
            except ValueError:
                pass  # Content-Length 格式错误，继续处理

        try:
            data = response.json()

            # 检查 API 响应格式
            if "info" not in data:
                raise ParseError("API 响应格式错误: 缺少 info 字段")

            info = data["info"]

            if "version" not in info:
                raise ParseError("API 响应格式错误: 缺少 version 字段")

            latest_version = info["version"]

            # 提取更新日志（从 description 或 summary）
            changelog = info.get("description", "") or info.get("summary", "")

            # 提取发布日期
            releases = data.get("releases", {})
            release_info = releases.get(latest_version, [])
            release_date = ""
            if release_info and len(release_info) > 0:
                release_date = release_info[0].get("upload_time", "")
                # 格式化日期，只保留日期部分
                if release_date:
                    release_date = release_date.split("T")[0]

            current_version = self.get_current_version()
            has_update = self._compare_versions(current_version, latest_version)

            return VersionInfo(
                current=current_version,
                latest=latest_version,
                has_update=has_update,
                changelog=changelog,
                release_date=release_date
            )

        except RecursionError:
            # JSON 嵌套过深导致栈溢出
            raise ParseError("JSON 格式错误: 嵌套层级过深")
        except ParseError:
            # 重新抛出 ParseError
            raise
        except (KeyError, IndexError, ValueError) as e:
            raise ParseError(f"API 响应格式错误: {str(e)}")
        except Exception as e:
            raise ParseError(f"解析失败: {str(e)}")

    def check_update(self) -> VersionInfo:
        """检查是否有可用更新

        对比本地版本和 PyPI 最新版本，返回完整的版本信息。

        Returns:
            VersionInfo: 包含当前版本、最新版本、是否有更新等信息

        Raises:
            NetworkError: 网络连接失败
            ParseError: API 响应解析失败
        """
        return self.get_latest_version()

    def _compare_versions(self, current: str, latest: str) -> bool:
        """对比两个版本号

        Args:
            current: 当前版本号
            latest: 最新版本号

        Returns:
            bool: 如果最新版本大于当前版本返回 True，否则返回 False
        """
        try:
            current_ver = Version(current)
            latest_ver = Version(latest)
            return latest_ver > current_ver
        except InvalidVersion:
            # 如果版本号格式无效，使用字符串对比
            return latest > current
