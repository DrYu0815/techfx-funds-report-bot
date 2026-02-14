import os
import re
import datetime
import subprocess
import asyncio
from io import StringIO

import pandas as pd
from playwright.async_api import async_playwright

URL = "https://tg.techfx88.com/special/app-h5/fund.html"
BASE_COLS = ["年初至今", "近6月", "近3月", "近1月", "近1年", "近3年"]

def pct_to_float(x):
    if x is None:
        return None
    s = str(x).replace(",", "").replace("%", "").strip()
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else None

async def get_rendered_html(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
            viewport={"width": 1400, "height": 900},
            locale="zh-CN",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60_000)
        await page.wait_for_timeout(2500)
        html = await page.content()
        await context.close()
        await browser.close()
        return html

def send_whatsapp(msg: str):
    wa_to = os.environ.get("WA_TO")
    if not wa_to:
        raise RuntimeError('WA_TO missing. Example: export WA_TO="+852..."')
    subprocess.run(
        ["openclaw", "message", "send", "--channel", "whatsapp", "--target", wa_to, "--message", msg],
        check=True,
    )

def fmt_row(r):
    name = str(r["筛选"]).replace("\n", " ").strip()
    return (
        f"{name} | 近1年 {r['近1年_pct']:.2f}% | 近6月 {r['近6月_pct']:.2f}% | 近3月 {r['近3月_pct']:.2f}%"
        f" | 近1月 {r['近1月_pct']:.2f}% | 年初至今 {r['年初至今_pct']:.2f}% | 近3年 {r['近3年_pct']:.2f}%"
    )

async def main():
    html = await get_rendered_html(URL)
    tables = pd.read_html(StringIO(html))
    if not tables:
        raise RuntimeError("No <table> parsed from page.")

    df = max(tables, key=lambda t: t.shape[1]).copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip()

    pct_cols = [c for c in BASE_COLS if c in df.columns]
    for c in pct_cols:
        df[c + "_pct"] = df[c].map(pct_to_float)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out_xlsx = f"/content/techfx_funds_{ts}_report.xlsx"
    df.to_excel(out_xlsx, index=False)

    need = ["筛选"] + [c + "_pct" for c in pct_cols]
    work = df[need].dropna(subset=["近1年_pct"]).copy()

    top10 = work.sort_values("近1年_pct", ascending=False).head(10)
    bottom10 = work.sort_values("近1年_pct", ascending=True).head(10)

    msg_top = "Top10（按近1年）\n" + "\n".join(f"{i+1}. {fmt_row(r)}" for i, r in top10.iterrows())
    msg_bottom = "Bottom10（按近1年）\n" + "\n".join(f"{i+1}. {fmt_row(r)}" for i, r in bottom10.iterrows())

    send_whatsapp(msg_top)
    send_whatsapp(msg_bottom)

    print("OK:", out_xlsx)

if __name__ == "__main__":
    asyncio.run(main())
