#!/usr/bin/env python3
import argparse
import csv
import re
import sys
import time
from datetime import datetime
from typing import Dict, Generator, List

import requests
from bs4 import BeautifulSoup

CATEGORY_CONFIG = {
    "national": {
        "name": "国家标准",
        "endpoint": "https://std.samr.gov.cn/gb/search/gbQueryPage",
        "method": "get",
    },
    "industry": {
        "name": "行业标准",
        "endpoint": "https://hbba.sacinfo.org.cn/stdQueryList",
        "method": "post",
    },
    "local": {
        "name": "地方标准",
        "endpoint": "https://dbba.sacinfo.org.cn/stdQueryList",
        "method": "post",
    },
}

ADVANCED_SEARCH_ENDPOINT = "https://std.samr.gov.cn/gb/search/gbAdvancedSearchPage"
TC_LIST_URL = "https://std.samr.gov.cn/gb/search/gbAdvancedSearch"

HTML_TAG_RE = re.compile(r"<.*?>", flags=re.S)
DETAIL_URL_TEMPLATE = "https://std.samr.gov.cn/gb/search/gbDetailed?id={}"

# Base fieldnames for keyword search
BASE_FIELDNAMES = [
    "keyword",
    "category",
    "standard_code",
    "standard_name",
    "standard_nature",
    "charge_dept",
    "guikou_unit",
    "drafting_units",
    "issue_date",
    "act_date",
    "state",
]
# Extra fields available from TC / advanced search
TC_FIELDNAMES = ["tc_code", "draft_staff", "ics"]
ALL_FIELDS = BASE_FIELDNAMES + TC_FIELDNAMES


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = HTML_TAG_RE.sub("", text)
    return text.strip()


def timestamp_to_date(value) -> str:
    if value is None or value == "":
        return ""
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return str(value).strip()
    # Some APIs return milliseconds, some return seconds.
    if timestamp > 10**11:
        timestamp = timestamp / 1000
    try:
        return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return str(value).strip()


