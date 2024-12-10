# solution_window.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from fractions import Fraction

class SimplexSolutionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simplex Method Solution Steps")
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
        self.prev_button = QPushButton("Previous Steps")
        self.next_button = QPushButton("Next Steps")
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

        self.watermark_label = QLabel()
        self.watermark_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.watermark_label.setTextFormat(Qt.TextFormat.RichText)
        self.watermark_label.setOpenExternalLinks(True)
        self.watermark_label.setText(
            ' <span style="color: rgba(128, 128, 128, 50%); font-size: 7pt;">'
            ' <a href="https://github.com/undefinedev/simplex_calculator" style="color: rgba(128, 128, 128, 50%); text-decoration: none;">undefinedev</a> © 2024'
            '</span>'
        )
        self.layout.addWidget(self.watermark_label)

        self.steps = []
        self.current_step_index = 0  # Start at 0 to display steps 0 and 1

        # Initialize variable lists
        self.basic_vars = []      # List of basic variable names (rows)
        self.non_basic_vars = []  # List of non-basic variable names (columns)
        self.is_maximization = False  # Flag to indicate if the original problem was maximization

    def add_step(self, tableau_df, basic_vars, non_basic_vars, pivot_row_index=None, pivot_col_index=None, is_maximization=False):
        """
        Add a new step to the steps list.
        """
        if tableau_df is None:
            return  # Error already displayed

        # Save the tableau, variable names, and pivot indices for this step
        self.steps.append({
            'tableau_df': tableau_df.copy(),
            'basic_vars': basic_vars.copy(),
            'non_basic_vars': non_basic_vars.copy(),
            'pivot_row_index': pivot_row_index,
            'pivot_col_index': pivot_col_index
        })

        # Assign basic_vars and non_basic_vars to instance variables
        self.basic_vars = basic_vars.copy()
        self.non_basic_vars = non_basic_vars.copy()

        # Store the is_maximization flag
        if len(self.steps) == 1:
            self.is_maximization = is_maximization

        # Enable or disable navigation buttons
        self.update_navigation_buttons()

        # If this is the first step, start the simplex method
        if len(self.steps) == 1:
            # Start the simplex method
            self.perform_simplex_method(tableau_df)

        # Display the current steps
        self.display_current_steps()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_step_index > 0)
        self.next_button.setEnabled(self.current_step_index + 1 < len(self.steps) - 1)

    def display_current_steps(self):
        """
        Display the current pair of steps in the QTableWidgets.
        """
        # Display left tableau (current step)
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
            self.left_label.setText(f"Step {self.current_step_index + 1}")
        else:
            self.left_table.clear()
            self.left_label.setText("")

        # Display right tableau (next step)
        next_index = self.current_step_index + 1
        if 0 <= next_index < len(self.steps):
            step_data = self.steps[next_index]
            self.display_tableau(
                self.right_table,
                step_data['tableau_df'],
                step_data['basic_vars'],
                step_data['non_basic_vars']
            )
            self.right_label.setText(f"Step {next_index + 1}")
        else:
            self.right_table.clear()
            self.right_label.setText("")

        # Update navigation buttons
        self.update_navigation_buttons()

    def display_tableau(self, table_widget, tableau_df, basic_vars, non_basic_vars, pivot_row_index=None, pivot_col_index=None):
        """
        Display the given tableau DataFrame in the provided QTableWidget.
        """
        rows, cols = tableau_df.shape
        table_widget.setRowCount(rows)
        table_widget.setColumnCount(cols)

        # Set headers
        col_labels = ['Si'] + non_basic_vars
        row_labels = basic_vars + ['F']

        table_widget.setHorizontalHeaderLabels(col_labels)
        table_widget.setVerticalHeaderLabels(row_labels)

        # Populate the table
        for i in range(rows):
            for j in range(cols):
                value = tableau_df.iloc[i, j]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table_widget.setItem(i, j, item)

        # Adjust column widths
        table_widget.resizeColumnsToContents()

        # Clear previous highlights
        self.clear_highlights(table_widget)

        # Highlight pivot element if provided
        if pivot_row_index is not None and pivot_col_index is not None:
            pivot_item = table_widget.item(pivot_row_index, pivot_col_index)
            if pivot_item:
                pivot_item.setBackground(QColor(255, 255, 0))  # Yellow color

    def clear_highlights(self, table_widget):
        """
        Clear all cell highlights in the tableau.
        """
        for i in range(table_widget.rowCount()):
            for j in range(table_widget.columnCount()):
                item = table_widget.item(i, j)
                if item:
                    item.setBackground(QColor(255, 255, 255))  # White color

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
        max_iterations = 100  # Prevent infinite loops

        # Convert all data in df to Fraction
        try:
            for col in df.columns:
                df[col] = df[col].apply(lambda x: Fraction(str(x)))
        except ValueError as e:
            QMessageBox.warning(
                self,
                "Value Error",
                f"Invalid value in the initial tableau: {e}"
            )
            return

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

                        # Before performing the pivot operation, save the current tableau with the pivot element highlighted
                        self.steps[-1]['pivot_row_index'] = pivot_row_index
                        self.steps[-1]['pivot_col_index'] = pivot_col_index
                        # Perform pivot operation
                        df = self.pivot_operation(df, pivot_row_index, pivot_col_index)

                        # After pivot operation, save the new tableau without highlighting pivot element
                        self.add_step(df.copy(), self.basic_vars.copy(), self.non_basic_vars.copy())

                        continue
                    else:
                        # No solution
                        QMessageBox.warning(
                            self,
                            "No Solution",
                            "No solution exists for this problem."
                        )
                        return
                else:
                    # Rule 2: Check if optimal solution is found
                    F_row_index = len(df.index) - 1
                    F_row = df.iloc[F_row_index, 1:]  # Exclude 'Si'
                    positive_F_entries = [j+1 for j, val in enumerate(F_row) if val > 0]
                    if not positive_F_entries:
                        # Optimal solution found
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
            "Iteration Limit Reached",
            "The maximum number of iterations was reached without finding an optimal solution."
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

        # Store original values before updates
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
            # Extract the optimal value
            F_row_index = len(df.index) - 1
            optimal_value = df.iloc[F_row_index, 0]  # Si column at index 0

            # Adjust optimal value if the original problem was maximization
            if self.is_maximization:
                optimal_value *= -1

            # Extract variable values
            variable_values = {}

            # Non-basic variables (values are zero)
            for var in self.non_basic_vars:
                variable_values[var] = Fraction(0)

            # Basic variables (values from Si column)
            for i, var in enumerate(self.basic_vars):
                value = df.iloc[i, 0]  # Si column at index 0
                variable_values[var] = value

            # Build the solution string
            solution_str = f"Оптимальное значение (F): {optimal_value}\n\n"
            solution_str += "Оптимальное решение:\n"
            for var in sorted(variable_values.keys()):
                solution_str += f"{var} = {variable_values[var]}\n"

            # Display the solution under the final matrix in solution window
            self.solution_label.setText(solution_str)

            # Update navigation buttons
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
