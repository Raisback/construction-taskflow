import sys
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QPushButton, QFormLayout, QLineEdit
)

class ProjectDashboard(QDialog):

    def __init__(self, project_id, project_name, db_manager):
        super().__init__()
        self.project_id = project_id
        self.project_name = project_name
        self.db = db_manager
        
        self.setWindowTitle(f"Project Dashboard: {project_name}")
        self.setGeometry(150, 150, 1200, 800) # Larger window for detailed management

        self.main_layout = QVBoxLayout(self)
        
        # Display the selected project name prominently
        self.title_label = QLabel(f"<h1>Project: {project_name} (ID: {project_id})</h1>")
        self.main_layout.addWidget(self.title_label)

        # Initialize the Tab Widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Setup the four main management tabs
        self.setup_task_management()
        self.setup_resource_inventory()
        self.setup_daily_log()
        self.setup_reports()

    def setup_task_management(self):
        
        task_tab = QWidget()
        # The actual layout for Task Management will go here
        task_layout = QVBoxLayout(task_tab)
        task_layout.addWidget(QLabel("<h2>Task Management (FR1.x)</h2>"))
        task_layout.addWidget(QLabel("<i>Task list and Dependency Controls go here.</i>"))
        
        # Placeholder for task table
        self.task_table = QTableWidget(5, 4)
        self.task_table.setHorizontalHeaderLabels(['ID', 'Name', 'Status', 'Parent ID'])
        task_layout.addWidget(self.task_table)

        self.tabs.addTab(task_tab, "Tasks & Dependencies")

    def setup_resource_inventory(self):
        
        resource_tab = QWidget()
        # The actual layout for Inventory will go here
        resource_layout = QVBoxLayout(resource_tab)
        resource_layout.addWidget(QLabel("<h2>Resource Inventory </h2>"))
        resource_layout.addWidget(QLabel("<i>Inventory Table, Consumption Form, and Alert System go here.</i>"))
        
        # Placeholder for inventory table
        self.inventory_table = QTableWidget(5, 5)
        self.inventory_table.setHorizontalHeaderLabels(['ID', 'Name', 'Qty', 'Cost', 'Threshold'])
        resource_layout.addWidget(self.inventory_table) 

        self.tabs.addTab(resource_tab, "Resources & Stock")

    def setup_daily_log(self):
        
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.addWidget(QLabel("<h2>Daily Progress Log </h2>"))
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
