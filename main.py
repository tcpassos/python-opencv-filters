import cv2
import sys
import enum
from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image
import numpy as np

class CaptureType(enum.Enum):
    camera = 1
    video = 2
    image = 3

class OpenCVFilters(QtWidgets.QWidget):

    def __init__(self, width=640, height=480, fps=30):
        QtWidgets.QWidget.__init__(self)

        # Configura janela
        self.setWindowTitle("Filtros OpenCV")
        icon = QtGui.QIcon("icon.png")
        self.setWindowIcon(icon)

        # Atributos da classe
        self.video_size = QtCore.QSize(width, height)
        self.camera_capture = cv2.VideoCapture(cv2.CAP_DSHOW)
        self.video_capture = cv2.VideoCapture()
        self.image = None
        self.frame_timer = QtCore.QTimer()
        self.sticker = None
        self.capture_type = CaptureType.camera

        self.setup_camera(fps)
        self.fps = fps

        # Configura o classificador de rostos
        cascPath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascPath)

        # Cria os componentes da janela
        self.frame_label = QtWidgets.QLabel()
        self.camera_button = QtWidgets.QPushButton("Usar webcam")
        self.capture_file_button = QtWidgets.QPushButton("Carregar arquivo")
        self.filter_combo = QtWidgets.QComboBox()
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
        self.apply_filter_button = QtWidgets.QPushButton("Aplicar filtro")
        self.load_sticker_button = QtWidgets.QPushButton("Carregar Adesivo")
        self.remove_sticker_button = QtWidgets.QPushButton("Remover Adesivo")
        self.main_layout = QtWidgets.QGridLayout()
        self.setup_ui()

        # Define os callbacks dos botões
        QtCore.QObject.connect(self.capture_file_button, QtCore.SIGNAL("clicked()"), self.capture_file)
        QtCore.QObject.connect(self.camera_button, QtCore.SIGNAL("clicked()"), self.capture_camera)
        QtCore.QObject.connect(self.apply_filter_button, QtCore.SIGNAL("clicked()"), self.apply_filter)
        QtCore.QObject.connect(self.load_sticker_button, QtCore.SIGNAL("clicked()"), self.load_sticker)
        QtCore.QObject.connect(self.remove_sticker_button, QtCore.SIGNAL("clicked()"), self.remove_sticker)

    def setup_ui(self):
        self.frame_label.setFixedSize(self.video_size)

        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.capture_file_button, 1, 0)
        self.main_layout.addWidget(self.camera_button, 1, 1)
        self.main_layout.addWidget(self.filter_combo, 2, 0)
        self.main_layout.addWidget(self.apply_filter_button, 2, 1)
        self.main_layout.addWidget(self.load_sticker_button, 3, 0)
        self.main_layout.addWidget(self.remove_sticker_button, 3, 1)

        self.setLayout(self.main_layout)

    def capture_file(self):
        self.video_capture.release()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(filter="Videos (*.mp4);;Images (*.png *.jpg *.jpeg)")
        if path.endswith(('.png', '.jpg', '.jpeg')):
            self.capture_type = CaptureType.image
            self.image = cv2.imread(path)
        elif path.endswith('.mp4'):
            self.capture_type = CaptureType.video
            self.video_capture.open(path)

    def capture_camera(self):
        self.video_capture.release()
        self.video_capture.open(2)
        self.capture_type = CaptureType.camera

    def setup_camera(self, fps):
        self.camera_capture.set(3, self.video_size.width())
        self.camera_capture.set(4, self.video_size.height())

        self.frame_timer.timeout.connect(self.display_video_stream)
        self.frame_timer.start(int(1000 // fps))
    
    def apply_filter(self):
        self.selected_filter = self.filter_combo.currentText()

    def display_video_stream(self):
        if self.capture_type == CaptureType.camera:
            ret, frame = self.camera_capture.read()
        elif self.capture_type == CaptureType.video:
            ret, frame = self.video_capture.read()
        elif self.capture_type == CaptureType.image:
            frame = self.image
            ret = frame is not None

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
            #else:
                #for (x, y, w, h) in faces:
                    #cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

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

        if self.capture_type == CaptureType.camera:
            frame = cv2.flip(frame, 1)
        else:
            frame = cv2.resize(frame, (self.video_size.width(), self.video_size.height()), interpolation=cv2.INTER_AREA)

        image = QtGui.QImage(frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

    def load_sticker(self):
        path = QtWidgets.QFileDialog.getOpenFileName(filter="Stickers (*.png)")
        self.sticker = Image.open(path[0])

    def remove_sticker(self):
        self.sticker = None

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