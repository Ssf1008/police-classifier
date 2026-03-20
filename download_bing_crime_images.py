import os
import re
import time
import math
import json
import html as ihtml
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

KEYWORDS = ["监控打架斗殴", "监控盗窃", "交通违法违停", "寻衅滋事"]
TARGET_PER_KEYWORD = 250
OUT_DIR = r"D:\crime_images"

# 并发与抓取强度（网络稳定可适当提高，但太高可能触发限制）
MAX_WORKERS = 12
PER_PAGE = 35          # Bing 图片 offset 一般按这个数量级
SLEEP_BETWEEN_PAGES = 0.9

# 补抓最多轮次：避免卡很久（通常够用）
MAX_COLLECT_ROUNDS = 8


def sanitize_name(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", s).strip()


def fetch_html(session: requests.Session, url: str) -> str:
    r = session.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.text


def extract_murl(html: str) -> list[str]:
    urls = []

    # 1) 常规 JSON 片段: "murl":"http..."
    urls.extend(re.findall(r'"murl":"(https?://[^"]+)"', html))

    # 2) HTML 转义片段: murl&quot;:&quot;http...&quot;
    urls.extend(re.findall(r"murl&quot;:&quot;(https?://.+?)&quot;", html))

    # 3) 先整体反转义后再匹配一次
    unescaped = ihtml.unescape(html)
    urls.extend(re.findall(r'"murl":"(https?://[^"]+)"', unescaped))

    # 4) Bing iusc 节点的 m 属性里通常是 JSON，包含 murl
    m_blocks = re.findall(r'\sm="([^"]+)"', html)
    for block in m_blocks:
        try:
            s = ihtml.unescape(block)
            data = json.loads(s)
            u = data.get("murl")
            if isinstance(u, str) and u.startswith(("http://", "https://")):
                urls.append(u)
        except Exception:
            continue

    seen = set()
    out = []
    for u in urls:
        # 把转义的 URL 规范化，减少重复
        u = u.replace("\\/", "/")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def allowed_by_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    ct = content_type.split(";")[0].strip().lower()
    if ct == "image/jpeg":
        return ".jpg"
    if ct == "image/png":
        return ".png"
    return None


def infer_ext_from_url(url: str) -> str | None:
    lower = url.lower()
    if lower.endswith(".png"):
        return ".png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return ".jpg"
    return None


def download_one(session: requests.Session, url: str, final_path_base: str, retries: int = 3):
    """
    final_path_base: 不带扩展名
    """
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers={"User-Agent": UA}, timeout=30, stream=True)
            # 处理被限流/临时失败
            if resp.status_code in (429, 503, 502, 504):
                time.sleep(1.5 * attempt)
                continue
            resp.raise_for_status()

            ext = allowed_by_content_type(resp.headers.get("Content-Type"))
            if ext is None:
                ext = infer_ext_from_url(url)
            if ext not in (".jpg", ".png"):
                return False

            final_path = final_path_base + ext
            with open(final_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception:
            time.sleep(0.8 * attempt)
            continue
    return False


def collect_urls_for_keyword(keyword: str, target_num: int) -> list[str]:
    keyword_q = quote(keyword)
    collected = []
    seen = set()

    pages_needed = math.ceil(target_num / PER_PAGE)

    with requests.Session() as session:
        round_idx = 0
        while len(collected) < target_num and round_idx < MAX_COLLECT_ROUNDS:
            pages_this_round = pages_needed + round_idx  # 每轮略微增加覆盖面
            for page_idx in range(pages_this_round):
                if len(collected) >= target_num:
                    break
                first = page_idx * PER_PAGE
                # 双通道：先用 async 接口（结构更稳定），再 fallback 到 search 页面
                async_url = f"https://cn.bing.com/images/async?q={keyword_q}&first={first}&count={PER_PAGE}&adlt=off"
                search_url = f"https://cn.bing.com/images/search?q={keyword_q}&form=HDRSC2&first={first}"
                print(f"  [collect:{keyword}] page={page_idx+1}/{pages_this_round} first={first} collected={len(collected)}/{target_num}")

                try:
                    html_text = fetch_html(session, async_url)
                    urls = extract_murl(html_text)

                    # async 没拿到则退回 search 页面
                    if not urls:
                        html_text = fetch_html(session, search_url)
                        urls = extract_murl(html_text)

                    if page_idx == 0 and round_idx == 0:
                        print(f"  [collect:{keyword}] extracted urls on first page: {len(urls)}")

                    for u in urls:
                        if u not in seen:
                            seen.add(u)
                            collected.append(u)
                            if len(collected) >= target_num:
                                break
                except Exception as e:
                    print(f"  [collect:{keyword}] page fetch failed: {e}")

                time.sleep(SLEEP_BETWEEN_PAGES)

            round_idx += 1

    return collected[:target_num]


def download_keyword(keyword: str, target_num: int):
    kw_dir = os.path.join(OUT_DIR, sanitize_name(keyword))
    os.makedirs(kw_dir, exist_ok=True)

    # 先收集一批 urls，下载时如果实际成功少于 target，会再补抓一轮
    round_no = 1
    total_success = 0
    used_urls = set()

    while total_success < target_num and round_no <= MAX_COLLECT_ROUNDS:
        need = target_num - total_success
        print(f"\n=== Keyword: {keyword} | need={need} | round={round_no} ===")

        urls = collect_urls_for_keyword(keyword, target_num=need + 30)  # 多收一点，容错非 jpg/png
        urls = [u for u in urls if u not in used_urls]
        used_urls.update(urls)

        if not urls:
            print(f"[{keyword}] 这轮没抓到可用链接，跳过。")
            break

        # 并发下载
        with requests.Session() as session:
            ok = 0
            futures = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                for i, u in enumerate(urls, start=1):
                    # 用“全局序号”命名：避免覆盖
                    # 成功数量不足时，后续 round 还会继续从成功数位置接着补
                    seq_base = total_success + (i - 1) + 1
                    base = os.path.join(kw_dir, f"{seq_base:04d}_{sanitize_name(keyword)}")
                    futures.append(ex.submit(download_one, session, u, base))

                for fut in as_completed(futures):
                    if fut.result():
                        ok += 1

            total_success += ok
            print(f"[{keyword}] round={round_no} downloaded_ok={ok} total_success={total_success}/{target_num}")

        round_no += 1

    print(f"=== Finished keyword: {keyword} | downloaded {total_success}/{target_num} ===")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    total_target = len(KEYWORDS) * TARGET_PER_KEYWORD
    print(f"Start downloading. Total target: {total_target} images -> {OUT_DIR}")

    for kw in KEYWORDS:
        download_keyword(kw, TARGET_PER_KEYWORD)


if __name__ == "__main__":
    main()