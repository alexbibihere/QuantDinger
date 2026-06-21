#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 趋势邮件通知服务

通过 SMTP 发送 HAMA 金叉/死叉趋势变化邮件通知。
"""
from __future__ import annotations

import html
import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class HamaEmailNotifier:
    """HAMA 趋势邮件通知器"""

    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "").strip()
        self.smtp_port = int(os.environ.get("SMTP_PORT", "465"))
        self.smtp_user = os.environ.get("SMTP_USER", "").strip()
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
        self.smtp_from = os.environ.get("SMTP_FROM", self.smtp_user).strip()
        self.smtp_use_tls = os.environ.get("SMTP_USE_TLS", "false").strip().lower() == "true"
        self.smtp_use_ssl = os.environ.get("SMTP_USE_SSL", "true").strip().lower() == "true"
        self.default_recipients = os.environ.get("HAMA_EMAIL_RECIPIENTS", "").strip()
        self.cooldown_seconds = int(os.environ.get("HAMA_EMAIL_COOLDOWN", "3600"))
        self.last_sent_times: Dict[str, float] = {}

        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP 配置不完整，邮件通知将不可用")
        else:
            logger.info(f"HAMA 邮件通知器已初始化 (SMTP: {self.smtp_host}:{self.smtp_port}, 收件人: {self.default_recipients})")

    def is_cooldown_active(self, symbol: str) -> bool:
        if symbol not in self.last_sent_times:
            return False
        elapsed = time.time() - self.last_sent_times[symbol]
        if elapsed < self.cooldown_seconds:
            remaining = int(self.cooldown_seconds - elapsed)
            logger.info(f"{symbol} 邮件冷却中，剩余 {remaining} 秒")
            return True
        return False

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
        screenshot_path: Optional[str] = None,
        full_chart_path: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        recipients: Optional[str] = None,
    ) -> bool:
        if self.is_cooldown_active(symbol):
            return False

        to_list = recipients or self.default_recipients
        if not to_list:
            logger.warning("没有配置收件人，跳过邮件发送")
            return False

        if cross_type == "cross_up":
            signal_emoji = "🟢"
            signal_text = "金叉信号 (Golden Cross)"
        elif cross_type == "cross_down":
            signal_emoji = "🔴"
            signal_text = "死叉信号 (Death Cross)"
        else:
            signal_emoji = "📊"
            signal_text = f"HAMA 趋势变化 ({hama_color})"

        subject = f"{signal_emoji} HAMA {signal_text} - {symbol}"
        color_dot = "🟢" if hama_color == "green" else ("🔴" if hama_color == "red" else "⚪")
        price_str = f"{price:.8f}".rstrip("0").rstrip(".") if price else "N/A"
        hama_str = f"{hama_value:.8f}".rstrip("0").rstrip(".") if hama_value else "N/A"

        rows = [
            ("币种", symbol),
            ("趋势", trend),
            ("HAMA 状态", f"{color_dot} {hama_color}"),
            ("HAMA 值", hama_str),
            ("价格", price_str),
            ("信号类型", signal_text),
            ("时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ]
        if extra_data:
            for k, v in extra_data.items():
                if v:
                    rows.append((k.replace("_", " ").title(), str(v)))

        tr_html = "\n".join(
            [
                (
                    "<tr>"
                    "<td style='padding:10px 12px;border-top:1px solid #eaecef;color:#57606a;width:160px;'>"
                    f"{html.escape(k)}"
                    "</td>"
                    "<td style='padding:10px 12px;border-top:1px solid #eaecef;color:#24292f;font-family:ui-monospace,monospace;'>"
                    f"{html.escape(str(v))}"
                    "</td>"
                    "</tr>"
                )
                for (k, v) in rows
            ]
        )

        html_body = f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f6f8fa;">
    <div style="max-width:640px;margin:0 auto;padding:24px;">
      <div style="background:#111827;color:#ffffff;padding:16px 18px;border-radius:12px 12px 0 0;">
        <div style="font-size:16px;font-weight:600;">{html.escape(subject)}</div>
        <div style="margin-top:6px;font-size:12px;color:#d1d5db;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
      </div>
      <div style="background:#ffffff;border:1px solid #eaecef;border-top:0;border-radius:0 0 12px 12px;overflow:hidden;">
        <table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;">
          {tr_html}
        </table>
        <div style="padding:14px 16px;color:#6e7781;font-size:12px;border-top:1px solid #eaecef;">
          Generated by QuantDinger HAMA Monitor
        </div>
      </div>
    </div>
  </body>
</html>"""

        text_body = "\n".join([f"{k}: {v}" for (k, v) in rows])

        success = self._send_email(
            to_list=to_list,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
        )

        if success:
            self.last_sent_times[symbol] = time.time()
            logger.info(f"✅ {symbol} 趋势邮件已发送至: {to_list}")
        else:
            logger.error(f"❌ {symbol} 趋势邮件发送失败")

        return success

    def notify_batch_complete(
        self, *, total: int, success: int, failed: int, symbols: List[str], recipients: Optional[str] = None
    ) -> bool:
        subject = f"📊 HAMA 批量监控完成 ({success}/{total})"
        text_body = f"HAMA 批量监控完成\n成功: {success}\n失败: {failed}\n总计: {total}\n币种: {', '.join(symbols)}"
        html_body = (
            "<h2>HAMA 批量监控完成</h2>"
            f"<p>成功: {success} | 失败: {failed} | 总计: {total}</p>"
            f"<p>币种: {', '.join(symbols)}</p>"
        )
        to_list = recipients or self.default_recipients
        if not to_list:
            return False
        return self._send_email(to_list=to_list, subject=subject, body_text=text_body, body_html=html_body)

    def _send_email(self, *, to_list: str, subject: str, body_text: str, body_html: str) -> bool:
        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP 未配置，无法发送邮件")
            return False
        if not to_list:
            logger.warning("收件人为空，无法发送邮件")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_from
            msg["To"] = to_list
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))
            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=15) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            logger.info(f"邮件发送成功: {subject} -> {to_list}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP 登录失败，请检查用户名/密码")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 发送异常: {e}")
            return False
        except Exception as e:
            logger.error(f"邮件发送异常: {e}")
            return False


_hama_email_notifier = None


def get_hama_email_notifier() -> HamaEmailNotifier:
    global _hama_email_notifier
    if _hama_email_notifier is None:
        _hama_email_notifier = HamaEmailNotifier()
    return _hama_email_notifier
