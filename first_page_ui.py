import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFormLayout, QTableWidget,
    QMessageBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView # New import for selection mode

# Import the new Dashboard UI (assuming project_dashboard_ui.py is in the same folder)
from project_dashboard_ui import ProjectDashboard

# --- 1. Database Management Class ---
class DatabaseManager:
    """SQLite connection, table creation, and execution."""
    def __init__(self, db_name='project_manager.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            # Display a critical error if connection fails
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
            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Table creation failed: {e}")

    def execute_query(self, query, params=()):
        
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            # Report specific errors (like UNIQUE constraint violations)
            QMessageBox.critical(None, "Database Error", f"Operation failed: {e}")
            return False

    def fetch_data(self, query, params=()):
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

# --- 2. Main Window Class ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Construction Manager: Project Entry")
        self.setGeometry(100, 100, 1000, 600)
        self.dashboard_window = None # To hold a reference to the dashboard

        # Initialize the database manager
        self.db = DatabaseManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_project_selection_ui()
        
        # Load existing projects when the UI starts
        self.load_project_data()

    def setup_project_selection_ui(self):
        # --- Left Panel: Project Creation Form (30% Width) ---
        creation_widget = QWidget()
        creation_layout = QVBoxLayout(creation_widget)

        creation_layout.addWidget(QLabel("<h2>1. Create New Project</h2>"))

        # Form for inputs (Name, Dates)
        creation_form = QFormLayout()

        self.new_project_name = QLineEdit()
        self.new_project_start = QLineEdit("YYYY-MM-DD")
        self.new_project_end = QLineEdit("YYYY-MM-DD")

        creation_form.addRow("Project Name:", self.new_project_name)
        creation_form.addRow("Start Date:", self.new_project_start)
        creation_form.addRow("Est. End Date:", self.new_project_end)

        creation_layout.addLayout(creation_form)

        # Action Button
        create_btn = QPushButton("Create Project & Start")
        create_btn.setStyleSheet("""
            padding: 10px; 
            background-color: #38761d; 
            color: white; 
            font-weight: bold; 
            border: 1px solid #38761d;
            border-radius: 5px;
        """)
        
        # CONNECTING THE BUTTON TO THE NEW LOGIC
        create_btn.clicked.connect(self.create_project) 
        
        creation_layout.addWidget(create_btn)
        creation_layout.addStretch(1) # Pushes content to the top
        
        # --- Right Panel: Project Selection Table (70% Width) ---
        selection_widget = QWidget()
        selection_layout = QVBoxLayout(selection_widget)

        selection_layout.addWidget(QLabel("<h2>2. Select Existing Project</h2>"))
        selection_layout.addWidget(QLabel("<i>Double-click a row to open the project dashboard.</i>"))

        # Project List Table
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(4)
        self.project_table.setHorizontalHeaderLabels(['ID', 'Name', 'Start Date', 'Status'])
        self.project_table.setAlternatingRowColors(True)
        self.project_table.horizontalHeader().setStretchLastSection(True)
        self.project_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Select entire row
        self.project_table.setSelectionMode(QAbstractItemView.SingleSelection) # Only one row at a time
        selection_layout.addWidget(self.project_table)

        # Connect double-click event for quick opening
        self.project_table.doubleClicked.connect(self.open_project)

        # Selection Action
        self.select_btn = QPushButton("Open Selected Project")
        self.select_btn.setStyleSheet("""
            padding: 8px; 
            background-color: #0b5394; 
            color: white; 
            font-weight: bold; 
            border: 1px solid #0b5394;
            border-radius: 5px;
        """)
        # CONNECTING BUTTON TO NEW LOGIC
        self.select_btn.clicked.connect(self.open_project) 

        selection_layout.addWidget(self.select_btn)
        
        # --- Final Integration ---
        self.main_layout.addWidget(creation_widget, 30) # 30% width
        self.main_layout.addWidget(selection_widget, 70) # 70% width

    def create_project(self):
        
        name = self.new_project_name.text().strip()
        start = self.new_project_start.text().strip()
        end = self.new_project_end.text().strip()

        # Basic input validation
        if not name:
            QMessageBox.warning(self, "Input Error", "Project Name cannot be empty.")
            return

        # Prepare and execute the query
        query = "INSERT INTO projects (name, start_date, end_date) VALUES (?, ?, ?)"
        
        if self.db.execute_query(query, (name, start, end)):
            QMessageBox.information(self, "Success", f"Project '{name}' created successfully.")
            self.new_project_name.clear()
            self.load_project_data() # Refresh the table instantly

    def load_project_data(self):
        
       
        #Fetch from the database

        projects = self.db.fetch_data("SELECT id, name, start_date, status FROM projects ORDER BY id DESC")
        
        # 2. Update the table widget
        self.project_table.setRowCount(len(projects))
        
        for row, (proj_id, name, start_date, status) in enumerate(projects):
            # ID
            self.project_table.setItem(row, 0, QTableWidgetItem(str(proj_id)))
            # Name
            self.project_table.setItem(row, 1, QTableWidgetItem(name))
            # Start Date
            self.project_table.setItem(row, 2, QTableWidgetItem(start_date))
            # Status
            self.project_table.setItem(row, 3, QTableWidgetItem(status))

    def open_project(self):

        """opens the Project Dashboard"""

        selected_rows = self.project_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a project from the table to open.")
            return
        
        # Get the row index of the first selected row
        row_index = selected_rows[0].row()
        
        # Get the project ID (column 0) and Name (column 1) from the selected row
        project_id_item = self.project_table.item(row_index, 0)
        project_name_item = self.project_table.item(row_index, 1)
        
        if project_id_item and project_name_item:
            project_id = int(project_id_item.text())
            project_name = project_name_item.text()

            # Hide the current window
            self.hide()
            
            # Create and show the dashboard window
            self.dashboard_window = ProjectDashboard(project_id, project_name, self.db)
            
            # Connect the dashboard's close event to showing the main window again
            self.dashboard_window.finished.connect(self.show)
            
            self.dashboard_window.exec_()
        else:
            QMessageBox.critical(self, "Data Error", "Could not retrieve project ID and Name.")


if __name__ == '__main__':
    # Ensure sys.argv is passed correctly
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

