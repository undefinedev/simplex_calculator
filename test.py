from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QGridLayout, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy, QTextEdit
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt
import sys


class SimplexSolutionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simplex Method Solution Steps")
        self.resize(600, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Add navigation buttons for iterations
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous Step")
        self.next_button = QPushButton("Next Step")
        self.prev_button.setEnabled(False)  # Initially disabled
        self.next_button.setEnabled(False)  # Initially disabled
        self.prev_button.clicked.connect(self.prev_step)
        self.next_button.clicked.connect(self.next_step)

        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.navigation_layout)

        self.steps = []
        self.current_step_index = -1

        self.solution_text = QTextEdit()
        self.solution_text.setReadOnly(True)
        self.layout.addWidget(self.solution_text)

    def add_step(self, step_text):
        self.steps.append(step_text)
        if len(self.steps) == 1:
            # If this is the first step, display it
            self.current_step_index = 0
            self.solution_text.setPlainText(self.steps[0])
            self.next_button.setEnabled(True)
        else:
            self.solution_text.append("" + step_text)
        self.solution_text.append(step_text)


    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.solution_text.setPlainText(self.steps[self.current_step_index])
            self.next_button.setEnabled(True)
        if self.current_step_index == 0:
            self.prev_button.setEnabled(False)

    def next_step(self):
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.solution_text.setPlainText(self.steps[self.current_step_index])
            self.prev_button.setEnabled(True)
        if self.current_step_index == len(self.steps) - 1:
            self.next_button.setEnabled(False)


class SimplexCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simplex Method Calculator")
        self.initUI()

    def initUI(self):
        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)

        # Top Section: Number of Variables and Constraints
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)  # Reduce spacing between elements
        top_layout.setAlignment(Qt.AlignLeft)  # Align the top section to the left
        label_vars = QLabel("Количество переменных:")
        label_vars.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_vars)

        # Create buttons for increasing/decreasing number of variables
        self.num_vars_minus_button = QPushButton("-")
        self.num_vars_minus_button.setFixedSize(25, 25)
        self.num_vars_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, -1))
        top_layout.addWidget(self.num_vars_minus_button)

        self.num_vars_spin = QSpinBox()
        self.num_vars_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.num_vars_spin.setMinimum(1)
        self.num_vars_spin.setMaximum(10)
        self.num_vars_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_vars_spin.setFixedWidth(70)
        self.num_vars_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_vars_spin)

        self.num_vars_plus_button = QPushButton("+")
        self.num_vars_plus_button.setFixedSize(25, 25)
        self.num_vars_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_vars_spin, 1))
        top_layout.addWidget(self.num_vars_plus_button)

        label_constraints = QLabel("Количество ограничений:")
        label_constraints.setStyleSheet("font-size: 11.5pt;")
        top_layout.addWidget(label_constraints)

        # Create buttons for increasing/decreasing number of constraints
        self.num_constraints_minus_button = QPushButton("-")
        self.num_constraints_minus_button.setFixedSize(25, 25)
        self.num_constraints_minus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, -1))
        top_layout.addWidget(self.num_constraints_minus_button)

        self.num_constraints_spin = QSpinBox()
        self.num_constraints_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.num_constraints_spin.setMinimum(1)
        self.num_constraints_spin.setMaximum(10)
        self.num_constraints_spin.setStyleSheet("font-size: 12.5pt;")
        self.num_constraints_spin.setFixedWidth(70)
        self.num_constraints_spin.valueChanged.connect(self.update_fields)
        top_layout.addWidget(self.num_constraints_spin)

        self.num_constraints_plus_button = QPushButton("+")
        self.num_constraints_plus_button.setFixedSize(25, 25)
        self.num_constraints_plus_button.clicked.connect(lambda: self.change_spin_value(self.num_constraints_spin, 1))
        top_layout.addWidget(self.num_constraints_plus_button)

        self.layout.addLayout(top_layout)

        # Goal Function Section
        goal_container_layout = QHBoxLayout()
        goal_container_layout.setAlignment(Qt.AlignLeft)
        goal_layout = QHBoxLayout()
        goal_layout.setSpacing(10)
        goal_layout.setAlignment(Qt.AlignCenter)  # Align goal function section to the center
        goal_label = QLabel("Целевая функция:")
        goal_label.setStyleSheet("font-size: 11.5pt;")
        goal_layout.addWidget(goal_label)

        self.goal_layout = QHBoxLayout()
        self.goal_layout.setSpacing(5)
        self.goal_layout.setAlignment(Qt.AlignLeft)
        self.goal_inputs = []

        goal_layout.addLayout(self.goal_layout)
        goal_layout.addStretch(1)

        # Arrow and type (min/max)
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 12pt;")
        arrow_label.setAlignment(Qt.AlignLeft)
        goal_layout.addWidget(arrow_label)

        self.goal_type = QComboBox()
        self.goal_type.addItems(["min", "max"])
        self.goal_type.setFixedWidth(70)
        goal_layout.addWidget(self.goal_type)

        goal_container_layout.addLayout(goal_layout)
        goal_container_layout.addStretch(1)
        self.layout.addLayout(goal_container_layout)

        # Constraints Section
        self.constraints_layout = QVBoxLayout()
        self.constraints_layout.setSpacing(5)  # Reduce spacing between constraints
        self.constraints_layout.setAlignment(Qt.AlignTop)  # Align constraints layout to the top
        self.layout.addLayout(self.constraints_layout)

        # Solve Button
        self.solve_button = QPushButton("Решить")
        self.solve_button.setFixedWidth(100)
        self.solve_button.clicked.connect(self.solve)
        self.layout.addWidget(self.solve_button, alignment=Qt.AlignCenter)

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
                plus_label.setAlignment(Qt.AlignCenter)
                self.goal_layout.addWidget(plus_label)

            input_field = QLineEdit()
            input_field.setValidator(QDoubleValidator(-9999, 9999, 5))
            input_field.setPlaceholderText("0")  # Default placeholder
            input_field.setStyleSheet("font-size: 12pt;")
            input_field.setFixedWidth(35)  # Smaller box size
            self.goal_inputs.append(input_field)
            self.goal_layout.addWidget(input_field)

            label = QLabel(f"x<sub>{i + 1}</sub>", self)
            label.setStyleSheet("font-size: 12pt;")
            label.setAlignment(Qt.AlignCenter)
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
        for i in range(num_constraints):
            constraint_centered_layout = QHBoxLayout()
            constraint_centered_layout.setAlignment(Qt.AlignCenter)  # Align constraints to the center
            constraint_centered_layout.addStretch(1)

            constraint_inputs = []
            for j in range(num_vars):
                if j > 0:  # Add `+` only after the first variable
                    plus_label = QLabel("+")
                    plus_label.setAlignment(Qt.AlignCenter)
                    constraint_centered_layout.addWidget(plus_label)

                input_field = QLineEdit()
                input_field.setValidator(QDoubleValidator(-9999, 9999, 5))
                input_field.setPlaceholderText("0")  # Default placeholder
                input_field.setFixedWidth(35)  # Smaller box size
                constraint_inputs.append(input_field)
                constraint_centered_layout.addWidget(input_field)

                label = QLabel(f"x<sub>{j + 1}</sub>", self)
                label.setStyleSheet("font-size: 12pt;")
                label.setAlignment(Qt.AlignCenter)
                constraint_centered_layout.addWidget(label)

            # Add dropdown for relation
            relation = QComboBox()
            relation.addItems(["≤", "≥", "="])
            relation.setFixedWidth(40)
            constraint_centered_layout.addWidget(relation)

            # Add RHS input
            rhs = QLineEdit()
            rhs.setValidator(QDoubleValidator(-9999, 9999, 5))
            rhs.setPlaceholderText("0")  # Default placeholder
            rhs.setStyleSheet("font-size: 12pt;")
            rhs.setFixedWidth(35)
            constraint_centered_layout.addWidget(rhs)

            constraint_centered_layout.addStretch(1)
            self.constraints_layout.addLayout(constraint_centered_layout)

    def solve(self):
        # Placeholder for the solving logic
        self.solution_window = SimplexSolutionWindow()
        self.solution_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimplexCalculator()
    window.resize(800, 600)  # Adjusted initial window size
    window.show()
    sys.exit(app.exec_())
