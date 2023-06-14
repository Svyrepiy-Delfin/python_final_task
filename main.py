import sys

from PyQt5.QtGui import QColor, QPixmap, QIcon, QResizeEvent
from PyQt5.QtMultimedia import QCameraInfo, QCamera, QCameraFocus, QCameraImageCapture
from PyQt5 import uic
from PyQt5.QtMultimediaWidgets import QCameraViewfinder
from PyQt5.QtWidgets import QMainWindow, QApplication, QErrorMessage, QVBoxLayout, QFileDialog, QColorDialog
import Canvas
from PyQt5.QtCore import Qt
import sqlite3
from random import randrange
import Dialogs


# Основной класс - CameraMainWindow, его мы и запускаем при старте
class CameraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('MainWin.ui', self)
        self.setWindowTitle('CamPaint')
        self.setWindowIcon(QIcon('main_icon.ico'))
        self.setCentralWidget(self.tabWidget)
        # Загружаем камеру, холст, sql файл и задаем цвета кнопок
        self.load_cam()
        self.load_painter()
        self.load_sql()
        self.load_colors()

    def load_cam(self):
        self.cam_page.setLayout(self.cam_page_lay)
        self.error_cam.hide()
        self.camera = QCameraInfo.defaultCamera()
        # Проверяем, что камера сущетсвует
        # Если нет, то переключаемся на вторую вкладку
        if self.camera.isNull():
            dialog = QErrorMessage()
            dialog.setWindowTitle('Warning')
            dialog.showMessage('Not enough cameras, the app will only be available in drawing mode')
            dialog.exec()
            self.error_cam.show()
            self.cam_page.setEnabled(False)
            self.tabWidget.setCurrentIndex(1)
        # Если да, то на первую
        else:
            self.tabWidget.setCurrentIndex(0)
            self.camera = QCamera(self.camera)
            self.view_cam = QCameraViewfinder(self)
            self.view_cam.setMediaObject(self.camera)
            self.view_cam.setAutoFillBackground(True)
            self.camera.setViewfinder(self.view_cam)
            self.box_lay = QVBoxLayout(self)
            self.box_lay.addWidget(self.view_cam)
            self.scrolling.setLayout(self.box_lay)
            # Запускаем камеру
            self.camera.start()
            # Подвязываем кнопку к слоту со снимком
            self.bt_cam.clicked.connect(self.make_ph)
            # Можно зумить фотографию
            #self.zoom.valueChanged.connect(self.zoom_pict)

    def make_ph(self):
        self.camera.setCaptureMode(QCamera.CaptureStillImage)
        self.capt = QCameraImageCapture(self.camera)
        # Останавливаем съемку
        self.camera.searchAndLock()
        # Вызываем диалог и иохранением файла
        dial = QFileDialog.getSaveFileName(self, 'Save file', '', 'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[
            0]
        if dial:
            self.capt.capture(dial)
            self.camera.unlock()

    def zoom_pict(self, value):
        # Вычисляем зум камеры по функции zoom=1.0 + value * 3 / 99
        # 1.0 - обязательный параметр
        QCameraFocus.zoomTo(self.camera.focus(), 1.0 + value * 3 / 99)

    def load_painter(self):
        # Загружаем холст
        self.paint_page.setLayout(self.paint_page_lay)
        # Текущий цвет - черный, ширина кисти - 10
        self.now_col = QColor(0, 0, 0)
        self.now_width = 10
        self.point_width.setValue(10)
        # Подвязываем кнопку с изменением ширины кисти к соответсвующему слоту
        self.point_width.valueChanged.connect(self.change_width)
        # Создаем холст как экземпляр класса Canvas из доп.модуля Canvas
        self.canvas = Canvas.Canvas(self.main_paint_widg)
        self.canvas.move(1, 1)
        self.canvas.resize(self.main_paint_widg.width() - 1, self.main_paint_widg.height() - 1)
        # Устанавливаем границы рамки
        self.border_lab.setStyleSheet(
            'border-style: solid; border-width: 2px; border-color: black;')
        self.canvas.setStyleSheet('background-color: white;')
        # Устанавливаем сильный фокус для перехвата всех событий
        # клавиатуры и мыши
        self.setFocusPolicy(Qt.StrongFocus)
        # Подвязываем действия из меню к слотам
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_as.triggered.connect(self.save_as_file)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionReference.triggered.connect(self.open_reference)
        # и кнопку очистки холста, а также задания цвета кисти
        self.bt_clear.clicked.connect(self.clear_canvas)
        self.bt_set_color.clicked.connect(self.set_color_with_bt)
        # Имя файла изначально не задано, файл не сохранен
        self.file_name = ''
        self.saved = False
        self.resizeEvent(QResizeEvent(self.size(), self.size()))

    def change_width(self, value):
        self.now_width = value

    def keyPressEvent(self, event):
        # Обрабатываем события клавитатуры
        if int(event.modifiers()) == Qt.CTRL and event.key() == Qt.Key_Z:
            # Функция 'назад', удаляем все объекты, которые нарисовали
            if self.canvas.obj:
                del self.canvas.obj[-1]
                self.canvas.update()
        elif int(event.modifiers()) == Qt.CTRL and event.key() == Qt.Key_S:
            # Функция 'сохранить', сохраняем файл, если есть изменения
            if self.canvas.obj:
                self.save_file()
        elif int(event.modifiers()) == Qt.CTRL and event.key() == Qt.Key_O:
            # Функция 'открыть', открываем файл
            self.open_file()
        elif int(event.modifiers()) == Qt.CTRL and event.key() == Qt.Key_H:
            # Функция 'справка', открываем справку
            self.open_reference()

    def resizeEvent(self, event):
        # При изменении размеров окна, устанавливаем соответствующие размеры холста и рамки
        self.canvas.resize(self.main_paint_widg.width() - 1, self.main_paint_widg.height() - 1)
        self.border_lab.resize(self.main_paint_widg.width(), self.main_paint_widg.height())

    def save_as_file(self):
        # Сохранение файла как
        dial = \
            QFileDialog.getSaveFileName(self, 'Save file as', '', 'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[
                0]
        if dial:
            # Захватываем изображжение с холста и сохраняем
            pixmap = QPixmap(self.canvas.grab())
            pixmap.save(dial)
            # Сохраняем имя файла в переменной self.file_name, чтобы использовать в функции save_file
            # Очищаем нарисованные объекты, так как уже их сохранили
            self.file_name = dial
            self.saved = True
            self.canvas.obj = []

    def save_file(self):
        # Если имя файла выбрано, просто сохраняем
        if self.file_name:
            pixmap = QPixmap(self.canvas.grab())
            pixmap.save(self.file_name)
            self.saved = True
            self.canvas.obj = []
        # В ином случае, сохраняем как
        else:
            self.save_as_file()

    def open_file(self):
        # Открываем новый файл
        dial = QFileDialog.getOpenFileName(self, 'Open file', '', 'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[
            0]
        if dial:
            # Если старый файл не сохранен, предлагаем сохранить его
            if self.canvas.obj and not self.saved:
                dial2 = Dialogs.Message()
                res = dial2.exec()
                if res == dial2.Save:
                    self.save_file()
                if res == dial2.Cancel:
                    pass
            # Сохраняем новое имя файла, вызываем функцию open_file в экземпляре холста
            self.file_name = dial
            self.canvas.obj = []
            self.canvas.open_file()

    def open_reference(self):
        dial = Dialogs.Reference()
        dial.exec()

    def clear_canvas(self):
        # Очищаем нарисованные объекты
        self.canvas.obj.clear()
        self.canvas.update()

    def set_color(self, color):
        # Устанавливаем текущий цвет
        self.now_col = color
        red, green, blue = color.red(), color.green(), color.blue()
        # Подключаемся к базе данных в папке проекта
        # и добавляем его к любимым цветам пользователя
        con = sqlite3.connect('own_colors_db.db')
        cur = con.cursor()
        colors = cur.execute(f'''SELECT * from colors WHERE red={red} and green={green} and blue={blue}''').fetchall()
        if colors:
            id = colors[0][0]
            cur.execute(f'''UPDATE colors SET counts=counts + 1 WHERE id={id}''')
        else:
            last_id = cur.execute(f'''SELECT id from colors''').fetchall()[-1][0]
            cur.execute(f'''INSERT INTO colors VALUES ({last_id + 1}, {red}, {green}, {blue}, 1)''')
        con.commit()
        con.close()

    def set_color_with_bt(self):
        # Слот для кнопки выбора цвета
        color = QColorDialog.getColor()
        self.set_color(color)

    def closeEvent(self, event):
        # Закрываем файл, обнуляя значение зума
        self.zoom.setValue(1)
        # И предлагаем сохранить файл, если он не сохранен
        if self.canvas.obj and not self.saved:
            dial = Dialogs.Message()
            res = dial.exec()
            if res == dial.Save:
                self.save_file()
            if res == dial.Cancel:
                event.ignore()

    def load_sql(self):
        # При отсутствии цветов в базе данных(в первом открытии приложения)
        # добавляем в базу данных новый цвет - черный
        con = sqlite3.connect('own_colors_db.db')
        cur = con.cursor()
        len_sql = len(cur.execute(f'''SELECT * from colors''').fetchall())
        if len_sql == 0:
            cur.execute('''INSERT INTO colors VALUES (1, 0, 0, 0, 1)''')
        con.commit()
        con.close()

    def load_colors(self):
        # Загружаем цвета в кнопки любимых цветов пользователя
        colors = []
        con = sqlite3.connect('own_colors_db.db')
        cur = con.cursor()
        ex_colors = sorted(cur.execute('''SELECT red, green, blue, counts from colors''').fetchall(),
                           key=lambda i: i[3])[:21]
        ex_colors = [(i[0], i[1], i[2]) for i in ex_colors]
        colors.extend(ex_colors)
        # Если цветов недостаточно, заполняем кнопки случайными цветами
        # вдруг какой-нибудь из них ползователю понравится
        if len(colors) < 20:
            for i in range(20 - len(colors)):
                new_color = (randrange(256), randrange(256), randrange(256))
                while new_color in colors:
                    new_color = (randrange(256), randrange(256), randrange(256))
                colors.append(new_color)
        # Сохраняем цвета кнопок в словарь, где ключ - кнопка, значение - цвет
        # А также подключаем кнопки к слоту и изменением цвета
        self.bt_colors_dict = {}
        for i in range(4):
            for j in range(5):
                exec(f'self.bt{i}{j}.setStyleSheet("background:rgb({colors[0][0]}, {colors[0][1]}, {colors[0][2]});")')
                color = QColor(colors[0][0], colors[0][1], colors[0][2])
                exec(f'self.bt_colors_dict[self.bt{i}{j}] = color')
                exec(f'self.bt{i}{j}.clicked.connect(self.set_color_with_bts)')
                del colors[0]

    def set_color_with_bts(self):
        # Слот для установки цвета кисти
        self.set_color(self.bt_colors_dict[self.sender()])


if __name__ == '__main__':
    # Запускаем окно приложения
    app = QApplication(sys.argv)
    mv = CameraMainWindow()
    mv.show()
    sys.exit(app.exec())

