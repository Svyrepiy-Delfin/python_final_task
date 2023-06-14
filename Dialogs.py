from PyQt5.QtWidgets import QMessageBox


# Класс с диалогом сохранения картинки
class Message(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Saving')
        self.setText('Saving the picture')
        self.setInformativeText('Do you want to save the picture?')
        self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Save | QMessageBox.Discard)
        self.setDefaultButton(QMessageBox.Save)
        self.setIcon(QMessageBox.Question)


class Reference(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Reference')
        self.setText('This application helps you to make photo and edit them with brush and other instruments. ' +
                     'Zoom the picture with slider. On painter page you can choose the instrument and change color. ' +
                     "Your favourite colors are in the top right. That's all. Good luck!")
