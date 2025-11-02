import sys
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QPushButton, QFormLayout, QLineEdit,
    QTableWidgetItem, QComboBox, QMessageBox, QTextEdit, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

class ProjectDashboard(QDialog):
    """
    The main management interface for an individual project.
    Uses QTabWidget to separate different management areas.
    """
    def __init__(self, project_id, project_name, db_manager):
        super().__init__()
        self.project_id = project_id
        self.project_name = project_name
        self.db = db_manager
        
        self.setWindowTitle(f"Project Dashboard: {project_name}")
        self.setGeometry(150, 150, 1200, 800) 

        self.main_layout = QVBoxLayout(self)
        
       
        self.title_label = QLabel(f"<h1 style='color:#0b5394;'>Project: {project_name} (ID: {project_id})</h1>")
        self.main_layout.addWidget(self.title_label)

        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        
        self.setup_task_management()
        self.setup_resource_inventory()
        self.setup_daily_log()
        self.setup_reports()

       
        self.load_all_data()

    def load_all_data(self):
        """Loads data for all tabs upon dashboard initialization."""
        self.load_tasks()
        self.load_materials()
        self.load_daily_logs()
        self.update_reports()

    # Task Management 

    def setup_task_management(self):
        """Creates the Tasks & Dependencies tab (FR1.x)."""
        task_tab = QWidget()
        task_layout = QVBoxLayout(task_tab)
        task_layout.addWidget(QLabel("<h2>Task Management</h2>"))

       
        input_group = QHBoxLayout()
        task_form = QFormLayout()

        self.task_name_input = QLineEdit()
        self.task_prereq_combo = QComboBox() 
        self.task_prereq_combo.addItem("None", None) 

        task_form.addRow("Task Name:", self.task_name_input)
        task_form.addRow("Prerequisite:", self.task_prereq_combo)
        
        add_task_btn = QPushButton("Add New Task")
        add_task_btn.setStyleSheet("background-color: #38761d; color: white; padding: 5px;")
        add_task_btn.clicked.connect(self.add_task)

        input_group.addLayout(task_form)
        input_group.addWidget(add_task_btn, 0, Qt.AlignBottom)
        task_layout.addLayout(input_group)
        task_layout.addWidget(self.create_separator())

        
        task_layout.addWidget(QLabel("<h3>Current Tasks</h3>"))
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(['ID', 'Task Name', 'Prerequisite', 'Status'])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Tasks are not directly editable in table
        task_layout.addWidget(self.task_table)

       
        task_action_layout = QHBoxLayout()

        progress_task_btn = QPushButton("Mark as In Progress")
        progress_task_btn.setStyleSheet("background-color: #e67e22; color: white; padding: 8px;") 
        progress_task_btn.clicked.connect(lambda: self.update_task_status("In Progress"))
        
        complete_task_btn = QPushButton("Mark Selected Task as Complete")
        complete_task_btn.setStyleSheet("background-color: #008080; color: white; padding: 8px;")
        complete_task_btn.clicked.connect(lambda: self.update_task_status("Complete"))

        delete_task_btn = QPushButton("Delete Selected Task")
        delete_task_btn.setStyleSheet("background-color: #cc0000; color: white; padding: 8px;")
        delete_task_btn.clicked.connect(self.delete_task)

        task_action_layout.addWidget(progress_task_btn)
        task_action_layout.addWidget(complete_task_btn)
        task_action_layout.addWidget(delete_task_btn)
        task_layout.addLayout(task_action_layout)

        self.tabs.addTab(task_tab, "Tasks & Dependencies")

    def add_task(self):
        """Adds a new task to the database."""
        name = self.task_name_input.text().strip()
        prereq_id = self.task_prereq_combo.currentData() 

        if not name:
            QMessageBox.warning(self, "Input Error", "Task Name cannot be empty.")
            return

        query = "INSERT INTO tasks (project_id, name, prerequisite_task_id) VALUES (?, ?, ?)"
        if self.db.execute_query(query, (self.project_id, name, prereq_id)):
            self.task_name_input.clear()
            self.load_tasks()
            QMessageBox.information(self, "Success", "Task added.")
        
    def load_tasks(self):
        """Loads tasks from the database into the table and prerequisite combo box."""
      
        query = """
        SELECT t1.id, t1.name, t2.name AS prereq_name, t1.status
        FROM tasks t1
        LEFT JOIN tasks t2 ON t1.prerequisite_task_id = t2.id
        WHERE t1.project_id = ? ORDER BY t1.id DESC
        """
        tasks = self.db.fetch_data(query, (self.project_id,))
        
        self.task_table.setRowCount(len(tasks))
        
       
        for row, (task_id, name, prereq_name, status) in enumerate(tasks):
            self.task_table.setItem(row, 0, QTableWidgetItem(str(task_id)))
            self.task_table.setItem(row, 1, QTableWidgetItem(name))
            self.task_table.setItem(row, 2, QTableWidgetItem(prereq_name if prereq_name else "None"))
            
            status_item = QTableWidgetItem(status)
            if status == "Complete":
                status_item.setBackground(Qt.green)
            elif status == "In Progress":
                status_item.setBackground(Qt.yellow)
            else:
                status_item.setBackground(Qt.red)
            self.task_table.setItem(row, 3, status_item)

        
        self.task_prereq_combo.clear()
        self.task_prereq_combo.addItem("None", None)
        for task_id, name, _, _ in tasks:
            self.task_prereq_combo.addItem(name, task_id)
            
        self.update_reports()

    def update_task_status(self, status):
        """Updates the status of the selected task (FR1.3)."""
        selected_rows = self.task_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a task to update.")
            return

        row_index = selected_rows[0].row()
        task_id_item = self.task_table.item(row_index, 0)
        
        if not task_id_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve task ID.")
            return
            
        task_id = int(task_id_item.text())

        
        if status == "Complete":
            prereq_query = """
            SELECT t2.name, t2.status 
            FROM tasks t1 
            JOIN tasks t2 ON t1.prerequisite_task_id = t2.id
            WHERE t1.id = ? AND t2.status != 'Complete'
            """
            prereq_data = self.db.fetch_data(prereq_query, (task_id,))

            if prereq_data:
                prereq_name = prereq_data[0][0]
                QMessageBox.warning(self, "Constraint Violation", 
                    f"Cannot mark task as '{status}'. Prerequisite task '{prereq_name}' must be completed first."
                )
                return

        query = "UPDATE tasks SET status = ? WHERE id = ?"
        if self.db.execute_query(query, (status, task_id)):
            self.load_tasks()
        
    def delete_task(self):
        """Deletes the selected task."""
        selected_rows = self.task_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a task to delete.")
            return

        row_index = selected_rows[0].row()
        task_id_item = self.task_table.item(row_index, 0)
        task_name_item = self.task_table.item(row_index, 1)

        if not task_id_item or not task_name_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve task ID or Name.")
            return
            
        task_id = int(task_id_item.text())
        task_name = task_name_item.text()

      
        reply = QMessageBox.question(self, 'Confirm Deletion', 
            f"Are you sure you want to delete task '{task_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        query = "DELETE FROM tasks WHERE id = ?"
        if self.db.execute_query(query, (task_id,)):
            QMessageBox.information(self, "Success", f"Task '{task_name}' deleted.")
            self.load_tasks()

    # Resource Inventory 

    def setup_resource_inventory(self):
        
        resource_tab = QWidget()
        resource_layout = QVBoxLayout(resource_tab)
        resource_layout.addWidget(QLabel("<h2>Resource Inventory</h2>"))

        
        forms_and_alerts = QHBoxLayout()
        
   
        add_form_widget = QWidget()
        add_form_layout = QFormLayout(add_form_widget)
        add_form_layout.addRow(QLabel("<h3>Add New Material</h3>"))

        self.material_name_input = QLineEdit()
        self.material_cost_input = QLineEdit()
        self.material_threshold_input = QLineEdit()
        
        self.add_qty_input = QLineEdit()
        
        add_form_layout.addRow("Name:", self.material_name_input)
        add_form_layout.addRow("Unit Cost:", self.material_cost_input)
        add_form_layout.addRow("Stock Alert Threshold:", self.material_threshold_input)
        add_form_layout.addRow("Initial Quantity:", self.add_qty_input)
        
        add_material_btn = QPushButton("Add Material")
        add_material_btn.setStyleSheet("background-color: #38761d; color: white; padding: 5px;")
        add_material_btn.clicked.connect(self.add_material)
        add_form_layout.addWidget(add_material_btn)
        
        forms_and_alerts.addWidget(add_form_widget)

        # Alert  

        alert_widget = QWidget()
        alert_layout = QVBoxLayout(alert_widget)
        alert_layout.addWidget(QLabel("<h3>Stock Alert System (FR2.3)</h3>"))

        self.alert_label = QLabel("All stock levels are adequate.")
        self.alert_label.setStyleSheet("padding: 15px; border: 2px solid green; background-color: #e6ffe6; color: green; font-weight: bold;")
        self.alert_label.setWordWrap(True)

        alert_layout.addWidget(self.alert_label)
        alert_layout.addStretch(1)

        forms_and_alerts.addWidget(alert_widget)
        resource_layout.addLayout(forms_and_alerts)
        resource_layout.addWidget(self.create_separator())
        
        # Inventory Table 
        resource_layout.addWidget(QLabel("<h3>Current Inventory (Double-click to update Qty)</h3>"))
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(['ID', 'Name', 'Qty', 'Unit Cost', 'Threshold'])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        resource_layout.addWidget(self.inventory_table) 

        
        self.inventory_table.doubleClicked.connect(self.prompt_quantity_update)
        
        delete_material_btn = QPushButton("Delete Selected Material")
        delete_material_btn.setStyleSheet("background-color: #cc0000; color: white; padding: 8px;")
        delete_material_btn.clicked.connect(self.delete_material)
        resource_layout.addWidget(delete_material_btn)

        self.tabs.addTab(resource_tab, "Resources & Stock")

    def add_material(self):
        """Adds a new material resource to the database (FR2.1)."""
        name = self.material_name_input.text().strip()
        cost_str = self.material_cost_input.text().strip()
        threshold_str = self.material_threshold_input.text().strip()
        qty_str = self.add_qty_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Material Name cannot be empty.")
            return
        
        try:
            cost = float(cost_str) if cost_str else 0.0
            threshold = float(threshold_str) if threshold_str else 0.0
            qty = float(qty_str) if qty_str else 0.0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Cost, Threshold, and Quantity must be valid numbers.")
            return

        query = "INSERT INTO materials (project_id, name, quantity, unit_cost, alert_threshold) VALUES (?, ?, ?, ?, ?)"
        
        if self.db.execute_query(query, (self.project_id, name, qty, cost, threshold)):
            self.material_name_input.clear()
            self.material_cost_input.clear()
            self.material_threshold_input.clear()
            self.add_qty_input.clear()
            self.load_materials()
            QMessageBox.information(self, "Success", f"Material '{name}' added.")

    def load_materials(self):
        
        query = "SELECT id, name, quantity, unit_cost, alert_threshold FROM materials WHERE project_id = ? ORDER BY name ASC"
        materials = self.db.fetch_data(query, (self.project_id,))
        
        self.inventory_table.setRowCount(len(materials))
        low_stock_materials = []
        
        for row, (mat_id, name, qty, cost, threshold) in enumerate(materials):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(mat_id)))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(name))
            
            qty_item = QTableWidgetItem(f"{qty:.2f}")
            self.inventory_table.setItem(row, 2, qty_item)
            self.inventory_table.setItem(row, 3, QTableWidgetItem(f"Rs.{cost:.2f}"))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(f"{threshold:.2f}"))
            
            if qty <= threshold:
                low_stock_materials.append(name)
                qty_item.setBackground(Qt.yellow)
        
        self.update_stock_alert(low_stock_materials)

    def update_stock_alert(self, low_stock_materials):
        """Updates the stock alert label (FR2.3)."""
        if low_stock_materials:
            materials_list = ", ".join(low_stock_materials)
            alert_text = f" LOW STOCK ALERT: The following materials are below their set thresholds: {materials_list}."
            self.alert_label.setText(alert_text)
            self.alert_label.setStyleSheet("padding: 15px; border: 2px solid red; background-color: #ffcccc; color: red; font-weight: bold;")
        else:
            self.alert_label.setText(" All stock levels are adequate.")
            self.alert_label.setStyleSheet("padding: 15px; border: 2px solid green; background-color: #e6ffe6; color: green; font-weight: bold;")

    def prompt_quantity_update(self):
        """Prompts the user to update the quantity of the double-clicked material (FR2.2)."""
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows: return

        row_index = selected_rows[0].row()
        mat_id_item = self.inventory_table.item(row_index, 0)
        mat_name_item = self.inventory_table.item(row_index, 1)
        
        if not mat_id_item or not mat_name_item: return

        mat_id = int(mat_id_item.text())
        mat_name = mat_name_item.text()

        # Custom dialog for quantity update

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Update Quantity for {mat_name}")
        dialog.setGeometry(200, 200, 300, 150)
        
        layout = QFormLayout(dialog)
        
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("Enter new total quantity (e.g., 50.5)")
        
        layout.addRow("New Quantity:", qty_input)
        
        update_btn = QPushButton("Update Stock")
        update_btn.setStyleSheet("background-color: #0b5394; color: white; padding: 5px;")
        
        def update_action():
            try:
                new_qty = float(qty_input.text().strip())
                query = "UPDATE materials SET quantity = ? WHERE id = ?"
                if self.db.execute_query(query, (new_qty, mat_id)):
                    QMessageBox.information(self, "Success", f"Quantity for {mat_name} updated to {new_qty:.2f}.")
                    self.load_materials()
                    dialog.accept()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to update quantity.")
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid number for quantity.")

        update_btn.clicked.connect(update_action)
        layout.addWidget(update_btn)

        dialog.exec_()
    
    def delete_material(self):
        """Deletes the selected material."""
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a material to delete.")
            return

        row_index = selected_rows[0].row()
        mat_id_item = self.inventory_table.item(row_index, 0)
        mat_name_item = self.inventory_table.item(row_index, 1)

        if not mat_id_item or not mat_name_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve material ID or Name.")
            return
            
        mat_id = int(mat_id_item.text())
        mat_name = mat_name_item.text()

        
        reply = QMessageBox.question(self, 'Confirm Deletion', 
            f"Are you sure you want to delete material '{mat_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        query = "DELETE FROM materials WHERE id = ?"
        if self.db.execute_query(query, (mat_id,)):
            QMessageBox.information(self, "Success", f"Material '{mat_name}' deleted.")
            self.load_materials()

    

    def setup_daily_log(self):
        """Creates the Daily Log tab (FR3.1)."""
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.addWidget(QLabel("<h2>Daily Progress Log (FR3.1)</h2>"))

        
        log_form_widget = QWidget()
        log_form_layout = QVBoxLayout(log_form_widget)
        
        input_form = QFormLayout()
        
        
        self.log_date_input = QLineEdit(QDate.currentDate().toString(Qt.ISODate))
        self.log_hours_input = QLineEdit()
        self.log_description_input = QTextEdit()
        self.log_description_input.setPlaceholderText("Enter detailed notes on progress, issues, and weather conditions...")
        self.log_description_input.setFixedHeight(80)

        input_form.addRow("Date (YYYY-MM-DD):", self.log_date_input)
        input_form.addRow("Hours Worked (e.g., 8.0):", self.log_hours_input)
        
        log_form_layout.addLayout(input_form)
        log_form_layout.addWidget(QLabel("Description:"))
        log_form_layout.addWidget(self.log_description_input)

        add_log_btn = QPushButton("Save Daily Log Entry")
        add_log_btn.setStyleSheet("background-color: #0b5394; color: white; padding: 8px;")
        add_log_btn.clicked.connect(self.add_daily_log)
        log_form_layout.addWidget(add_log_btn)

        log_layout.addWidget(log_form_widget)
        log_layout.addWidget(self.create_separator())

        # Log History Table 
        log_layout.addWidget(QLabel("<h3>Log History</h3>"))
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(['ID', 'Date', 'Hours', 'Description'])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Date
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Hours
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Description
        self.log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        log_layout.addWidget(self.log_table) 
        
        delete_log_btn = QPushButton("Delete Selected Log Entry")
        delete_log_btn.setStyleSheet("background-color: #cc0000; color: white; padding: 8px;")
        delete_log_btn.clicked.connect(self.delete_log_entry)
        log_layout.addWidget(delete_log_btn)

        self.tabs.addTab(log_tab, "Daily Log")
        
    def add_daily_log(self):
        """Adds a new daily log entry to the database."""
        log_date = self.log_date_input.text().strip()
        hours_str = self.log_hours_input.text().strip()
        description = self.log_description_input.toPlainText().strip()

        if not log_date or not hours_str:
            QMessageBox.warning(self, "Input Error", "Date and Hours Worked are required.")
            return

        try:
            hours = float(hours_str)
            
            datetime.strptime(log_date, '%Y-%m-%d')
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Hours must be a number, and Date must be in YYYY-MM-DD format.")
            return

        query = "INSERT INTO daily_log (project_id, log_date, description, hours_worked) VALUES (?, ?, ?, ?)"
        
        if self.db.execute_query(query, (self.project_id, log_date, description, hours)):
            self.log_hours_input.clear()
            self.log_description_input.clear()
            self.log_date_input.setText(QDate.currentDate().toString(Qt.ISODate))
            self.load_daily_logs()
            QMessageBox.information(self, "Success", "Daily log entry saved.")
            
    def load_daily_logs(self):
        """Loads daily logs from the database into the log history table."""
        query = "SELECT id, log_date, hours_worked, description FROM daily_log WHERE project_id = ? ORDER BY log_date DESC"
        logs = self.db.fetch_data(query, (self.project_id,))
        
        self.log_table.setRowCount(len(logs))
        
        for row, (log_id, date, hours, description) in enumerate(logs):
            self.log_table.setItem(row, 0, QTableWidgetItem(str(log_id)))
            self.log_table.setItem(row, 1, QTableWidgetItem(date))
            self.log_table.setItem(row, 2, QTableWidgetItem(f"{hours:.1f}"))
            self.log_table.setItem(row, 3, QTableWidgetItem(description))

    def delete_log_entry(self):
        """Deletes the selected daily log entry."""
        selected_rows = self.log_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a log entry to delete.")
            return

        row_index = selected_rows[0].row()
        log_id_item = self.log_table.item(row_index, 0)
        
        if not log_id_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve log ID.")
            return
            
        log_id = int(log_id_item.text())

        # Confirmation Dialog

        reply = QMessageBox.question(self, 'Confirm Deletion', 
            f"Are you sure you want to delete this log entry (ID: {log_id})? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        query = "DELETE FROM daily_log WHERE id = ?"
        if self.db.execute_query(query, (log_id,)):
            QMessageBox.information(self, "Success", "Log entry deleted.")
            self.load_daily_logs()

    # reports 

    def setup_reports(self):
        """Creates the Status Reports tab (FR3.3)."""
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        report_layout.addWidget(QLabel("<h2>Status Report (FR3.3)</h2>"))
        
        # summary area

        summary_widget = QWidget()
        summary_layout = QFormLayout(summary_widget)
        
        self.status_label = QLabel("Loading...")
        self.completion_label = QLabel("N/A")
        self.total_tasks_label = QLabel("N/A")
        self.total_hours_label = QLabel("N/A")
        self.total_cost_label = QLabel("N/A")
        
        summary_layout.addRow("Project Status:", self.status_label)
        summary_layout.addRow("Project Completion:", self.completion_label)
        summary_layout.addRow("Total Tasks:", self.total_tasks_label)
        summary_layout.addRow("Total Hours Logged:", self.total_hours_label)
        summary_layout.addRow("Estimated Material Cost:", self.total_cost_label)
        
        report_layout.addWidget(summary_widget)
        report_layout.addWidget(self.create_separator())
        report_layout.addStretch(1) # Push content to the top

        self.tabs.addTab(report_tab, "Reports")

    def update_reports(self):
        """Calculates and updates all report labels (FR3.3)."""
        
        # Completion Percentage (Based on Tasks)

        total_tasks_query = "SELECT COUNT(*) FROM tasks WHERE project_id = ?"
        completed_tasks_query = "SELECT COUNT(*) FROM tasks WHERE project_id = ? AND status = 'Complete'"
        
        total_tasks = self.db.fetch_data(total_tasks_query, (self.project_id,))[0][0]
        completed_tasks = self.db.fetch_data(completed_tasks_query, (self.project_id,))[0][0]
        
        if total_tasks > 0:
            completion_percent = (completed_tasks / total_tasks) * 100
        else:
            completion_percent = 0
            
        self.total_tasks_label.setText(str(total_tasks))
        self.completion_label.setText(f"{completion_percent:.1f}%")
        
        
        if completion_percent == 100 and total_tasks > 0:
            status = "Completed"
            status_style = "color: green; font-weight: bold;"
            
            self.db.execute_query("UPDATE projects SET status = 'Completed' WHERE id = ?", (self.project_id,))
        elif completion_percent > 0:
            status = "In Progress"
            status_style = "color: orange; font-weight: bold;"
        else:
            status = "Not Started"
            status_style = "color: red; font-weight: bold;"
            
        self.status_label.setText(status)
        self.status_label.setStyleSheet(status_style)


       
        hours_query = "SELECT SUM(hours_worked) FROM daily_log WHERE project_id = ?"
        total_hours = self.db.fetch_data(hours_query, (self.project_id,))[0][0] or 0.0
        self.total_hours_label.setText(f"{total_hours:.1f} hours")
        
       
        cost_query = "SELECT SUM(quantity * unit_cost) FROM materials WHERE project_id = ?"
        total_cost = self.db.fetch_data(cost_query, (self.project_id,))[0][0] or 0.0
        self.total_cost_label.setText(f"Rs.{total_cost:,.2f}")


    # funtions

    def create_separator(self):
        #horizontal line
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #cccccc;")
        return separator

    def closeEvent(self, event):
       
        self.finished.emit()
        event.accept()

