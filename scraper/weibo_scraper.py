from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import csv
import time
import re

BASE_URL = "https://s.weibo.com/weibo"

KEYWORD = "世界杯"

MAX_PAGES = 5

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def clean_text(text):
    if text is None:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def parse_count(text):
    text = clean_text(text)

    text = (
        text.replace("转发", "")
            .replace("评论", "")
            .replace("点赞", "")
            .replace("赞", "")
            .strip()
    )

    if text == "":
        return 0

    if "万" in text:
        number = text.replace("万", "").strip()

        try:
            return int(float(number) * 10000)
        except:
            return 0

    match = re.search(r"\d+", text)

    if match:
        return int(match.group())

    return 0


def get_text(item, selector):
    if item.locator(selector).count() > 0:
        return clean_text(item.locator(selector).first.text_content())

    return ""


def get_attribute(item, selector, attr):
    if item.locator(selector).count() > 0:
        return item.locator(selector).first.get_attribute(attr) or ""

    return ""

def is_ad_item(item):
    ad_count = item.locator("div.from .wb-ad-title").count()
    from_text = get_text(item, "div.from")
    item_text = clean_text(item.inner_text())

    if ad_count > 0:
        print("检测到广告：wb-ad-title")
        return True

    if "广告" in from_text:
        print("检测到广告：from 区域包含广告")
        return True

    if "蒙牛" in item_text and "广告" in item_text[:200]:
        print("检测到广告：蒙牛广告兜底")
        return True

    return False


def build_search_url(page_num):
    keyword_encoded = quote(KEYWORD)

    return f"{BASE_URL}?q={keyword_encoded}&page={page_num}"


def scrape_weibo(page, page_num):
    rows = []
    failed_rows = []
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    url = build_search_url(page_num)

    print(f"Scraping page: {page_num}")
    print(url)

    try:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

        except Exception as e:
            error_text = str(e)

            if "interrupted by another navigation" in error_text:
                print(f"Page {page_num}: 页面被登录跳转打断，等待后重试...")

                page.wait_for_timeout(8000)

                page.goto(url, wait_until="domcontentloaded", timeout=30000)

            else:
                raise e

        page.wait_for_timeout(3000)

        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(1000)

        body_text = page.locator("body").text_content()

        if "验证码" in body_text or "访问过于频繁" in body_text:
            failed_rows.append([page_num, 0, "captcha or frequency limit detected"])
            return rows, failed_rows

        page.wait_for_selector("div[action-type='feed_list_item']", timeout=15000)

        items = page.locator("div[action-type='feed_list_item']").all()

        print(f"Found {len(items)} weibo items.")

        for index, item in enumerate(items, start=1):
            try:
                if is_ad_item(item):
                    print(f"Skip ad item on page {page_num}, index {index}")
                    continue

                mid = item.get_attribute("mid") or ""

                username = get_text(item, "a.name")

                if username == "":
                    username = get_attribute(item, "p[node-type='feed_list_content']", "nick-name")

                content = get_text(item, "p[node-type='feed_list_content']")

                if content == "":
                    content = get_text(item, "p.txt")

                publish_time = ""
                source = ""

                from_links = item.locator("div.from a").all()

                if len(from_links) >= 1:
                    publish_time = clean_text(from_links[0].text_content())

                if len(from_links) >= 2:
                    source = clean_text(from_links[1].text_content())

                repost_text = get_text(item, "a[action-type='feed_list_forward']")
                comment_text = get_text(item, "a[action-type='feed_list_comment']")
                like_text = get_text(item, "a[action-type='feed_list_like'] .woo-like-count")

                if like_text == "":
                    like_text = get_text(item, "a[action-type='feed_list_like']")

                repost_count = parse_count(repost_text)
                comment_count = parse_count(comment_text)
                like_count = parse_count(like_text)

                if username == "" and content == "":
                    raise ValueError("empty username and content")

                rows.append([
                    username,
                    content,
                    publish_time,
                    source,
                    repost_count,
                    comment_count,
                    like_count,
                    page_num,
                    index,
                    mid,
                    scraped_at
                ])

            except Exception as e:
                failed_rows.append([page_num, index, str(e)])
                continue

    except PlaywrightTimeoutError as e:
        failed_rows.append([page_num, 0, f"timeout: {str(e)}"])

    except Exception as e:
        failed_rows.append([page_num, 0, str(e)])

    return rows, failed_rows


def save_to_csv(rows, filename):
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def run():
    all_rows = []
    all_failed_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto(build_search_url(1), wait_until="domcontentloaded", timeout=30000)
        except Exception:
            print("首次打开可能被登录页跳转打断，这是正常情况。")

        print("请先在浏览器中完成微博登录，并确认页面已经回到微博搜索结果列表，再回到终端按 Enter 继续...")
        input()

        for page_num in range(1, MAX_PAGES + 1):
            rows, failed_rows = scrape_weibo(page, page_num)

            all_rows.extend(rows)
            all_failed_rows.extend(failed_rows)

            print(f"Page {page_num}: scraped {len(rows)} items, failed {len(failed_rows)} items.")

            time.sleep(3)

        browser.close()

    unique_rows = []
    seen_mids = set()

    for row in all_rows:
        mid = row[-2]
        content = row[1]

        unique_key = mid if mid != "" else content

        if unique_key not in seen_mids:
            unique_rows.append(row)
            seen_mids.add(unique_key)

    weibo_header = [[
        "username",
        "content",
        "publish_time",
        "source",
        "repost_count",
        "comment_count",
        "like_count",
        "page",
        "item_index",
        "mid",
        "scraped_at"
    ]]

    failed_header = [[
        "page",
        "item_index",
        "error"
    ]]

    save_to_csv(weibo_header + unique_rows, DATA_DIR / "raw_weibo.csv")
    save_to_csv(failed_header + all_failed_rows, DATA_DIR / "failed_weibo.csv")

    print(f"Total scraped weibos before deduplication: {len(all_rows)}")
    print(f"Total scraped weibos after deduplication: {len(unique_rows)}")
    print(f"Total failed items: {len(all_failed_rows)}")
    print(f"Saved to: {DATA_DIR / 'raw_weibo.csv'}")

if __name__ == "__main__":
    run()
