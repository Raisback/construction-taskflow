import sys
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTableWidget, QPushButton, QFormLayout, QLineEdit
)

class ProjectDashboard(QDialog):
    
    #The main management interface for an individual project.
    
    def __init__(self, project_id, project_name, db_manager):
        super().__init__()
        self.project_id = project_id
        self.project_name = project_name
        self.db = db_manager
        
        self.setWindowTitle(f"Project Dashboard: {project_name}")
        self.setGeometry(150, 150, 1200, 800) 
        self.main_layout = QVBoxLayout(self)
        
        

