#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 趋势邮件通知服务
当 HAMA 监控识别到趋势形成时发送邮件通知
"""
import os
import smtplib
import html
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Dict, Any, Optional, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class HamaEmailNotifier:
    """HAMA 趋势邮件通知器"""

    def __init__(self):
        """初始化邮件通知器"""
        # SMTP 配置
        self.smtp_host = (os.getenv("SMTP_HOST") or "").strip()
        try:
            self.smtp_port = int(os.getenv("SMTP_PORT") or "587")
        except Exception:
            self.smtp_port = 587
        self.smtp_user = (os.getenv("SMTP_USER") or "").strip()
        self.smtp_password = (os.getenv("SMTP_PASSWORD") or "").strip()
        self.smtp_from = (os.getenv("SMTP_FROM") or self.smtp_user or "").strip()
        self.smtp_use_tls = (os.getenv("SMTP_USE_TLS") or "true").strip().lower() == "true"
        self.smtp_use_ssl = (os.getenv("SMTP_USE_SSL") or "").strip().lower() == "true"

        # 默认收件人（可配置多个，逗号分隔）
        self.default_recipients = os.getenv("HAMA_EMAIL_RECIPIENTS", "").strip()

        # 邮件通知冷却时间（秒），避免频繁发送
        self.cooldown_seconds = int(os.getenv("HAMA_EMAIL_COOLDOWN", "3600"))  # 默认1小时

        # 记录上次发送时间（用于冷却控制）- 从数据库加载
        self.last_sent_times = self._load_last_sent_times_from_db()  # {symbol: timestamp}

        logger.info(f"HAMA邮件通知器初始化完成 (冷却时间: {self.cooldown_seconds}秒)")
        logger.info(f"从数据库加载了 {len(self.last_sent_times)} 个币种的邮件发送时间")

    def is_cooldown_active(self, symbol: str) -> bool:
        """
        检查是否在冷却期内

        Args:
            symbol: 币种符号

        Returns:
            True 表示在冷却期内，不应发送邮件
        """
        if symbol not in self.last_sent_times:
            return False

        elapsed = datetime.now().timestamp() - self.last_sent_times[symbol]
        return elapsed < self.cooldown_seconds

    def notify_trend_formed(
        self,
        *,
        symbol: str,
        trend: str,
        hama_color: str,
        hama_value: float,
        price: float,
        cross_type: Optional[str] = None,
        screenshot_url: Optional[str] = None,
        screenshot_path: Optional[str] = None,  # 新增：截图文件路径
        extra_data: Optional[Dict[str, Any]] = None,
        recipients: Optional[str] = None
    ) -> bool:
        """
        发送 HAMA 趋势形成通知邮件

        Args:
            symbol: 币种符号
            trend: 趋势方向 (up/down/neutral)
            hama_color: HAMA 颜色 (green/red)
            hama_value: HAMA 值
            price: 当前价格
            cross_type: 交叉类型 (cross_up/cross_down) - 可选
            screenshot_url: 截图 URL - 可选
            screenshot_path: 截图文件路径（用于附件）- 可选
            extra_data: 额外数据 - 可选
            recipients: 收件人邮箱（逗号分隔），不指定则使用默认收件人

        Returns:
            是否发送成功
        """
        # 检查 SMTP 配置
        if not self.smtp_host:
            logger.warning("SMTP_HOST 未配置，无法发送邮件")
            return False
        if not self.smtp_from:
            logger.warning("SMTP_FROM 未配置，无法发送邮件")
            return False

        # 检查冷却时间
        if self.is_cooldown_active(symbol):
            logger.info(f"{symbol} 在冷却期内，跳过邮件发送")
            return False

        # 确定收件人
        to_emails = recipients or self.default_recipients
        if not to_emails:
            logger.warning("未指定邮件收件人，跳过发送")
            return False

        # 解析收件人列表
        recipient_list = [email.strip() for email in to_emails.split(",") if email.strip()]
        if not recipient_list:
            logger.warning("收件人列表为空，跳过发送")
            return False

        try:
            # 构建邮件内容
            subject, body_text, body_html = self._build_trend_email(
                symbol=symbol,
                trend=trend,
                hama_color=hama_color,
                hama_value=hama_value,
                price=price,
                cross_type=cross_type,
                screenshot_url=screenshot_url,
                extra_data=extra_data
            )

            # 发送邮件
            msg = EmailMessage()
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(recipient_list)
            msg["Subject"] = subject
            msg.set_content(body_text)
            if body_html:
                msg.add_alternative(body_html, subtype="html")

            # 添加截图附件（如果提供了文件路径）
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    with open(screenshot_path, 'rb') as f:
                        image_data = f.read()
                        msg.add_attachment(
                            image_data,
                            maintype='image',
                            subtype='png',
                            filename=os.path.basename(screenshot_path)
                        )
                    logger.info(f"✅ 已添加截图附件: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"添加截图附件失败: {e}")

            # 连接 SMTP 服务器并发送
            use_ssl = bool(self.smtp_use_ssl) or int(self.smtp_port or 0) == 465
            if use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if self.smtp_use_tls:
                        server.starttls()
                        server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            # 更新最后发送时间
            self.last_sent_times[symbol] = datetime.now().timestamp()

            logger.info(f"✅ {symbol} HAMA 趋势邮件已发送至 {len(recipient_list)} 个收件人")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败 {symbol}: {e}")
            return False

    def _build_trend_email(
        self,
        *,
        symbol: str,
        trend: str,
        hama_color: str,
        hama_value: float,
        price: float,
        cross_type: Optional[str],
        screenshot_url: Optional[str],
        extra_data: Optional[Dict[str, Any]]
    ) -> tuple[str, str, str]:
        """
        构建 HAMA 趋势邮件内容

        Returns:
            (subject, body_text, body_html)
        """
        now = datetime.now(timezone.utc)
        timestamp_iso = now.isoformat()
        timestamp_cn = now.strftime("%Y-%m-%d %H:%M:%S")

        # 趋势描述
        trend_text = {
            "up": "🟢 上涨趋势",
            "down": "🔴 下跌趋势",
            "neutral": "⚪ 中性"
        }.get(trend, "⚪ 未知")

        # 颜色描述
        color_text = {
            "green": "绿色（看涨）",
            "red": "红色（看跌）"
        }.get(hama_color, hama_color)

        # 交叉信号
        signal_text = ""
        if cross_type == "cross_up":
            signal_text = "🟢 金叉信号 (HAMA Close 上穿 MA)"
        elif cross_type == "cross_down":
            signal_text = "🔴 死叉信号 (HAMA Close 下穿 MA)"

        # 邮件主题
        subject = f"🎯 HAMA趋势提醒 | {symbol} | {trend_text}"

        # 纯文本内容
        text_lines = [
            "QuantDinger HAMA 趋势监控",
            "",
            f"币种: {symbol}",
            f"时间: {timestamp_cn} (UTC)",
            "",
            "=== HAMA 状态 ===",
            f"趋势: {trend_text}",
            f"颜色: {color_text}",
            f"HAMA 值: {hama_value:.6f}",
            f"当前价格: ${price:.6f}",
        ]

        if signal_text:
            text_lines.append(f"信号: {signal_text}")

        # 额外数据
        if extra_data:
            text_lines.append("")
            text_lines.append("=== 额外信息 ===")
            for key, value in extra_data.items():
                if value is not None:
                    text_lines.append(f"{key}: {value}")

        # 截图链接
        if screenshot_url:
            text_lines.append("")
            text_lines.append(f"截图: {screenshot_url}")

        text_lines.append("")
        text_lines.append("---")
        text_lines.append("本邮件由 QuantDinger HAMA 监控系统自动发送")
        text_lines.append("如需停止接收此邮件，请联系管理员")

        body_text = "\n".join(text_lines)

        # HTML 内容
        def esc(s):
            return html.escape(str(s or ""))

        # 趋势颜色
        trend_color = "#2ECC71" if trend == "up" else ("#E74C3C" if trend == "down" else "#95A5A6")
        hama_color_bg = "#2ECC71" if hama_color == "green" else "#E74C3C"

        # 构建表格行
        table_rows = [
            ("币种", esc(symbol)),
            ("时间", esc(timestamp_cn)),
            ("趋势", f"<span style='color:{trend_color};font-weight:bold;'>{esc(trend_text)}</span>"),
            ("HAMA 颜色", f"<span style='color:{hama_color_bg};font-weight:bold;'>{esc(color_text)}</span>"),
            ("HAMA 值", f"{hama_value:.6f}"),
            ("当前价格", f"${price:.6f}"),
        ]

        if signal_text:
            table_rows.append(("信号", esc(signal_text)))

        # 多时间周期数据
        if extra_data and 'timeframes' in extra_data:
            timeframes = extra_data['timeframes']

            # 添加15分钟周期
            if '15m' in timeframes:
                tf_15m = timeframes['15m']
                tf_color_15m = "#2ECC71" if tf_15m.get('color') == 'green' else "#E74C3C"
                tf_trend_15m = "🟢 上涨" if tf_15m.get('trend') == 'up' else ("🔴 下跌" if tf_15m.get('trend') == 'down' else "⚪ 中性")
                table_rows.append((
                    "15m 周期",
                    f"<span style='color:{tf_color_15m};font-weight:bold;'>{esc(tf_trend_15m)}</span> | 值: {tf_15m.get('hama_value', 0):.6f}"
                ))

            # 添加1小时周期
            if '1h' in timeframes:
                tf_1h = timeframes['1h']
                tf_color_1h = "#2ECC71" if tf_1h.get('color') == 'green' else "#E74C3C"
                tf_trend_1h = "🟢 上涨" if tf_1h.get('trend') == 'up' else ("🔴 下跌" if tf_1h.get('trend') == 'down' else "⚪ 中性")
                table_rows.append((
                    "1h 周期",
                    f"<span style='color:{tf_color_1h};font-weight:bold;'>{esc(tf_trend_1h)}</span> | 值: {tf_1h.get('hama_value', 0):.6f}"
                ))

            # 添加4小时周期
            if '4h' in timeframes:
                tf_4h = timeframes['4h']
                tf_color_4h = "#2ECC71" if tf_4h.get('color') == 'green' else "#E74C3C"
                tf_trend_4h = "🟢 上涨" if tf_4h.get('trend') == 'up' else ("🔴 下跌" if tf_4h.get('trend') == 'down' else "⚪ 中性")
                table_rows.append((
                    "4h 周期",
                    f"<span style='color:{tf_color_4h};font-weight:bold;'>{esc(tf_trend_4h)}</span> | 值: {tf_4h.get('hama_value', 0):.6f}"
                ))

        # 额外数据（排除 timeframes 避免重复显示）
        if extra_data:
            for key, value in extra_data.items():
                if key != 'timeframes' and value is not None:
                    table_rows.append((esc(key), esc(str(value))))

        # 生成表格 HTML
        tr_html = "\n".join([
            f"""<tr>
                <td style='padding:12px 16px;border-top:1px solid #eaecef;color:#57606a;width:180px;'>
                    {esc(k)}
                </td>
                <td style='padding:12px 16px;border-top:1px solid #eaecef;color:#24292f;'>
                    {v}
                </td>
            </tr>"""
            for k, v in table_rows
        ])

        # 截图 HTML（如果有）
        screenshot_html = ""
        if screenshot_url:
            screenshot_html = f"""
            <tr>
                <td style='padding:12px 16px;border-top:1px solid #eaecef;color:#57606a;'>
                    截图
                </td>
                <td style='padding:12px 16px;border-top:1px solid #eaecef;'>
                    <a href='{esc(screenshot_url)}' style='color:#0969da;text-decoration:none;'>点击查看截图</a>
                </td>
            </tr>
            """

        body_html = f"""<!doctype html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ margin:0; padding:0; background:#f6f8fa; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; }}
    </style>
