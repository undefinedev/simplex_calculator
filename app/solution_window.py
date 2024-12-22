# solution_window.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QFrame, QAbstractItemView, QDialog, QRadioButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from fractions import Fraction
import time


class SimplexSolutionWindow(QWidget):
    def __init__(self, dark_theme, task_info, original_constraints=None, num_vars=0):
        super().__init__()
        self.setWindowTitle("Simplex Method Solution Steps")
        self.is_dark_theme = dark_theme
        self.task_info = task_info
        self.original_constraints = original_constraints if original_constraints else []
        self.num_vars = num_vars
        self.calculation_start_time = None
        self.calculation_end_time = None
        self.elapsed_time = None
        self.resize(1000, 600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Labels for the tableaus
        self.tableau_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        self.left_label = QLabel("Current Step")
        self.right_label = QLabel("Next Step")
        self.left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(self.left_label)
        self.right_layout.addWidget(self.right_label)

        # Initialize QTableWidgets
        self.left_table = QTableWidget()
        self.right_table = QTableWidget()
        self.left_layout.addWidget(self.left_table)
        self.right_layout.addWidget(self.right_table)

        # Disable editing
        self.left_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.right_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Add an arrow between the tables
        self.arrow_label = QLabel("→")
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arrow_label.setStyleSheet("font-size: 24pt;")

        # Combine layouts
        self.tableau_layout.addLayout(self.left_layout)
        self.tableau_layout.addWidget(self.arrow_label)
        self.tableau_layout.addLayout(self.right_layout)
        self.layout.addLayout(self.tableau_layout)

        # Add navigation buttons
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущий шаг")
        self.next_button = QPushButton("Следующий шаг")
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.prev_button.clicked.connect(self.prev_steps)
        self.next_button.clicked.connect(self.next_steps)

        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.navigation_layout)

        # Solution label to display the final answer
        self.solution_label = QLabel()
        self.solution_label.setStyleSheet("font-size: 12pt;")
        self.layout.addWidget(self.solution_label)

        self.save_button = QPushButton("Сохранить ответ")
        self.save_button.setFixedWidth(110)
        self.save_button.clicked.connect(self.open_save_dialog)
        self.layout.addWidget(self.save_button)

        self.watermark_label = QLabel()
        self.watermark_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.watermark_label.setTextFormat(Qt.TextFormat.RichText)
        self.watermark_label.setOpenExternalLinks(True)
        self.watermark_label.setText(
            ' <span style="color: rgba(128, 128, 128, 50%); font-size: 7pt;">'
            ' <a href="https://github.com/undefinedev/simplex_calculator" style="color: rgba(128, 128, 128, 50%);'
            ' text-decoration: none;">undefinedev © 2024</a>'
            '</span>'
        )
        self.layout.addWidget(self.watermark_label)

        self.steps = []
        self.current_step_index = 0

        # Initialize variable lists
        self.basic_vars = []
        self.non_basic_vars = []
        self.is_maximization = False

    def add_step(self, tableau_df, basic_vars, non_basic_vars, pivot_row_index=None, pivot_col_index=None,
                 is_maximization=False):
        """
        Add a new step to the steps list.
        """
        if tableau_df is None:
            return

        self.steps.append({
            'tableau_df': tableau_df.copy(),
            'basic_vars': basic_vars.copy(),
            'non_basic_vars': non_basic_vars.copy(),
            'pivot_row_index': pivot_row_index,
            'pivot_col_index': pivot_col_index
        })

        self.basic_vars = basic_vars.copy()
        self.non_basic_vars = non_basic_vars.copy()

        if len(self.steps) == 1:
            self.is_maximization = is_maximization

        self.update_navigation_buttons()

        check = ""
        if len(self.steps) == 1:
            check = self.perform_simplex_method(tableau_df)

        if check is not None and check == "no_solution":
            self.solution_label.setText("Нет решения (возврат алгоритма преобразования матриц).")

        self.display_current_steps()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_step_index > 0)
        self.next_button.setEnabled(self.current_step_index + 1 < len(self.steps) - 1)

    def display_current_steps(self):
        """
        Display the current pair of steps in the QTableWidgets.
        """
        if 0 <= self.current_step_index < len(self.steps):
            step_data = self.steps[self.current_step_index]
            self.display_tableau(
                self.left_table,
                step_data['tableau_df'],
                step_data['basic_vars'],
                step_data['non_basic_vars'],
                step_data.get('pivot_row_index'),
                step_data.get('pivot_col_index')
            )
            self.left_label.setText(f"Шаг {self.current_step_index + 1}")
        else:
            self.left_table.clear()
            self.left_label.setText("")

        next_index = self.current_step_index + 1
        if 0 <= next_index < len(self.steps):
            step_data = self.steps[next_index]
            self.display_tableau(
                self.right_table,
                step_data['tableau_df'],
                step_data['basic_vars'],
                step_data['non_basic_vars']
            )
            self.right_label.setText(f"Шаг {next_index + 1}")
        else:
            self.right_table.clear()
            self.right_label.setText("")

        self.update_navigation_buttons()

    def display_tableau(self, table_widget, tableau_df, basic_vars, non_basic_vars, pivot_row_index=None,
                        pivot_col_index=None):
        """
        Display the given tableau DataFrame in the provided QTableWidget.
        """
        rows, cols = tableau_df.shape
        table_widget.setRowCount(rows)
        table_widget.setColumnCount(cols)

        col_labels = ['Si'] + non_basic_vars
        row_labels = basic_vars + ['F']

        table_widget.setHorizontalHeaderLabels(col_labels)
        table_widget.setVerticalHeaderLabels(row_labels)

        for i in range(rows):
            for j in range(cols):
                value = tableau_df.iloc[i, j]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table_widget.setItem(i, j, item)

        table_widget.resizeColumnsToContents()

        self.clear_highlights(table_widget)

        if pivot_row_index is not None and pivot_col_index is not None:
            pivot_item = table_widget.item(pivot_row_index, pivot_col_index)
            if pivot_item:
                if self.is_dark_theme:
                    pivot_item.setBackground(QColor("blue"))
                else:
                    pivot_item.setBackground(QColor("#37AEFE"))

    def clear_highlights(self, table_widget):
        """
        Clear all cell highlights in the tableau.
        """
        for i in range(table_widget.rowCount()):
            for j in range(table_widget.columnCount()):
                item = table_widget.item(i, j)
                if item:
                    if self.is_dark_theme:
                        item.setBackground(QColor("#19232D"))
                    else:
                        item.setBackground(QColor("#FAFAFA"))

    def prev_steps(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.display_current_steps()
        self.update_navigation_buttons()

    def next_steps(self):
        if self.current_step_index + 1 < len(self.steps) - 1:
            self.current_step_index += 1
            self.display_current_steps()
        self.update_navigation_buttons()

    def perform_simplex_method(self, df):
        """
        Perform the simplex method iterations according to the corrected algorithm.
        """
        iteration = 0
        max_iterations = 300  # Prevent infinite loops

        try:
            for col in df.columns:
                df[col] = df[col].apply(lambda x: Fraction(x) if not isinstance(x, Fraction) else x)
        except ValueError as e:
            QMessageBox.warning(
                self,
                "Value Error",
                f"Invalid value in the initial tableau: {e}"
            )
            return

        self.calculation_start_time = time.perf_counter()
        while iteration < max_iterations:
            iteration += 1

            try:
                # Step 1: Check Si column from basic variable rows (excluding 'F' row)
                basic_rows = list(range(len(self.basic_vars)))  # Row indices
                negative_Si_rows = [i for i in basic_rows if df.iloc[i, 0] < 0]  # Si column is at index 0

                if negative_Si_rows:
                    # Rule 3: Take first negative from Si column from basic variable rows
                    pivot_row_index = negative_Si_rows[0]
                    # Look for first negative in this row (excluding 'Si' at index 0)
                    row_series = df.iloc[pivot_row_index, 1:]  # Exclude 'Si'
                    negative_cols = [j+1 for j, val in enumerate(row_series) if val < 0]  # Adjust for 'Si' at index 0
                    if negative_cols:
                        # First negative in this row is pivot element
                        pivot_col_index = negative_cols[0]

                        # Before performing the pivot operation, save current tableau with the pivot element highlighted
                        self.steps[-1]['pivot_row_index'] = pivot_row_index
                        self.steps[-1]['pivot_col_index'] = pivot_col_index
                        # Perform pivot operation
                        df = self.pivot_operation(df, pivot_row_index, pivot_col_index)

                        # After pivot operation, save the new tableau without highlighting pivot element
                        self.add_step(df.copy(), self.basic_vars.copy(), self.non_basic_vars.copy())

                        continue
                    else:
                        QMessageBox.warning(
                            self,
                            "Нет решения",
                            "Нет решения для этого задания."
                        )
                        return "no_solution"
                else:
                    # Rule 2: Check if optimal solution is found
                    F_row_index = len(df.index) - 1
                    F_row = df.iloc[F_row_index, 1:]  # Exclude 'Si'
                    positive_F_entries = [j+1 for j, val in enumerate(F_row) if val > 0]
                    if not positive_F_entries:
                        # Optimal solution found
                        self.calculation_end_time = time.perf_counter()
                        self.elapsed_time = self.calculation_end_time - self.calculation_start_time
                        self.display_optimal_solution(df)
                        return
                    else:
                        # Rule 4: Take first positive from F row except Si
                        for pivot_col_index in positive_F_entries:
                            # Check if column above selected element in basic variable rows has positive element
                            positive_rows = [i for i in basic_rows if df.iloc[i, pivot_col_index] > 0]
                            if not positive_rows:
                                # No positive elements in this column, continue to next positive element in F row
                                continue
                            else:
                                # Calculate ratios Si / column value for positive elements
                                ratios = []
                                for i in positive_rows:
                                    value = df.iloc[i, pivot_col_index]
                                    if value != 0:
                                        ratio = df.iloc[i, 0] / value  # Si column is at index 0
                                        if ratio >= 0:
                                            ratios.append((ratio, i))
                                if ratios:
                                    # Select pivot row with smallest positive ratio
                                    pivot_row_index = min(ratios, key=lambda x: x[0])[1]

                                    # Before performing the pivot operation, save the current tableau with the pivot element highlighted
                                    self.steps[-1]['pivot_row_index'] = pivot_row_index
                                    self.steps[-1]['pivot_col_index'] = pivot_col_index
                                    # Perform pivot operation
                                    df = self.pivot_operation(df, pivot_row_index, pivot_col_index)

                                    # After pivot operation, save the new tableau without highlighting pivot element
                                    self.add_step(df.copy(), self.basic_vars.copy(), self.non_basic_vars.copy())

                                    break
                        else:
                            # Optimal solution found (no positive elements in F row under non-basic variables)
                            self.calculation_end_time = time.perf_counter()
                            self.elapsed_time = self.calculation_end_time - self.calculation_start_time
                            self.display_optimal_solution(df)
                            return
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"An error occurred during the simplex method: {e}"
                )
                return

        QMessageBox.warning(
            self,
            "Лимит итераций",
            "Максимальное чисто итераций алгоритма было достигнуто без нахождения оптимального решения."
        )
        return

    def pivot_operation(self, df, pivot_row_index, pivot_col_index):
        """
        Perform the pivot operation according to the corrected algorithm.
        """
        df = df.copy()
        y = df.iloc[pivot_row_index, pivot_col_index]  # Pivot element

        if y == 0:
            QMessageBox.warning(
                self,
                "Pivot Error",
                "Pivot element is zero. Cannot perform pivot operation."
            )
            raise Exception("Pivot element is zero. Cannot perform pivot operation.")

        original_df = df.copy()

        try:
            # Step 1: Compute new values for all elements not in pivot row or pivot column
            for i in range(len(df)):
                if i != pivot_row_index:
                    for j in range(len(df.columns)):
                        if j != pivot_col_index:
                            t1 = original_df.iloc[i, j]
                            y1 = original_df.iloc[i, pivot_col_index]
                            y2 = original_df.iloc[pivot_row_index, j]
                            t2 = t1 - (y1 * y2) / y
                            df.iloc[i, j] = t2

            # Step 2: Update pivot row (excluding pivot element)
            for j in range(len(df.columns)):
                if j != pivot_col_index:
                    t1 = original_df.iloc[pivot_row_index, j]
                    df.iloc[pivot_row_index, j] = t1 / y

            # Step 3: Update pivot column (excluding pivot element)
            for i in range(len(df)):
                if i != pivot_row_index:
                    t1 = original_df.iloc[i, pivot_col_index]
                    df.iloc[i, pivot_col_index] = t1 / -y

            # Step 4: Update pivot element
            df.iloc[pivot_row_index, pivot_col_index] = Fraction(1, y)

            # Swap basic and non-basic variable names
            leaving_var = self.basic_vars[pivot_row_index]
            entering_var = self.non_basic_vars[pivot_col_index - 1]  # Adjust for 'Si' at index 0

            # Update basic_vars and non_basic_vars
            self.basic_vars[pivot_row_index] = entering_var
            self.non_basic_vars[pivot_col_index - 1] = leaving_var

        except Exception as e:
            QMessageBox.warning(
                self,
                "Pivot Operation Error",
                f"An error occurred during the pivot operation: {e}"
            )
            raise

        return df

    def display_optimal_solution(self, df):
        """
        Display the optimal solution under the final tableau.
        """
        try:
            F_row_index = len(df.index) - 1
            optimal_value = df.iloc[F_row_index, 0]

            if self.is_maximization:
                optimal_value *= -1

            variable_values = {}

            for var in self.non_basic_vars:
                variable_values[var] = Fraction(0)

            for i, var in enumerate(self.basic_vars):
                value = df.iloc[i, 0]
                variable_values[var] = value

            if not self.final_feasibility_check(variable_values):
                self.solution_label.setText("Нет решения (итоговые переменные не удовлетворяют ограничениям).")
                return

            solution_str = f"Оптимальное значение (F): {optimal_value}\n\n"
            solution_str += "Оптимальное решение:\n"
            for var in sorted(variable_values.keys()):
                solution_str += f"{var} = {variable_values[var]}\n"

            if hasattr(self, 'elapsed_time'):
                solution_str += f"\nВремя вычисления: {self.elapsed_time:.10f} секунд"

            self.solution_label.setText(solution_str)

            self.update_navigation_buttons()

            # Display the final steps
            self.display_current_steps()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Display Error",
                f"An error occurred while displaying the optimal solution: {e}"
            )
            return

    def final_feasibility_check(self, variable_values):
        """
        variable_values: dict { "X1": fraction, "X2": fraction, ... }
        returns True if all constraints are satisfied, otherwise False
        """
        tol = Fraction(0)  # If you want a small tolerance for floats, but here we have Fractions

        for (coeffs, relation, rhs) in self.original_constraints:
            LHS = sum(coeffs[j] * variable_values.get(f"X{j + 1}", Fraction(0)) for j in range(self.num_vars))
            if relation == "≤":
                if LHS > rhs + tol:
                    return False
            elif relation == "≥":
                if LHS < rhs - tol:
                    return False
            elif relation == "=":
                if LHS != rhs:
                    return False
            else:
                # Unexpected relation?
                return False
        return True

    def run_simplex_silently(self, df, basic_vars, non_basic_vars, is_maximization):
        """
    Run the simplex method without GUI updates.
    Returns: (final_df, final_basic_vars, final_non_basic_vars, elapsed_time, status)
    status can be:
       "optimal"        if an optimal solution is found,
       "no_solution"     if no feasible solution exists,
       "iteration_limit" if the maximum number of iterations was reached.
    """
        start_time = time.perf_counter()

        try:
            for col in df.columns:
                df[col] = df[col].apply(lambda x: Fraction(x) if not isinstance(x, Fraction) else x)
        except ValueError as e:
            QMessageBox.warning(
                self,
                "Value Error",
                f"Invalid value in the initial tableau: {e}"
            )
            return df, basic_vars, non_basic_vars, 0, "no_solution"

        iteration = 0
        max_iterations = 1000

        try:
            while iteration < max_iterations:
                iteration += 1
                basic_rows = list(range(len(basic_vars)))
                negative_Si_rows = [i for i in basic_rows if df.iloc[i, 0] < 0]

                if negative_Si_rows:
                    pivot_row_index = negative_Si_rows[0]
                    row_series = df.iloc[pivot_row_index, 1:]
                    negative_cols = [j + 1 for j, val in enumerate(row_series) if val < 0]
                    if negative_cols:
                        pivot_col_index = negative_cols[0]
                        df, basic_vars, non_basic_vars = self.pivot_operation_silent(df, pivot_row_index,
                                                                                     pivot_col_index, basic_vars,
                                                                                     non_basic_vars)
                        continue
                    else:
                        QMessageBox.warning(
                            self,
                            "No Solution",
                            "No solution exists for this problem."
                        )
                        end_time = time.perf_counter()
                        return df, basic_vars, non_basic_vars, (end_time - start_time), "no_solution"
                else:
                    F_row_index = len(df.index) - 1
                    F_row = df.iloc[F_row_index, 1:]
                    positive_F_entries = [j + 1 for j, val in enumerate(F_row) if val > 0]
                    if not positive_F_entries:
                        end_time = time.perf_counter()
                        elapsed_time = end_time - start_time

                        variable_values = {}
                        for i, var in enumerate(basic_vars):
                            variable_values[var] = df.iloc[i, 0]
                        for var in non_basic_vars:
                            variable_values[var] = Fraction(0)

                        if not self.final_feasibility_check(variable_values):
                            return df, basic_vars, non_basic_vars, elapsed_time, "no_solution"

                        return df, basic_vars, non_basic_vars, elapsed_time, "optimal"
                    else:
                        done_pivot = False
                        for pivot_col_index in positive_F_entries:
                            positive_rows = [i for i in basic_rows if df.iloc[i, pivot_col_index] > 0]
                            if not positive_rows:
                                continue
                            ratios = []
                            for i in positive_rows:
                                value = df.iloc[i, pivot_col_index]
                                if value != 0:
                                    ratio = df.iloc[i, 0] / value
                                    if ratio >= 0:
                                        ratios.append((ratio, i))
                            if ratios:
                                pivot_row_index = min(ratios, key=lambda x: x[0])[1]
                                df, basic_vars, non_basic_vars = self.pivot_operation_silent(df, pivot_row_index,
                                                                                             pivot_col_index,
                                                                                             basic_vars, non_basic_vars)
                                done_pivot = True
                                break
                        if not done_pivot:
                            end_time = time.perf_counter()
                            elapsed_time = end_time - start_time

                            variable_values = {}
                            for i, var in enumerate(basic_vars):
                                variable_values[var] = df.iloc[i, 0]
                            for var in non_basic_vars:
                                variable_values[var] = Fraction(0)

                            if not self.final_feasibility_check(variable_values):
                                return df, basic_vars, non_basic_vars, elapsed_time, "no_solution"

                            return df, basic_vars, non_basic_vars, elapsed_time, "optimal"
            QMessageBox.warning(
                self,
                "Iteration Limit Reached",
                "The maximum number of iterations was reached without finding an optimal solution."
            )
            end_time = time.perf_counter()
            return df, basic_vars, non_basic_vars, (end_time - start_time), "iteration_limit"

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"An error occurred during the silent simplex method: {e}"
            )
            end_time = time.perf_counter()
            return df, basic_vars, non_basic_vars, (end_time - start_time), "no_solution"

    def pivot_operation_silent(self, df, pivot_row_index, pivot_col_index, basic_vars, non_basic_vars):
        """
        Perform the pivot operation in silent mode (no GUI updates), with error handling.
        """
        df = df.copy()
        y = df.iloc[pivot_row_index, pivot_col_index]

        if y == 0:
            QMessageBox.warning(
                self,
                "Pivot Error",
                "Pivot element is zero. Cannot perform silent pivot operation."
            )
            raise Exception("Pivot element is zero in silent mode.")

        original_df = df.copy()

        try:
            # Step 1: Compute new values for all elements not in pivot row or column
            for i in range(len(df)):
                if i != pivot_row_index:
                    for j in range(len(df.columns)):
                        if j != pivot_col_index:
                            t1 = original_df.iloc[i, j]
                            y1 = original_df.iloc[i, pivot_col_index]
                            y2 = original_df.iloc[pivot_row_index, j]
                            t2 = t1 - (y1 * y2) / y
                            df.iloc[i, j] = t2

            # Step 2: Update pivot row (excluding pivot element)
            for j in range(len(df.columns)):
                if j != pivot_col_index:
                    t1 = original_df.iloc[pivot_row_index, j]
                    df.iloc[pivot_row_index, j] = t1 / y

            # Step 3: Update pivot column (excluding pivot element)
            for i in range(len(df)):
                if i != pivot_row_index:
                    t1 = original_df.iloc[i, pivot_col_index]
                    df.iloc[i, pivot_col_index] = t1 / -y

            # Step 4: Update pivot element
            df.iloc[pivot_row_index, pivot_col_index] = Fraction(1, y)

            # Swap basic and non-basic variable names
            leaving_var = basic_vars[pivot_row_index]
            entering_var = non_basic_vars[pivot_col_index - 1]
            basic_vars[pivot_row_index] = entering_var
            non_basic_vars[pivot_col_index - 1] = leaving_var

            return df, basic_vars, non_basic_vars

        except Exception as e:
            QMessageBox.warning(
                self,
                "Pivot Operation Error",
                f"An error occurred during the silent pivot operation: {e}"
            )
            raise

    def format_matrix_text(self, df):
        values_str = [[format_number(df.iloc[i, j]) for j in range(df.shape[1])]
                      for i in range(df.shape[0])]
        col_widths = [max(len(row[j]) for row in values_str) for j in range(df.shape[1])]

        header_line = "     " + " ".join(f"{col:>{w}}" for col, w in zip(df.columns, col_widths))
        lines = [header_line]
        for i, idx in enumerate(df.index):
            line = " ".join(f"{values_str[i][j]:>{col_widths[j]}}" for j in range(df.shape[1]))
            line = f"{idx:<3} {line}"
            lines.append(line)
        return "\n".join(lines)

    def format_matrix_html(self, df):
        html = "<table border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse; font-family: sans-serif;'>"
        html += "<tr><th></th>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"
        for idx in df.index:
            html += f"<tr><th>{idx}</th>" + "".join(
                f"<td>{format_number(df.loc[idx, col])}</td>" for col in df.columns) + "</tr>"
        html += "</table>"
        return html

    def open_save_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Сохранить ответ")

        layout = QVBoxLayout(dialog)

        info_label = QLabel("Выберите формат для сохранения ответа:")
        layout.addWidget(info_label)

        rb_txt = QRadioButton("Текстовый файл (.txt)")
        rb_html = QRadioButton("HTML файл (.html)")
        rb_txt.setChecked(True)  # default

        layout.addWidget(rb_txt)
        layout.addWidget(rb_html)

        h_layout = QHBoxLayout()
        choose_file_button = QPushButton("Выбрать файл...")
        h_layout.addWidget(choose_file_button)
        save_button = QPushButton("Сохранить")
        h_layout.addWidget(save_button)
        cancel_button = QPushButton("Отмена")
        h_layout.addWidget(cancel_button)

        layout.addLayout(h_layout)

        def choose_file():
            if rb_txt.isChecked():
                ext = "txt"
                filter_str = "Text Files (*.txt);;All Files (*)"
            else:
                ext = "html"
                filter_str = "HTML Files (*.html);;All Files (*)"

            rows = len(self.basic_vars)
            cols = len(self.non_basic_vars) + 1
            is_max = self.is_maximization
            from save_answer import generate_default_filename
            default_filename = generate_default_filename(rows, cols, is_max, ext)

            from save_answer import save_file_dialog
            chosen_file = save_file_dialog(default_filename, filter_str)
            if chosen_file:
                choose_file_button.setText(chosen_file)
                choose_file_button.setToolTip(chosen_file)

        choose_file_button.clicked.connect(choose_file)

        def do_save():
            chosen_path = choose_file_button.text()
            if chosen_path.startswith("Выбрать файл"):
                QMessageBox.warning(self, "Файл не выбран", "Пожалуйста, выберите файл для сохранения.")
                return

            rows = len(self.basic_vars)
            cols = len(self.non_basic_vars) + 1
            is_max = self.is_maximization
            task_info = self.task_info
            start_step = self.steps[0]
            start_df = start_step['tableau_df']
            start_basic = start_step['basic_vars']
            start_non_basic = start_step['non_basic_vars']
            start_df_renamed = rename_df_headers(start_df, start_basic, start_non_basic)

            end_step = self.steps[-1]
            end_df = end_step['tableau_df']
            end_basic = end_step['basic_vars']
            end_non_basic = end_step['non_basic_vars']
            end_df_renamed = rename_df_headers(end_df, end_basic, end_non_basic)

            start_matrix_text = self.format_matrix_text(start_df_renamed)
            end_matrix_text = self.format_matrix_text(end_df_renamed)
            start_matrix_html = self.format_matrix_html(start_df_renamed)
            end_matrix_html = self.format_matrix_html(end_df_renamed)
            solution_str = self.solution_label.text()

            from save_answer import save_as_text, save_as_html

            if rb_txt.isChecked():
                save_as_text(rows, cols, is_max, task_info, start_matrix_text, end_matrix_text, solution_str,
                             chosen_path)
            else:
                save_as_html(rows, cols, is_max, task_info, start_matrix_html, end_matrix_html, solution_str,
                             chosen_path)

            dialog.accept()

        save_button.clicked.connect(do_save)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()


def format_number(num):
    if hasattr(num, 'denominator'):
        if num.denominator == 1:
            return str(num.numerator)
        else:
            return f"{num.numerator}/{num.denominator}"
    else:
        val = float(num)
        if val.is_integer():
            return str(int(val))
        else:
            return str(val)


def rename_df_headers(df, basic_vars, non_basic_vars):
    df_renamed = df.copy()
    df_renamed.index = basic_vars + ['F']
    df_renamed.columns = ['Si'] + non_basic_vars
    return df_renamed
