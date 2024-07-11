import json
import os
from flask import Flask, request

app = Flask(__name__)

# Путь к файлу JSON, в который будут сохраняться чеки
json_filename = "all_checks.json"


@app.route("/")
def root():
    return "PCS KKT ATOL SERVER (5034)"


@app.route("/checkProcessing", methods=['POST'])
def loadCheck():
    content = request.json

    doc_osn = content.get('doc_osn')

    if not doc_osn:
        return "0==", 400  # Bad Request если нет 'doc_osn'

    # Чтение существующих чеков из файла или создание нового словаря, если файла нет
    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            checks = json.load(f)
    else:
        checks = {}

    # Добавление нового чека в словарь с использованием doc_osn в качестве ключа
    checks[str(doc_osn)] = content

    # Запись всех чеков обратно в файл
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(checks, f, ensure_ascii=False, indent=4)

    # Формирование ответа для 1С
    status = 1  # Успешное сохранение
    fiscalSign = ""  # Нет фискального признака для сохранения чека
    dateTime = ""  # Время операции не указывается

    return f"{status}={fiscalSign}={dateTime}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5034)
