import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QListWidget, QListWidgetItem,
                             QLineEdit, QTextEdit, QDateEdit, QDateTimeEdit,
                             QHBoxLayout, QMessageBox, QCheckBox)
import PyQt5.QtCore
from PyQt5 import QtWidgets


class Task:
    def __init__(self, title, description, due_date, notifications=None, subtasks=None):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.notifications = notifications if notifications else []
        self.subtasks = subtasks if subtasks else []
        self.completed = False


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        # Инициализация тестовых данных
        self.current_user = "User1"
        self.tasks = [
            Task("Задача 1", "Описание задачи 1", PyQt5.QtCore.QDate.currentDate().addDays(1),
                 ["Уведомление 1"], ["Подзадача 1"]),
            Task("Задача 2", "Описание задачи 2", PyQt5.QtCore.QDate.currentDate(),
                 ["Уведомление 2", "Уведомление 3"], ["Подзадача 2", "Подзадача 3"]),
            Task("Задача 3", "Описание задачи 3", PyQt5.QtCore.QDate.currentDate().addDays(-1))
        ]

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Task Manager")
        self.setGeometry(300, 300, 800, 600)

        # Главный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Левая панель - список задач
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.show_task_details)
        self.left_layout.addWidget(self.task_list)

        self.btn_refresh = QPushButton("Обновить список задач")
        self.btn_refresh.clicked.connect(self.refresh_task_list)
        self.left_layout.addWidget(self.btn_refresh)

        # Правая панель - детали задачи
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Название задачи")
        self.right_layout.addWidget(self.task_title)

        self.task_description = QTextEdit()
        self.task_description.setPlaceholderText("Описание задачи")
        self.right_layout.addWidget(self.task_description)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(PyQt5.QtCore.QDate.currentDate())
        self.right_layout.addWidget(QLabel("Срок выполнения:"))
        self.right_layout.addWidget(self.due_date_edit)

        # Чекбокс для статуса задачи
        self.completed_checkbox = QCheckBox("Задача выполнена")
        self.right_layout.addWidget(self.completed_checkbox)

        # Список подзадач
        self.right_layout.addWidget(QLabel("Подзадачи:"))
        self.subtasks_list = QListWidget()
        self.right_layout.addWidget(self.subtasks_list)

        # Поля для добавления новой подзадачи
        self.new_subtask_input = QLineEdit()
        self.new_subtask_input.setPlaceholderText("Новая подзадача")
        self.right_layout.addWidget(self.new_subtask_input)

        self.btn_add_subtask = QPushButton("Добавить подзадачу")
        self.btn_add_subtask.clicked.connect(self.add_subtask)
        self.right_layout.addWidget(self.btn_add_subtask)

        # Список уведомлений
        self.right_layout.addWidget(QLabel("Уведомления:"))
        self.notifications_list = QListWidget()
        self.right_layout.addWidget(self.notifications_list)

        # Поля для добавления нового уведомления
        self.new_notification_input = QLineEdit()
        self.new_notification_input.setPlaceholderText("Новое уведомление")
        self.right_layout.addWidget(self.new_notification_input)

        self.btn_add_notification = QPushButton("Добавить уведомление")
        self.btn_add_notification.clicked.connect(self.add_notification)
        self.right_layout.addWidget(self.btn_add_notification)

        # Кнопки сохранения и создания новой задачи
        self.btn_save = QPushButton("Сохранить изменения")
        self.btn_save.clicked.connect(self.save_task)
        self.right_layout.addWidget(self.btn_save)

        self.btn_new_task = QPushButton("Новая задача")
        self.btn_new_task.clicked.connect(self.new_task)
        self.right_layout.addWidget(self.btn_new_task)

        # Добавляем панели в главный layout
        self.main_layout.addWidget(self.left_panel, 1)
        self.main_layout.addWidget(self.right_panel, 2)

        # Обновляем список задач
        self.refresh_task_list()

        # Скрываем детали до выбора задачи
        self.right_panel.setEnabled(False)

    def refresh_task_list(self):
        """Обновляет список задач для текущего пользователя"""
        self.task_list.clear()
        today = PyQt5.QtCore.QDate.currentDate()

        for task in self.tasks:
            if task.due_date >= today:  # Показываем только задачи на сегодня и позже
                item = QListWidgetItem(f"{task.title} - {task.due_date.toString('dd.MM.yyyy')}")
                item.setData(PyQt5.QtCore.Qt.UserRole, task)
                if task.completed:
                    item.setBackground(PyQt5.QtCore.Qt.green)
                self.task_list.addItem(item)

    def show_task_details(self, item):
        """Показывает детали выбранной задачи"""
        self.current_task = item.data(PyQt5.QtCore.Qt.UserRole)
        self.right_panel.setEnabled(True)

        self.task_title.setText(self.current_task.title)
        self.task_description.setText(self.current_task.description)
        self.due_date_edit.setDate(self.current_task.due_date)
        self.completed_checkbox.setChecked(self.current_task.completed)

        # Обновляем список подзадач
        self.subtasks_list.clear()
        for subtask in self.current_task.subtasks:
            self.subtasks_list.addItem(subtask)

        # Обновляем список уведомлений
        self.notifications_list.clear()
        for notification in self.current_task.notifications:
            self.notifications_list.addItem(notification)

    def save_task(self):
        """Сохраняет изменения в задаче"""
        if not hasattr(self, 'current_task'):
            return

        self.current_task.title = self.task_title.text()
        self.current_task.description = self.task_description.toPlainText()
        self.current_task.due_date = self.due_date_edit.date()
        self.current_task.completed = self.completed_checkbox.isChecked()

        QMessageBox.information(self, "Сохранено", "Изменения сохранены")
        self.refresh_task_list()

    def new_task(self):
        """Создает новую задачу"""
        new_task = Task("Новая задача", "", PyQt5.QtCore.QDate.currentDate().addDays(1))
        self.tasks.append(new_task)

        # Выбираем новую задачу в списке
        self.refresh_task_list()
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(PyQt5.QtCore.Qt.UserRole) == new_task:
                self.task_list.setCurrentItem(item)
                self.show_task_details(item)
                break

    def add_subtask(self):
        """Добавляет подзадачу к текущей задаче"""
        if not hasattr(self, 'current_task'):
            return

        subtask = self.new_subtask_input.text()
        if subtask:
            self.current_task.subtasks.append(subtask)
            self.subtasks_list.addItem(subtask)
            self.new_subtask_input.clear()

    def add_notification(self):
        """Добавляет уведомление к текущей задаче"""
        if not hasattr(self, 'current_task'):
            return

        notification = self.new_notification_input.text()
        if notification:
            self.current_task.notifications.append(notification)
            self.notifications_list.addItem(notification)
            self.new_notification_input.clear()


def application():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


application()
