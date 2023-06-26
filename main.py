import cv2
import sys
import enum
from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image
import numpy as np

# Tipo de captura a ser processada
class CaptureType(enum.Enum):
    camera = 1
    video = 2
    image = 3

# Classe com os atributos de um adesivo
class Sticker:
    def __init__(self, x, y, path, identifier):
        self.x = x
        self.y = y
        self.img = Image.open(path[0])
        self.identifier = identifier

# Classe principal com o processamento de imagens
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
        self.capture_type = CaptureType.camera
        self.image = None
        self.frame = None
        self.frame_timer = QtCore.QTimer()
        self.face_sticker = None
        self.stickers = []

        # Configuração da câmera
        self.setup_camera(fps)
        self.fps = fps

        # Configura o classificador de rostos
        cascPath = "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascPath)

        # Inicia valores para filtros
        self.rvalue = 0
        self.gvalue = 0
        self.bvalue = 0
        self.limitvalue = 0

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

        # Cria componentes de controle dos filtros
        self.control_bslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)      
        self.control_bslider.setMinimum(0)
        self.control_bslider.setMaximum(255)
        self.control_bslider.setTickInterval(1)        
        self.control_bslider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.control_blabel = QtWidgets.QLabel()
        self.control_blabel.setText(f"B: {self.bvalue}")
        self.control_blabel.setAlignment(QtCore.Qt.AlignCenter)     
        self.control_gslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)      
        self.control_gslider.setMinimum(0)
        self.control_gslider.setMaximum(255)
        self.control_gslider.setTickInterval(1)        
        self.control_gslider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.control_glabel = QtWidgets.QLabel()
        self.control_glabel.setText(f"G: {self.gvalue}")
        self.control_glabel.setAlignment(QtCore.Qt.AlignCenter)
        self.control_rslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)      
        self.control_rslider.setMinimum(0)
        self.control_rslider.setMaximum(255)
        self.control_rslider.setTickInterval(1)        
        self.control_rslider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.control_rlabel = QtWidgets.QLabel()
        self.control_rlabel.setText(f"R: {self.rvalue}")
        self.control_rlabel.setAlignment(QtCore.Qt.AlignCenter)
        self.control_limitslider = QtWidgets.QSlider(QtCore.Qt.Horizontal)      
        self.control_limitslider.setMinimum(0)
        self.control_limitslider.setMaximum(255)
        self.control_limitslider.setTickInterval(1)        
        self.control_limitslider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.control_limitlabel = QtWidgets.QLabel()
        self.control_limitlabel.setText(f"Limiar: {self.limitvalue}")
        self.control_limitlabel.setAlignment(QtCore.Qt.AlignCenter)
        self.control_layout = QtWidgets.QGridLayout()
        self.control_layout.addWidget(self.control_rlabel, 0, 0)
        self.control_layout.addWidget(self.control_rslider, 1, 0)   
        self.control_layout.addWidget(self.control_glabel, 0, 1)
        self.control_layout.addWidget(self.control_gslider, 1, 1)
        self.control_layout.addWidget(self.control_blabel, 0, 2)
        self.control_layout.addWidget(self.control_bslider, 1, 2)        
        self.control_layout.addWidget(self.control_limitlabel, 0, 0)
        self.control_layout.addWidget(self.control_limitslider, 1, 0) 
        self.control_groupbox = QtWidgets.QGroupBox("Controle")
        self.control_groupbox.setLayout(self.control_layout)  

        # Esconde campos específico de determinados filtros
        self.set_rgb_controls_visible(False)
        self.set_threshold_controls_visible(False)

        self.load_face_sticker_button = QtWidgets.QPushButton("Carregar Máscara")
        self.remove_stickers_button = QtWidgets.QPushButton("Remover Adesivos")
        self.sticker = QtWidgets.QGridLayout()
        self.sticker_layout = QtWidgets.QGridLayout()
        self.sticker_layout.addWidget(self.load_face_sticker_button, 0, 0)
        self.sticker_layout.addWidget(self.remove_stickers_button, 1, 0)
        self.sticker_groupbox = QtWidgets.QGroupBox("Adesivos (Clique na imagem para adicionar adesivos)")
        self.sticker_groupbox.setLayout(self.sticker_layout)

        self.save_frame_button = QtWidgets.QPushButton("Salvar Imagem")
        self.main_layout = QtWidgets.QGridLayout()
        self.setup_ui()

        # Define os callbacks dos sliders
        self.control_bslider.valueChanged.connect(self.set_bvalue)
        self.control_gslider.valueChanged.connect(self.set_gvalue)
        self.control_rslider.valueChanged.connect(self.set_rvalue)
        self.control_limitslider.valueChanged.connect(self.set_limitvalue)

        # Define os callbacks dos botões
        QtCore.QObject.connect(self.capture_file_button, QtCore.SIGNAL("clicked()"), self.on_capture_file)
        QtCore.QObject.connect(self.camera_button, QtCore.SIGNAL("clicked()"), self.on_capture_camera)
        QtCore.QObject.connect(self.apply_filter_button, QtCore.SIGNAL("clicked()"), self.on_filter_change)
        QtCore.QObject.connect(self.load_face_sticker_button, QtCore.SIGNAL("clicked()"), self.on_load_face_sticker)
        QtCore.QObject.connect(self.remove_stickers_button, QtCore.SIGNAL("clicked()"), self.on_remove_stickers)
        QtCore.QObject.connect(self.save_frame_button, QtCore.SIGNAL("clicked()"), self.on_save_frame)

        # Configura o callback de renderização do frame
        self.frame_timer.timeout.connect(self.display_video_stream)
        self.frame_timer.start(int(1000 // fps))

    def setup_ui(self):
        self.frame_label.setFixedSize(self.video_size)
        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.capture_file_button, 1, 0)
        self.main_layout.addWidget(self.camera_button, 1, 1)
        self.main_layout.addWidget(self.filter_groupbox, 2, 0, 1, 2)
        self.main_layout.addWidget(self.control_groupbox, 3, 0, 1, 2)
        self.main_layout.addWidget(self.sticker_groupbox, 4, 0, 1, 2)
        self.main_layout.addWidget(self.save_frame_button, 5, 0, 1, 2)
        self.setLayout(self.main_layout)

    def on_capture_file(self):
        self.video_capture.release()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(filter="Videos (*.mp4);;Imagens (*.png *.jpg *.jpeg)")
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.capture_type = CaptureType.image
            self.image = cv2.imread(path)
        elif path.lower().endswith('.mp4'):
            self.capture_type = CaptureType.video
            self.video_capture.open(path)

    def on_capture_camera(self):
        self.video_capture.release()
        self.video_capture.open(2)
        self.capture_type = CaptureType.camera

    def setup_camera(self, fps):
        self.camera_capture.set(3, self.video_size.width())
        self.camera_capture.set(4, self.video_size.height())
    
    def on_filter_change(self):           
        self.selected_filter = self.filter_combo.currentText()        
        self.set_rgb_controls_visible(self.selected_filter == "Colorização")
        self.set_threshold_controls_visible(self.selected_filter == "Binarização")
    
    def set_rgb_controls_visible(self, visible):
        if (visible):
            self.control_rlabel.show()
            self.control_rslider.show()
            self.control_glabel.show()
            self.control_gslider.show()
            self.control_blabel.show()
            self.control_bslider.show()
        else:
            self.control_rlabel.hide()
            self.control_rslider.hide()
            self.control_glabel.hide()
            self.control_gslider.hide()
            self.control_blabel.hide()
            self.control_bslider.hide()

    def set_threshold_controls_visible(self, visible):
        if(visible):
            self.control_limitlabel.show()
            self.control_limitslider.show()
        else:
            self.control_limitlabel.hide()
            self.control_limitslider.hide()

    def on_save_frame(self):
        if self.frame is not None:
            current_frame = self.frame
            dialog = QtWidgets.QFileDialog()
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
            if dialog.exec():
                file_path = dialog.selectedFiles()[0]
                cv2.imwrite(file_path, cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB))

    # Quando for clicado no frame será aberto uma janela para a seleção do adesivo a ser adicionado nessa posição
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            x = event.x()
            y = event.y()
            if x > 0 and x < self.video_size.width() and y > 0 and y < self.video_size.height():
                path = QtWidgets.QFileDialog.getOpenFileName(filter="Stickers (*.png)", dir=".\Stickers")
                if(path[0] != ''):
                    self.stickers.append(Sticker(x, y, path, path[0].split('/').pop()))
            
    def set_bvalue(self, value):
        self.bvalue = value
        self.control_blabel.setText(f"B: {value}")

    def set_gvalue(self, value):
        self.gvalue = value
        self.control_glabel.setText(f"G: {value}")

    def set_rvalue(self, value):
        self.rvalue = value              
        self.control_rlabel.setText(f"R: {value}")
        
    def set_limitvalue(self, value):
        self.limitvalue = value              
        self.control_limitlabel.setText(f"Limiar: {value}")

    # Abre a janela para seleção do adesivo de rosto
    def on_load_face_sticker(self):
        path = QtWidgets.QFileDialog.getOpenFileName(filter="Stickers (*.png)", dir="./Masks")
        if(path[0] != ''):
            self.face_sticker = Image.open(path[0])

    # Remove todos os adesivos do frame
    def on_remove_stickers(self):
        self.face_sticker = None
        self.stickers.clear()

    # ============================================================================================================
    # Processamento e renderização do frame
    # ============================================================================================================
    def display_video_stream(self):
        if not self.read_frame():
            return False
        # Detecta os rostos no frame
        faces = self.detect_faces()
        # Aplica o filtro selecionado
        self.apply_filter()
        # Desenha o sticker do rosto
        self.draw_face_sticker(faces)
        # BGR -> RGB
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        # Se for webcam, espelha a imagem
        if self.capture_type == CaptureType.camera:
            self.frame = cv2.flip(self.frame, 1)
        # Se for vídeo/imagem, redimensiona encaixar na janela
        else:
            self.frame = cv2.resize(self.frame, (self.video_size.width(), self.video_size.height()), interpolation=cv2.INTER_AREA)
        # Desenha os stickers
        self.draw_stickers()
        # Adiciona o frame processado pelo OpenCV na janela
        image = QtGui.QImage(self.frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))
    
    def read_frame(self):
        if self.capture_type == CaptureType.camera:
            ret, self.frame = self.camera_capture.read()
        elif self.capture_type == CaptureType.video:
            ret, self.frame = self.video_capture.read()
        elif self.capture_type == CaptureType.image:
            self.frame = self.image
            ret = self.frame is not None
        return ret
    
    def detect_faces(self):
        faces = []
        if self.face_cascade is not None and self.face_sticker is not None:
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 50)
            )
        return faces

    def draw_face_sticker(self, faces):
        if self.face_sticker is None:
            return
        for (x, y, w, h) in faces:
            sticker = self.face_sticker.resize((int(w*4/3), int(h*4/3)))
            frame_pil = Image.fromarray(self.frame)
            frame_pil.paste(sticker, (int(x-(w/6)), int(y-(h/6))), sticker)
            self.frame = np.array(frame_pil)

    def draw_stickers(self):
        for sticker in self.stickers:   
            if(sticker.img.size[0] > sticker.img.size[1]):
                x = 120
                y = int(sticker.img.size[1]*x/sticker.img.size[0])
            else:
                y = 120
                x = int(sticker.img.size[0]*y/sticker.img.size[1])
            stc = sticker.img.resize((x, y))
            frame_pil = Image.fromarray(self.frame)
            try:
                frame_pil.paste(stc, (sticker.x-int(x/2), sticker.y-int(y/2)), stc)
            except:
                frame_pil.paste(stc, (sticker.x-int(x/2), sticker.y-int(y/2)))
            self.frame = np.array(frame_pil)

    def apply_filter(self):
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
            toColor = [self.bvalue, self.gvalue, self.rvalue]
            r = np.sum([channels[0] | toColor[0]], axis=0)
            g = np.sum([channels[1] | toColor[1]], axis=0)
            b = np.sum([channels[2] | toColor[2]], axis=0)
            self.frame = cv2.merge([np.full_like(channels[0], r), np.full_like(channels[1], g), np.full_like(channels[2], b)])
        elif self.selected_filter == "Inversão":
            self.frame = cv2.bitwise_not(self.frame)
        elif self.selected_filter == "Binarização":
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            l, self.frame = cv2.threshold(self.frame, self.limitvalue, 255, cv2.THRESH_BINARY)
        elif self.selected_filter == "Sepia":
            sepia_matrix = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
            self.frame = cv2.transform(self.frame, sepia_matrix)

    def close_win(self):
        self.camera_capture.release()
        self.video_capture.release()
        cv2.destroyAllWindows()
        self.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    player = OpenCVFilters()
    player.on_filter_change()
    player.show()
    sys.exit(app.exec_())