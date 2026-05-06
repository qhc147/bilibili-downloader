"""
yt-dlp 更新管理器

协调版本检查、更新执行和 UI 交互的中间层。
负责线程管理和状态同步。
"""

import threading
from typing import Callable, Any
from src.updater.version_checker import VersionChecker, VersionInfo, NetworkError, ParseError
from src.updater.updater import Updater, UpdateError, PipNotFoundError, BackupError, RollbackError


class UpdateManager:
    """更新管理器，协调版本检查和更新流程"""

    def __init__(self, app):
        """
        初始化更新管理器

        Args:
            app: 主窗口实例（用于 after 调度）
        """
        self._app = app
        self._version_checker = VersionChecker()
        self._updater = Updater()
        self._is_checking = False
        self._is_updating = False

    def check_update(self, on_result: Callable[[bool, Any], None]):
        """
        后台检查更新

        Args:
            on_result: 回调函数，签名为 (success: bool, data: Any)
                      成功时 data 为 VersionInfo
                      失败时 data 为错误信息字符串
        """
        if self._is_checking:
            return

        self._is_checking = True

        def _check_thread():
            try:
                version_info = self._version_checker.check_update()
                # 在主线程调用回调
                self._app.after(0, lambda: self._on_check_complete(True, version_info, on_result))
            except (NetworkError, ParseError) as e:
                # 立即捕获异常字符串，避免闭包引用被覆盖
                error_msg = str(e)
                self._app.after(0, lambda: self._on_check_complete(False, error_msg, on_result))
            except Exception as e:
                # 捕获所有未预期的异常
                error_msg = f"未知错误: {str(e)}"
                self._app.after(0, lambda: self._on_check_complete(False, error_msg, on_result))

        thread = threading.Thread(target=_check_thread, daemon=True)
        thread.start()

    def _on_check_complete(self, success: bool, data: Any, callback: Callable):
        """检查完成的内部回调"""
        self._is_checking = False
        callback(success, data)

    def start_update(
        self,
        on_progress: Callable[[str], None],
        on_complete: Callable[[bool, str], None]
    ):
        """
        后台执行更新

        Args:
            on_progress: 进度回调，接收状态字符串
            on_complete: 完成回调，签名为 (success: bool, message: str)
        """
        if self._is_updating:
            return

        self._is_updating = True

        def _update_thread():
            try:
                # 进度回调包装（在主线程执行）
                def progress_wrapper(line: str):
                    self._app.after(0, on_progress, line)

                # 执行更新
                self._updater.update(on_progress=progress_wrapper)

                # 更新成功
                self._app.after(0, lambda: self._on_update_complete(True, "更新成功", on_complete))

            except PipNotFoundError as e:
                error_msg = str(e)
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))
            except BackupError as e:
                error_msg = f"备份失败: {str(e)}"
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))
            except RollbackError as e:
                error_msg = str(e)
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))
            except UpdateError as e:
                error_msg = str(e)
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))
            except PermissionError as e:
                error_msg = "权限不足，请以管理员身份运行软件"
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))
            except Exception as e:
                error_type = type(e).__name__
                error_msg = f"未知错误 ({error_type}): {str(e)}"
                self._app.after(0, lambda: self._on_update_complete(False, error_msg, on_complete))

        thread = threading.Thread(target=_update_thread, daemon=True)
        thread.start()

    def _on_update_complete(self, success: bool, message: str, callback: Callable):
        """更新完成的内部回调"""
        self._is_updating = False
        callback(success, message)

    def is_busy(self) -> bool:
        """
        检查是否有操作正在进行

        Returns:
            bool: 如果正在检查更新或正在更新返回 True
        """
        return self._is_checking or self._is_updating
