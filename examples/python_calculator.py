import tkinter as tk
from tkinter import ttk


class SimpleCalculator:
    """A small four-operation calculator built with Python's Tkinter GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title("StudyBuddy Python Calculator")
        self.root.geometry("340x460")
        self.root.minsize(300, 420)
        self.root.configure(bg="#0b1020")

        self.current = "0"
        self.stored_value = None
        self.operator = None
        self.waiting_for_operand = False

        self.display_var = tk.StringVar(value=self.current)
        display = ttk.Entry(
            root,
            textvariable=self.display_var,
            justify="right",
            state="readonly",
            font=("Consolas", 24),
        )
        display.grid(row=0, column=0, columnspan=4, padx=12, pady=(16, 10), sticky="nsew", ipady=10)

        buttons = [
            ("AC", 1, 0, "clear"), ("DEL", 1, 1, "delete"),
            ("%", 1, 2, "percent"), ("÷", 1, 3, "/"),
            ("7", 2, 0, "7"), ("8", 2, 1, "8"), ("9", 2, 2, "9"), ("×", 2, 3, "*"),
            ("4", 3, 0, "4"), ("5", 3, 1, "5"), ("6", 3, 2, "6"), ("−", 3, 3, "-"),
            ("1", 4, 0, "1"), ("2", 4, 1, "2"), ("3", 4, 2, "3"), ("+", 4, 3, "+"),
            ("0", 5, 0, "0"), (".", 5, 2, "decimal"), ("=", 5, 3, "equals"),
        ]

        for label, row, column, action in buttons:
            color = "#302950" if action in {"+", "-", "*", "/", "equals"} else "#1c2941"
            foreground = "#d5c1ff" if action in {"+", "-", "*", "/"} else "#eff4ff"
            if action == "equals":
                color, foreground = "#b9c9ff", "#101629"
            elif action in {"clear", "delete", "percent"}:
                color, foreground = "#202e49", "#c4d2f2"

            button = tk.Button(
                root,
                text=label,
                command=lambda selected=action: self.press(selected),
                bg=color,
                fg=foreground,
                activebackground="#53658b",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                font=("Segoe UI", 14, "bold"),
                cursor="hand2",
            )
            column_span = 2 if label == "0" else 1
            button.grid(
                row=row,
                column=column,
                columnspan=column_span,
                padx=5,
                pady=5,
                sticky="nsew",
                ipady=9,
            )

        for column in range(4):
            root.columnconfigure(column, weight=1, uniform="calculator")
        for row in range(1, 6):
            root.rowconfigure(row, weight=1, uniform="keys")

        self.status_var = tk.StringVar(value="Keyboard: digits, +, -, *, /, Enter")
        status = tk.Label(
            root,
            textvariable=self.status_var,
            bg="#0b1020",
            fg="#9baac4",
            font=("Segoe UI", 8),
        )
        status.grid(row=6, column=0, columnspan=4, padx=8, pady=(5, 10))
        root.bind("<Key>", self.handle_key)
        root.focus_set()

    def show(self, value):
        self.current = str(value)
        self.display_var.set(self.current)

    @staticmethod
    def calculate(left, right, operator):
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise ZeroDivisionError("Cannot divide by zero.")
            return left / right
        raise ValueError("Unknown operation.")

    @staticmethod
    def format_number(value):
        if value.is_integer():
            return str(int(value))
        return format(value, ".12g")

    def press(self, action):
        if action.isdigit():
            self.enter_digit(action)
        elif action == "decimal":
            self.enter_decimal()
        elif action in {"+", "-", "*", "/"}:
            self.choose_operator(action)
        elif action == "equals":
            self.equals()
        elif action == "clear":
            self.clear()
        elif action == "delete":
            self.delete()
        elif action == "percent":
            try:
                self.show(self.format_number(float(self.current) / 100))
            except ValueError:
                self.show("0")

    def enter_digit(self, digit):
        if self.waiting_for_operand or self.current in {"Error", "Cannot divide"}:
            self.show(digit)
            self.waiting_for_operand = False
        elif self.current == "0":
            self.show(digit)
        elif len(self.current) < 16:
            self.show(self.current + digit)
        self.status_var.set("")

    def enter_decimal(self):
        if self.waiting_for_operand or self.current in {"Error", "Cannot divide"}:
            self.show("0.")
            self.waiting_for_operand = False
        elif "." not in self.current:
            self.show(self.current + ".")
        self.status_var.set("")

    def choose_operator(self, next_operator):
        try:
            value = float(self.current)
        except ValueError:
            self.status_var.set("Enter a number first.")
            return

        if self.operator is not None and not self.waiting_for_operand:
            try:
                result = self.calculate(self.stored_value, value, self.operator)
            except (ZeroDivisionError, ValueError) as error:
                self.status_var.set(str(error))
                return
            self.show(self.format_number(float(result)))
            value = float(self.current)

        self.stored_value = value
        self.operator = next_operator
        self.waiting_for_operand = True
        self.status_var.set("")

    def equals(self):
        if self.operator is None or self.stored_value is None:
            return
        try:
            result = self.calculate(self.stored_value, float(self.current), self.operator)
            self.show(self.format_number(float(result)))
            self.stored_value = None
            self.operator = None
            self.waiting_for_operand = True
            self.status_var.set("")
        except ZeroDivisionError:
            self.show("Error")
            self.status_var.set("Cannot divide by zero.")
            self.stored_value = None
            self.operator = None
            self.waiting_for_operand = True
        except (ValueError, OverflowError):
            self.show("Error")
            self.status_var.set("Please enter a valid calculation.")
            self.stored_value = None
            self.operator = None
            self.waiting_for_operand = True

    def clear(self):
        self.show("0")
        self.stored_value = None
        self.operator = None
        self.waiting_for_operand = False
        self.status_var.set("")

    def delete(self):
        if self.waiting_for_operand or self.current in {"Error", "Cannot divide"}:
            self.show("0")
            self.waiting_for_operand = False
        elif len(self.current) > 1:
            remaining = self.current[:-1]
            self.show("0" if remaining in {"", "-"} else remaining)
        else:
            self.show("0")

    def handle_key(self, event):
        char = event.char
        if char.isdigit():
            self.enter_digit(char)
            return "break"
        if char == ".":
            self.enter_decimal()
            return "break"
        if char in {"+", "-", "*", "/"}:
            self.choose_operator(char)
            return "break"
        if event.keysym in {"Return", "KP_Enter"}:
            self.equals()
            return "break"
        if event.keysym == "Escape":
            self.clear()
            return "break"
        if event.keysym == "BackSpace":
            self.delete()
            return "break"
        return None


def main():
    root = tk.Tk()
    SimpleCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
