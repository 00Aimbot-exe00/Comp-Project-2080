import sys
import sqlite3
import calendar
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QStackedWidget,
    QFrame, QMessageBox, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

DB_NAME = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY,
        source TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        category TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY,
        type TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY,
        type TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY,
        name TEXT,
        target REAL,
        progress REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY,
        type TEXT,
        value REAL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        message TEXT,
        status TEXT
    )""")
    conn.commit()

    c.execute("SELECT COUNT(*) FROM income")
    if c.fetchone()[0] == 0:
        sample_income = [
            ("E-commerce", 2100.0, "2024-05-05"),
            ("Google AdSense", 950.0, "2024-05-12"),
            ("My Shop", 8000.0, "2024-05-20"),
            ("Salary", 13000.0, "2024-05-01"),
        ]
        c.executemany("INSERT INTO income (source, amount, date) VALUES (?, ?, ?)", sample_income)

    c.execute("SELECT COUNT(*) FROM expenses")
    if c.fetchone()[0] == 0:
        sample_expenses = [
            ("Housing", 3452.0, "2024-05-02"),
            ("Personal", 2200.0, "2024-05-10"),
            ("Transportation", 2190.0, "2024-05-15"),
            ("Pet Food", 950.0, "2024-05-18"),
        ]
        c.executemany("INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)", sample_expenses)

    c.execute("SELECT COUNT(*) FROM investments")
    if c.fetchone()[0] == 0:
        sample_invest = [
            ("Business", 50000.0, "2024-05-01"),
            ("Securities", 22500.0, "2024-05-01"),
            ("Gold", 15700.0, "2024-05-01"),
            ("Real Estate", 120000.0, "2024-05-01"),
            ("Crypto", 8000.0, "2024-05-01"),
        ]
        c.executemany("INSERT INTO investments (type, amount, date) VALUES (?, ?, ?)", sample_invest)

    c.execute("SELECT COUNT(*) FROM debts")
    if c.fetchone()[0] == 0:
        sample_debts = [
            ("Mortgage", 40000.0, "2024-05-01"),
            ("Credit Card", 8000.0, "2024-05-01"),
            ("Car Leasing", 5000.0, "2024-05-01"),
        ]
        c.executemany("INSERT INTO debts (type, amount, date) VALUES (?, ?, ?)", sample_debts)

    c.execute("SELECT COUNT(*) FROM goals")
    if c.fetchone()[0] == 0:
        sample_goals = [
            ("House Down Payment", 200000.0, 42000.0, "2024-05-01"),
            ("Emergency Fund", 30000.0, 8000.0, "2024-05-01"),
        ]
        c.executemany("INSERT INTO goals (name, target, progress, date) VALUES (?, ?, ?, ?)", sample_goals)

    c.execute("SELECT COUNT(*) FROM notifications")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO notifications (message, status) VALUES (?, ?)",
                  ("3 Bills are past due. Pay soon to avoid late fees.", "active"))

    conn.commit()
    conn.close()

def fetch_month_data(table, year, month):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    month_str = f"{year}-{month:02d}"
    if table in ("income", "expenses"):
        c.execute(f"SELECT id, { 'source' if table=='income' else 'category' }, amount, date FROM {table} WHERE date LIKE ?", (month_str + "%",))
    else:
        if table == "goals":
            c.execute("SELECT id, name, target, progress, date FROM goals")
        else:
            c.execute(f"SELECT id, type, amount, date FROM {table}")
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_summary(year, month):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    month_str = f"{year}-{month:02d}"
    c.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (month_str + "%",))
    income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (month_str + "%",))
    expenses = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM investments")
    investments = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM debts")
    debts = c.fetchone()[0] or 0
    c.execute("SELECT SUM(value) FROM assets")
    assets = c.fetchone()[0] or 0
    c.execute("SELECT message FROM notifications WHERE status='active'")
    notifications = [r[0] for r in c.fetchall()]
    conn.close()
    return {"income": income, "expenses": expenses, "investments": investments, "debts": debts, "assets": assets, "notifications": notifications}

def save_row(table, row_id, col_values):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if table == "income":
        if row_id is None:
            c.execute("INSERT INTO income (source, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE income SET source=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "expenses":
        if row_id is None:
            c.execute("INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE expenses SET category=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "investments":
        if row_id is None:
            c.execute("INSERT INTO investments (type, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE investments SET type=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "debts":
        if row_id is None:
            c.execute("INSERT INTO debts (type, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE debts SET type=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "goals":
        if row_id is None:
            c.execute("INSERT INTO goals (name, target, progress, date) VALUES (?, ?, ?, ?)", (col_values[0], col_values[1], col_values[2], col_values[3]))
        else:
            c.execute("UPDATE goals SET name=?, target=?, progress=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], col_values[3], row_id))
    conn.commit()
    conn.close()
class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        fig.tight_layout()

    def plot_income_expenses(self, income_rows, expense_rows):
        self.ax.clear()
        def daily_sums(rows):
            sums = {}
            for r in rows:
                date = r[3]
                try:
                    day = int(date.split("-")[2])
                except Exception:
                    continue
                sums.setdefault(day, 0)
                sums[day] += float(r[2])
            return sums
        inc = daily_sums(income_rows)
        exp = daily_sums(expense_rows)
        days = list(range(1, 32))
        inc_vals = [inc.get(d, 0) for d in days]
        exp_vals = [exp.get(d, 0) for d in days]
        self.ax.plot(days, inc_vals, label="Income", color="#4CAF50", linewidth=2)
        self.ax.plot(days, exp_vals, label="Expenses", color="#F44336", linewidth=2)
        self.ax.set_xlim(1, 31)
        self.ax.set_xlabel("Day")
        self.ax.set_ylabel("Amount")
        self.ax.set_title("Daily Income vs Expenses")
        self.ax.legend()
        self.draw()

    def plot_pie_income_share(self, income_rows):
        self.ax.clear()
        labels = [r[1] for r in income_rows]
        vals = [r[2] for r in income_rows]
        if not vals:
            self.ax.text(0.5, 0.5, "No data", ha="center")
        else:
            self.ax.pie(vals, labels=labels, autopct="%1.0f%%", colors=plt.cm.Set3.colors)
        self.ax.set_title("Income Share")
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Finance Tracker")
        self.setGeometry(80, 40, 1400, 900)
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.fullscreen = False

        central = QWidget()
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        nav_frame = QFrame()
        nav_frame.setObjectName("nav")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(16, 16, 16, 16)
        nav_layout.setSpacing(12)

        profile_container = QVBoxLayout()
        profile_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        profile_circle = QFrame()
        profile_circle.setFixedSize(72, 72)
        profile_circle.setObjectName("profile_circle")
        profile_circle.setStyleSheet("""
            QFrame#profile_circle {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                    stop:0 #4facfe, stop:1 #00f2fe);
                border-radius: 36px;
                border: 2px solid rgba(255,255,255,0.08);
            }
        """)
        profile_container.addWidget(profile_circle, alignment=Qt.AlignmentFlag.AlignHCenter)

        name_label = QLabel("Wong Ho Ye")
        name_label.setObjectName("sidebar_name")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_label = QLabel("Student")
        role_label.setObjectName("sidebar_role")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_container.addWidget(name_label)
        profile_container.addWidget(role_label)

        nav_layout.addLayout(profile_container)

        self.nav_buttons = {}
        nav_items = ["Dashboard", "Budgeting", "Income", "Expenses", "Investments", "Debts", "Financial Goals", "Setting", "Help", "Log Out"]
        for name in nav_items:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.make_nav_handler(name))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            nav_layout.addWidget(btn)
            self.nav_buttons[name] = btn

        nav_layout.addStretch()
        main_layout.addWidget(nav_frame, 1)

        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        months_bar = QHBoxLayout()
        months_bar.setSpacing(6)
        self.month_buttons = {}
        for i, m in enumerate(calendar.month_abbr):
            if i == 0: continue
            b = QPushButton(m)
            b.setCheckable(True)
            b.clicked.connect(self.make_month_handler(i))
            months_bar.addWidget(b)
            self.month_buttons[i] = b
        right_layout.addLayout(months_bar)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.date_label = QLabel("")
        header_layout.addWidget(self.date_label)
        right_layout.addLayout(header_layout)

        self.stack = QStackedWidget()
        self.pages = {}
        self.pages["Dashboard"] = self.build_dashboard_page()
        self.pages["Budgeting"] = self.build_budgeting_page()
        self.pages["Income"] = self.build_income_page()
        self.pages["Expenses"] = self.build_expenses_page()
        self.pages["Investments"] = self.build_investments_page()
        self.pages["Debts"] = self.build_debts_page()
        self.pages["Financial Goals"] = self.build_goals_page()
        self.pages["Setting"] = self.build_simple_page("Setting")
        self.pages["Help"] = self.build_simple_page("Help")
        self.pages["Log Out"] = self.build_simple_page("Log Out")

        for name, widget in self.pages.items():
            self.stack.addWidget(widget)

        right_layout.addWidget(self.stack, 1)
        main_layout.addWidget(right_frame, 4)

        toggle_full = QAction("Toggle Fullscreen", self)
        toggle_full.setShortcut("F11")
        toggle_full.triggered.connect(self.toggle_fullscreen)
        self.addAction(toggle_full)

        exit_full = QAction("Exit", self)
        exit_full.setShortcut("Esc")
        exit_full.triggered.connect(self.close)
        self.addAction(exit_full)

        self.setStyleSheet(self.stylesheet())

        self.select_month(self.current_month)
        self.select_nav("Dashboard")

    def build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        cards = QHBoxLayout()
        self.card_balance = self.make_card("Available Balance", "$0")
        self.card_net = self.make_card("Total Net Worth", "$0")
        self.card_income = self.make_card("Income (month)", "$0")
        self.card_expenses = self.make_card("Expenses (month)", "$0")
        cards.addWidget(self.card_balance)
        cards.addWidget(self.card_net)
        cards.addWidget(self.card_income)
        cards.addWidget(self.card_expenses)
        layout.addLayout(cards)

        mid = QHBoxLayout()

        left_col = QVBoxLayout()
        self.line_chart = ChartCanvas(width=6, height=3)
        left_col.addWidget(self.line_chart)
        mid.addLayout(left_col, 3)

        right_col = QVBoxLayout()
        self.pie_chart = ChartCanvas(width=4, height=3)
        right_col.addWidget(self.pie_chart)

        self.ranking_label = QLabel("Income Ranking")
        self.ranking_label.setObjectName("ranking")
        right_col.addWidget(self.ranking_label)

        self.credit_card = self.make_card("Card •••• 5678", "$7,538.00")
        right_col.addWidget(self.credit_card)

        mid.addLayout(right_col, 2)
        layout.addLayout(mid)

        self.notif_label = QLabel("")
        self.notif_label.setObjectName("notif")
        layout.addWidget(self.notif_label)

        return page

    def build_budgeting_page(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel("Budgeting — coming soon"))
        return w

    def build_income_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Income Sources (editable)"))

        self.income_table = QTableWidget()
        self.income_table.setColumnCount(4)
        self.income_table.setHorizontalHeaderLabels(["ID", "Source", "Amount", "Date (YYYY-MM-DD)"])
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.income_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_income_row)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_income_table)
        btns.addWidget(add_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_expenses_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Expenses (editable)"))

        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(4)
        self.exp_table.setHorizontalHeaderLabels(["ID", "Category", "Amount", "Date (YYYY-MM-DD)"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.exp_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_expense_row)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_exp_table)
        btns.addWidget(add_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_investments_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Investments (editable)"))

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(4)
        self.inv_table.setHorizontalHeaderLabels(["ID", "Type", "Amount", "Date (YYYY-MM-DD)"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.inv_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_invest_row)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_inv_table)
        btns.addWidget(add_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_debts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Debts (editable)"))

        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(4)
        self.debt_table.setHorizontalHeaderLabels(["ID", "Type", "Amount", "Date (YYYY-MM-DD)"])
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.debt_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_debt_row)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_debt_table)
        btns.addWidget(add_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_goals_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Financial Goals (editable)"))

        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(5)
        self.goals_table.setHorizontalHeaderLabels(["ID", "Name", "Target", "Progress", "Date (YYYY-MM-DD)"])
        self.goals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.goals_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Goal")
        add_btn.clicked.connect(self.add_goal_row)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_goals_table)
        btns.addWidget(add_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_simple_page(self, title):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size:18px; font-weight:bold;")
        l.addWidget(lbl)
        return w

    def make_card(self, title, value):
        f = QFrame()
        f.setObjectName("card")
        v = QVBoxLayout(f)
        t = QLabel(title)
        t.setObjectName("card_title")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("card_value")
        v.addWidget(t)
        v.addWidget(v_lbl)
        return f

    def make_nav_handler(self, name):
        def handler():
            self.select_nav(name)
        return handler

    def make_month_handler(self, month_index):
        def handler():
            self.select_month(month_index)
        return handler

    def select_nav(self, name):
        idx = list(self.pages.keys()).index(name)
        self.stack.setCurrentIndex(idx)
        for n, btn in self.nav_buttons.items():
            btn.setStyleSheet(self.nav_button_style(n == name))
        self.refresh_current_page()

    def select_month(self, month_index):
        for i, b in self.month_buttons.items():
            b.setChecked(i == month_index)
            b.setStyleSheet(self.month_button_style(i == month_index))
        self.current_month = month_index
        self.date_label.setText(f"{calendar.month_name[month_index]} {self.current_year}")
        self.refresh_current_page()

    def refresh_current_page(self):
        summary = fetch_summary(self.current_year, self.current_month)
        balance = summary["income"] - summary["expenses"]
        net = summary["assets"] + balance
        self.card_balance.findChild(QLabel, "card_value").setText(f"${balance:,.2f}")
        self.card_net.findChild(QLabel, "card_value").setText(f"${net:,.2f}")
        self.card_income.findChild(QLabel, "card_value").setText(f"${summary['income']:,.2f}")
        self.card_expenses.findChild(QLabel, "card_value").setText(f"${summary['expenses']:,.2f}")
        self.notif_label.setText("\n".join(summary["notifications"]) if summary["notifications"] else "")
        income_rows = fetch_month_data("income", self.current_year, self.current_month)
        expense_rows = fetch_month_data("expenses", self.current_year, self.current_month)
        self.line_chart.plot_income_expenses(income_rows, expense_rows)
        self.pie_chart.plot_pie_income_share(income_rows)
        ranking = sorted([(r[1], r[2]) for r in income_rows], key=lambda x: -float(x[1]))[:5]
        ranking_text = "<b>Income Ranking</b><br>" + "<br>".join([f"{name}: ${amt:,.2f}" for name, amt in ranking]) if ranking else "No income data"
        self.ranking_label.setText(ranking_text)

        current_widget = self.stack.currentWidget()
        if current_widget == self.pages["Income"]:
            self.populate_income_table()
        if current_widget == self.pages["Expenses"]:
            self.populate_exp_table()
        if current_widget == self.pages["Investments"]:
            self.populate_inv_table()
        if current_widget == self.pages["Debts"]:
            self.populate_debt_table()
        if current_widget == self.pages["Financial Goals"]:
            self.populate_goals_table()

    def populate_income_table(self):
        rows = fetch_month_data("income", self.current_year, self.current_month)
        self.income_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.income_table.setItem(i, 0, id_item)
            self.income_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.income_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.income_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_income_row(self):
        r = self.income_table.rowCount()
        self.income_table.insertRow(r)
        self.income_table.setItem(r, 0, QTableWidgetItem(""))
        self.income_table.setItem(r, 1, QTableWidgetItem("New Source"))
        self.income_table.setItem(r, 2, QTableWidgetItem("0"))
        self.income_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_income_table(self):
        rows = self.income_table.rowCount()
        for i in range(rows):
            id_item = self.income_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            source = self.income_table.item(i, 1).text() if self.income_table.item(i, 1) else ""
            amount_text = self.income_table.item(i, 2).text() if self.income_table.item(i, 2) else "0"
            date = self.income_table.item(i, 3).text() if self.income_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid amount", f"Row {i+1} amount is invalid.")
                return
            save_row("income", row_id, (source, amount, date))
        QMessageBox.information(self, "Saved", "Income table saved.")
        self.refresh_current_page()

    def populate_exp_table(self):
        rows = fetch_month_data("expenses", self.current_year, self.current_month)
        self.exp_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exp_table.setItem(i, 0, id_item)
            self.exp_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.exp_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.exp_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_expense_row(self):
        r = self.exp_table.rowCount()
        self.exp_table.insertRow(r)
        self.exp_table.setItem(r, 0, QTableWidgetItem(""))
        self.exp_table.setItem(r, 1, QTableWidgetItem("New Category"))
        self.exp_table.setItem(r, 2, QTableWidgetItem("0"))
        self.exp_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_exp_table(self):
        rows = self.exp_table.rowCount()
        for i in range(rows):
            id_item = self.exp_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            category = self.exp_table.item(i, 1).text() if self.exp_table.item(i, 1) else ""
            amount_text = self.exp_table.item(i, 2).text() if self.exp_table.item(i, 2) else "0"
            date = self.exp_table.item(i, 3).text() if self.exp_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid amount", f"Row {i+1} amount is invalid.")
                return
            save_row("expenses", row_id, (category, amount, date))
        QMessageBox.information(self, "Saved", "Expenses table saved.")
        self.refresh_current_page()

    def populate_inv_table(self):
        rows = fetch_month_data("investments", self.current_year, self.current_month)
        self.inv_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inv_table.setItem(i, 0, id_item)
            self.inv_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.inv_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.inv_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_invest_row(self):
        r = self.inv_table.rowCount()
        self.inv_table.insertRow(r)
        self.inv_table.setItem(r, 0, QTableWidgetItem(""))
        self.inv_table.setItem(r, 1, QTableWidgetItem("New Type"))
        self.inv_table.setItem(r, 2, QTableWidgetItem("0"))
        self.inv_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_inv_table(self):
        rows = self.inv_table.rowCount()
        for i in range(rows):
            id_item = self.inv_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            typ = self.inv_table.item(i, 1).text() if self.inv_table.item(i, 1) else ""
            amount_text = self.inv_table.item(i, 2).text() if self.inv_table.item(i, 2) else "0"
            date = self.inv_table.item(i, 3).text() if self.inv_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid amount", f"Row {i+1} amount is invalid.")
                return
            save_row("investments", row_id, (typ, amount, date))
        QMessageBox.information(self, "Saved", "Investments saved.")
        self.refresh_current_page()

    def populate_debt_table(self):
        rows = fetch_month_data("debts", self.current_year, self.current_month)
        self.debt_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.debt_table.setItem(i, 0, id_item)
            self.debt_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.debt_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.debt_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_debt_row(self):
        r = self.debt_table.rowCount()
        self.debt_table.insertRow(r)
        self.debt_table.setItem(r, 0, QTableWidgetItem(""))
        self.debt_table.setItem(r, 1, QTableWidgetItem("New Debt"))
        self.debt_table.setItem(r, 2, QTableWidgetItem("0"))
        self.debt_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_debt_table(self):
        rows = self.debt_table.rowCount()
        for i in range(rows):
            id_item = self.debt_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            typ = self.debt_table.item(i, 1).text() if self.debt_table.item(i, 1) else ""
            amount_text = self.debt_table.item(i, 2).text() if self.debt_table.item(i, 2) else "0"
            date = self.debt_table.item(i, 3).text() if self.debt_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid amount", f"Row {i+1} amount is invalid.")
                return
            save_row("debts", row_id, (typ, amount, date))
        QMessageBox.information(self, "Saved", "Debts saved.")
        self.refresh_current_page()

    def populate_goals_table(self):
        rows = fetch_month_data("goals", self.current_year, self.current_month)
        self.goals_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.goals_table.setItem(i, 0, id_item)
            self.goals_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.goals_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.goals_table.setItem(i, 3, QTableWidgetItem(str(r[3])))
            self.goals_table.setItem(i, 4, QTableWidgetItem(str(r[4])))

    def add_goal_row(self):
        r = self.goals_table.rowCount()
        self.goals_table.insertRow(r)
        self.goals_table.setItem(r, 0, QTableWidgetItem(""))
        self.goals_table.setItem(r, 1, QTableWidgetItem("New Goal"))
        self.goals_table.setItem(r, 2, QTableWidgetItem("0"))
        self.goals_table.setItem(r, 3, QTableWidgetItem("0"))
        self.goals_table.setItem(r, 4, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_goals_table(self):
        rows = self.goals_table.rowCount()
        for i in range(rows):
            id_item = self.goals_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            name = self.goals_table.item(i, 1).text() if self.goals_table.item(i, 1) else ""
            target_text = self.goals_table.item(i, 2).text() if self.goals_table.item(i, 2) else "0"
            progress_text = self.goals_table.item(i, 3).text() if self.goals_table.item(i, 3) else "0"
            date = self.goals_table.item(i, 4).text() if self.goals_table.item(i, 4) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                target = float(target_text)
                progress = float(progress_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid number", f"Row {i+1} target/progress is invalid.")
                return
            save_row("goals", row_id, (name, target, progress, date))
        QMessageBox.information(self, "Saved", "Goals saved.")
        self.refresh_current_page()

    def stylesheet(self):
        return """
        QMainWindow { background: #0f1720; color: #e6eef6; }
        #nav { background: #071126; border-right: 1px solid #1f2a37; }
        QPushButton { background: transparent; color: #cfe6ff; border: none; padding: 8px; text-align: left; }
        QPushButton:hover { background: #0b2a44; }
        QPushButton:checked { background: #0f4b6f; color:white; font-weight: bold; }
        QFrame#card { background: #0b2233; border-radius: 8px; padding: 12px; margin: 6px; }
        QLabel#card_title { color: #9fbcd8; font-size: 12px; }
        QLabel#card_value { color: #ffffff; font-size: 20px; font-weight: bold; }
        QLabel#profile { color: #cfe6ff; font-weight: bold; }
        QLabel#notif { color: #ffcccb; font-weight: bold; }
        QLabel#ranking { color: #dbefff; }
        QLabel#sidebar_name { color: #eaf6ff; font-weight: bold; font-size: 13px; }
        QLabel#sidebar_role { color: #9fbcd8; font-size: 11px; margin-bottom: 8px; }
        QFrame#profile_circle { margin-bottom: 6px; }
        QTableWidget { background: #071826; color: #e6eef6; gridline-color: #123; }
        QHeaderView::section { background: #0b2a3a; color: #dbefff; padding: 6px; }
        """

    def nav_button_style(self, active):
        if active:
            return "background:#0f4b6f; color:white; font-weight:bold; padding:8px;"
        return "background:transparent; color:#cfe6ff; padding:8px;"

    def month_button_style(self, active):
        if active:
            return "background:#1f6f8f; color:white; padding:6px; border-radius:4px;"
        return "background:transparent; color:#cfe6ff; padding:6px;"

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.showNormal()
            self.fullscreen = False
        else:
            self.showFullScreen()
            self.fullscreen = True

def main():
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

