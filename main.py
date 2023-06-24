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

class Sticker:
    def __init__(self, x, y, identifier):
        self.x = x
        self.y = y
        self.identifier = identifier

class OpenCVFilters(QtWidgets.QWidget):

    def __init__(self, width=640, height=480, fps=30):
        QtWidgets.QWidget.__init__(self)

        # Configura janela
        self.setWindowTitle("Filtros OpenCV")
        icon = QtGui.QIcon("icon.png")
        self.setWindowIcon(icon)
        self.setMouseTracking(True)

        # Atributos da classe
        self.video_size = QtCore.QSize(width, height)
        self.camera_capture = cv2.VideoCapture(cv2.CAP_DSHOW)
        self.video_capture = cv2.VideoCapture()
        self.image = None
        self.frame = None
        self.frame_timer = QtCore.QTimer()
        self.face_sticker = None
        self.stickers = []
        self.capture_type = CaptureType.camera

        # Configuração da câmera
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
        self.apply_filter_button = QtWidgets.QPushButton("Aplicar Filtro")
        self.filter_layout = QtWidgets.QGridLayout()
        self.filter_layout.addWidget(self.filter_combo, 0, 0)
        self.filter_layout.addWidget(self.apply_filter_button, 0, 1)
        self.filter_groupbox = QtWidgets.QGroupBox("Filtros")
        self.filter_groupbox.setLayout(self.filter_layout)

        self.sticker_combo = QtWidgets.QComboBox()
        self.sticker_combo.setPlaceholderText("[Selecione um adesivo]")
        self.sticker_combo.addItem("Teste")
        self.load_face_sticker_button = QtWidgets.QPushButton("Carregar Máscara")
        self.remove_stickers_button = QtWidgets.QPushButton("Remover Adesivos")
        self.sticker = QtWidgets.QGridLayout()
        self.sticker_layout = QtWidgets.QGridLayout()
        self.sticker_layout.addWidget(self.sticker_combo, 0, 0)
        self.sticker_layout.addWidget(self.load_face_sticker_button, 0, 1)
        self.sticker_layout.addWidget(self.remove_stickers_button, 1, 0, 1, 2)
        self.sticker_groupbox = QtWidgets.QGroupBox("Adesivos")
        self.sticker_groupbox.setLayout(self.sticker_layout)

        self.save_frame_button = QtWidgets.QPushButton("Salvar Imagem")
        self.main_layout = QtWidgets.QGridLayout()
        self.setup_ui()

        # Define os callbacks dos botões
        QtCore.QObject.connect(self.capture_file_button, QtCore.SIGNAL("clicked()"), self.capture_file)
        QtCore.QObject.connect(self.camera_button, QtCore.SIGNAL("clicked()"), self.capture_camera)
        QtCore.QObject.connect(self.apply_filter_button, QtCore.SIGNAL("clicked()"), self.apply_filter)
        QtCore.QObject.connect(self.load_face_sticker_button, QtCore.SIGNAL("clicked()"), self.load_face_sticker)
        QtCore.QObject.connect(self.remove_stickers_button, QtCore.SIGNAL("clicked()"), self.remove_stickers)
        QtCore.QObject.connect(self.save_frame_button, QtCore.SIGNAL("clicked()"), self.save_frame)

        # Configura o callback de renderização do frame
        self.frame_timer.timeout.connect(self.display_video_stream)
        self.frame_timer.start(int(1000 // fps))

    def setup_ui(self):
        self.frame_label.setFixedSize(self.video_size)
        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.capture_file_button, 1, 0)
        self.main_layout.addWidget(self.camera_button, 1, 1)
        self.main_layout.addWidget(self.filter_groupbox, 2, 0, 1, 2)
        self.main_layout.addWidget(self.sticker_groupbox, 3, 0, 1, 2)
        self.main_layout.addWidget(self.save_frame_button, 4, 0, 1, 2)
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
    
    def apply_filter(self):
        self.selected_filter = self.filter_combo.currentText()

    def save_frame(self):
        if self.frame is not None:
            current_frame = self.frame
            dialog = QtWidgets.QFileDialog()
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
            if dialog.exec():
                file_path = dialog.selectedFiles()[0]
                cv2.imwrite(file_path, cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            x = event.x()
            y = event.y()
            self.stickers.append(Sticker(x, y, 'teste'))

    # ============================================================================================================
    # Renderização do frame
    # ============================================================================================================
    def display_video_stream(self):
        if self.capture_type == CaptureType.camera:
            ret, self.frame = self.camera_capture.read()
        elif self.capture_type == CaptureType.video:
            ret, self.frame = self.video_capture.read()
        elif self.capture_type == CaptureType.image:
            self.frame = self.image
            ret = self.frame is not None

        if not ret:
            return False

        if self.faceCascade is not None:
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Detecta os rostos no frame
            faces = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 50)
            )

            # Desenha o sticker do rosto
            if self.face_sticker is not None:
                for (x, y, w, h) in faces:
                    sticker = self.face_sticker.resize((int(w*4/3), int(h*4/3)))
                    frame_pil = Image.fromarray(self.frame)
                    frame_pil.paste(sticker, (int(x-(w/6)), int(y-(h/6))), sticker)
                    self.frame = np.array(frame_pil)
            #else:
                #for (x, y, w, h) in faces:
                    #cv2.rectangle(self.frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        channels = cv2.split(self.frame)
        if self.selected_filter == "Cinza":
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        elif self.selected_filter == "Desfoque":
            self.frame = cv2.GaussianBlur(self.frame, (11, 11), 0)
        elif self.selected_filter == "Bordas":
            self.frame = cv2.Canny(self.frame, 100, 200)
        elif self.selected_filter == "Canal vermelho":
            self.frame = cv2.merge([np.zeros_like(channels[0]), np.zeros_like(channels[1]), channels[2]])
        elif self.selected_filter == "Canal azul":
            self.frame = cv2.merge([channels[0], np.zeros_like(channels[1]), np.zeros_like(channels[2])])
        elif self.selected_filter == "Canal verde":
            self.frame = cv2.merge([np.zeros_like(channels[0]), channels[1], np.zeros_like(channels[2])])
        elif self.selected_filter == "Colorização":
            toColor = [200, 0, 0]
            r = np.sum([channels[0] | toColor[0]], axis=0)
            g = np.sum([channels[1] | toColor[1]], axis=0)
            b = np.sum([channels[2] | toColor[2]], axis=0)
            self.frame = cv2.merge([np.full_like(channels[0], r), np.full_like(channels[1], g), np.full_like(channels[2], b)])
        elif self.selected_filter == "Inversão":
            self.frame = cv2.bitwise_not(self.frame)
        elif self.selected_filter == "Binarização":
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            l, self.frame = cv2.threshold(self.frame, 120, 255, cv2.THRESH_BINARY)
        elif self.selected_filter == "Sepia":
            sepia_matrix = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
            self.frame = cv2.transform(self.frame, sepia_matrix)

        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

        image = QtGui.QImage(self.frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

        if self.capture_type == CaptureType.camera:
            self.frame = cv2.flip(self.frame, 1)
        else:
            self.frame = cv2.resize(self.frame, (self.video_size.width(), self.video_size.height()), interpolation=cv2.INTER_AREA)
        
        # Desenha os stickers
        for sticker in self.stickers:
            cv2.circle(self.frame, (sticker.x, sticker.y), 5, (255, 0, 0), -1)

        image = QtGui.QImage(self.frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

    def load_face_sticker(self):
        path = QtWidgets.QFileDialog.getOpenFileName(filter="Stickers (*.png)")
        self.face_sticker = Image.open(path[0])

    def remove_stickers(self):
        self.face_sticker = None
        self.stickers.clear()

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