import re
import json

# Пример текста
texts = ["Пациент принимал аспирин при гипертонии."]

# Примитивная автоматическая разметка
results = []
for text in texts:
    entities = []
    if re.search(r"аспирин", text, re.IGNORECASE):
        entities.append({"text": "аспирин", "label": "DRUG"})
    if re.search(r"гипертони[ия]", text, re.IGNORECASE):
        entities.append({"text": "гипертонии", "label": "DISEASE"})
    results.append({"text": text, "entities": entities})

with open("rule_based_annotations.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
