# main.py
import os.path as path
import sys
from pandas import DataFrame
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QMessageBox, QAbstractSpinBox
)
from PyQt6.QtGui import QDoubleValidator, QIcon
from PyQt6.QtCore import Qt
from fractions import Fraction

# Import the SimplexSolutionWindow from solution_window.py
from solution_window import SimplexSolutionWindow


class SimplexCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симплекс Метод Калькулятор v1.2")
        self.initUI()

    def initUI(self):
        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Top Section: Number of Variables and Constraints
        top_layout = QHBoxLayout()
        top_layout.setSpacing(1)  # Reduce spacing between elements
        top_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align the top section to the left
        label_vars = QLabel("Количество переменных:")
        label_vars.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_vars)

        # Create buttons for increasing/decreasing number of variables
        self.num_vars_minus_button = QPushButton("-")
        self.num_vars_minus_button.setFixedSize(25, 25)
        self.num_vars_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, -1))
        top_layout.addWidget(self.num_vars_minus_button)

        self.num_vars_spin = QSpinBox()
        self.num_vars_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.num_vars_spin.setMinimum(1)  # Minimum of 1 variable
        self.num_vars_spin.setMaximum(10)
        self.num_vars_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_vars_spin.setFixedWidth(60)
        self.num_vars_spin.setValue(3)  # Default to 3 variables
        self.num_vars_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_vars_spin)

        self.num_vars_plus_button = QPushButton("+")
        self.num_vars_plus_button.setFixedSize(25, 25)
        self.num_vars_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, 1))
        top_layout.addWidget(self.num_vars_plus_button)

        label_constraints = QLabel("    Количество ограничений:")
        label_constraints.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_constraints)

        # Create buttons for increasing/decreasing number of constraints
        self.num_constraints_minus_button = QPushButton("-")
        self.num_constraints_minus_button.setFixedSize(25, 25)
        self.num_constraints_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, -1))
        top_layout.addWidget(self.num_constraints_minus_button)

        self.num_constraints_spin = QSpinBox()
        self.num_constraints_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.num_constraints_spin.setMinimum(1)
        self.num_constraints_spin.setMaximum(10)
        self.num_constraints_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_constraints_spin.setFixedWidth(60)
        self.num_constraints_spin.setValue(3)  # Default to 3 constraints
        self.num_constraints_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_constraints_spin)

        self.num_constraints_plus_button = QPushButton("+")
        self.num_constraints_plus_button.setFixedSize(25, 25)
        self.num_constraints_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, 1))
        top_layout.addWidget(self.num_constraints_plus_button)

        self.layout.addLayout(top_layout)

        # Goal Function Section
        goal_container_layout = QHBoxLayout()
        goal_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        goal_layout = QHBoxLayout()
        goal_layout.setSpacing(10)
        goal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Align goal function section to the center
        goal_label = QLabel("Целевая функция:")
        goal_label.setStyleSheet("font-size: 11.5pt;")
        goal_layout.addWidget(goal_label)

        self.goal_layout = QHBoxLayout()
        self.goal_layout.setSpacing(5)
        self.goal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.goal_inputs = []

        goal_layout.addLayout(self.goal_layout)
        goal_layout.addStretch(1)

        # Arrow and type (min/max)
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 13pt;")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        goal_layout.addWidget(arrow_label)

        self.goal_type = QComboBox()
        self.goal_type.addItems(["min", "max"])
        self.goal_type.setStyleSheet("font-size: 12pt;")
        self.goal_type.setFixedWidth(70)
        self.goal_type.setCurrentText("min")  # Set 'min' as the default selection
        goal_layout.addWidget(self.goal_type)

        goal_container_layout.addLayout(goal_layout)
        goal_container_layout.addStretch(1)
        self.layout.addLayout(goal_container_layout)

        # Constraints Section
        self.constraints_layout = QVBoxLayout()
        self.constraints_layout.setSpacing(5)  # Reduce spacing between constraints
        self.constraints_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align constraints layout to the top
        self.layout.addLayout(self.constraints_layout)

        # Solve Button
        self.solve_button = QPushButton("Решить")
        self.solve_button.setFixedWidth(100)
        self.solve_button.clicked.connect(self.solve)
        self.layout.addWidget(self.solve_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.layout)
        self.update_fields()

    def change_spin_value(self, spin_box, delta):
        current_value = spin_box.value()
        new_value = current_value + delta
        if spin_box.minimum() <= new_value <= spin_box.maximum():
            spin_box.setValue(new_value)

    def update_fields(self):
        # Update Goal Function Fields
        while self.goal_layout.count():
            widget = self.goal_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.goal_inputs.clear()

        num_vars = self.num_vars_spin.value()

        for i in range(num_vars):
            if i > 0:  # Add `+` only after the first variable
                plus_label = QLabel("+")
                plus_label.setStyleSheet("font-size: 12pt;")
                plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.goal_layout.addWidget(plus_label)

            input_field = QLineEdit()
            input_field.setValidator(QDoubleValidator(-9999, 9999, 5))
            input_field.setPlaceholderText("0")  # Default placeholder
            input_field.setStyleSheet("font-size: 12pt;")
            input_field.setFixedWidth(45)  # Smaller box size
            self.goal_inputs.append(input_field)
            self.goal_layout.addWidget(input_field)

            label = QLabel(f"x<sub>{i + 1}</sub>", self)
            label.setStyleSheet("font-size: 14pt;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.goal_layout.addWidget(label)

        # Update Constraint Fields
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
            constraint_centered_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Align constraints to the center
            constraint_centered_layout.addStretch(1)

            for j in range(num_vars):
                if j > 0:  # Add `+` only after the first variable
                    plus_label = QLabel("+")
                    plus_label.setStyleSheet("font-size: 12pt;")
                    plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    constraint_centered_layout.addWidget(plus_label)

                input_field = QLineEdit()
                input_field.setValidator(QDoubleValidator(-9999, 9999, 5))
                input_field.setStyleSheet("font-size: 12pt;")
                input_field.setPlaceholderText("0")  # Default placeholder
                input_field.setFixedWidth(45)  # Smaller box size
                constraint_centered_layout.addWidget(input_field)

                label = QLabel(f"x<sub>{j + 1}</sub>", self)
                label.setStyleSheet("font-size: 14pt;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                constraint_centered_layout.addWidget(label)

            # Add dropdown for relation
            relation = QComboBox()
            relation.addItems(["≤", "≥", "="])
            relation.setStyleSheet("font-size: 13pt;")
            relation.setFixedWidth(40)
            constraint_centered_layout.addWidget(relation)

            # Add RHS input
            rhs = QLineEdit()
            rhs.setValidator(QDoubleValidator(-9999, 9999, 5))
            rhs.setPlaceholderText("0")  # Default placeholder
            rhs.setStyleSheet("font-size: 12.5pt;")
            rhs.setFixedWidth(45)
            constraint_centered_layout.addWidget(rhs)

            constraint_centered_layout.addStretch(1)
            self.constraints_layout.addLayout(constraint_centered_layout)

    def solve(self):
        try:
            # Retrieve goal function coefficients
            goal_values = [float(field.text()) if field.text() else 0.0 for field in self.goal_inputs]
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
                # Handle unexpected cases
                QMessageBox.warning(
                    self,
                    "Input Error",
                    "Пожалуйста, выберите тип целевой функции (min или max)."
                )
                return

            num_vars = self.num_vars_spin.value()
            num_constraints = self.num_constraints_spin.value()

            # Initialize decision variables (e.g., ['X1', 'X2', ..., 'Xn'])
            decision_vars = [f"X{i+1}" for i in range(num_vars)]

            # Read all constraints
            constraints = []
            for i in range(num_constraints):
                layout = self.constraints_layout.itemAt(i).layout()
                if layout is None:
                    continue

                # Collect all widgets in the layout
                widgets = [layout.itemAt(j).widget() for j in range(layout.count())]

                # Extract QLineEdits and QComboBox
                qlineedits = [widget for widget in widgets if isinstance(widget, QLineEdit)]
                qcomboboxes = [widget for widget in widgets if isinstance(widget, QComboBox)]

                # Validate the number of widgets
                expected_qlineedits = num_vars + 1  # Coefficients + RHS
                if len(qlineedits) < expected_qlineedits or len(qcomboboxes) < 1:
                    QMessageBox.warning(
                        self,
                        "Input Error",
                        f"Уравнение {i + 1} имеет неверные поля ввода."
                    )
                    return

                # Extract coefficients for decision variables
                coeffs = []
                for j in range(num_vars):
                    text = qlineedits[j].text()
                    coef = float(text) if text else 0.0
                    coeffs.append(coef)

                # Extract relation
                relation = qcomboboxes[0].currentText()

                # Extract RHS
                rhs_value = float(qlineedits[-1].text()) if qlineedits[-1].text() else 0.0

                constraints.append((coeffs, relation, rhs_value))

            # Assign Basic Variables
            basic_vars = {}  # constraint_index: basic_var
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
                        # Assign the single valid candidate as the basic variable
                        basic_var = valid_candidates[0]
                        basic_vars[idx] = basic_var
                    elif len(valid_candidates) > 1:
                        # If multiple valid candidates, assign the first one and inform the user
                        basic_var = valid_candidates[0]
                        basic_vars[idx] = basic_var
                        QMessageBox.information(
                            self,
                            "Базисная переменная выбрана автоматически",
                            f"Для ограничения {idx + 1} было выбрано {basic_var} как базисная переменная."
                        )
                    else:
                        # No suitable basic variable found, prompt to add a new one
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
                    # Assign a new basic variable (slack or surplus) without adding it to tableau columns
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

            # Compile all decision variables excluding any that are basic variables
            final_decision_vars = [var for var in decision_vars if var not in basic_vars.values()]

            if len(final_decision_vars) < len(decision_vars):
                QMessageBox.information(
                    self,
                    "Исключение базисных переменных",
                    "Некоторые переменные были автоматически исключены из целевой функции, так как они являются базисными переменными."
                )

            # Prepare the tableau data with fractions
            tableau_data = []
            row_names = []

            for idx, (coeffs, relation, rhs) in enumerate(constraints):
                basic_var = basic_vars[idx]
                row_names.append(basic_var)

                # Adjust coefficients based on relation
                adjusted_rhs = rhs
                adjusted_coeffs = coeffs.copy()

                if relation == "≥":
                    # For '≥' constraints, multiply coefficients and RHS by -1 to convert to '≤'
                    adjusted_coeffs = [-c for c in adjusted_coeffs]
                    adjusted_rhs = -rhs

                # Prepare the row: [Si, X1, X2, ..., Xn] excluding basic variables
                row = [str(Fraction(adjusted_rhs))]
                for var in final_decision_vars:
                    var_index = decision_vars.index(var)
                    coef = adjusted_coeffs[var_index] if var_index < len(adjusted_coeffs) else 0.0
                    row.append(str(Fraction(coef)))
                tableau_data.append(row)

            # Append the objective function row
            objective_row = [str(Fraction(0))]  # 0 for Si
            for var in final_decision_vars:
                var_index = decision_vars.index(var)
                # The goal function is already adjusted based on min or max
                coef = adjusted_goal_values[var_index]
                objective_row.append(str(Fraction(coef)))
            row_names.append("F")
            tableau_data.append(objective_row)

            # Define columns: Si + final_decision_vars
            columns = ["Si"] + final_decision_vars

            # Create pandas DataFrame for the tableau
            df = DataFrame(tableau_data, columns=columns, index=row_names)

            copy_basic_vars = row_names[:-1]
            copy_non_basic_vars = columns[1:]
            maximization_flag = True if goal_type_selected == "max" else False

            # Display the initial tableau in the solution window
            self.solution_window = SimplexSolutionWindow()
            self.solution_window.add_step(df, copy_basic_vars, copy_non_basic_vars, is_maximization=maximization_flag)
            self.solution_window.show()

        except ValueError as e:
            # Catch specific ValueError and provide detailed feedback
            QMessageBox.warning(
                self,
                "Input Error",
                f"Пожалуйста, убедитесь, что все поля заполнены корректно и содержат числовые значения.\n\nОшибка: {e}"
            )
            return


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
    window.resize(800, 600)  # Adjusted initial window size
    window.show()
    sys.exit(app.exec())
