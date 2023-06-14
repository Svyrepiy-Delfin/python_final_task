from PyQt5.QtGui import QBrush, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt


# Главный класс файла - Canvas
class Canvas(QWidget):
    def __init__(self, parent):
        super(Canvas, self).__init__(parent)
        self.obj = []
        # Подвязываем изменение пользователем инструмента к слоту
        parent.parent().parent().parent().parent().instruments.currentTextChanged.connect(self.set_instr)
        self.instr = parent.parent().parent().parent().parent().instruments.currentText().lower()
        self.opening = False

    def paintEvent(self, event):
        # При событии рисования файл не сохранен
        self.parent().parent().parent().parent().parent().saved = False
        if self.parent().parent().parent().parent().parent().file_name:
            # Если есть файл, рисуем его
            pt = QPainter(self)
            pt.begin(self)
            pt.drawPixmap(0, 0,
                          QPixmap(self.parent().parent().parent().parent().parent().file_name).scaled(self.width(),
                                                                                                      self.height()))
            pt.end()
        # При открытии файла рисование нужно проигнорировать
        if not self.opening:
            pt = QPainter(self)
            pt.begin(self)
            for obj in self.obj:
                # Если объект - список из точек, то рисуем каждую точку в отдельности
                if isinstance(obj, list):
                    for point in obj:
                        point.draw(pt)
                # Иначе рисуем просто объект
                else:
                    obj.draw(pt)
            pt.end()
        else:
            self.opening = False
            self.update()

    def mousePressEvent(self, event):
        # Обрабатываем событие нажатия мыши
        # Если инструменты - кисть, овал и прямоугольник, то добавляем объект
        # Иначе - инструмент точка, и тогда мы создаем список точек
        if self.instr == 'brush':
            self.obj.append(
                [BrushPoint(event.x(), event.y(),
                            self.parent().parent().parent().parent().parent().now_col,
                            self.parent().parent().parent().parent().parent().now_width)])
        if self.instr == 'line':
            self.obj.append(
                Line(event.x(), event.y(), event.x(), event.y(),
                     self.parent().parent().parent().parent().parent().now_col,
                     self.parent().parent().parent().parent().parent().now_width))
        if self.instr == 'circle':
            self.obj.append(
                Ellipse(event.x(), event.y(), event.x(), event.y(),
                        self.parent().parent().parent().parent().parent().now_col,
                        self.parent().parent().parent().parent().parent().now_width))
        if self.instr == 'rectangle':
            self.obj.append(
                Rectangle(event.x(), event.y(), 0, 0,
                          self.parent().parent().parent().parent().parent().now_col,
                          self.parent().parent().parent().parent().parent().now_width))
        self.update()

    def mouseMoveEvent(self, event):
        # Обработчик событий движения мыши
        # Задаем координату последнего элемента как координату события
        # Если инструмент - кисть, то добавляем точки в список
        if self.instr == 'brush':
            self.obj[-1].append(
                BrushPoint(event.x(), event.y(),
                           self.parent().parent().parent().parent().parent().now_col,
                           self.parent().parent().parent().parent().parent().now_width))
        if self.instr == 'line' or self.instr == 'circle':
            self.obj[-1].ex = event.x()
            self.obj[-1].ey = event.y()
        if self.instr == 'rectangle':
            self.obj[-1].w = event.x() - self.obj[-1].sx
            self.obj[-1].h = event.y() - self.obj[-1].sy
        # Обновляем холст
        self.update()

    def set_instr(self, text):
        self.instr = text.lower()

    def open_file(self):
        # При открытии файла мы сохраняем данный факт в переменную self.opening
        self.opening = True


class BrushPoint:
    def __init__(self, x, y, color, width):
        self.x = x
        self.y = y
        self.color = color
        self.width = width

    def draw(self, pt):
        # Устанавливаем кисть, цвет, и прочее
        pen = QPen()
        pen.setBrush(QBrush(self.color))
        pen.setWidth(self.width)
        pt.setPen(pen)
        pt.drawEllipse(self.x - self.width // 2, self.y - self.width // 2, self.width, self.width)


class Line:
    def __init__(self, sx, sy, ex, ey, color, width):
        self.sx = sx
        self.sy = sy
        self.ex = ex
        self.ey = ey
        self.color = color
        self.width = width

    def draw(self, pt):
        # Устанавливаем кисть, цвет, и прочее
        pen = QPen()
        pen.setBrush(QBrush(self.color))
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(self.width)
        pt.setPen(pen)
        pt.drawLine(self.sx, self.sy, self.ex, self.ey)


class Ellipse:
    def __init__(self, sx, sy, ex, ey, color, width):
        self.sx = sx
        self.sy = sy
        self.ey = ey
        self.ex = ex
        self.width = width
        self.color = color

    def draw(self, pt):
        # Устанавливаем кисть, цвет, и прочее
        # Находим радиус окружностипо формуле из геометрии
        pen = QPen()
        pen.setBrush(QBrush(self.color))
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(self.width)
        pt.setPen(pen)
        rad = int(((self.ex - self.sx) ** 2 + (self.ey - self.sy) ** 2) ** 0.5)
        pt.drawEllipse(self.ex - rad, self.ey - rad, 2 * rad, 2 * rad)


class Rectangle:
    def __init__(self, sx, sy, w, h, color, width):
        self.sx = sx
        self.sy = sy
        self.w = w
        self.h = h
        self.width = width
        self.color = color

    def draw(self, pt):
        # Устанавливаем кисть, цвет, и прочее
        pen = QPen()
        pen.setBrush(QBrush(self.color))
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(self.width)
        pt.setPen(pen)
        pt.drawRect(self.sx, self.sy, self.w, self.h)