# saving_answer.py

import os
import datetime
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QDir


def generate_default_filename(rows, cols, is_max, ext):
    mode = 'max' if is_max else 'min'
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"simplex-{rows}-{cols}-{mode}-{date_str}.{ext}"
    return filename


def save_file_dialog(default_filename, filter_str):
    downloads_path = QDir.homePath()
    potential_downloads = os.path.join(QDir.homePath(), "Downloads")
    if os.path.exists(potential_downloads):
        downloads_path = potential_downloads

    dialog = QFileDialog()
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setNameFilter(filter_str)
    dialog.setDirectory(downloads_path)
    dialog.selectFile(default_filename)

    if dialog.exec():
        selected_files = dialog.selectedFiles()
        if selected_files:
            return selected_files[0]
    return ""


def save_as_text(rows, cols, is_max, task_info, start_matrix, end_matrix, solution_str, filepath):
    content = []
    content.append("Задача:\n")
    content.append(task_info + "\n\n")
    content.append("Начальная матрица:\n")
    content.append(start_matrix + "\n\n")
    content.append("Конечная матрица:\n")
    content.append(end_matrix + "\n\n")
    content.append("Ответ:\n")
    content.append(solution_str + "\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(content))


def save_as_html(rows, cols, is_max, task_info, start_matrix_html, end_matrix_html, solution_str, filepath):
    mode = 'max' if is_max else 'min'
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8" />
        <title>Результаты Симплекс-метода</title>
        <style>
            body {{
                background: #fafafa;
                color: #333;
                font-family: sans-serif;
                margin: 20px;
            }}
            h1, h2 {{
                color: #333;
            }}
            .matrix {{
                margin: 10px 0;
                padding: 10px;
                background: #f9f9f9;
                border: 1px solid #ccc;
            }}
            table {{
                border-collapse: collapse;
                font-size: 14px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 5px 10px;
                text-align: center;
            }}
            .answer {{
                background: #e0ffe0;
                padding: 10px;
                margin-top: 20px;
                border: 1px solid #ccc;
            }}
            .task {{
                background: #e0f7fa;
                padding: 10px;
                border: 1px solid #ccc;
            }}
        </style>
    </head>
    <body>
        <h1>Результаты Симплекс-метода</h1>

        <h2>Задача:</h2>
        <div class="task">
        <pre>{task_info}</pre>
        </div>

        <h2>Начальная матрица:</h2>
        <div class="matrix">
        {start_matrix_html}
        </div>

        <h2>Конечная матрица:</h2>
        <div class="matrix">
        {end_matrix_html}
        </div>

        <h2>Ответ:</h2>
        <div class="answer">
        <pre>{solution_str}</pre>
        </div>
    </body>
    </html>
    """

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
