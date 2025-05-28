import sys
import json
import os
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QListWidget, QListWidgetItem,
                             QLineEdit, QTextEdit, QDateEdit, QDateTimeEdit,
                             QHBoxLayout, QMessageBox, QCheckBox, QDialog,
                             QDialogButtonBox, QFormLayout, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5 import QtWidgets


class Task:
    def __init__(self, title, description, due_date, notifications=None, subtasks=None, attachments=None,
                 completed=False):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.notifications = notifications if notifications else []
        self.subtasks = subtasks if subtasks else []
        self.attachments = attachments if attachments else []
        self.completed = completed

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.toString(Qt.ISODate),
            'notifications': self.notifications,
            'subtasks': self.subtasks,
            'attachments': self.attachments,
            'completed': self.completed
        }

    @classmethod
    def from_dict(cls, data):
        due_date = QDate.fromString(data['due_date'], Qt.ISODate)
        return cls(
            data['title'],
            data['description'],
            due_date,
            data['notifications'],
            data['subtasks'],
            data['attachments'],
            data['completed']
        )


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Логин:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_credentials(self):
        return self.username_input.text(), self.password_input.text()


class Window(QMainWindow):
    def __init__(self, username):
        super(Window, self).__init__()
        self.current_user = username
        self.data_file = f"{username}_tasks.json"
        self.tasks = self.load_tasks()

        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Task Manager - {self.current_user}")
        self.setGeometry(300, 300, 900, 700)

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
        self.due_date_edit.setDate(QDate.currentDate())
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

        # Список вложений
        self.right_layout.addWidget(QLabel("Вложения:"))
        self.attachments_list = QListWidget()
        self.right_layout.addWidget(self.attachments_list)

        # Кнопка для добавления вложений
        self.btn_add_attachment = QPushButton("Добавить файл")
        self.btn_add_attachment.clicked.connect(self.add_attachment)
        self.right_layout.addWidget(self.btn_add_attachment)

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

    def load_tasks(self):
        """Загружает задачи из файла или создаёт первую задачу при первом запуске"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Task.from_dict(task_data) for task_data in data]

        # Если файла нет - создаём первую задачу
        first_task = Task(
            title="Моя первая задача",
            description="Это пример задачи. Можете отредактировать или удалить её",
            due_date=QDate.currentDate().addDays(3),
            notifications=["Пример уведомления"],
            subtasks=["Подзадача 1", "Подзадача 2"]
        )

        # Сохраняем в файл
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump([first_task.to_dict()], f, ensure_ascii=False, indent=2)

        return [first_task]

    def save_tasks(self):
        """Сохраняет задачи в файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            tasks_data = [task.to_dict() for task in self.tasks]
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

    def refresh_task_list(self):
        """Обновляет список задач для текущего пользователя"""
        self.task_list.clear()
        today = QDate.currentDate()

        for task in self.tasks:
            item = QListWidgetItem(f"{task.title} - {task.due_date.toString('dd.MM.yyyy')}")
            item.setData(Qt.UserRole, task)

            if task.completed:
                item.setBackground(Qt.green)
            elif task.due_date < today:
                item.setBackground(Qt.red)

            self.task_list.addItem(item)

    def show_task_details(self, item):
        """Показывает детали выбранной задачи"""
        self.current_task = item.data(Qt.UserRole)
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

        # Обновляем список вложений
        self.attachments_list.clear()
        for attachment in self.current_task.attachments:
            self.attachments_list.addItem(attachment)

    def save_task(self):
        """Сохраняет изменения в задаче"""
        if not hasattr(self, 'current_task'):
            return

        self.current_task.title = self.task_title.text()
        self.current_task.description = self.task_description.toPlainText()
        self.current_task.due_date = self.due_date_edit.date()
        self.current_task.completed = self.completed_checkbox.isChecked()

        self.save_tasks()
        QMessageBox.information(self, "Сохранено", "Изменения сохранены")
        self.refresh_task_list()

    def new_task(self):
        """Создает новую задачу"""
        new_task = Task("Новая задача", "", QDate.currentDate().addDays(1))
        self.tasks.append(new_task)
        self.save_tasks()

        # Выбираем новую задачу в списке
        self.refresh_task_list()
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == new_task:
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
            self.save_tasks()

    def add_notification(self):
        """Добавляет уведомление к текущей задаче"""
        if not hasattr(self, 'current_task'):
            return

        notification = self.new_notification_input.text()
        if notification:
            self.current_task.notifications.append(notification)
            self.notifications_list.addItem(notification)
            self.new_notification_input.clear()
            self.save_tasks()

    def add_attachment(self):
        """Добавляет вложение к текущей задаче"""
        if not hasattr(self, 'current_task'):
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if file_path:
            file_name = os.path.basename(file_path)
            self.current_task.attachments.append(file_name)
            self.attachments_list.addItem(file_name)

            # Сохраняем файл в папку с данными пользователя
            user_data_dir = f"{self.current_user}_attachments"
            os.makedirs(user_data_dir, exist_ok=True)
            dest_path = os.path.join(user_data_dir, file_name)

            if not os.path.exists(dest_path):
                with open(file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())

            self.save_tasks()

    def closeEvent(self, event):
        """Сохраняет задачи при закрытии приложения"""
        self.save_tasks()
        event.accept()


def application():
    app = QApplication(sys.argv)

    # Авторизация
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        username, password = login_dialog.get_credentials()

        # Проверка логина и пароля
        if username == "bka" and password == "123":
            window = Window(username)
            window.show()
            sys.exit(app.exec_())
        else:
            QMessageBox.warning(None, "Ошибка", "Неверный логин или пароль")
            sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    application()
