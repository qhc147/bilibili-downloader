"""
yt-dlp 更新执行模块

提供 yt-dlp 的备份、更新和回滚功能。
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from typing import Callable, Optional
from pathlib import Path


# 自定义异常
class BackupError(Exception):
    """备份失败异常"""
    pass


class PipNotFoundError(Exception):
    """pip 不存在异常"""
    pass


class UpdateError(Exception):
    """更新失败异常"""
    pass


class RollbackError(Exception):
    """回滚失败异常"""
    pass


class Updater:
    """yt-dlp 更新器"""

    def __init__(self):
        """初始化更新器，定位关键路径"""
        # 软件根目录：从 python.exe 往上两级
        # python\python.exe -> python\ -> 根目录
        self.python_exe = sys.executable
        self.python_dir = os.path.dirname(self.python_exe)
        self.root_dir = os.path.dirname(self.python_dir)

        # pip 路径（使用 Path 规范化并校验）
        pip_path = Path(self.python_dir) / "Scripts" / "pip.exe"
        try:
            # 规范化路径，解析符号链接和相对路径
            pip_resolved = pip_path.resolve(strict=True)
            # 验证路径在预期目录内（防止路径遍历攻击）
            python_dir_resolved = Path(self.python_dir).resolve()
            if not str(pip_resolved).startswith(str(python_dir_resolved)):
                raise PipNotFoundError(f"pip 路径不在预期目录内: {pip_resolved}")
            self.pip_exe = str(pip_resolved)
        except (FileNotFoundError, RuntimeError):
            raise PipNotFoundError(f"pip 未找到: {pip_path}")

        # yt-dlp 安装路径（规范化路径）
        ytdlp_path = Path(self.python_dir) / "Lib" / "site-packages" / "yt_dlp"
        self.ytdlp_dir = str(ytdlp_path.resolve())

        # 备份根目录（规范化路径）
        backup_path = Path(self.root_dir) / "backup"
        self.backup_root = str(backup_path.resolve())

    def _check_disk_space(self, required_mb: int = 10):
        """
        检查磁盘空间是否足够

        Args:
            required_mb: 需要的最小空间（MB）

        Raises:
            BackupError: 磁盘空间不足
        """
        try:
            stat = shutil.disk_usage(self.root_dir)
            free_mb = stat.free / (1024 * 1024)
            if free_mb < required_mb:
                raise BackupError(f"磁盘空间不足，至少需要 {required_mb} MB")
        except BackupError:
            # 重新抛出 BackupError
            raise
        except Exception:
            # 检查失败时假设空间足够（避免误拦）
            pass

    def _get_backup_path(self) -> str:
        """
        生成备份路径（带时间戳，避免冲突）

        Returns:
            str: 备份目录路径
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_path = os.path.join(
            self.backup_root,
            f"yt-dlp-backup-{timestamp}"
        )

        # 如果路径已存在，加序号
        if not os.path.exists(base_path):
            return base_path

        counter = 1
        while True:
            path = f"{base_path}-{counter}"
            if not os.path.exists(path):
                return path
            counter += 1

    def backup_current_version(self) -> str:
        """
        备份当前 yt-dlp 版本

        Returns:
            str: 备份路径

        Raises:
            BackupError: 备份失败
        """
        # 检查 yt-dlp 是否存在
        if not os.path.exists(self.ytdlp_dir):
            raise BackupError(f"yt-dlp 目录不存在: {self.ytdlp_dir}")

        # 检查磁盘空间
        self._check_disk_space(10)

        # 生成备份路径
        backup_path = self._get_backup_path()

        try:
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)

            # 复制 yt_dlp 目录
            backup_ytdlp_dir = os.path.join(backup_path, "yt_dlp")
            shutil.copytree(self.ytdlp_dir, backup_ytdlp_dir)

            # 验证备份完整性：检查关键文件是否存在
            critical_files = ["__init__.py", "version.py"]
            for filename in critical_files:
                file_path = os.path.join(backup_ytdlp_dir, filename)
                if not os.path.exists(file_path):
                    # 验证失败，删除备份目录
                    shutil.rmtree(backup_path)
                    raise BackupError(f"备份验证失败: {filename} 不存在")

            return backup_path

        except PermissionError as e:
            # 清理失败的备份
            if os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                except Exception:
                    pass
            raise BackupError(f"权限不足，请以管理员身份运行软件")
        except OSError as e:
            # 清理失败的备份
            if os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                except Exception:
                    pass
            raise BackupError(f"无法创建备份目录: {backup_path}")
        except Exception as e:
            # 清理失败的备份
            if os.path.exists(backup_path):
                try:
                    shutil.rmtree(backup_path)
                except Exception:
                    pass
            raise BackupError(f"备份失败: {str(e)}")

    def update(self, on_progress: Optional[Callable[[str], None]] = None) -> bool:
        """
        执行 yt-dlp 更新

        Args:
            on_progress: 进度回调函数，接收输出行

        Returns:
            bool: 更新是否成功

        Raises:
            PipNotFoundError: pip 不存在
            UpdateError: 更新失败（已自动回滚）
        """
        # 检查 pip 是否存在
        if not os.path.exists(self.pip_exe):
            raise PipNotFoundError("pip 未找到，请检查 Python 环境")

        # 备份当前版本
        try:
            backup_path = self.backup_current_version()
        except BackupError as e:
            raise UpdateError(f"备份失败，更新中止: {str(e)}")

        # 执行更新
        try:
            cmd = [self.pip_exe, "install", "--upgrade", "yt-dlp"]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 捕获输出
            for line in process.stdout:
                line = line.rstrip()
                if on_progress:
                    on_progress(line)

            # 等待进程结束
            return_code = process.wait()

            # 检查返回码
            if return_code != 0:
                # 更新失败，自动回滚
                try:
                    self.rollback(backup_path)
                    raise UpdateError(
                        f"更新失败（返回码 {return_code}），已自动回滚"
                    )
                except RollbackError as e:
                    raise UpdateError(
                        f"更新失败且回滚失败: {str(e)}"
                    )

            return True

        except PermissionError as e:
            # 权限不足，尝试回滚
            try:
                self.rollback(backup_path)
                raise UpdateError("权限不足，请以管理员身份运行软件")
            except RollbackError as e:
                raise UpdateError(
                    f"权限不足且回滚失败: {str(e)}"
                )
        except subprocess.SubprocessError as e:
            # 进程执行异常，尝试回滚
            try:
                self.rollback(backup_path)
                raise UpdateError(f"更新进程异常，已自动回滚: {str(e)}")
            except RollbackError as e:
                raise UpdateError(
                    f"更新进程异常且回滚失败: {str(e)}"
                )

    def rollback(self, backup_path: str) -> bool:
        """
        从备份回滚 yt-dlp

        Args:
            backup_path: 备份目录路径

        Returns:
            bool: 回滚是否成功

        Raises:
            RollbackError: 回滚失败
        """
        # 检查备份路径是否存在
        backup_ytdlp_dir = os.path.join(backup_path, "yt_dlp")
        if not os.path.exists(backup_ytdlp_dir):
            raise RollbackError(f"备份路径不存在: {backup_ytdlp_dir}")

        # 原子性回滚：先复制到临时目录，验证后再替换
        temp_dir = self.ytdlp_dir + "_temp"

        try:
            # 步骤 1: 复制备份到临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            shutil.copytree(backup_ytdlp_dir, temp_dir)

            # 步骤 2: 验证临时目录完整性
            init_file = os.path.join(temp_dir, "__init__.py")
            if not os.path.exists(init_file):
                raise RollbackError("备份验证失败: __init__.py 不存在")

            # 步骤 3: 删除当前 yt_dlp 目录
            if os.path.exists(self.ytdlp_dir):
                shutil.rmtree(self.ytdlp_dir)

            # 步骤 4: 重命名临时目录为正式目录
            os.rename(temp_dir, self.ytdlp_dir)

            return True

        except Exception as e:
            # 清理临时目录
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            raise RollbackError(
                f"回滚失败: {str(e)}。备份路径: {backup_path}"
            )
