import json
import itertools

# Набори фраз для генерації варіантів
ASK_PREFIXES = [
    "Як", "Скажіть, будь ласка, як", "Підкажіть, як", 
    "Хочу дізнатися, як", "Поясніть, будь ласка, як"
]

NEED_PREFIXES = [
    "Що потрібно", "Що треба", "Які документи треба", 
    "Які документи потрібні", "Що необхідно"
]

ABOUT_PREFIXES = [
    "Де можна знайти", "Де подивитися", 
    "Куди зайти, щоб побачити", 
    "Як знайти", "Підкажіть, де знайти"
]

HOSTEL_PREFIXES = [
    "Як отримати", "Як подати заявку на", "Хто може отримати", 
    "Що треба для", "Умови отримання"
]

GREETING_PREFIXES = [
    "Привіт", "Добрий день", "Скажіть, будь ласка"
]


def generate_variants(base_question: str):
    """Генерує варіанти питання на основі ключових слів."""

    q = base_question.lower()

    variants = set()
    variants.add(base_question)

    # 1. Варіанти для вступу
    if "вступ" in q or "поступ" in q or "абітурієнт" in q:
        for p in ASK_PREFIXES:
            variants.add(f"{p} {base_question.lower()}?")
        for p in NEED_PREFIXES:
            variants.add(f"{p} для того, щоб {base_question.lower()}?")
        variants.add(base_question.replace("Як", "Де можна"))

    # 2. Гуртожиток
    if "гуртожит" in q:
        for p in HOSTEL_PREFIXES:
            variants.add(f"{p} {base_question.lower()}?")
        variants.add(f"Що потрібно знати про {base_question.lower()}?")

    # 3. Документи
    if "документ" in q:
        for p in NEED_PREFIXES:
            variants.add(f"{p} для {base_question.lower()}?")
        variants.add(f"Які саме документи потрібні, щоб {base_question.lower()}?")

    # 4. Розклад
    if "розклад" in q:
        for p in ABOUT_PREFIXES:
            variants.add(f"{p} {base_question.lower()}?")
        variants.add("Де глянути розклад пар?")

    # 5. Загальні типові варіанти
    variants.update({
        base_question + "?",
        base_question.replace("?", ""),
        base_question.lower(),
        "Мене цікавить: " + base_question.lower(),
        "Питання: " + base_question.lower(),
    })

    # Почистимо
    cleaned = list(set(v.strip().rstrip("?") for v in variants))

    return cleaned



def expand_faq(input_json="faqs.json", output_json="faqs_expanded.json"):
    """Створює новий JSON з розширеними питаннями."""

    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    expanded = []

    for item in data:
        question = item["question"]
        answer = item["answer"]

        variants = generate_variants(question)

        for v in variants:
            expanded.append({
                "question": v,
                "answer": answer
            })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(expanded, f, ensure_ascii=False, indent=2)

    print(f"Готово! Створено {len(expanded)} записів у {output_json}")


if __name__ == "__main__":
    expand_faq()
