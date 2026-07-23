import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


STATUS_URL = "https://tgepass.cgg.gov.in/HomeServicePostmatricKnowApplication"
STATE_PATH = Path("epass-notification-state.md")
MESSAGE_PATH = Path("epass-notification-message.md")

APPLICATIONS = [
    {"ordinal": "first", "application": "202111856079", "academic_year": "2021-22"},
    {"ordinal": "second", "application": "202211856079", "academic_year": "2022-23"},
    {"ordinal": "third", "application": "202311856079", "academic_year": "2023-24"},
    {"ordinal": "fourth", "application": "202411856079", "academic_year": "2024-25"},
]


def load_state():
    if not STATE_PATH.exists():
        return {}
    text = STATE_PATH.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", text, re.S)
    if not match:
        return {}
    return json.loads(match.group(1))


def write_state(state):
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S %Z")
    body = (
        "# Telangana ePASS Notification State\n\n"
        f"Last updated: {now}\n\n"
        "```json\n"
        f"{json.dumps(state, indent=2, sort_keys=True)}\n"
        "```\n"
    )
    STATE_PATH.write_text(body, encoding="utf-8")


def visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def has_bank_remitted_date(text):
    if not re.search(r"Bank\s+Remitted\s+Date|Remittance\s+Date|Payment\s+Date", text, re.I):
        return False
    return bool(re.search(r"(Bank\s+Remitted\s+Date|Remittance\s+Date|Payment\s+Date)\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", text, re.I))


def parse_amounts(text):
    explicit_103000 = bool(re.search(r"(?<!\d)103000(?:\.0+)?(?!\d)", text))
    totals = []

    row_patterns = [
        r"sanctioned\s+Amount\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)",
        r"Sanctioned\s+Amount\s*\(Rs\)\s*([0-9]+(?:\.[0-9]+)?)",
        r"sanctioned\s+Amount\s*:\s*([0-9]+(?:\.[0-9]+)?)",
    ]
    for pattern in row_patterns:
        for match in re.finditer(pattern, text, re.I):
            totals.append(float(match.groups()[-1]))

    fee_labels = ["Tuition Fee", "Tution Fee", "Special Fee", "Other Fee", "Exam Fee", "Mess Charges"]
    fee_total = 0.0
    fee_found = False
    for label in fee_labels:
        match = re.search(rf"{label}\s*(?:\(Rs\))?\s*:?\s*([0-9]+(?:\.[0-9]+)?)", text, re.I)
        if match:
            fee_total += float(match.group(1))
            fee_found = True

    if fee_found:
        totals.append(fee_total)

    amount = 103000.0 if explicit_103000 else (max(totals) if totals else 0.0)
    return amount, explicit_103000


def close_popups(page):
    for label in ["Close", "×", "Cancel", "OK"]:
        try:
            page.get_by_text(label, exact=True).first.click(timeout=1200)
        except Exception:
            pass


def check_one(page, item):
    page.goto(STATUS_URL, wait_until="domcontentloaded", timeout=60000)
    close_popups(page)
    page.locator("select").first.select_option(label=item["academic_year"])
    page.locator("input").first.fill(item["application"])
    page.get_by_text("Get Status", exact=False).click(timeout=10000)
    page.wait_for_load_state("networkidle", timeout=30000)
    text = visible_text(page.content())
    amount, explicit_103000 = parse_amounts(text)
    return {
        "last_observed_total_or_summed_sanctioned_amount": amount,
        "explicit_103000_shown": explicit_103000,
        "bank_remitted_date_present": has_bank_remitted_date(text),
        "last_successful_check": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
    }


def conditions_for(item, observed):
    amount = observed["last_observed_total_or_summed_sanctioned_amount"]
    conditions = []
    if amount > 35000:
        conditions.append(("above_35000", f"{item['ordinal']} year sanctioned amount {amount:g}"))
    if amount == 103000 and not observed["bank_remitted_date_present"]:
        conditions.append(("103000_sanctioned", f"{item['ordinal']} year 103000 sanctioned — done"))
    if amount == 103000 and observed["bank_remitted_date_present"]:
        conditions.append(("103000_released", f"{item['ordinal']} year 103000 sanctioned and released — done"))
    return conditions


def main():
    MESSAGE_PATH.unlink(missing_ok=True)
    state = load_state()
    notifications = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        for item in APPLICATIONS:
            key = f"{item['application']}|{item['academic_year']}"
            current = state.get(key, {"reported_conditions": []})
            observed = check_one(page, item)
            reported = set(current.get("reported_conditions", []))

            for condition_key, message in conditions_for(item, observed):
                if condition_key not in reported:
                    notifications.append(f"{message}\nApplication {item['application']}, academic year {item['academic_year']}")
                    reported.add(condition_key)

            observed["reported_conditions"] = sorted(reported)
            state[key] = observed
        browser.close()

    write_state(state)
    if notifications:
        MESSAGE_PATH.write_text("\n\n".join(notifications) + "\n", encoding="utf-8")
        print("\n\n".join(notifications))
    else:
        print("No new matching condition found.")


if __name__ == "__main__":
    main()

