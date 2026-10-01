#!/usr/bin/env python3

import os
import random
import sys

import requests  # pylint: disable=import-error  # pyright: ignore[reportMissingModuleSource]


class FatalError(Exception):
    "Fatal error."


def get_envar(name: str) -> str:
    "Read environment variable."
    val = os.environ.get(name)
    if val is None:
        raise FatalError(f"Missing '{name}' environment variable!")
    return val


def lines_to_notes(lines: list[str]) -> list[list[str]]:
    "Split lines into notes (lists of lines)."
    # Пропускаем пустые строки в начале файла.
    for i, line in enumerate(lines):
        if line.strip():
            break
    else:
        return []
    # Разделяем файл на отдельные заметки по признаку "две пустых строки подряд"
    nsep = 2
    result: list[list[str]] = [[]]  # Сразу добавляем одну пустую заметку.
    cnt = 0
    for line in lines[i:]:
        # Если строка пустая, то просто увеличиваем счетчик пустых строк.
        if not line.strip():
            cnt += 1
        else:
            # Если строка не пустая, добавляем ее в результат, но сначала обрабатываем
            # накопившиеся пустые строки. Если их много, то переходим к новой пустой
            # заметке, иначе добавляем данное количество пустых строк к текущей заметке.
            if cnt >= nsep:
                result.append([])
            else:
                result[-1].extend([""] * cnt)
            result[-1].append(line)
            cnt = 0
    return result


def send_message(*, bot_token: str, chat_id: str | int, text: str):
    "Send a message to Telegram using the Bot API."
    # Replace these with your actual bot token and chat ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload: dict[str, str | int] = {
        "chat_id": chat_id,
        "text": text,
        # "parse_mode": "HTML" # Позволит использовать базовые теги, если захотите
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise FatalError(f"Failed to send message: {response.text}")


def main():
    "Main function."
    notes_file_url = get_envar("NOTES_FILE_URL")
    telegram_token = get_envar("TELEGRAM_TOKEN")
    chat_id = get_envar("CHAT_ID")

    try:
        max_msg_size = int(get_envar("MAX_MSG_SIZE"))
    except ValueError as e:
        raise FatalError("Incorrect value for MAX_MSG_SIZE variable") from e

    response = requests.get(notes_file_url)
    if response.status_code != 200:
        raise FatalError("Failed to download the file")
    response.encoding = "utf-8"
    file_content = response.text
    lines = file_content.splitlines()

    notes = lines_to_notes(lines)
    if not notes:
        raise FatalError("File contains no notes.")

    # Выбор и отправка случайной заметки
    note_lines = random.choice(notes)
    note_text = "\n".join(note_lines)

    if len(note_text) > max_msg_size:
        skip_warn = "\n...[SKIPPED]"
        note_text = note_text[:max_msg_size - len(skip_warn)] + skip_warn

    send_message(bot_token=telegram_token, chat_id=chat_id, text=note_text)


if __name__ == "__main__":
    try:
        main()
    except FatalError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
