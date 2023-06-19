import cv2
import sys
from PySide6 import QtCore, QtGui, QtWidgets

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
        self.main_layout = QtWidgets.QGridLayout()

        self.setup_ui()

        QtCore.QObject.connect(self.camera_video_button, QtCore.SIGNAL("clicked()"), self.camera_video)
        QtCore.QObject.connect(self.camera_button, QtCore.SIGNAL("clicked()"), self.camera)

    def setup_ui(self):

        self.frame_label.setFixedSize(self.video_size)

        self.main_layout.addWidget(self.frame_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.camera_video_button, 1, 0, 1, 2)
        self.main_layout.addWidget(self.camera_button, 2, 0, 1, 2)

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

    def display_video_stream(self):

        if not self.video:
            ret, frame = self.camera_capture.read()
        else:
            ret, frame = self.video_capture.read()

        if not ret:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if not self.video:
            frame = cv2.flip(frame, 1)
        else:
            frame = cv2.resize(frame, (self.video_size.width(), self.video_size.height()), interpolation=cv2.INTER_AREA)

        image = QtGui.QImage(frame, self.video_size.width(), self.video_size.height(), self.video_size.width() * 3, QtGui.QImage.Format_RGB888)
        self.frame_label.setPixmap(QtGui.QPixmap.fromImage(image))

    def close_win(self):
        self.camera_capture.release()
        self.video_capture.release()
        cv2.destroyAllWindows()
        self.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    player = OpenCVFilters()
    player.show()
    sys.exit(app.exec_())