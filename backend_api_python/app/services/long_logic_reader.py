"""
LongLogic 配置读取服务

功能：
1. 读取 longLogic.txt 配置文件
2. 解析配置并应用更新
3. 支持热重载配置
"""

import os
import re
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LongLogicReader:
    """LongLogic 配置读取器"""

    def __init__(self, config_path: str = None):
        """
        初始化配置读取器

        Args:
            config_path: longLogic.txt 文件路径
        """
        if config_path is None:
            # 默认路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'file', 'longLogic.txt')

        self.config_path = config_path
        self.config = {}
        self.last_modified_time = None

        logger.info(f"LongLogic 配置读取器初始化: {config_path}")

    def read_config(self) -> Dict[str, any]:
        """
        读取 longLogic.txt 配置文件

        Returns:
            配置字典
        """
        if not os.path.exists(self.config_path):
            logger.error(f"配置文件不存在: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            config = self._parse_config(content)
            self.last_modified_time = datetime.now()

            logger.info(f"✅ 成功读取 longLogic.txt (最后修改: {self.last_modified_time})")
            return config

        except Exception as e:
            logger.error(f"读取配置文件失败: {e}", exc_info=True)
            return {}

    def _parse_config(self, content: str) -> Dict[str, any]:
        """
        解析配置文件内容

        Args:
            content: 文件内容

        Returns:
            配置字典
        """
        config = {
            'tradingview_url': None,
            'cookies': {},
            'account': {},
            'frontend_port': 8000,
            'brave_path': '',
            'hama_workflow': [],
            'email': {},
            'file_organization': {},
            'health_check_rule': ''
        }

        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            line = line.replace('\r', '')  # 移除 Windows 换行符

            # 跳过空行和箭头标记
            if not line or line.startswith('→') or line.isdigit() and len(line) < 3:
                continue

            # 解析 TradingView URL
            if 'tradingview.com/chart/' in line:
                config['tradingview_url'] = line.strip()
                logger.debug(f"找到 TradingView URL: {config['tradingview_url']}")

            # 解析 Cookie
            elif line.startswith('cookie:') or 'cookie' in line.lower():
                if '=' in line and not line.startswith('#'):
                    # 提取 cookie 字符串
                    cookie_match = re.search(r'cookie:\s*(.+)', line)
                    if cookie_match:
                        cookie_str = cookie_match.group(1).strip()
                        config['cookies'] = self._parse_cookies(cookie_str)
                        logger.debug(f"解析到 {len(config['cookies'])} 个 cookies")

            # 解析账号密码
            elif '账号' in line or 'account' in line.lower():
                for next_line in lines[lines.index(line)+1:lines.index(line)+3]:
                    if '密码' in next_line or 'password' in next_line.lower():
                        # 提取密码
                        pwd_match = re.search(r'[：:]\s*(.+)', next_line)
                        if pwd_match:
                            config['account']['password'] = pwd_match.group(1).strip()
                            logger.debug("找到账号密码")
                    elif 'alexbibiherr' in next_line:
                        config['account']['username'] = next_line.strip()

            # 解析前端端口
            elif '前端端口' in line or 'frontend' in line.lower():
                port_match = re.search(r'(\d+)', line)
                if port_match:
                    config['frontend_port'] = int(port_match.group(1))
                    logger.debug(f"前端端口: {config['frontend_port']}")

            # 解析 Brave 路径
            elif 'brave' in line.lower() and '.exe' in line:
                brave_match = re.search(r'([A-Z]:\\\\[^:]+?\.exe)', line)
                if brave_match:
                    config['brave_path'] = brave_match.group(1).strip()
                    logger.debug(f"Brave 路径: {config['brave_path']}")

            # 解析 HAMA 工作流程
            elif 'hama指标访问流程' in line or 'workflow' in line.lower():
                # 读取后续几行的流程描述
                workflow_start = lines.index(line)
                workflow_lines = []
                for i in range(workflow_start + 1, min(workflow_start + 10, len(lines))):
                    if lines[i].strip() and not lines[i].startswith('→'):
                        workflow_lines.append(lines[i].strip())
                    elif lines[i].strip().startswith('QQ邮件') or 'email' in lines[i].lower():
                        break
                config['hama_workflow'] = workflow_lines
                logger.debug(f"HAMA 流程: {len(workflow_lines)} 步")

            # 解析 QQ 邮件配置
            elif 'QQ邮件' in line or 'email' in line.lower():
                email_config = {}
                for i in range(lines.index(line), min(lines.index(line) + 5, len(lines))):
                    curr_line = lines[i]
                    if '邮箱' in curr_line or 'mail' in curr_line.lower():
                        mail_match = re.search(r'[：:]\s*(.+)', curr_line)
                        if mail_match and '@' in mail_match.group(1):
                            email_config['sender'] = mail_match.group(1).strip()
                    elif '授权码' in curr_line or 'auth' in curr_line.lower():
                        auth_match = re.search(r'[：:]\s*(.+)', curr_line)
                        if auth_match:
                            email_config['auth_code'] = auth_match.group(1).strip()
                    elif '收件人' in curr_line or 'receiver' in curr_line.lower():
                        receivers_match = re.search(r'[：:]\s*(.+)', curr_line)
                        if receivers_match:
                            receivers_str = receivers_match.group(1).strip()
                            email_config['receivers'] = [r.strip() for r in receivers_str.split(',')]

                config['email'] = email_config
                logger.debug(f"邮件配置: 发件人={email_config.get('sender')}, 收件人={len(email_config.get('receivers', []))} 个")

            # 解析文件组织规则
            elif '新创建' in line and '文件夹' in line:
                config['file_organization']['rule'] = line.strip()

            # 解析健康检查规则
            elif 'hama列表检测不到' in line or 'health' in line.lower():
                config['health_check_rule'] = line.strip()
                logger.debug(f"健康检查规则: {line.strip()}")

        self.config = config
        return config

    def _parse_cookies(self, cookie_str: str) -> Dict[str, str]:
        """
        解析 Cookie 字符串

        Args:
            cookie_str: Cookie 字符串

        Returns:
            Cookie 字典
        """
        cookies = {}

        # 移除 'cookie:' 前缀
        cookie_str = re.sub(r'^cookie:\s*', '', cookie_str)

        # 按分号分割
        for pair in cookie_str.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies[key.strip()] = value.strip()

        return cookies

    def reload_config(self) -> Dict[str, any]:
        """
        重新加载配置文件

        Returns:
            最新的配置字典
        """
        logger.info("🔄 重新加载 longLogic.txt 配置...")

        old_config = self.config.copy()
        new_config = self.read_config()

        # 对比配置变化
        changes = self._detect_config_changes(old_config, new_config)

        if changes:
            logger.info(f"⚠️ 配置已发生变化: {len(changes)} 项")
            for change in changes:
                logger.info(f"  - {change}")
        else:
            logger.info("✅ 配置未发生变化")

        return new_config

    def _detect_config_changes(self, old_config: Dict, new_config: Dict) -> list:
        """
        检测配置变化

        Args:
            old_config: 旧配置
            new_config: 新配置

        Returns:
            变化列表
        """
        changes = []

        # 检查关键字段变化
        key_fields = ['tradingview_url', 'frontend_port', 'brave_path']

        for field in key_fields:
            if old_config.get(field) != new_config.get(field):
                changes.append(f"{field}: {old_config.get(field)} -> {new_config.get(field)}")

        # 检查账号变化
        if old_config.get('account', {}).get('password') != new_config.get('account', {}).get('password'):
            changes.append("账号密码已更新")

        # 检查邮件配置变化
        if old_config.get('email', {}).get('auth_code') != new_config.get('email', {}).get('auth_code'):
            changes.append("邮件授权码已更新")

        return changes

    def apply_config(self, config: Dict = None):
        """
        应用配置到系统

        Args:
            config: 配置字典，如果为 None 则使用当前配置
        """
        if config is None:
            config = self.config

        logger.info("📝 应用 longLogic 配置...")

        # 这里可以根据配置更新系统设置
        # 例如：更新环境变量、重新初始化服务等

        # 更新 TradingView URL
        if config.get('tradingview_url'):
            logger.info(f"  TradingView URL: {config['tradingview_url']}")

        # 更新 Brave 路径
        if config.get('brave_path'):
            logger.info(f"  Brave 路径: {config['brave_path']}")

        # 更新邮件配置
        if config.get('email'):
            logger.info(f"  邮件发送者: {config['email'].get('sender')}")
            logger.info(f"  邮件收件人: {len(config['email'].get('receivers', []))} 个")

        logger.info("✅ 配置应用完成")

    def get_config(self) -> Dict:
        """获取当前配置"""
        return self.config.copy()

    def get_last_modified_time(self):
        """获取最后修改时间"""
        return self.last_modified_time


# 全局单例
_long_logic_reader = None


def get_long_logic_reader() -> LongLogicReader:
    """获取 LongLogic 读取器单例"""
    global _long_logic_reader
    if _long_logic_reader is None:
        _long_logic_reader = LongLogicReader()
        _long_logic_reader.read_config()
    return _long_logic_reader
