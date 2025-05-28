import sys
import os
import json
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QListWidget, QListWidgetItem,
                             QLineEdit, QTextEdit, QDateEdit, QDateTimeEdit,
                             QHBoxLayout, QMessageBox, QCheckBox, QDialog,
                             QDialogButtonBox, QFormLayout, QFileDialog, QTimeEdit,
                             QMenuBar, QMenu, QAction, QSystemTrayIcon)
from PyQt5.QtCore import Qt, QDate, QDateTime, QUrl, QFileInfo, QTimer, QTime
from PyQt5.QtGui import QColor, QPalette, QFont, QDesktopServices, QIcon, QPixmap
from PyQt5 import QtWidgets


class Task:
    def __init__(self, title, description, due_date, notifications=None, subtasks=None, attachments=None,
                 completed=False, skipped=False):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.notifications = notifications if notifications else []
        self.subtasks = subtasks if subtasks else []
        self.attachments = attachments if attachments else []
        self.completed = completed
        self.skipped = skipped
        self.notification_shown = False

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.toString(Qt.ISODate),
            'notifications': self.notifications,
            'subtasks': self.subtasks,
            'attachments': self.attachments,
            'completed': self.completed,
            'skipped': self.skipped,
            'notification_shown': self.notification_shown
        }

    @classmethod
    def from_dict(cls, data):
        due_date = QDate.fromString(data['due_date'], Qt.ISODate)
        task = cls(
            data['title'],
            data['description'],
            due_date,
            data.get('notifications', []),
            data.get('subtasks', []),
            data.get('attachments', []),
            data.get('completed', False),
            data.get('skipped', False)
        )
        task.notification_shown = data.get('notification_shown', False)
        return task


class NotificationManager:
    def __init__(self, window):
        self.window = window
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(60000)  # Проверка каждую минуту

    def check_notifications(self):
        now = QDateTime.currentDateTime()

        for task in self.window.tasks:
            if task.completed or task.skipped or task.notification_shown:
                continue

            for notification in task.notifications:
                try:
                    parts = notification.split()
                    if len(parts) >= 2:
                        date_str = ' '.join(parts[:2])
                        notify_time = QDateTime.fromString(date_str, "dd.MM.yyyy HH:mm")

                        if notify_time.isValid() and now >= notify_time:
                            self.show_notification(task, notification)
                            task.notification_shown = True
                            self.window.save_tasks()
                except Exception as e:
                    print(f"Ошибка обработки уведомления: {e}")

    def show_notification(self, task, notification_text):
        msg = QMessageBox(self.window)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Напоминание о задаче")
        msg.setText(f"Задача: {task.title}\n"
                    f"Срок: {task.due_date.toString('dd.MM.yyyy')}\n"
                    f"Напоминание: {notification_text}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Планировщик задач')
        self.setFixedSize(600, 600)

        # Меню с выходом
        menubar = QMenuBar(self)
        file_menu = menubar.addMenu('Файл')
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close_application)
        file_menu.addAction(exit_action)

        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #4a4a4a;
                font-size: 14px;
            }
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)

        self.title_label = QLabel('Добро пожаловать в планировщик задач')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 20px;
        """)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            font-size: 40px;
            color: #3b82f6;
            margin-bottom: 10px;
        """)
        self.icon_label.setText("📅")

        self.username = QLineEdit()
        self.username.setPlaceholderText('Введите имя пользователя')

        self.password = QLineEdit()
        self.password.setPlaceholderText('Введите пароль')
        self.password.setEchoMode(QLineEdit.Password)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText('Войти')
        button_box.button(QDialogButtonBox.Cancel).setText('Отмена')
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setMenuBar(menubar)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)

        form_layout = QFormLayout()
        form_layout.addRow('Имя пользователя:', self.username)
        form_layout.addRow('Пароль:', self.password)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(40, 20, 40, 20)

        layout.addLayout(form_layout)
        layout.addWidget(button_box, alignment=Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        self.setLayout(layout)

    def close_application(self):
        QApplication.quit()


class AttachmentItem(QListWidgetItem):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        file_info = QFileInfo(file_path)
        self.setText(file_info.fileName())
        self.setToolTip(file_path)

        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            self.setIcon(QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))
        else:
            self.setIcon(QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileLinkIcon))


