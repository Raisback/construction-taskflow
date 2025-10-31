import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFormLayout, QTableWidget,
    QMessageBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView 


from project_dashboard_ui import ProjectDashboard

class DatabaseManager:
    def __init__(self, db_name='project_manager.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Connection failed: {e}")
            sys.exit(1)

    def create_tables(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'Active'
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'Not Started',
                    prerequisite_task_id INTEGER,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity REAL DEFAULT 0,
                    unit_cost REAL DEFAULT 0.0,
                    alert_threshold REAL DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_log (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    log_date TEXT NOT NULL,
                    description TEXT,
                    hours_worked REAL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Table creation failed: {e}")

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Operation failed: {e}")
            return False

    def fetch_data(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Construction Manager: Project Entry")
        self.setGeometry(100, 100, 1000, 600)
        self.dashboard_window = None 

        self.db = DatabaseManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_project_selection_ui()
        
        self.load_project_data()

    def setup_project_selection_ui(self):
        creation_widget = QWidget()
        creation_layout = QVBoxLayout(creation_widget)

        creation_layout.addWidget(QLabel("<h2>1. Create New Project</h2>"))

        creation_form = QFormLayout()

        self.new_project_name = QLineEdit()
        self.new_project_start = QLineEdit("YYYY-MM-DD")
        self.new_project_end = QLineEdit("YYYY-MM-DD")

        creation_form.addRow("Project Name:", self.new_project_name)
        creation_form.addRow("Start Date:", self.new_project_start)
        creation_form.addRow("Est. End Date:", self.new_project_end)

        creation_layout.addLayout(creation_form)

        create_btn = QPushButton("Create Project & Start")
        create_btn.setStyleSheet("""
            padding: 10px; 
            background-color: #38761d; 
            color: white; 
            font-weight: bold; 
            border: 1px solid #38761d;
            border-radius: 5px;
        """)
        
        create_btn.clicked.connect(self.create_project) 
        
        creation_layout.addWidget(create_btn)
        creation_layout.addStretch(1) 
        
        selection_widget = QWidget()
        selection_layout = QVBoxLayout(selection_widget)

        selection_layout.addWidget(QLabel("<h2>2. Select Existing Project</h2>"))
        selection_layout.addWidget(QLabel("<i>Double-click a row to open the project dashboard.</i>"))

        self.project_table = QTableWidget()
        self.project_table.setColumnCount(4)
        self.project_table.setHorizontalHeaderLabels(['ID', 'Name', 'Start Date', 'Status'])
        self.project_table.setAlternatingRowColors(True)
        self.project_table.horizontalHeader().setStretchLastSection(True)
        self.project_table.setSelectionBehavior(QAbstractItemView.SelectRows) 
        self.project_table.setSelectionMode(QAbstractItemView.SingleSelection) 
        selection_layout.addWidget(self.project_table)

        self.project_table.doubleClicked.connect(self.open_project)

        # --- Button Group for Selection and Deletion ---
        button_group = QHBoxLayout()

        self.select_btn = QPushButton("Open Selected Project")
        self.select_btn.setStyleSheet("""
            padding: 8px; 
            background-color: #0b5394; 
            color: white; 
            font-weight: bold; 
            border: 1px solid #0b5394;
            border-radius: 5px;
        """)
        self.select_btn.clicked.connect(self.open_project) 
        
        self.delete_btn = QPushButton("Delete Selected Project")
        self.delete_btn.setStyleSheet("""
            padding: 8px; 
            background-color: #cc0000; 
            color: white; 
            font-weight: bold; 
            border: 1px solid #cc0000;
            border-radius: 5px;
        """)
        self.delete_btn.clicked.connect(self.delete_project)

        button_group.addWidget(self.select_btn)
        button_group.addWidget(self.delete_btn)

        selection_layout.addLayout(button_group)
        # --- End Button Group ---
        
        self.main_layout.addWidget(creation_widget, 30) 
        self.main_layout.addWidget(selection_widget, 70) 

    def create_project(self):
        name = self.new_project_name.text().strip()
        start = self.new_project_start.text().strip()
        end = self.new_project_end.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Project Name cannot be empty.")
            return

        query = "INSERT INTO projects (name, start_date, end_date) VALUES (?, ?, ?)"
        
        if self.db.execute_query(query, (name, start, end)):
            QMessageBox.information(self, "Success", f"Project '{name}' created successfully.")
            self.new_project_name.clear()
            self.load_project_data() 

    def delete_project(self):
        selected_rows = self.project_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a project to delete.")
            return
        
        row_index = selected_rows[0].row()
        project_id_item = self.project_table.item(row_index, 0)
        project_name_item = self.project_table.item(row_index, 1)
        
        if not project_id_item or not project_name_item:
            QMessageBox.critical(self, "Data Error", "Could not retrieve project ID or Name.")
            return
            
        project_id = int(project_id_item.text())
        project_name = project_name_item.text()

        # Confirmation Dialog (Required)
        reply = QMessageBox.question(self, 'Confirm Deletion', 
            f"Are you sure you want to permanently delete project '{project_name}' (ID: {project_id}) and ALL its associated tasks, materials, and logs? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        # Perform cascading deletion to maintain database integrity
        
        # 1. Delete tasks
        self.db.execute_query("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        # 2. Delete materials
        self.db.execute_query("DELETE FROM materials WHERE project_id = ?", (project_id,))
        # 3. Delete daily_log
        self.db.execute_query("DELETE FROM daily_log WHERE project_id = ?", (project_id,))
        
        # 4. Delete project itself
        if self.db.execute_query("DELETE FROM projects WHERE id = ?", (project_id,)):
            QMessageBox.information(self, "Success", f"Project '{project_name}' and all related data have been permanently deleted.")
            self.load_project_data()
        else:
            QMessageBox.critical(self, "Error", f"Failed to delete project '{project_name}'. Please check the console for database errors.")

    def load_project_data(self):
        projects = self.db.fetch_data("SELECT id, name, start_date, status FROM projects ORDER BY id DESC")
        
        self.project_table.setRowCount(len(projects))
        
        for row, (proj_id, name, start_date, status) in enumerate(projects):
            self.project_table.setItem(row, 0, QTableWidgetItem(str(proj_id)))
            self.project_table.setItem(row, 1, QTableWidgetItem(name))
            self.project_table.setItem(row, 2, QTableWidgetItem(start_date))
            self.project_table.setItem(row, 3, QTableWidgetItem(status))

    def open_project(self):
        selected_rows = self.project_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a project from the table to open.")
            return
        
        row_index = selected_rows[0].row()
        
        project_id_item = self.project_table.item(row_index, 0)
        project_name_item = self.project_table.item(row_index, 1)
        
        if project_id_item and project_name_item:
            project_id = int(project_id_item.text())
            project_name = project_name_item.text()

            self.hide()
            
            self.dashboard_window = ProjectDashboard(project_id, project_name, self.db)
            
            self.dashboard_window.finished.connect(self.show)
            
            self.dashboard_window.exec_()
        else:
            QMessageBox.critical(self, "Data Error", "Could not retrieve project ID and Name.")


if __name__ == '__main__':
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

