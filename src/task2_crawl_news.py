"""
Task 2 — Crawl bài viết/thông báo về pháp luật bất động sản.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng requests + markitdown.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Yêu cầu:
    - content_markdown sau strip() phải ≥300 ký tự, nếu <300 sẽ bỏ qua
    - Mỗi URL được crawl đúng 1 lần với tên file ổn định (hash URL)
    - Lỗi 1 bài không làm crash batch — catch exception từng URL
    - In tóm tắt: thành công / bỏ qua / lỗi
"""

import hashlib
import json
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

import requests
from markitdown import MarkItDown


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # Bài viết về pháp luật, bảo vệ người tiêu dùng, nhà ở, bất động sản
    "https://baochinhphu.vn/them-nhieu-quy-dinh-moi-bao-ve-tang-cuong-quyen-va-loi-ich-cho-nguoi-mua-nha-102240702102626908.htm",
    "https://tuoitre.vn/tu-1-8-mua-bat-dong-san-nha-o-hinh-thanh-trong-tuong-lai-phai-biet-dieu-nay-20240721173924396.htm",
    "https://luatvietnam.vn/dat-dai-nha-o/diem-moi-cua-luat-kinh-doanh-bat-dong-san-567-96340-article.html",
    "https://xaydungchinhsach.chinhphu.vn/mau-hop-dong-mua-ban-thue-mua-nha-o-119240827171655617.htm",
    "https://tuoitre.vn/bao-ve-quyen-cua-nguoi-mua-nha-chung-cu-khi-ca-hai-bo-cung-ban-tam-106926857.htm",
    "https://luatvietnam.vn/dat-dai-nha-o/hop-dong-mua-ban-nha-567-29833-article.html",
    "https://baochinhphu.vn/tam-khien-bao-ve-nguoi-dan-va-doanh-nghiep-trong-giao-dich-bat-dong-san-102230509181822512.htm",
    "https://baochinhphu.vn/dinh-huong-nguon-luc-vao-nhu-can-thuc-gop-phan-on-dinh-mat-bang-nha-o-102260822144934209.htm",
]


class TitleExtractor(HTMLParser):
    """Extract <title> from HTML."""
    def __init__(self):
        super().__init__()
        self.title = None
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and not self.title:
            self.title = data.strip()


def extract_title_from_html(html: str, url: str) -> str:
    """Extract title from <title> tag or fallback to URL slug."""
    try:
        extractor = TitleExtractor()
        extractor.feed(html)
        if extractor.title and len(extractor.title) > 0:
            return extractor.title[:200]
    except Exception:
        pass

    # Fallback: use URL slug
    slug = url.split("/")[-1].replace("-", " ").split("?")[0][:100]
    return slug if slug else "Unknown"


def crawl_article(url: str) -> dict:
    """Crawl article from URL using requests + markitdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Fetch HTML
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    # Extract title from <title> tag
    title = extract_title_from_html(response.text, url)

    # Convert HTML to Markdown using MarkItDown
    md_converter = MarkItDown()
    stream = BytesIO(response.text.encode('utf-8'))
    result = md_converter.convert_stream(stream, file_extension='.html')
    markdown_content = result.text_content

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": markdown_content,
    }


def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    skipped_count = 0
    error_count = 0
    skipped_urls = []
    error_urls = []

    for url in ARTICLE_URLS:
        try:
            print(f"Crawling: {url}")
            article = crawl_article(url)

            # Kiểm độ dài content_markdown
            content_stripped = article["content_markdown"].strip()
            content_length = len(content_stripped)

            if content_length < 300:
                print(f"  ⚠️  BỎ QUA: Nội dung quá ngắn ({content_length} ký tự, yêu cầu ≥300)")
                skipped_count += 1
                skipped_urls.append((url, content_length))
                continue

            # Tạo tên file ổn định từ URL (hash MD5)
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"article_{url_hash}.json"
            output_path = DATA_DIR / filename

            # Lưu file JSON
            output_path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"  ✓ Saved: {filename} ({content_length} ký tự)")
            success_count += 1

        except Exception as error:
            print(f"  ✗ Lỗi: {error}")
            error_count += 1
            error_urls.append((url, str(error)))

    # In tóm tắt
    print("\n" + "=" * 60)
    print(f"📊 TÓM TẮT CRAWL NEWS")
    print("=" * 60)
    print(f"✓ Thành công: {success_count} bài")
    print(f"⚠️  Bỏ qua (nội dung <300 ký tự): {skipped_count} bài")
    if skipped_urls:
        for url, length in skipped_urls:
            print(f"    - {url[:60]}... ({length} ký tự)")
    print(f"✗ Lỗi: {error_count} bài")
    if error_urls:
        for url, err in error_urls:
            print(f"    - {url[:60]}... | {err[:50]}")
    print("=" * 60)


if __name__ == "__main__":
    crawl_all()
