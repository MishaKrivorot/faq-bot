import requests
from bs4 import BeautifulSoup
import json
import re


BASE_URL = "https://rex.knu.ua"

# ------------------------------
# УТИЛІТИ
# ------------------------------

def get_soup(url):
    """Завантаження HTML-сторінки"""
    r = requests.get(url, timeout=10)
    return BeautifulSoup(r.text, "html.parser")

def clean_text(t):
    return re.sub(r"\s+", " ", t).strip()

# ------------------------------
# ПАРСИНГ РОЗДІЛІВ
# ------------------------------

def parse_contacts():
    """Контакти деканату та кафедр"""
    faq = []
    url = f"{BASE_URL}/contacts"
    soup = get_soup(url)

    blocks = soup.select(".contact-block")

    for b in blocks:
        title = clean_text(b.select_one("h3").text)
        text = clean_text(b.text)

        faq.append({
            "question": f"Які контакти підрозділу {title}?",
            "answer": text
        })

    return faq


def parse_hostel():
    """Інформація про гуртожиток"""
    faq = []
    url = f"{BASE_URL}/hostel"
    soup = get_soup(url)

    paragraphs = soup.select("p")

    for p in paragraphs:
        txt = clean_text(p.text)
        if len(txt) < 30:
            continue

        # автоматично генеруємо питання
        faq.append({
            "question": f"Інформація про гуртожиток: {txt[:50]}?",
            "answer": txt
        })

    return faq


def parse_admission():
    """Вступ / абітурієнтам"""
    faq = []
    url = f"{BASE_URL}/admission"
    soup = get_soup(url)

    paragraphs = soup.select("p")
    for p in paragraphs:
        txt = clean_text(p.text)
        if len(txt) < 30:
            continue

        faq.append({
            "question": f"Що потрібно знати абітурієнту? {txt[:60]}?",
            "answer": txt
        })

    return faq


def parse_departments():
    """Парсинг кафедр"""
    faq = []
    url = f"{BASE_URL}/departments"
    soup = get_soup(url)

    cards = soup.select(".department-card")

    for c in cards:
        title = clean_text(c.select_one("h3").text)
        desc = clean_text(c.select_one("p").text)

        faq.append({
            "question": f"Що вивчає кафедра {title}?",
            "answer": desc
        })

    return faq


# ------------------------------
# АВТОГЕНЕРАЦІЯ FAQ
# ------------------------------

def generate_faq():
    faq = []

    print("Парсимо контакти...")
    faq += parse_contacts()

    print("Парсимо гуртожиток...")
    faq += parse_hostel()

    print("Парсимо вступ...")
    faq += parse_admission()

    print("Парсимо кафедри...")
    faq += parse_departments()

    print(f"Загалом питань: {len(faq)}")

    # зберігаємо у файл
    with open("faqs.json", "w", encoding="utf-8") as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)

    print("Готово! Збережено у faqs.json")


if __name__ == "__main__":
    generate_faq()
