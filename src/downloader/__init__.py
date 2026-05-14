def friendly_error(msg: str) -> str:
    if "No video formats found" in msg:
        if "Bangumi" in msg or "bangumi" in msg:
            return "该番剧需要大会员才能下载，当前账号无权限访问此内容"
        return "无法获取视频流，可能需要大会员或该视频已下架"
    if "geo" in msg.lower() or "not available in your" in msg.lower():
        return "该视频存在地区限制，当前网络无法访问"
    if "login" in msg.lower() or "credential" in msg.lower():
        return "需要登录才能访问此内容，请先扫码登录"
    if "timed out" in msg.lower() or "connection" in msg.lower():
        return "网络连接超时，请检查网络后重试"
    return msg
