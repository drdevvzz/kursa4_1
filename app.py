from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
import sys

class Window(QMainWindow):
    def __init__(self):  #конструктор
        super(Window, self).__init__()  #вызывает конструктор из родительского класса

        self.setWindowTitle("Test")
        self.setGeometry(300, 300, 550, 300)  # первые две-смещение относительно левого верхнего угла?????. вторые две-размеры окна

        self.new_text = QLabel(self)

        self.main_text = QtWidgets.QLabel(self)  # надпись
        self.main_text.setText("Я тут все стер")
        self.main_text.move(240, 30)
        self.new_text.adjustSize()

        self.button = QtWidgets.QPushButton(self)  # кнопка
        self.button.move(180, 150)
        self.button.setText("Put on me")
        self.button.setFixedWidth(200)
        self.button.clicked.connect(self.add_label)



    def add_label(self):
        self.new_text.setText("Кнопка была нажата")
        self.new_text.move(220, 70)
        self.new_text.adjustSize()

def application():
    app = QApplication(sys.argv) #класс
    window = Window() #класс

    window.show() #показываем само окно
    sys.exit(app.exec()) #чтобы программа закрывалась корректно

application()

