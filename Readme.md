# TechFX Funds Daily Report Bot

一个用 Python + Playwright 抓取 TechFX 基金列表网页、生成收益率榜单，并通过 OpenClaw/WhatsApp 推送 Top10 / Bottom10 的小工具。

## 功能概览

- 使用 Playwright 打开 `https://tg.techfx88.com/special/app-h5/fund.html`，等待页面渲染完成后抓取完整 HTML。
- 用 `pandas.read_html` 解析基金列表表格，抽取以下列：
  - 年初至今
  - 近 6 月
  - 近 3 月
  - 近 1 月
  - 近 1 年
  - 近 3 年
- 将带百分号的字符串（例如 `+ 19.94%`）转换为浮点数，便于排序和后续计算。
- 生成完整 Excel 报表文件，命名类似：
  - `techfx_funds_YYYYMMDD_HHMM_report.xlsx`
- 按「近 1 年」收益率：
  - 选出 Top10 基金，并格式化为一段可读文本
  - 选出 Bottom10 基金，并格式化为一段可读文本
- 通过 OpenClaw CLI 调用 WhatsApp 通道，将 Top10 / Bottom10 两段消息推送到指定手机号。

## 依赖

运行前需要：

- Python 3.10+
- [Playwright for Python](https://playwright.dev/python/)
- pandas
- openpyxl（写 Excel 用）
- 已安装并可用的 `openclaw` CLI（用于发送 WhatsApp 消息）
- 一个已配置好的 OpenClaw WhatsApp 通道（在同一台机器上 `openclaw channels login --channel whatsapp` 并扫码完成配对）

安装依赖示例：

```bash
pip install -U pandas openpyxl playwright
python -m playwright install chromium
# OpenClaw CLI 请参考官方文档安装

环境变量
脚本通过环境变量读取配置，不在代码中硬编码任何密钥或手机号。

需要在运行前设置：

export WA_TO="+852XXXXXXXX"        # 接收 WhatsApp 消息的手机号（E.164 格式）
# 如果你的 OpenClaw Gateway / Gemini 调用依赖额外变量，例如：
# export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
# export OPENCLAW_GATEWAY_TOKEN="YOUR_GATEWAY_TOKEN_HERE"

配置环境变量（至少设置 WA_TO）：

export WA_TO="+852XXXXXXXX"

确认 OpenClaw WhatsApp 通道已登录：

openclaw channels login --channel whatsapp
终端看到 “Linked! Credentials saved for future sends.” 即表示绑定成功。

运行脚本：

python run_techfx_report.py

运行后会：

在当前目录下生成一个类似 techfx_funds_YYYYMMDD_HHMM_report.xlsx 的报表文件

通过 OpenClaw/WhatsApp 向 WA_TO 对应的号码发送两条消息：

一条 Top10（按近 1 年收益）

一条 Bottom10（按近 1 年收益）

实现细节
使用 playwright.async_api 的 chromium.launch(headless=True, args=["--no-sandbox"]) 创建无头浏览器。

page.goto(url, wait_until="networkidle", timeout=60000) 等待网络空闲，再额外 wait_for_timeout(2500)，保证表格渲染完成。

pandas.read_html(StringIO(html)) 解析页面中的 <table>，选择列数最多的一张表作为主表。

列名标准化后，对 BASE_COLS = ["年初至今","近6月","近3月","近1月","近1年","近3年"] 中实际存在的列，增加对应的 *_pct 数值列。

近1年_pct 用于排序 Top10 / Bottom10，文本格式类似：

基金名称 | 近1年 100.28% | 近6月 43.66% | 近3月 21.45% | 近1月 4.22% | 年初至今 19.94% | 近3年 120.56%

通过 subprocess.run(["openclaw", "message", "send", "--channel", "whatsapp", "--target", WA_TO, "--message", msg]) 发送消息。

风险与注意事项
网页结构变更：如果目标网页的表格结构或列名发生变化，可能需要调整脚本中的列名和解析逻辑。

频率限制：脚本本身只调用一次页面抓取+一次报表生成，属于极低频使用；如要改为高频定时任务，请注意浏览器资源与目标站点访问频率。

隐私与安全：

不要在仓库中提交任何真实的 API Key、Token 或手机号。

推荐将真实配置放在本地环境变量或未提交的配置文件中。

许可证
（根据你的意愿选择许可证，例如 MIT / Apache-2.0 / 私有，如果不确定可以先留空或简单写 “All rights reserved.”）