class Window(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.current_user = username
        self.data_file = f"{username}_tasks.json"
        self.tasks = []

        self.load_tasks()

        if not self.tasks:
            self.tasks = [
                Task("Лабораторная работа", "Выполнить эксперименты", QDate.currentDate().addDays(3)),
                Task("Курсовая работа", "Написать главу 2", QDate.currentDate().addDays(7)),
                Task("Подготовка к экзамену", "Повторить лекции", QDate.currentDate().addDays(14))
            ]
            self.tasks[0].notifications = [
                f"{QDate.currentDate().addDays(2).toString('dd.MM.yyyy')} 09:00 - Начать за 2 дня"]
            self.tasks[0].subtasks = ["Подготовить оборудование"]
            self.save_tasks()

        self.initUI()
        self.setWindowTitle(f"Планировщик задач - {self.current_user}")

        self.notification_manager = NotificationManager(self)
        self.init_system_tray()

    def init_system_tray(self):
        """Инициализация системного трея"""
        self.tray_icon = QSystemTrayIcon(self)

        # Создаем иконку (можно заменить на свою)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.blue)
        self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.setToolTip("Планировщик задач")

        # Создаем меню для трея
        tray_menu = QMenu()

        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_normal)
        tray_menu.addAction(show_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Обработчик клика по иконке в трее
        self.tray_icon.activated.connect(self.tray_icon_clicked)

    def tray_icon_clicked(self, reason):
        """Обработка кликов по иконке в трее"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()

    def show_normal(self):
        """Восстановление окна из трея"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def initUI(self):
        self.setGeometry(300, 300, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
            }
            QTextEdit, QLineEdit, QDateEdit {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)

        # Главное меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')

        # Пункт меню "Выход"
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.quit_application)
        file_menu.addAction(exit_action)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Левая панель - список задач
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.show_task_details)
        self.left_layout.addWidget(self.task_list)

        self.btn_refresh = QPushButton("Обновить список")
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

        # Статус задачи
        status_layout = QHBoxLayout()
        self.completed_checkbox = QCheckBox("Выполнена")
        self.completed_checkbox.stateChanged.connect(self.update_task_status)
        status_layout.addWidget(self.completed_checkbox)

        self.skipped_checkbox = QCheckBox("Пропущена")
        self.skipped_checkbox.stateChanged.connect(self.update_task_status)
        status_layout.addWidget(self.skipped_checkbox)

        self.right_layout.addLayout(status_layout)

        # Вложения
        self.right_layout.addWidget(QLabel("Вложения:"))
        self.attachments_list = QListWidget()
        self.attachments_list.itemDoubleClicked.connect(self.open_attachment)
        self.right_layout.addWidget(self.attachments_list)

        attachment_buttons = QHBoxLayout()
        self.btn_add_attachment = QPushButton("Добавить вложение")
        self.btn_add_attachment.clicked.connect(self.add_attachment)
        attachment_buttons.addWidget(self.btn_add_attachment)

        self.btn_open_attachment = QPushButton("Открыть вложение")
        self.btn_open_attachment.clicked.connect(lambda: self.open_attachment(self.attachments_list.currentItem()))
        attachment_buttons.addWidget(self.btn_open_attachment)

        self.btn_remove_attachment = QPushButton("Удалить вложение")
        self.btn_remove_attachment.clicked.connect(self.remove_attachment)
        attachment_buttons.addWidget(self.btn_remove_attachment)

        self.right_layout.addLayout(attachment_buttons)

        # Подзадачи
        self.right_layout.addWidget(QLabel("Подзадачи:"))
        self.subtasks_list = QListWidget()
        self.right_layout.addWidget(self.subtasks_list)

        self.new_subtask_input = QLineEdit()
        self.new_subtask_input.setPlaceholderText("Новая подзадача")
        self.right_layout.addWidget(self.new_subtask_input)

        self.btn_add_subtask = QPushButton("Добавить подзадачу")
        self.btn_add_subtask.clicked.connect(self.add_subtask)
        self.right_layout.addWidget(self.btn_add_subtask)

        # Уведомления
        self.right_layout.addWidget(QLabel("Уведомления:"))
        self.notifications_list = QListWidget()
        self.right_layout.addWidget(self.notifications_list)

        # Поля для ввода даты и времени уведомления
        notification_layout = QHBoxLayout()

        self.notification_date = QDateEdit()
        self.notification_date.setCalendarPopup(True)
        self.notification_date.setDate(QDate.currentDate())
        notification_layout.addWidget(self.notification_date)

        self.notification_time = QTimeEdit()
        self.notification_time.setTime(QTime.currentTime())
        notification_layout.addWidget(self.notification_time)

        self.notification_text = QLineEdit()
        self.notification_text.setPlaceholderText("Текст уведомления")
        notification_layout.addWidget(self.notification_text)

        self.right_layout.addLayout(notification_layout)

        self.btn_add_notification = QPushButton("Добавить уведомление")
        self.btn_add_notification.clicked.connect(self.add_notification)
        self.right_layout.addWidget(self.btn_add_notification)

        # Кнопки управления
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_task)
        button_layout.addWidget(self.btn_save)

        self.btn_new_task = QPushButton("Новая задача")
        self.btn_new_task.clicked.connect(self.new_task)
        button_layout.addWidget(self.btn_new_task)

        self.btn_delete_task = QPushButton("Удалить задачу")
        self.btn_delete_task.clicked.connect(self.delete_task)
        button_layout.addWidget(self.btn_delete_task)

        self.btn_skip_task = QPushButton("Пропустить задачу")
        self.btn_skip_task.clicked.connect(self.skip_task)
        button_layout.addWidget(self.btn_skip_task)

        # Кнопка выхода
        self.btn_exit = QPushButton("Выход")
        self.btn_exit.clicked.connect(self.quit_application)
        button_layout.addWidget(self.btn_exit)

        self.right_layout.addLayout(button_layout)

        self.main_layout.addWidget(self.left_panel, 1)
        self.main_layout.addWidget(self.right_panel, 2)

        self.refresh_task_list()
        self.right_panel.setEnabled(False)

    def quit_application(self):
        """Корректный выход из приложения"""
        reply = QMessageBox.question(
            self, 'Подтверждение выхода',
            'Вы уверены, что хотите выйти? Все несохраненные данные будут потеряны.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.save_tasks()
            self.tray_icon.hide()  # Скрываем иконку в трее
            QApplication.quit()

    def closeEvent(self, event):
        """Обработчик события закрытия окна"""
        self.save_tasks()
        # Можно выбрать - сворачивать в трей или закрывать
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Закрыть приложение или свернуть в трей?',
            QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Close:
            self.tray_icon.hide()
            event.accept()
        else:
            self.hide()
            event.ignore()

    # ... (остальные методы класса Window остаются без изменений)

    def load_tasks(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in data]
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить задачи: {str(e)}")

    def save_tasks(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([task.to_dict() for task in self.tasks], f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить задачи: {str(e)}")

    def refresh_task_list(self):
        self.task_list.clear()
        today = QDate.currentDate()

        for task in self.tasks:
            status = ""
            if task.completed:
                status = " (Выполнена)"
            elif task.skipped:
                status = " (Пропущена)"

            item = QListWidgetItem(f"{task.title} - {task.due_date.toString('dd.MM.yyyy')}{status}")
            item.setData(Qt.UserRole, task)

            if task.completed:
                item.setBackground(QColor(220, 252, 231))
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            elif task.skipped:
                item.setBackground(QColor(253, 230, 138))
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
            elif task.due_date < today:
                item.setBackground(QColor(254, 226, 226))

            self.task_list.addItem(item)

    def show_task_details(self, item):
        self.current_task = item.data(Qt.UserRole)
        self.right_panel.setEnabled(True)

        self.task_title.setText(self.current_task.title)
        self.task_description.setText(self.current_task.description)
        self.due_date_edit.setDate(self.current_task.due_date)

        self.completed_checkbox.blockSignals(True)
        self.skipped_checkbox.blockSignals(True)

        self.completed_checkbox.setChecked(self.current_task.completed)
        self.skipped_checkbox.setChecked(self.current_task.skipped)

        self.completed_checkbox.blockSignals(False)
        self.skipped_checkbox.blockSignals(False)

        self.subtasks_list.clear()
        for subtask in self.current_task.subtasks:
            self.subtasks_list.addItem(subtask)

        self.notifications_list.clear()
        for notification in self.current_task.notifications:
            self.notifications_list.addItem(notification)

        self.attachments_list.clear()
        for attachment in self.current_task.attachments:
            item = AttachmentItem(attachment)
            self.attachments_list.addItem(item)

    def update_task_status(self):
        if not hasattr(self, 'current_task'):
            return

        if self.completed_checkbox.isChecked():
            self.current_task.completed = True
            self.current_task.skipped = False
            self.skipped_checkbox.setChecked(False)
        elif self.skipped_checkbox.isChecked():
            self.current_task.skipped = True
            self.current_task.completed = False
            self.completed_checkbox.setChecked(False)
        else:
            self.current_task.completed = False
            self.current_task.skipped = False

        self.save_tasks()
        self.refresh_task_list()

    def save_task(self):
        if not hasattr(self, 'current_task'):
            return

        self.current_task.title = self.task_title.text()
        self.current_task.description = self.task_description.toPlainText()
        self.current_task.due_date = self.due_date_edit.date()

        self.save_tasks()
        QMessageBox.information(self, "Сохранено", "Изменения сохранены")
        self.refresh_task_list()

    def new_task(self):
        new_task = Task("Новая задача", "", QDate.currentDate().addDays(1))
        self.tasks.append(new_task)
        self.save_tasks()

        self.refresh_task_list()
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item.data(Qt.UserRole) == new_task:
                self.task_list.setCurrentItem(item)
                self.show_task_details(item)
                break

    def delete_task(self):
        if not hasattr(self, 'current_task'):
            return

        reply = QMessageBox.question(
            self, 'Удаление задачи',
            f'Вы уверены, что хотите удалить задачу "{self.current_task.title}"?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tasks.remove(self.current_task)
            self.save_tasks()
            self.refresh_task_list()
            self.right_panel.setEnabled(False)

    def skip_task(self):
        if not hasattr(self, 'current_task'):
            return

        self.current_task.skipped = True
        self.current_task.completed = False
        self.skipped_checkbox.setChecked(True)
        self.completed_checkbox.setChecked(False)
        self.save_tasks()
        self.refresh_task_list()

    def add_subtask(self):
        if not hasattr(self, 'current_task'):
            return

        subtask = self.new_subtask_input.text()
        if subtask:
            self.current_task.subtasks.append(subtask)
            self.subtasks_list.addItem(subtask)
            self.new_subtask_input.clear()
            self.save_tasks()

    def add_notification(self):
        if not hasattr(self, 'current_task'):
            return

        date = self.notification_date.date().toString("dd.MM.yyyy")
        time = self.notification_time.time().toString("HH:mm")
        text = self.notification_text.text()

        if text:
            notification = f"{date} {time} - {text}"
            self.current_task.notifications.append(notification)
            self.notifications_list.addItem(notification)
            self.notification_text.clear()
            self.current_task.notification_shown = False
            self.save_tasks()

    def add_attachment(self):
        if not hasattr(self, 'current_task'):
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "",
            "Все файлы (*);;Изображения (*.png *.jpg *.jpeg *.gif *.bmp);;Документы (*.pdf *.doc *.docx *.txt)"
        )

        if file_path:
            self.current_task.attachments.append(file_path)
            item = AttachmentItem(file_path)
            self.attachments_list.addItem(item)
            self.save_tasks()

    def remove_attachment(self):
        if not hasattr(self, 'current_task') or not self.attachments_list.currentItem():
            return

        current_row = self.attachments_list.currentRow()
        if 0 <= current_row < len(self.current_task.attachments):
            self.current_task.attachments.pop(current_row)
            self.attachments_list.takeItem(current_row)
            self.save_tasks()

    def open_attachment(self, item):
        if item and hasattr(item, 'file_path'):
            file_path = item.file_path
            if os.path.exists(file_path):
                url = QUrl.fromLocalFile(file_path)
                if not QDesktopServices.openUrl(url):
                    QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {file_path}")
            else:
                QMessageBox.warning(self, "Ошибка", f"Файл не найден: {file_path}")


def application():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        if login.username.text():
            window = Window(login.username.text())
            window.show()
            sys.exit(app.exec_())
        else:
            QMessageBox.warning(None, 'Ошибка', 'Введите имя пользователя')
            sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    application()
