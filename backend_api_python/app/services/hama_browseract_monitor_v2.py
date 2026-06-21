    def _extract_via_browser_session(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        使用浏览器会话方式提取数据（从页面标题获取价格）

        Args:
            symbol: 交易对符号
            timeframe: 时间周期

        Returns:
            提取的数据字典
        """
        session_name = None
        try:
            import uuid
            import re
            from app.config.browseract_config import BrowserActConfig

            # 获取配置的浏览器
            browser_config = BrowserActConfig.get_browser_config()
            browser_id = browser_config['id']
            browser_type = browser_config.get('type', 'chrome')

            session_name = f"hama_{symbol}_{uuid.uuid4().hex[:8]}"
            tradingview_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}"

            logger.info(f"🔄 使用浏览器会话方式提取 {symbol} 数据...")

            # 清理旧会话
            self._cleanup_old_sessions(browser_id)

            # Chrome浏览器不使用代理
            if browser_type == 'chrome':
                env_vars = {k: v for k, v in os.environ.items() if k not in ['HTTP_PROXY', 'HTTPS_PROXY']}
            else:
                env_vars = os.environ.copy()

            # 打开浏览器会话
            cmd_open = [
                self.browseract_cmd,
                '--session', session_name,
                'browser', 'open', browser_id,
                tradingview_url
            ]

            result = subprocess.run(
                cmd_open,
                capture_output=True,
                text=False,
                timeout=60,
                env=env_vars
            )

            if result.returncode != 0:
                logger.error(f"浏览器会话打开失败")
                return None

            logger.info(f"浏览器会话已打开，等待页面加载...")

            # 等待页面加载
            import time
            time.sleep(15)

            # 获取页面标题（包含价格信息）
            cmd_title = [
                self.browseract_cmd,
                '--session', session_name,
                'get', 'title'
            ]

            result = subprocess.run(
                cmd_title,
                capture_output=True,
                text=True,
                timeout=10,
                env=env_vars
            )

            # 获取页面内容
            cmd_content = [
                self.browseract_cmd,
                '--session', session_name,
                'get', 'markdown'
            ]

            result_content = subprocess.run(
                cmd_content,
                capture_output=True,
                text=True,
                timeout=10,
                env=env_vars
            )

            # 关闭会话
            try:
                subprocess.run(
                    [self.browseract_cmd, '--session', session_name, 'session', 'close'],
                    capture_output=True,
                    timeout=10,
                    env=env_vars
                )
            except:
                pass

            # 解析数据
            hama_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'hama_trend': 'neutral',
                'hama_color': 'gray',
                'hama_value': None,
                'price': None,
                'trend': 'neutral',
                'color': 'gray',
                'current_price': None,
                'bollinger_status': None,
                'candle_ma_status': None,
                'last_cross_info': None,
                'last_cross_time': None,
                'data_source': 'browseract_title',
                'extraction_method': 'session_title'
            }

            # 从标题提取价格和趋势
            if result.returncode == 0 and result.stdout:
                title = result.stdout.strip()
                logger.info(f"页面标题: {title}")

                # 解析价格: ETHUSDT 2,131.96 ▼ −0.08% 史蒂夫
                price_match = re.search(r'(\d+\.?\d*)', title)
                if price_match:
                    try:
                        price = float(price_match.group(1))
                        hama_data['price'] = price
                        hama_data['current_price'] = price
                        logger.info(f"✅ 提取到价格: {price}")
                    except:
                        pass

                # 解析趋势方向（从标题中的箭头符号）
                if '▼' in title:
                    # 下跌
                    hama_data['hama_trend'] = '下跌'
                    hama_data['trend'] = 'down'
                    hama_data['hama_color'] = 'red'
                    hama_data['color'] = 'red'
                elif '▲' in title:
                    # 上涨
                    hama_data['hama_trend'] = '上涨'
                    hama_data['trend'] = 'up'
                    hama_data['hama_color'] = 'green'
                    hama_data['color'] = 'green'

            # 从内容中查找更多信息
            if result_content.returncode == 0 and result_content.stdout:
                content = result_content.stdout.upper()

                # 检查 HAMA 相关关键词
                if any(kw in content for kw in ['HAMA', 'HULL', 'GOLDEN CROSS', '金叉']):
                    hama_data['has_hama_indicator'] = True

                # 根据关键词调整趋势
                if any(kw in content for kw in ['GOLDEN CROSS', '金叉', 'BULLISH', '买入']):
                    hama_data['hama_trend'] = '金叉'
                    hama_data['trend'] = 'up'
                    hama_data['hama_color'] = 'green'
                    hama_data['color'] = 'green'
                elif any(kw in content for kw in ['DEATH CROSS', '死叉', 'BEARISH', '卖出']):
                    hama_data['hama_trend'] = '死叉'
                    hama_data['trend'] = 'down'
                    hama_data['hama_color'] = 'red'
                    hama_data['color'] = 'red'

            logger.info(f"✅ {symbol} 数据解析完成: {hama_data['hama_color']} ({hama_data['hama_trend']}) | 价格: {hama_data['price']}")

            return hama_data

        except subprocess.TimeoutExpired:
            logger.error(f"浏览器会话提取 {symbol} 超时")
            if session_name:
                self._close_session_safe(session_name)
            return None
        except Exception as e:
            logger.error(f"浏览器会话提取异常: {e}")
            if session_name:
                self._close_session_safe(session_name)
            return None