</head>
<body>
    <div style="max-width:640px;margin:0 auto;padding:24px;">
        <!-- 头部 -->
        <div style="background:#111827;color:#ffffff;padding:20px 24px;border-radius:12px 12px 0 0;">
            <div style="font-size:18px;font-weight:600;letter-spacing:0.3px;">
                🎯 HAMA 趋势监控提醒
            </div>
            <div style="margin-top:8px;font-size:13px;color:#9CA3AF;">
                {esc(timestamp_iso)}
            </div>
        </div>

        <!-- 内容 -->
        <div style="background:#ffffff;border:1px solid #eaecef;border-top:0;border-radius:0 0 12px 12px;overflow:hidden;">
            <table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;">
                {tr_html}
                {screenshot_html}
            </table>

            <!-- 底部 -->
            <div style="padding:16px 24px;background:#f9fafb;border-top:1px solid #eaecef;color:#6e7781;font-size:12px;">
                <p style="margin:0 0 8px 0;">
                    本邮件由 QuantDinger HAMA 监控系统自动发送
                </p>
                <p style="margin:0;color:#9CA3AF;">
                    提示: 同一币种在 {self.cooldown_seconds // 60} 分钟内只会发送一次提醒
                </p>
            </div>
        </div>

        <!-- 页脚 -->
        <div style="text-align:center;padding:24px 0 12px 0;color:#6e7781;font-size:11px;">
            QuantDinger - 本地优先的 AI 量化交易平台
        </div>
    </div>
</body>
</html>
"""

        return subject, body_text, body_html

    def notify_batch_complete(
        self,
        *,
        total: int,
        success: int,
        failed: int,
        symbols: List[str],
        recipients: Optional[str] = None
    ) -> bool:
        """
        发送批量监控完成通知（可选，用于汇总报告）

        Args:
            total: 总币种数
            success: 成功数
            failed: 失败数
            symbols: 所有币种列表
            recipients: 收件人

        Returns:
            是否发送成功
        """
        # 检查配置
        if not self.smtp_host or not self.smtp_from:
            return False

        to_emails = recipients or self.default_recipients
        if not to_emails:
            return False

        recipient_list = [email.strip() for email in to_emails.split(",") if email.strip()]
        if not recipient_list:
            return False

        try:
            now = datetime.now(timezone.utc)
            subject = f"📊 HAMA批量监控完成报告 | {success}/{total}"

            text_lines = [
                "QuantDinger HAMA 批量监控报告",
                "",
                f"时间: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                f"总计: {total} 个币种",
                f"成功: {success} 个",
                f"失败: {failed} 个",
                "",
                "监控币种列表:",
            ]
            text_lines.extend([f"  - {s}" for s in symbols])
            text_lines.append("")
            text_lines.append("---")
            text_lines.append("QuantDinger HAMA 监控系统")

            msg = EmailMessage()
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(recipient_list)
            msg["Subject"] = subject
            msg.set_content("\n".join(text_lines))

            # 发送
            use_ssl = bool(self.smtp_use_ssl) or int(self.smtp_port or 0) == 465
            if use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    if self.smtp_use_tls:
                        server.starttls()
                        server.ehlo()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"批量监控报告邮件已发送")
            return True

        except Exception as e:
            logger.error(f"发送批量报告邮件失败: {e}")
            return False

    def _load_last_sent_times_from_db(self) -> Dict[str, float]:
        """
        从数据库加载上次发送邮件的时间，用于重启后恢复冷却控制

        Returns:
            {symbol: timestamp}
        """
        last_sent_times = {}

        try:
            import sqlite3
            import os

            # 数据库路径
            db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db'
            )
            db_path = os.path.abspath(db_path)

            if not os.path.exists(db_path):
                logger.info("数据库文件不存在，无法加载邮件发送时间")
                return last_sent_times

            # 连接数据库
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询所有发送过邮件的币种和时间
            cursor.execute("""
                SELECT symbol, email_sent_at
                FROM hama_monitor_cache
                WHERE email_sent = 1 AND email_sent_at IS NOT NULL
                ORDER BY email_sent_at DESC
            """)

            rows = cursor.fetchall()

            for row in rows:
                symbol = row['symbol']
                sent_at = row['email_sent_at']

                # 转换为时间戳
                if isinstance(sent_at, str):
                    try:
                        # SQLite 存储的是字符串格式的时间
                        dt = datetime.fromisoformat(sent_at.replace('T', ' ').replace('+00:00', ''))
                        timestamp = dt.timestamp()
                    except:
                        continue
                else:
                    continue

                # 只保留第一次出现的（最新的发送时间）
                if symbol not in last_sent_times:
                    last_sent_times[symbol] = timestamp

            conn.close()
            logger.info(f"✅ 从数据库加载了 {len(last_sent_times)} 个币种的邮件发送时间")

        except Exception as e:
            logger.warning(f"从数据库加载邮件发送时间失败: {e}")

        return last_sent_times


# 全局单例
_hama_email_notifier = None


def get_hama_email_notifier() -> HamaEmailNotifier:
    """获取 HAMA 邮件通知器单例"""
    global _hama_email_notifier
    if _hama_email_notifier is None:
        _hama_email_notifier = HamaEmailNotifier()
    return _hama_email_notifier
