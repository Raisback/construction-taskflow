import sys
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QPushButton, QFormLayout, QLineEdit,
    QMessageBox, QTableWidgetItem, QComboBox, QHeaderView,
    QDoubleSpinBox
)
from PyQt5.QtCore import Qt

class ProjectDashboard(QDialog):
    def __init__(self, project_id, project_name, db_manager):
        super().__init__()
        self.project_id = project_id
        self.project_name = project_name
        self.db = db_manager
        
        self.setWindowTitle(f"Project Dashboard: {project_name}")
        self.setGeometry(150, 150, 1200, 800) 

        self.main_layout = QVBoxLayout(self)
        
        self.title_label = QLabel(f"<h1>Project: {project_name} (ID: {project_id})</h1>")
        self.main_layout.addWidget(self.title_label)

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.setup_task_management()
        self.setup_resource_inventory()
        self.setup_daily_log()
        self.setup_reports()
        
        self.load_tasks()
        self.load_materials()

    def setup_task_management(self):
        task_tab = QWidget()
        task_layout = QVBoxLayout(task_tab)
        
        creation_group = QWidget()
        creation_layout = QFormLayout(creation_group)
        creation_layout.setContentsMargins(10, 10, 10, 10)
        
        self.new_task_name = QLineEdit()
        self.new_task_prereq = QComboBox()
        self.new_task_prereq.addItem("None", None)

        creation_layout.addRow("Task Name:", self.new_task_name)
        creation_layout.addRow("Prerequisite Task:", self.new_task_prereq)
        
        create_task_btn = QPushButton("Add New Task")
        create_task_btn.setStyleSheet("background-color: #3c78d8; color: white; padding: 8px; border-radius: 4px;")
        create_task_btn.clicked.connect(self.create_task)
        creation_layout.addWidget(create_task_btn)
        
        task_layout.addWidget(QLabel("<h3>Add New Task</h3>"))
        task_layout.addWidget(creation_group)
        
        task_layout.addWidget(QLabel("<h3>Project Tasks</h3>"))
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(['ID', 'Name', 'Prerequisite ID', 'Status'])
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)

        task_layout.addWidget(self.task_table)
        
        control_group = QWidget()
        control_layout = QHBoxLayout(control_group)
        
        self.task_status_combo = QComboBox()
        self.task_status_combo.addItems(['Not Started', 'In Progress', 'Completed', 'On Hold'])
        
        update_status_btn = QPushButton("Update Status of Selected Task")
        update_status_btn.setStyleSheet("background-color: #f1c232; color: black; padding: 8px; border-radius: 4px;")
        update_status_btn.clicked.connect(self.update_task_status)
        
        control_layout.addWidget(QLabel("New Status:"))
        control_layout.addWidget(self.task_status_combo)
        control_layout.addWidget(update_status_btn)
        control_layout.addStretch(1)

        task_layout.addWidget(control_group)

        self.tabs.addTab(task_tab, "Tasks & Dependencies")

    def create_task(self):
        name = self.new_task_name.text().strip()
        prereq_id = self.new_task_prereq.currentData()
        
        if not name:
            QMessageBox.warning(self, "Input Error", "Task Name cannot be empty.")
            return

        query = "INSERT INTO tasks (project_id, name, prerequisite_task_id) VALUES (?, ?, ?)"
        params = (self.project_id, name, prereq_id)
        
        if self.db.execute_query(query, params):
            self.new_task_name.clear()
            QMessageBox.information(self, "Success", f"Task '{name}' added.")
            self.load_tasks()

    def load_tasks(self):
        query = "SELECT id, name, prerequisite_task_id, status FROM tasks WHERE project_id = ?"
        tasks = self.db.fetch_data(query, (self.project_id,))
        
        self.task_table.setRowCount(len(tasks))
        
        self.new_task_prereq.clear()
        self.new_task_prereq.addItem("None", None)
        
        for row, (task_id, name, prereq_id, status) in enumerate(tasks):
            self.task_table.setItem(row, 0, QTableWidgetItem(str(task_id)))
            self.task_table.setItem(row, 1, QTableWidgetItem(name))
            self.task_table.setItem(row, 2, QTableWidgetItem(str(prereq_id) if prereq_id else ''))
            self.task_table.setItem(row, 3, QTableWidgetItem(status))
            
            self.new_task_prereq.addItem(f"{task_id}: {name}", task_id)

    def update_task_status(self):
        selected_rows = self.task_table.selectionModel().selectedRows()
        new_status = self.task_status_combo.currentText()

        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a task to update.")
            return

        row_index = selected_rows[0].row()
        task_id_item = self.task_table.item(row_index, 0)
        prereq_id_item = self.task_table.item(row_index, 2).text()
        
        if not task_id_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve Task ID.")
            return

        task_id = int(task_id_item.text())
        prereq_id = int(prereq_id_item) if prereq_id_item.isdigit() else None
        
        if new_status in ['In Progress', 'Completed'] and prereq_id is not None:
            query = "SELECT status FROM tasks WHERE id = ?"
            prereq_data = self.db.fetch_data(query, (prereq_id,))
            
            if prereq_data and prereq_data[0][0] != 'Completed':
                QMessageBox.critical(self, "Dependency Error", 
                                     f"Task {task_id} requires prerequisite task {prereq_id} to be 'Completed' before proceeding.")
                return 
        
        update_query = "UPDATE tasks SET status = ? WHERE id = ?"
        
        if self.db.execute_query(update_query, (new_status, task_id)):
            QMessageBox.information(self, "Success", f"Task {task_id} status updated to '{new_status}'.")
            self.load_tasks()

    def setup_resource_inventory(self):
        resource_tab = QWidget()
        resource_layout = QVBoxLayout(resource_tab)
        
        main_h_layout = QHBoxLayout()
        
        inv_management_widget = QWidget()
        inv_management_layout = QVBoxLayout(inv_management_widget)
        inv_management_layout.addWidget(QLabel("<h3>Inventory Management</h3>"))
        
        inv_form = QFormLayout()
        self.material_name = QLineEdit()
        self.material_quantity = QDoubleSpinBox()
        self.material_quantity.setRange(0.0, 99999.0)
        self.material_cost = QDoubleSpinBox()
        self.material_cost.setRange(0.0, 99999.0)
        self.material_threshold = QDoubleSpinBox()
        self.material_threshold.setRange(0.0, 99999.0)

        inv_form.addRow("Material Name:", self.material_name)
        inv_form.addRow("Initial Quantity:", self.material_quantity)
        inv_form.addRow("Unit Cost:", self.material_cost)
        inv_form.addRow("Alert Threshold:", self.material_threshold)
        
        add_material_btn = QPushButton("Add Material to Inventory")
        add_material_btn.setStyleSheet("background-color: #38761d; color: white; padding: 8px; border-radius: 4px;")
        add_material_btn.clicked.connect(self.create_material)
        
        inv_management_layout.addLayout(inv_form)
        inv_management_layout.addWidget(add_material_btn)
        inv_management_layout.addStretch(1)

        consumption_widget = QWidget()
        consumption_layout = QVBoxLayout(consumption_widget)
        consumption_layout.addWidget(QLabel("<h3>Log Consumption</h3>"))

        cons_form = QFormLayout()
        self.cons_material_combo = QComboBox()
        self.cons_quantity = QDoubleSpinBox()
        self.cons_quantity.setRange(0.0, 99999.0)

        cons_form.addRow("Select Material:", self.cons_material_combo)
        cons_form.addRow("Quantity Used:", self.cons_quantity)

        log_consumption_btn = QPushButton("Log Use & Check Stock")
        log_consumption_btn.setStyleSheet("background-color: #cc0000; color: white; padding: 8px; border-radius: 4px;")
        log_consumption_btn.clicked.connect(self.log_consumption)

        consumption_layout.addLayout(cons_form)
        consumption_layout.addWidget(log_consumption_btn)
        consumption_layout.addStretch(1)

        main_h_layout.addWidget(inv_management_widget, 40)
        main_h_layout.addWidget(consumption_widget, 40)
        
        resource_layout.addLayout(main_h_layout)
        
        resource_layout.addWidget(QLabel("<h3>Current Inventory Stock</h3>"))
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(['ID', 'Name', 'Qty', 'Unit Cost', 'Threshold'])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        resource_layout.addWidget(self.inventory_table) 
        
        self.tabs.addTab(resource_tab, "Resources & Stock")

    def create_material(self):
        name = self.material_name.text().strip()
        quantity = self.material_quantity.value()
        cost = self.material_cost.value()
        threshold = self.material_threshold.value()

        if not name:
            QMessageBox.warning(self, "Input Error", "Material Name cannot be empty.")
            return

        query = "INSERT INTO materials (project_id, name, quantity, unit_cost, alert_threshold) VALUES (?, ?, ?, ?, ?)"
        params = (self.project_id, name, quantity, cost, threshold)
        
        if self.db.execute_query(query, params):
            self.material_name.clear()
            self.material_quantity.setValue(0.0)
            self.material_cost.setValue(0.0)
            self.material_threshold.setValue(0.0)
            QMessageBox.information(self, "Success", f"Material '{name}' added to inventory.")
            self.load_materials()

    def load_materials(self):
        query = "SELECT id, name, quantity, unit_cost, alert_threshold FROM materials WHERE project_id = ?"
        materials = self.db.fetch_data(query, (self.project_id,))
        
        self.inventory_table.setRowCount(len(materials))
        
        self.cons_material_combo.clear()
        
        for row, (mat_id, name, qty, cost, threshold) in enumerate(materials):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(mat_id)))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(name))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(f"{qty:.2f}"))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${cost:.2f}"))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(f"{threshold:.2f}"))
            
            self.cons_material_combo.addItem(f"{name} (ID: {mat_id})", (mat_id, qty, threshold))

    def log_consumption(self):
        material_data = self.cons_material_combo.currentData()
        quantity_used = self.cons_quantity.value()

        if material_data is None:
            QMessageBox.warning(self, "Selection Error", "Please select a material to log consumption.")
            return
            
        mat_id, current_qty, threshold = material_data
        
        new_qty = current_qty - quantity_used
        
        if new_qty < 0:
            QMessageBox.critical(self, "Stock Error", 
                                 f"Insufficient stock! Cannot use {quantity_used:.2f}. Current stock: {current_qty:.2f}.")
            return

        update_query = "UPDATE materials SET quantity = ? WHERE id = ?"
        
        if self.db.execute_query(update_query, (new_qty, mat_id)):
            
            if new_qty <= threshold:
                QMessageBox.warning(self, "LOW STOCK ALERT",
                                    f"WARNING: Material '{self.cons_material_combo.currentText()}' is below its alert threshold ({threshold:.2f}). Current stock: {new_qty:.2f}")
            else:
                QMessageBox.information(self, "Success", f"Consumption logged. New stock: {new_qty:.2f}.")
                
            self.load_materials()
        
    def setup_daily_log(self):
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.addWidget(QLabel("<h2>Daily Progress Log</h2>"))
        log_layout.addWidget(QLabel("<i>Daily entry form and log history table go here.</i>"))
        
        self.log_table = QTableWidget(5, 3)
        self.log_table.setHorizontalHeaderLabels(['Date', 'Description', 'Hours'])
        log_layout.addWidget(self.log_table) 

        self.tabs.addTab(log_tab, "Daily Log")

    def setup_reports(self):
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        report_layout.addWidget(QLabel("<h2>Status Report</h2>"))
        report_layout.addWidget(QLabel("<i>Summary labels and completion percentage display go here.</i>"))
        
        self.report_label = QLabel("Completion %: 0%")
        report_layout.addWidget(self.report_label) 

        self.tabs.addTab(report_tab, "Reports")

