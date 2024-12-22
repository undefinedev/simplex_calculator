# main.py
import datetime
import os.path as path
import sys
import random
import qdarkstyle
from pandas import DataFrame
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QMessageBox, QAbstractSpinBox, QPlainTextEdit, QTabWidget, QFileDialog,
    QRadioButton, QDialog
)
from PyQt6.QtGui import QIcon, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression, QDir
from fractions import Fraction

from solution_window import SimplexSolutionWindow, rename_df_headers, format_number
from save_answer import generate_default_filename, save_as_text, save_as_html


class SimplexCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симплекс Метод Калькулятор v1.3.0")
        self.is_dark_theme = False
        self.initUI()

    def initUI(self):
        self.apply_theme()

        self.tab_widget = QTabWidget(self)

        # GUI mode tab
        gui_mode_widget = QWidget()
        gui_layout = QVBoxLayout(gui_mode_widget)
        self.create_gui_tab(gui_layout)
        self.tab_widget.addTab(gui_mode_widget, "GUI Mode")

        # Text mode tab
        text_mode_widget = QWidget()
        text_layout = QVBoxLayout(text_mode_widget)

        info_label = QLabel("Введите задачу в текстовом формате или загрузите из файла.\n"
                            "Формат:\n"
                            "Первая строка: кол-во_переменных кол-во_ограничений\n"
                            "Вторая строка: коэфф. цел. функции и min/max\n"
                            "Далее ограничения: коэффы, знак, правая часть.\n"
                            "Поддержка чисел: целые, десятичные (2.5), дроби (3/2).")
        text_layout.addWidget(info_label)

        self.text_edit = QPlainTextEdit()
        text_layout.addWidget(self.text_edit)

        h_layout = QHBoxLayout()
        self.load_file_button = QPushButton("Загрузить из файла")
        self.load_file_button.clicked.connect(self.load_task_from_file)
        h_layout.addWidget(self.load_file_button)

        self.solve_text_button = QPushButton("Решить")
        self.solve_text_button.clicked.connect(self.solve_text_mode)
        h_layout.addWidget(self.solve_text_button)

        self.back_to_gui_button = QPushButton("Вернуться в GUI режим")
        self.back_to_gui_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        h_layout.addWidget(self.back_to_gui_button)

        text_layout.addLayout(h_layout)
        self.tab_widget.addTab(text_mode_widget, "Text Mode")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        self.update_fields()

    def create_gui_tab(self, layout):
        top_layout = QHBoxLayout()
        top_layout.setSpacing(1)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vars = QLabel("Количество переменных:")
        label_vars.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_vars)

        self.num_vars_minus_button = QPushButton("-")
        self.num_vars_minus_button.setFixedSize(25, 25)
        self.num_vars_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, -1))
        top_layout.addWidget(self.num_vars_minus_button)

        self.num_vars_spin = QSpinBox()
        self.num_vars_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.num_vars_spin.setMinimum(1)
        self.num_vars_spin.setMaximum(12)
        self.num_vars_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_vars_spin.setFixedWidth(60)
        self.num_vars_spin.setValue(3)
        self.num_vars_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_vars_spin)

        self.num_vars_plus_button = QPushButton("+")
        self.num_vars_plus_button.setFixedSize(25, 25)
        self.num_vars_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, 1))
        top_layout.addWidget(self.num_vars_plus_button)

        label_constraints = QLabel("    Количество ограничений:")
        label_constraints.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_constraints)

        self.num_constraints_minus_button = QPushButton("-")
        self.num_constraints_minus_button.setFixedSize(25, 25)
        self.num_constraints_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, -1))
        top_layout.addWidget(self.num_constraints_minus_button)

        self.num_constraints_spin = QSpinBox()
        self.num_constraints_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.num_constraints_spin.setMinimum(1)
        self.num_constraints_spin.setMaximum(12)
        self.num_constraints_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_constraints_spin.setFixedWidth(60)
        self.num_constraints_spin.setValue(3)
        self.num_constraints_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_constraints_spin)

        self.num_constraints_plus_button = QPushButton("+")
        self.num_constraints_plus_button.setFixedSize(25, 25)
        self.num_constraints_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, 1))
        top_layout.addWidget(self.num_constraints_plus_button)

        layout.addLayout(top_layout)

        goal_container_layout = QHBoxLayout()
        goal_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        goal_layout = QHBoxLayout()
        goal_layout.setSpacing(5)
        goal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        goal_label = QLabel("Целевая функция:")
        goal_label.setStyleSheet("font-size: 11.5pt;")
        goal_layout.addWidget(goal_label)

        self.goal_layout = QHBoxLayout()
        self.goal_layout.setSpacing(5)
        self.goal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.goal_inputs = []

        goal_layout.addLayout(self.goal_layout)
        goal_layout.addStretch(1)

        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 13pt;")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        goal_layout.addWidget(arrow_label)

        self.goal_type = QComboBox()
        self.goal_type.addItems(["min", "max"])
        self.goal_type.setStyleSheet("""
                QComboBox {
                    font-size: 12pt;
                }
                QComboBox::drop-down {
                    width: 0px; 
                    border: none; 
                }
                QComboBox::down-arrow {
                    image: none;
                }
            """)
        self.goal_type.setFixedWidth(55)
        self.goal_type.setCurrentText("min")
        goal_layout.addWidget(self.goal_type)

        goal_container_layout.addLayout(goal_layout)
        goal_container_layout.addStretch(1)
        layout.addLayout(goal_container_layout)

        self.constraints_layout = QVBoxLayout()
        self.constraints_layout.setSpacing(5)
        self.constraints_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self.constraints_layout)

        self.solve_button = QPushButton("Решить")
        self.solve_button.setFixedWidth(100)
        self.solve_button.clicked.connect(self.solve)
        layout.addWidget(self.solve_button, alignment=Qt.AlignmentFlag.AlignCenter)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(5)
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.toggle_theme_button = QPushButton("Изменить тему")
        self.toggle_theme_button.setFixedWidth(100)
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        bottom_layout.addWidget(self.toggle_theme_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.random_button = QPushButton("Сгенерировать задачу")
        self.random_button.setFixedWidth(150)
        self.random_button.clicked.connect(self.generate_random_task)
        bottom_layout.addWidget(self.random_button, alignment=Qt.AlignmentFlag.AlignBottom)

        self.save_input_task_button = QPushButton("Сохранить задачу")
        self.save_input_task_button.setFixedWidth(130)
        self.save_input_task_button.clicked.connect(self.save_current_task)
        bottom_layout.addWidget(self.save_input_task_button, alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(bottom_layout)

    def apply_theme(self):
        if self.is_dark_theme:
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6', palette=qdarkstyle.DarkPalette))
            app.setStyleSheet(app.styleSheet() + """
                QTableView::item {
                    color: #ffffff;
                }
                QTableView::item:selected {
                    background-color: #3c3d40;
                    color: #ffffff;
                }
                """)
        else:
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6', palette=qdarkstyle.LightPalette))

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

        if hasattr(self, 'solution_window'):
            self.solution_window.is_dark_theme = self.is_dark_theme

    def change_spin_value(self, spin_box, delta):
        current_value = spin_box.value()
        new_value = current_value + delta
        if spin_box.minimum() <= new_value <= spin_box.maximum():
            spin_box.setValue(new_value)

    def update_fields(self):
        while self.goal_layout.count():
            widget = self.goal_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.goal_inputs.clear()

        num_vars = self.num_vars_spin.value()
        regex = QRegularExpression(r"^-?\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?$")
        validator = QRegularExpressionValidator(regex)

        for i in range(num_vars):
            if i > 0:
                plus_label = QLabel("+")
                plus_label.setStyleSheet("font-size: 12pt;")
                plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.goal_layout.addWidget(plus_label)

            input_field = QLineEdit()
            input_field.setValidator(validator)
            input_field.setPlaceholderText("0")
            input_field.setStyleSheet("font-size: 12pt;")
            input_field.setFixedWidth(55)
            self.goal_inputs.append(input_field)
            self.goal_layout.addWidget(input_field)

            label = QLabel(f"x<sub>{i + 1}</sub>", self)
            label.setStyleSheet("font-size: 14pt;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.goal_layout.addWidget(label)

        while self.constraints_layout.count():
            layout = self.constraints_layout.takeAt(0).layout()
            if layout:
                while layout.count():
                    widget = layout.takeAt(0).widget()
                    if widget:
                        widget.deleteLater()
                self.constraints_layout.removeItem(layout)

        num_constraints = self.num_constraints_spin.value()
        num_vars = self.num_vars_spin.value()
        for i in range(num_constraints):
            constraint_centered_layout = QHBoxLayout()
            constraint_centered_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            constraint_centered_layout.addStretch(1)

            for j in range(num_vars):
                if j > 0:
                    plus_label = QLabel("+")
                    plus_label.setStyleSheet("font-size: 12pt;")
                    plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    constraint_centered_layout.addWidget(plus_label)

                input_field = QLineEdit()
                input_field.setValidator(validator)
                input_field.setStyleSheet("font-size: 12pt;")
                input_field.setPlaceholderText("0")
                input_field.setFixedWidth(55)
                constraint_centered_layout.addWidget(input_field)

                label = QLabel(f"x<sub>{j + 1}</sub>", self)
                label.setStyleSheet("font-size: 14pt;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                constraint_centered_layout.addWidget(label)

            relation = QComboBox()
            relation.addItems(["≤", "≥", "="])
            relation.setStyleSheet("""
                QComboBox {
                    font-size: 13pt;
                }
                QComboBox::drop-down {
                    width: 0px; 
                    border: none; 
                }
                
                QComboBox::down-arrow {
                    image: none;
                }
            """)
            relation.setFixedWidth(40)
            constraint_centered_layout.addWidget(relation)

            # Add RHS input
            rhs = QLineEdit()
            rhs.setValidator(validator)
            rhs.setPlaceholderText("0")
            rhs.setStyleSheet("font-size: 12.5pt;")
            rhs.setFixedWidth(55)
            constraint_centered_layout.addWidget(rhs)

            constraint_centered_layout.addStretch(1)
            self.constraints_layout.addLayout(constraint_centered_layout)

    def solve(self):
        try:
            goal_values = [parse_input_number(field.text()) if field.text() else 0.0 for field in self.goal_inputs]
            goal_type_selected = self.goal_type.currentText().lower()

            # Handle goal function based on selection
            if goal_type_selected == "min":
                # For minimization, set F row as 0 - (original goal function)
                # E.g., min X2 - X1 → F = 0 - (X1 - X2) = -X1 + X2
                adjusted_goal_values = [-val for val in goal_values]
            elif goal_type_selected == "max":
                # For maximization, convert to minimization by negating coefficients
                # F row will be 0 - (-original) = +original
                # E.g., max 2X1 + 3X2 → F = 0 - (-2X1 -3X2) = 2X1 +3X2
                adjusted_goal_values = [val for val in goal_values]
            else:
                QMessageBox.warning(
                    self,
                    "Input Error",
                    "Пожалуйста, выберите тип целевой функции (min или max)."
                )
                return

            num_vars = self.num_vars_spin.value()
            num_constraints = self.num_constraints_spin.value()

            decision_vars = [f"X{i+1}" for i in range(num_vars)]

            constraints = []
            for i in range(num_constraints):
                layout = self.constraints_layout.itemAt(i).layout()
                if layout is None:
                    continue

                widgets = [layout.itemAt(j).widget() for j in range(layout.count())]

                qlineedits = [widget for widget in widgets if isinstance(widget, QLineEdit)]
                qcomboboxes = [widget for widget in widgets if isinstance(widget, QComboBox)]

                expected_qlineedits = num_vars + 1
                if len(qlineedits) < expected_qlineedits or len(qcomboboxes) < 1:
                    QMessageBox.warning(
                        self,
                        "Input Error",
                        f"Уравнение {i + 1} имеет неверные поля ввода."
                    )
                    return

                coeffs = []
                for j in range(num_vars):
                    text = qlineedits[j].text()
                    coef = parse_input_number(text) if text else 0.0
                    coeffs.append(coef)

                relation = qcomboboxes[0].currentText()

                rhs_value = parse_input_number(qlineedits[-1].text()) if qlineedits[-1].text() else 0.0

                constraints.append((coeffs, relation, rhs_value))

            basic_vars = {}
            added_basic_vars = set()

            for idx, (coeffs, relation, rhs) in enumerate(constraints):
                if relation == "=":
                    # Check for decision variables with coefficient 1 or -1
                    basic_var_candidates = [var for var, coef in zip(decision_vars, coeffs) if abs(coef) == 1.0]

                    # Further filter candidates by checking uniqueness across constraints
                    valid_candidates = []
                    for var in basic_var_candidates:
                        var_index = decision_vars.index(var)
                        appears_in_other_constraints = False
                        for other_idx, (other_coeffs, _, _) in enumerate(constraints):
                            if other_idx != idx and other_coeffs[var_index] != 0.0:
                                appears_in_other_constraints = True
                                break
                        if not appears_in_other_constraints:
                            valid_candidates.append(var)

                    if len(valid_candidates) == 1:
                        basic_var = valid_candidates[0]
                        basic_vars[idx] = basic_var
                    elif len(valid_candidates) > 1:
                        basic_var = valid_candidates[0]
                        basic_vars[idx] = basic_var
                        QMessageBox.information(
                            self,
                            "Базисная переменная выбрана автоматически",
                            f"Для ограничения {idx + 1} было выбрано {basic_var} как базисная переменная."
                        )
                    else:
                        reply = QMessageBox.question(
                            self,
                            "Отсутствует базисная переменная",
                            f"В ограничении {idx + 1} нет переменной с коэффициентом 1 или -1, которая уникальна.\n"
                            "Хотите автоматически добавить новую базисную переменную?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            # Automatically assign a new basic variable
                            next_num = num_vars + len(added_basic_vars) + 1
                            new_basic_var = f"X{next_num}"
                            basic_vars[idx] = new_basic_var
                            added_basic_vars.add(new_basic_var)
                            # Inform the user
                            QMessageBox.information(
                                self,
                                "Добавлена новая базисная переменная",
                                f"Базисная переменная {new_basic_var} была автоматически добавлена для ограничения {idx + 1}."
                            )
                        else:
                            # User chooses to go back and edit constraints
                            QMessageBox.information(
                                self,
                                "Редактирование ограничений",
                                "Пожалуйста, отредактируйте ограничения, чтобы каждая базисная переменная была уникальной и имела коэффициент 1 или -1."
                            )
                            return
                elif relation in ["≤", "≥"]:
                    next_num = num_vars + len(added_basic_vars) + 1
                    new_basic_var = f"X{next_num}"
                    basic_vars[idx] = new_basic_var
                    added_basic_vars.add(new_basic_var)
                else:
                    QMessageBox.warning(
                        self,
                        "Input Error",
                        f"Уравнение {idx + 1} имеет недопустимое отношение."
                    )
                    return

            final_decision_vars = [var for var in decision_vars if var not in basic_vars.values()]

            if len(final_decision_vars) < len(decision_vars):
                QMessageBox.information(
                    self,
                    "Исключение базисных переменных",
                    "Некоторые переменные были автоматически исключены из целевой функции, так как они являются базисными переменными."
                )

            tableau_data = []
            row_names = []

            for idx, (coeffs, relation, rhs) in enumerate(constraints):
                basic_var = basic_vars[idx]
                row_names.append(basic_var)

                adjusted_rhs = rhs
                adjusted_coeffs = coeffs.copy()

                if relation == "≥":
                    adjusted_coeffs = [-c for c in adjusted_coeffs]
                    adjusted_rhs = -rhs

                row = [Fraction(adjusted_rhs)]
                for var in final_decision_vars:
                    var_index = decision_vars.index(var)
                    coef = adjusted_coeffs[var_index] if var_index < len(adjusted_coeffs) else 0.0
                    row.append(Fraction(coef))
                tableau_data.append(row)

            objective_row = [Fraction(0)]  # 0 for Si
            for var in final_decision_vars:
                var_index = decision_vars.index(var)
                coef = adjusted_goal_values[var_index]
                objective_row.append(Fraction(coef))
            row_names.append("F")
            tableau_data.append(objective_row)

            columns = ["Si"] + final_decision_vars

            df = DataFrame(tableau_data, columns=columns, index=row_names)

            copy_basic_vars = row_names[:-1]
            copy_non_basic_vars = columns[1:]
            maximization_flag = True if goal_type_selected == "max" else False

            terms = []
            for i, coef in enumerate(goal_values):
                if coef != 0:
                    if i == 0:
                        if coef < 0:
                            sign = "-"
                        else:
                            sign = ""
                    else:
                        if coef > 0:
                            sign = "+"
                        else:
                            sign = "-"

                    fcoef = format_task_number(Fraction(abs(coef)))
                    if abs(coef) == 1:
                        terms.append(f"{sign}x{i + 1}")
                    else:
                        terms.append(f"{sign}{fcoef}x{i + 1}")

            if not terms:
                terms = ["0"]

            goal_type_selected = self.goal_type.currentText().lower()
            task_info = "Целевая функция: " + " ".join(terms) + f" → {goal_type_selected}\n\nУсловия:\n"

            for i, (coeffs, relation, rhs) in enumerate(constraints, start=1):
                constraint_terms = []
                for j, c in enumerate(coeffs):
                    if c != 0:
                        if j == 0:
                            if c < 0:
                                sign = "-"
                            else:
                                sign = ""
                        else:
                            if c > 0:
                                sign = "+"
                            else:
                                sign = "-"

                        fc = format_task_number(Fraction(abs(c)))
                        if abs(c) == 1:
                            constraint_terms.append(f"{sign}x{j + 1}")
                        else:
                            constraint_terms.append(f"{sign}{fc}x{j + 1}")

                if not constraint_terms:
                    constraint_terms = ["0"]

                frhs = format_task_number(Fraction(rhs))
                constraint_str = constraint_terms[0]
                for t in constraint_terms[1:]:
                    if t.startswith('+'):
                        constraint_str += " " + t.replace('+', '+ ')
                    elif t.startswith('-'):
                        constraint_str += " " + t.replace('-', '- ')
                    else:
                        constraint_str += " " + t

                if constraint_str.startswith('+'):
                    constraint_str = constraint_str[1:].strip()

                constraint_str += f" {relation} {frhs}"
                task_info += f"{constraint_str}\n"

            # Display the initial tableau in the solution window
            self.solution_window = SimplexSolutionWindow(dark_theme=self.is_dark_theme, task_info=task_info,
                                                         original_constraints=constraints, num_vars=num_vars)
            self.solution_window.add_step(df, copy_basic_vars, copy_non_basic_vars, is_maximization=maximization_flag)
            self.solution_window.show()

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Input Error",
                f"Пожалуйста, убедитесь, что все поля заполнены корректно и содержат числовые значения.\n\nОшибка: {e}"
            )
            return

    def save_current_task(self):
        """
        Save the currently inputted task in a txt file in the required format:
        Line 1: num_vars num_constraints
        Line 2: goal_coefs ... goal_type
        Then constraints each line: coefs ... relation rhs
        """
        # Gather current input
        num_vars = self.num_vars_spin.value()
        num_constraints = self.num_constraints_spin.value()

        # Parse goal function coefficients
        goal_values = []
        for field in self.goal_inputs:
            txt = field.text().strip()
            if txt:
                val = parse_input_number(txt)
            else:
                val = Fraction(0)
            goal_values.append(val)

        goal_type_selected = self.goal_type.currentText().lower()

        # Parse constraints
        constraints = []
        for i in range(num_constraints):
            layout = self.constraints_layout.itemAt(i).layout()
            if layout is None:
                continue

            widgets = [layout.itemAt(j).widget() for j in range(layout.count())]

            qlineedits = [w for w in widgets if isinstance(w, QLineEdit)]
            qcomboboxes = [w for w in widgets if isinstance(w, QComboBox)]

            expected_qlineedits = num_vars + 1
            if len(qlineedits) < expected_qlineedits or len(qcomboboxes) < 1:
                QMessageBox.warning(
                    self,
                    "Input Error",
                    f"Уравнение {i + 1} имеет неверные поля ввода."
                )
                return

            coeffs = []
            for j in range(num_vars):
                text = qlineedits[j].text().strip()
                if text:
                    c = parse_input_number(text)
                else:
                    c = Fraction(0)
                coeffs.append(c)

            relation = qcomboboxes[0].currentText()
            rhs_text = qlineedits[-1].text().strip()
            rhs_val = parse_input_number(rhs_text) if rhs_text else Fraction(0)

            constraints.append((coeffs, relation, rhs_val))

        # Create default filename
        now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_filename = f"simple_task_{num_vars}_{num_constraints}_{now_str}.txt"

        # Open file dialog to save
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить задачу",
            QDir.homePath() + "/" + default_filename,
            "Text Files (*.txt);;All Files (*)"
        )
        if not filepath:
            return  # user canceled

        # Write to file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Line 1: num_vars num_constraints
                f.write(f"{num_vars} {num_constraints}\n")

                # Line 2: goal_coefs ... goal_type
                # Convert goal_values to str. Just use numerator/denominator if fraction:
                goal_line_parts = []
                for gv in goal_values:
                    if gv.denominator == 1:
                        goal_line_parts.append(str(gv.numerator))
                    else:
                        goal_line_parts.append(f"{gv.numerator}/{gv.denominator}")
                goal_line = " ".join(goal_line_parts) + " " + goal_type_selected
                f.write(goal_line + "\n")

                # Constraints
                for (coeffs, relation, rhs) in constraints:
                    # Convert coeffs and rhs to strings
                    c_strs = []
                    for c in coeffs:
                        if c.denominator == 1:
                            c_strs.append(str(c.numerator))
                        else:
                            c_strs.append(f"{c.numerator}/{c.denominator}")

                    if rhs.denominator == 1:
                        rhs_str = str(rhs.numerator)
                    else:
                        rhs_str = f"{rhs.numerator}/{rhs.denominator}"

                    # relation should be converted to original: if we have "≤","≥","="?
                    # Original input format maybe used <, <=, >, >=, =. Let's revert them:
                    # If user typed them from UI as "≤", "≥", "=" we must choose consistent original sign
                    # The original format said we can keep the sign as is: if we want ASCII:
                    # Replace "≤" with "<=", "≥" with ">=" for saving:
                    if relation == "≤":
                        rel_str = "<="
                    elif relation == "≥":
                        rel_str = ">="
                    else:
                        rel_str = "="

                    f.write(" ".join(c_strs) + f" {rel_str} {rhs_str}\n")

            QMessageBox.information(self, "Успех", f"Задача сохранена в файл:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка записи файла", f"Не удалось записать файл:\n{e}")

    def load_task_from_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Выбрать файл с задачей", QDir.homePath(), "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_edit.setPlainText(content)

    def solve_text_mode(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Текст задачи пуст.")
            return

        lines = text.split('\n')
        if len(lines) < 2:
            QMessageBox.warning(self, "Ошибка", "Недостаточно строк.")
            return

        first_line = lines[0].strip().split()
        if len(first_line) != 2:
            QMessageBox.warning(self, "Ошибка", "Первая строка: 2 числа (переменные и ограничения).")
            return

        try:
            num_vars = int(first_line[0])
            num_constraints = int(first_line[1])
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Первая строка нечисловая.")
            return

        if num_vars > 25 or num_constraints > 25:
            QMessageBox.warning(self, "Отказ", "Не больше 25 переменных и уравнений")

        second_line = lines[1].strip().split()
        if len(second_line) != (num_vars+1):
            QMessageBox.warning(self, "Ошибка", "Вторая строка: коэфф. + min/max")
            return

        goal_values_str = second_line[:num_vars]
        goal_type_str = second_line[num_vars].lower()
        if goal_type_str not in ["min","max"]:
            QMessageBox.warning(self,"Ошибка","Должно быть min или max в конце второй строки.")
            return

        goal_values = []
        for gs in goal_values_str:
            val = parse_input_number(gs)
            goal_values.append(val)

        if len(lines)<2+num_constraints:
            QMessageBox.warning(self,"Ошибка","Ограничений меньше, чем указано.")
            return

        allowed_relations = {"<":"≤","<=":"≤",">":"≥",">=":"≥","=":"="}
        constraints = []
        from_line = 2
        for i in range(num_constraints):
            line = lines[from_line+i].strip().split()
            if len(line)!=(num_vars+2):
                QMessageBox.warning(self,"Ошибка",f"Огр. {i+1} неверный формат.")
                return
            coeffs_str = line[:num_vars]
            relation_str = line[num_vars]
            rhs_str = line[num_vars+1]
            if relation_str not in allowed_relations:
                QMessageBox.warning(self,"Ошибка",f"Неверный знак в огр. {i+1}")
                return
            relation = allowed_relations[relation_str]

            coeffs=[]
            for cs in coeffs_str:
                c=parse_input_number(cs)
                coeffs.append(c)
            rhs_val = parse_input_number(rhs_str)
            constraints.append((coeffs,relation,rhs_val))

        num_vars_i = num_vars
        decision_vars = [f"X{i+1}" for i in range(num_vars_i)]
        goal_type_selected = goal_type_str
        if goal_type_selected=="min":
            adjusted_goal_values = [-val for val in goal_values]
        else:
            adjusted_goal_values = [val for val in goal_values]


        basic_vars = {}
        added_basic_vars = set()
        for idx,(coeffs,relation,rhs) in enumerate(constraints):
            if relation=="=":
                basic_var_candidates=[var for var,coef in zip(decision_vars,coeffs) if abs(coef)==1.0]
                valid_candidates=[]
                for var in basic_var_candidates:
                    var_index=decision_vars.index(var)
                    appears_in_others=False
                    for other_idx,(other_coeffs,_,_) in enumerate(constraints):
                        if other_idx!=idx and other_coeffs[var_index]!=0.0:
                            appears_in_others=True
                            break
                    if not appears_in_others:
                        valid_candidates.append(var)
                if len(valid_candidates)==1:
                    basic_vars[idx]=valid_candidates[0]
                elif len(valid_candidates)>1:
                    basic_vars[idx]=valid_candidates[0]

                else:
                    next_num=num_vars_i+len(added_basic_vars)+1
                    new_basic_var = f"X{next_num}"
                    basic_vars[idx]=new_basic_var
                    added_basic_vars.add(new_basic_var)
            elif relation in ["≤","≥"]:
                next_num=num_vars_i+len(added_basic_vars)+1
                new_basic_var=f"X{next_num}"
                basic_vars[idx]=new_basic_var
                added_basic_vars.add(new_basic_var)
            else:
                QMessageBox.warning(self,"Ошибка",f"Неверное отношение {relation}")
                return

        final_decision_vars=[var for var in decision_vars if var not in basic_vars.values()]


        tableau_data=[]
        row_names=[]
        for idx,(coeffs,relation,rhs) in enumerate(constraints):
            basic_var=basic_vars[idx]
            row_names.append(basic_var)
            adjusted_rhs=rhs
            adjusted_coeffs=coeffs.copy()
            if relation=="≥":
                adjusted_coeffs = [-c for c in adjusted_coeffs]
                adjusted_rhs=-rhs
            row=[Fraction(adjusted_rhs)]
            for var in final_decision_vars:
                var_index=decision_vars.index(var)
                coef= adjusted_coeffs[var_index] if var_index<len(adjusted_coeffs) else 0.0
                row.append(Fraction(coef))
            tableau_data.append(row)

        objective_row=[Fraction(0)]
        for var in final_decision_vars:
            var_index=decision_vars.index(var)
            coef=adjusted_goal_values[var_index]
            objective_row.append(Fraction(coef))
        row_names.append("F")
        tableau_data.append(objective_row)

        columns=["Si"]+final_decision_vars
        df=DataFrame(tableau_data,columns=columns,index=row_names)

        is_max=(goal_type_selected=="max")

        sw=SimplexSolutionWindow(dark_theme=self.is_dark_theme,task_info="From Text Mode",
                                 original_constraints=constraints, num_vars=num_vars)
        final_df, final_basic_vars, final_non_basic_vars, elapsed_time, status = sw.run_simplex_silently(df,row_names[:-1],final_decision_vars,is_max)

        reverse_relations = {"≤": "<=", "≥": ">=", "=": "="}
        task_info_str = f"{num_vars} {num_constraints}\n"
        # goal line
        goal_line_parts = []
        for gv in goal_values:
            if gv.denominator == 1:
                goal_line_parts.append(str(gv.numerator))
            else:
                goal_line_parts.append(f"{gv.numerator}/{gv.denominator}")
        goal_line = " ".join(goal_line_parts) + " " + goal_type_str
        task_info_str += goal_line + "\n"

        for (coeffs, relation, rhs) in constraints:
            c_strs = []
            for c in coeffs:
                if c.denominator == 1:
                    c_strs.append(str(c.numerator))
                else:
                    c_strs.append(f"{c.numerator}/{c.denominator}")
            if rhs.denominator == 1:
                rhs_str = str(rhs.numerator)
            else:
                rhs_str = f"{rhs.numerator}/{rhs.denominator}"
            rel_str = reverse_relations[relation]
            task_info_str += " ".join(c_strs) + f" {rel_str} {rhs_str}\n"

        if status == "optimal":
            F_row_index = len(final_df.index) - 1
            optimal_value = final_df.iloc[F_row_index, 0]
            if is_max:
                optimal_value = optimal_value * -1

            variable_values = {}
            for i, var in enumerate(final_basic_vars):
                val = final_df.iloc[i, 0]
                variable_values[var] = val
            for var in final_non_basic_vars:
                variable_values[var] = Fraction(0)

            result_str = f"Оптимальное значение (F): {optimal_value}\n\nОптимальное решение:\n"
            for var in sorted(variable_values.keys()):
                result_str += f"{var} = {variable_values[var]}\n"
            result_str += f"\nВремя вычисления: {elapsed_time:.10f} секунд"

            QMessageBox.information(self, "Результат", result_str)

            self.save_text_mode_solution(task_info_str, result_str, is_max)
        elif status == "no_solution":
            QMessageBox.information(self, "Результат", "Нет решения для данной задачи.")
        elif status == "iteration_limit":
            QMessageBox.information(self, "Результат", "Достигнут предел итераций без нахождения оптимума.")

    def save_text_mode_solution(self, task_info_str, solution_str, is_max):
        """
        Prompt user to select format (txt or html) and file path, then save using save_answer.py methods.
        """
        # Show dialog to choose format
        dialog = QDialog(self)
        dialog.setWindowTitle("Сохранить ответ")
        v_layout = QVBoxLayout(dialog)

        info_label = QLabel("Выберите формат для сохранения ответа:")
        v_layout.addWidget(info_label)

        rb_txt = QRadioButton("Текстовый файл (.txt)")
        rb_html = QRadioButton("HTML файл (.html)")
        rb_txt.setChecked(True)

        v_layout.addWidget(rb_txt)
        v_layout.addWidget(rb_html)

        h_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        h_layout.addWidget(save_button)
        h_layout.addWidget(cancel_button)
        v_layout.addLayout(h_layout)

        def do_save():
            dialog.accept()
            if rb_txt.isChecked():
                ext = "txt"
                filter_str = "Text Files (*.txt);;All Files (*)"
            else:
                ext = "html"
                filter_str = "HTML Files (*.html);;All Files (*)"

            rows = 0
            cols = 0
            first_line = task_info_str.split('\n', 1)[0].strip()
            parts = first_line.split()
            if len(parts) == 2:
                try:
                    rows = int(parts[1])
                    cols = int(parts[0])
                except:
                    pass

            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = generate_default_filename(cols, rows, is_max, ext)

            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить ответ",
                QDir.homePath() + "/" + default_filename,
                filter_str
            )
            if not filepath:
                return

            if rb_txt.isChecked():
                save_as_text(rows, cols, is_max, task_info_str, "", "", solution_str, filepath)
            else:
                save_as_html(rows, cols, is_max, task_info_str, "", "", solution_str, filepath)

            QMessageBox.information(self, "Успех", f"Ответ сохранён в файл:\n{filepath}")

        save_button.clicked.connect(do_save)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    def generate_random_task(self):
        # Generate random coefficients for goal function and constraints
        num_vars = self.num_vars_spin.value()
        num_constraints = self.num_constraints_spin.value()

        for field in self.goal_inputs:
            field.setText(self.random_coef())

        for i in range(num_constraints):
            layout = self.constraints_layout.itemAt(i).layout()
            if layout is None:
                continue

            widgets = [layout.itemAt(j).widget() for j in range(layout.count()) if layout.itemAt(j).widget()]
            qlineedits = [w for w in widgets if isinstance(w, QLineEdit)]
            qcomboboxes = [w for w in widgets if isinstance(w, QComboBox)]

            for j in range(num_vars):
                qlineedits[j].setText(self.random_coef())

            qcomboboxes[0].setCurrentText(random.choice(["≤", "≥", "="]))

            qlineedits[-1].setText(self.random_coef())

    def random_coef(self):
        # Decide on integer or decimal:
        # 80% int, 20% decimal
        if random.random() < 0.8:
            val = random.randint(-100, 100)
            return str(val)
        else:
            val = random.randint(-100, 100)
            decimal_part = random.choice([".5", ".25"])
            return f"{val}{decimal_part}"


def parse_input_number(text):
    text = text.strip()
    if not text:
        return Fraction(0)

    # Replace comma with dot for decimals
    text = text.replace(',', '.')

    if '/' in text:
        parts = text.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid fraction format: {text}")

        num_str, den_str = parts

        if '.' in num_str or '.' in den_str:
            raise ValueError("Fractions must be integers only (e.g. '3/2', not '3.5/2').")

        try:
            numerator = int(num_str)
            denominator = int(den_str)
        except ValueError:
            raise ValueError(f"Invalid integer in fraction: {text}")

        if denominator == 0:
            raise ValueError("Division by zero in fraction")

        return Fraction(numerator, denominator)
    else:
        if '.' in text:
            # Decimal number, convert to fraction by counting decimals
            # e.g. 2.1 => integral:2, decimal:1 digit -> 2.1 = 21/10
            # e.g. -3.25 => -3 and 25 -> numerator = (-3)*100 + 25 = -300+25 = -275/100
            sign = 1
            if text.startswith('-'):
                sign = -1
                text = text[1:]

            integral_str, decimal_str = text.split('.')
            if not integral_str:
                integral_str = '0'
            try:
                integral_part = int(integral_str)
            except ValueError:
                raise ValueError(f"Invalid integral part: {integral_str}")

            if not decimal_str.isdigit():
                raise ValueError(f"Invalid decimal part: {decimal_str}")

            decimal_length = len(decimal_str)
            denominator = 10**decimal_length
            numerator = integral_part * denominator + int(decimal_str)
            numerator *= sign

            return Fraction(numerator, denominator)
        else:
            # Pure integer
            try:
                val = int(text)  # If user typed something like '2' or '-3'
                return Fraction(val)
            except ValueError:
                raise ValueError(f"Invalid integer: {text}")


def format_task_number(num):
    if num.denominator == 1:
        return str(num.numerator)
    else:
        return f"{num.numerator}/{num.denominator}"


if __name__ == "__main__":
    APP_PATH = ""
    if getattr(sys, "frozen", False):
        APP_PATH = sys._MEIPASS
    elif __file__:
        APP_PATH = path.dirname(__file__)
    else:
        pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(path.join(APP_PATH, "icons/solution.ico")))
    window = SimplexCalculator()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
