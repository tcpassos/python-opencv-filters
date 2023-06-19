import cv2
import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image
import numpy as np

class OpenCVFilters(QtWidgets.QWidget):

    video = False

    def __init__(self, width=640, height=480, fps=30):
        QtWidgets.QWidget.__init__(self)

        self.video_size = QtCore.QSize(width, height)
        self.camera_capture = cv2.VideoCapture(cv2.CAP_DSHOW)
        self.video_capture = cv2.VideoCapture()
        self.frame_timer = QtCore.QTimer()

        self.setup_camera(fps)
        self.fps = fps

        cascPath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascPath)

        self.frame_label = QtWidgets.QLabel()
        self.camera_button = QtWidgets.QPushButton("Usar webcam")
        self.camera_video_button = QtWidgets.QPushButton("Carregar vídeo")
        self.filter_combo = QtWidgets.QComboBox()  # ComboBox para seleção de filtros
        self.filter_combo.addItem("Nenhum")
        self.filter_combo.addItem("Cinza")
        self.filter_combo.addItem("Desfoque")
        self.filter_combo.addItem("Bordas")
        self.filter_combo.addItem("Canal vermelho")        
        self.filter_combo.addItem("Canal azul")
        self.filter_combo.addItem("Canal verde")
        self.filter_combo.addItem("Colorização")        
        self.filter_combo.addItem("Inversão")
        self.filter_combo.addItem("Binarização")        
        self.filter_combo.addItem("Sepia")
        self.apply_filter_button = QtWidgets.QPushButton("Aplicar filtro")  # Botão para aplicar filtro
        self.load_sticker_button = QtWidgets.QPushButton("Carregar Adesivo")
        self.main_layout = QtWidgets.QGridLayout()

        self.sticker = None

        self.setup_ui()

        QtCore.QObject.connect(self.camera_video_button, QtCore.SIGNAL("clicked()"), self.camera_video)
        QtCore.QObject.connect(self.camera_button, QtCore.SIGNAL("clicked()"), self.camera)
        QtCore.QObject.connect(self.apply_filter_button, QtCore.SIGNAL("clicked()"), self.apply_filter)
        QtCore.QObject.connect(self.load_sticker_button, QtCore.SIGNAL("clicked()"), self.load_sticker)

    def setup_ui(self):
        self.frame_label.setFixedSize(self.video_size)

        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.camera_video_button, 1, 0)
        self.main_layout.addWidget(self.camera_button, 1, 1)
        self.main_layout.addWidget(self.filter_combo, 2, 0)
        self.main_layout.addWidget(self.apply_filter_button, 2, 1)
        self.main_layout.addWidget(self.load_sticker_button, 3, 0, 1, 2)

        self.setLayout(self.main_layout)

    def camera_video(self):
        if not self.video:
            path = QtWidgets.QFileDialog.getOpenFileName(filter="Videos (*.mp4)")
            if len(path[0]) > 0:
                self.video_capture.open(path[0])
                self.video = not self.video
        else:
            self.video_capture.release()
            self.video = not self.video

    def camera(self):
        if not self.video:
            self.video_capture.open(2)
            self.video = not self.video
        else:
            self.video_capture.release()
            self.video = not self.video

    def setup_camera(self, fps):
        self.camera_capture.set(3, self.video_size.width())
        self.camera_capture.set(4, self.video_size.height())

        self.frame_timer.timeout.connect(self.display_video_stream)
        self.frame_timer.start(int(1000 // fps))
    
    def apply_filter(self):
        self.selected_filter = self.filter_combo.currentText()

    def display_video_stream(self):
        if not self.video:
            ret, frame = self.camera_capture.read()
        else:
            ret, frame = self.video_capture.read()

        if not ret:
            return False

        if self.faceCascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 50)
            )

            if self.sticker is not None:
                for (x, y, w, h) in faces:
                    sticker = self.sticker.resize((int(w*4/3), int(h*4/3)))
                    frame_pil = Image.fromarray(frame)
                    frame_pil.paste(sticker, (int(x-(w/6)), int(y-(h/6))), sticker)
                    frame = np.array(frame_pil)
            else:
                # Draw a rectangle around the faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        channels = cv2.split(frame)
        if self.selected_filter == "Cinza":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif self.selected_filter == "Desfoque":
            frame = cv2.GaussianBlur(frame, (11, 11), 0)
        elif self.selected_filter == "Bordas":
            frame = cv2.Canny(frame, 100, 200)
        elif self.selected_filter == "Canal vermelho":
            frame = cv2.merge([np.zeros_like(channels[0]), np.zeros_like(channels[1]), channels[2]])
        elif self.selected_filter == "Canal azul":
            frame = cv2.merge([channels[0], np.zeros_like(channels[1]), np.zeros_like(channels[2])])
        elif self.selected_filter == "Canal verde":
            frame = cv2.merge([np.zeros_like(channels[0]), channels[1], np.zeros_like(channels[2])])
        elif self.selected_filter == "Colorização":
            toColor = [200, 0, 0]
            r = np.sum([channels[0] | toColor[0]], axis=0)
            g = np.sum([channels[1] | toColor[1]], axis=0)
            b = np.sum([channels[2] | toColor[2]], axis=0)
            frame = cv2.merge([np.full_like(channels[0], r), np.full_like(channels[1], g), np.full_like(channels[2], b)])
        elif self.selected_filter == "Inversão":
            frame = cv2.bitwise_not(frame)
        elif self.selected_filter == "Binarização":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            l, frame = cv2.threshold(frame, 120, 255, cv2.THRESH_BINARY)
        elif self.selected_filter == "Sepia":
            sepia_matrix = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
            frame = cv2.transform(frame, sepia_matrix)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = QtGui.QImage(frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

        if not self.video:
            frame = cv2.flip(frame, 1)
        else:
            frame = cv2.resize(frame, (self.video_size.width(), self.video_size.height()), interpolation=cv2.INTER_AREA)

        image = QtGui.QImage(frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

    def load_sticker(self):
        path = QtWidgets.QFileDialog.getOpenFileName(filter="stickers (*.png)")
        self.sticker = Image.open(path[0])

def close_win(self):
    self.camera_capture.release()
    self.video_capture.release()
    cv2.destroyAllWindows()
    self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    player = OpenCVFilters()
    player.apply_filter()
    player.show()
    sys.exit(app.exec_())