def fetch_national_detail(detail_id: str) -> Dict[str, str]:
    result = {"guikou_unit": "", "drafting_units": ""}
    try:
        response = requests.get(DETAIL_URL_TEMPLATE.format(detail_id), timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 归口单位通常出现在“委托 ... 执行”段落内，以 TC 开头的技术委员会为主。
        found = False
        for p in soup.find_all("p"):
            text = p.get_text(separator="", strip=True)
            if "归口" in text and "委托" in text and "执行" in text:
                html = str(p)
                match = re.search(r"委托.*?<a[^>]*>([^<]+)</a>\s*（([^）]+)）.*?执行", html, re.S)
                if match:
                    result["guikou_unit"] = f"{match.group(1)}（{match.group(2)}）"
                    found = True
                    break

        if not found:
            for p in soup.find_all("p"):
                html = str(p)
                match = re.search(r"由.*?<a[^>]*>([^<]+)</a>\s*（([^）]+)）归口", html, re.S)
                if match:
                    result["guikou_unit"] = f"{match.group(1)}（{match.group(2)}）"
                    break

        drafting_units = []
        for span in soup.find_all("span"):
            if span.get("draft_unit") or span.get("DRAFT_UNIT"):
                unit = span.get_text(strip=True)
                if unit:
                    drafting_units.append(unit)
                if len(drafting_units) >= 3:
                    break
        result["drafting_units"] = "; ".join(drafting_units)
    except Exception:
        pass
    return result


def fetch_tc_committees() -> List[Dict[str, str]]:
    """Fetch the TC committee list from the advanced search page."""
    committees = []
    try:
        response = requests.get(TC_LIST_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        sel = soup.find("select", {"name": "std_p16"})
        if sel:
            for opt in sel.find_all("option"):
                code = opt.get("value", "").strip()
                name = opt.get_text(strip=True)
                if code and name and not name.startswith("--"):
                    committees.append({"code": code, "name": name})
    except Exception:
        pass
    return committees


def fetch_tc_search_page(tc_code: str, page_number: int = 1, page_size: int = 15) -> Dict:
    """Fetch search results for a specific TC committee via the advanced search API."""
    params = {
        "tid": "2",
        "std_p16": tc_code,
        "std_p1": "",
        "std_p2": "",
        "std_p3": "",
        "std_p4": "",
        "std_p5": "",
        "std_p6_1": "",
        "std_p6_2": "",
        "std_p7": "",
        "std_p24": "",
        "std_p25": "",
        "std_p17": "",
        "std_p26": "",
        "std_p8": "",
        "std_p9": "",
        "std_p10": "",
        "std_p11": "",
        "std_p12": "",
        "std_p13": "",
        "std_p14": "",
        "std_p15": "",
        "std_p18": "",
        "std_p19": "",
        "std_p20": "",
        "std_p21": "",
        "pageNumber": page_number,
        "pageSize": page_size,
    }
    response = requests.get(ADVANCED_SEARCH_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_tc_rows(keyword: str, tc_code: str, data: Dict) -> List[Dict[str, str]]:
    """Parse advanced search API response into the unified row format."""
    rows = []
    for item in data.get("rows", []):
        rows.append(
            {
                "keyword": keyword or "",
                "category": "national",
                "standard_code": clean_text(
                    item.get("C_STD_CODE", "")
                    or item.get("STD_CODE", "")
                    or item.get("STD_CODE3", "")
                ),
                "standard_name": clean_text(
                    item.get("C_NAME", "")
                    or item.get("C_C_NAME", "")
                ),
                "standard_nature": clean_text(item.get("STD_NATURE", "")),
                "charge_dept": clean_text(item.get("CD_NAME", "")),
                "guikou_unit": clean_text(
                    item.get("TA_NAME", "")
                    or item.get("TM_NAME", "")
                ),
                "drafting_units": clean_text(item.get("DRAFT_UNIT", "")),
                "issue_date": clean_text(item.get("ISSUE_DATE", "")),
                "act_date": clean_text(item.get("ACT_DATE", "")),
                "state": clean_text(item.get("STATE", "")),
                "tc_code": clean_text(
                    item.get("TA_CODE", "")
                    or item.get("TM_CODE", "")
                ),
                "draft_staff": clean_text(item.get("DRAFT_STAFF", "")),
                "ics": clean_text(
                    item.get("ICS", "")
                    or item.get("ICS_NAME1_FULL", "")
                ),
            }
        )
    return rows


def iter_tc_results(
    tc_code: str, page_size: int = 15, max_pages: int = 0
) -> Generator[Dict[str, str], None, None]:
    """Iterate through all pages of TC search results."""
    page_number = 1
    while True:
        data = fetch_tc_search_page(tc_code, page_number=page_number, page_size=page_size)
        if not data:
            break
        rows = parse_tc_rows("", tc_code, data)
        if not rows:
            break
        yield from rows

        if max_pages and page_number >= max_pages:
            break

        if len(rows) < page_size:
            break

        total = int(data.get("total", 0) or 0)
        if page_number * page_size >= total:
            break

        page_number += 1
        time.sleep(0.6)


def fetch_search_page(category: str, keyword: str, page_number: int = 1, page_size: int = 15) -> Dict:
    config = CATEGORY_CONFIG[category]
    if config["method"] == "get":
        params = {
            "searchText": keyword,
            "ics": "",
            "state": "",
            "ISSUE_DATE": "",
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        response = requests.get(config["endpoint"], params=params, timeout=30)
    else:
        data = {
            "current": page_number,
            "size": page_size,
            "key": keyword,
            "ministry": "",
            "industry": "",
            "pubdate": "",
            "date": "",
            "status": "",
        }
        response = requests.post(config["endpoint"], data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_rows(category: str, keyword: str, data: Dict) -> List[Dict[str, str]]:
    rows = []
    if category == "national":
        for item in data.get("rows", []):
            detail = fetch_national_detail(item.get("id", "")) if item.get("id") else {"guikou_unit": "", "drafting_units": ""}
            rows.append(
                {
                    "keyword": keyword,
                    "category": category,
                    "standard_code": clean_text(item.get("C_STD_CODE", "")),
                    "standard_name": clean_text(item.get("C_C_NAME", "")),
                    "standard_nature": clean_text(item.get("STD_NATURE", "")),
                    "charge_dept": "",
                    "guikou_unit": detail.get("guikou_unit", ""),
                    "drafting_units": detail.get("drafting_units", ""),
                    "issue_date": clean_text(item.get("ISSUE_DATE", "")),
                    "act_date": clean_text(item.get("ACT_DATE", "")),
                    "state": clean_text(item.get("STATE", "")),
                    "tc_code": "",
                    "draft_staff": "",
                    "ics": "",
                }
            )
    else:
        for item in data.get("records", []):
            rows.append(
                {
                    "keyword": keyword,
                    "category": category,
                    "standard_code": clean_text(item.get("code", "")),
                    "standard_name": clean_text(item.get("chName", "")),
                    "standard_nature": clean_text(item.get("industry", "")),
                    "charge_dept": clean_text(item.get("chargeDept", "")),
                    "guikou_unit": "",
                    "drafting_units": "",
                    "issue_date": timestamp_to_date(item.get("issueDate", "")),
                    "act_date": timestamp_to_date(item.get("actDate", "")),
                    "state": clean_text(item.get("status", "")),
                    "tc_code": "",
                    "draft_staff": "",
                    "ics": "",
                }
            )
    return rows


def iter_keyword_results(category: str, keyword: str, page_size: int = 15, max_pages: int = 0) -> Generator[Dict[str, str], None, None]:
    page_number = 1
    while True:
        data = fetch_search_page(category, keyword, page_number=page_number, page_size=page_size)
        if not data:
            break
        rows = parse_rows(category, keyword, data)
        if not rows:
            break
        for row in rows:
            yield row

        if max_pages and page_number >= max_pages:
            break

        row_count = len(rows)
        if row_count < page_size:
            break

        if category == "national":
            total = int(data.get("total", 0) or 0)
            if page_number * page_size >= total:
                break
        else:
            pages = int(data.get("pages", 0) or 0)
            current = int(data.get("current", 0) or 0)
            if pages and current >= pages:
                break

        page_number += 1
        time.sleep(0.6)


def write_csv(filename: str, rows: List[Dict[str, str]]) -> None:
    if not rows:
        print("没有可保存的数据。", file=sys.stderr)
        return
    fieldnames = ALL_FIELDS
    with open(filename, mode="w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"已将 {len(rows)} 条结果保存到 {filename}")


def load_keywords_from_file(path: str) -> List[str]:
    with open(path, encoding="utf-8") as fp:
        return [line.strip() for line in fp if line.strip()]


def build_categories(args) -> List[str]:
    categories = []
    if getattr(args, "category", None):
        categories.extend(args.category)
    if getattr(args, "categories", None):
        categories.extend([item.strip() for item in args.categories.split(",") if item.strip()])
    if not categories:
        categories = ["national"]
    return categories


def main() -> None:
    parser = argparse.ArgumentParser(description="标准关键词爬虫，支持按类别检索和按 TC 标委会检索，保存结果为 CSV。")
    parser.add_argument("--keyword", help="单个检索关键词。")
    parser.add_argument("--keywords-file", help="包含多个关键词的文本文件，每行一个关键词。")
    parser.add_argument("--output", help="输出 CSV 文件路径（不指定时输出到 stdout）。")
    parser.add_argument("--category", action="append", choices=CATEGORY_CONFIG.keys(), help="检索标准类别，可重复指定。例如 --category national --category industry。")
    parser.add_argument("--categories", help="逗号分隔的类别列表，等价于 --category。")
    parser.add_argument("--page-size", type=int, default=15, help="每页检索数量，默认 15。")
    parser.add_argument("--max-pages", type=int, default=0, help="最大爬取页数，0 表示不限制。")
    parser.add_argument("--tc", action="append", help="按 TC 标委会筛选（仅国家标准），可重复指定。例如 --tc TC90 --tc TC402。")
    parser.add_argument("--list-tc", action="store_true", help="列出所有可用的 TC 标委会。")
    args = parser.parse_args()

    # --list-tc mode: just print committees and exit
    if args.list_tc:
        committees = fetch_tc_committees()
        if not committees:
            print("无法获取 TC 列表，请检查网络连接。", file=sys.stderr)
            sys.exit(1)
        print(f"共 {len(committees)} 个 TC 标委会：\n")
        for c in committees:
            print(f"  {c['code']:>6s}  {c['name']}")
        return

    # --tc mode: search by TC committee (only national, via advanced search API)
    if args.tc:
        if args.output:
            output = args.output
        else:
            output = f"tc_{'_'.join(args.tc)}.csv"

        tc_codes = args.tc
        results = []
        for tc_code in tc_codes:
            tc_code = tc_code.upper().strip()
            print(f"开始检索 TC 标委会：{tc_code}")
            for row in iter_tc_results(tc_code, page_size=args.page_size, max_pages=args.max_pages):
                results.append(row)

        write_csv(output, results)
        return

    # Keyword search mode (existing behavior)
    if not args.keyword and not args.keywords_file:
        parser.error("请提供 --keyword、--keywords-file 或 --tc。")

    if not args.output:
        parser.error("关键词搜索模式下需要 --output 参数。")

    categories = build_categories(args)
    keywords = []
    if args.keywords_file:
        keywords = load_keywords_from_file(args.keywords_file)
    if args.keyword:
        keywords.append(args.keyword)

    results = []
    for category in categories:
        if category not in CATEGORY_CONFIG:
            continue
        print(f"使用类别：{CATEGORY_CONFIG[category]['name']} ({category})")
        for keyword in keywords:
            print(f"开始检索关键词：{keyword}")
            for row in iter_keyword_results(category, keyword, page_size=args.page_size, max_pages=args.max_pages):
                results.append(row)

    write_csv(args.output, results)


if __name__ == "__main__":
    main()
