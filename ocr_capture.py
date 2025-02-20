import sys
import mss
import pyperclip
import threading
import time
from pynput import keyboard
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal, QObject, QMetaObject

from paddleocr import PaddleOCR

# Global variables
ocr_model = None
running = True
ctrl_pressed = shift_pressed = alt_pressed = False  # Modifier key tracking
current_selector = None #global variable



class Communicator(QObject):
    """Signal communicator for thread-safe operations."""
    capture_signal = pyqtSignal()
    toggle_ocr_signal = pyqtSignal()
    stop_signal = pyqtSignal()


comm = Communicator()


class ScreenSelector(QWidget):
    """ Transparent overlay for selecting a screen region. """
    closed = pyqtSignal(tuple)  # Signal to emit selected region

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        self.start_x = self.start_y = self.end_x = self.end_y = 0
        self.dragging = False

    def mousePressEvent(self, event):
        """ Start selection on mouse press. """
        self.start_x, self.start_y = event.globalX(), event.globalY()
        self.end_x, self.end_y = self.start_x, self.start_y
        self.dragging = True
        self.update()

    def mouseMoveEvent(self, event):
        """ Update selection area while dragging. """
        if self.dragging:
            self.end_x, self.end_y = event.globalX(), event.globalY()
            self.update()

    def mouseReleaseEvent(self, event):
        """ Finish selection on mouse release. """
        self.dragging = False
        self.update()
        region = self.get_selected_region()
        self.closed.emit(region)  # Emit selected region signal
        self.close()

    def paintEvent(self, event):
        """ Draw the transparent overlay with the selected region. """
        if self.dragging:
            painter = QPainter(self)
            painter.setPen(QColor(255, 0, 0, 200))
            painter.setBrush(QColor(0, 0, 0, 50))
            rect = QRect(self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y)
            painter.drawRect(rect)

    def get_selected_region(self):
        """ Return the selected screen coordinates. """
        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        width, height = abs(self.end_x - self.start_x), abs(self.end_y - self.start_y)
        return x1, y1, width, height


class FloatingTextWindow(QWidget):
    """ Floating window to display recognized text. """
    def __init__(self, text):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 200)

        self.text_display = QTextEdit(self)
        self.text_display.setGeometry(0, 0, 400, 200)
        self.text_display.setText(text)
        self.text_display.setFont(QFont("Arial", 14))
        self.text_display.setStyleSheet("background-color: black; color: white; border: 2px solid white;")
        self.text_display.setReadOnly(True)

        self.show()


def toggle_ocr_model():
    """ Load or unload the OCR model. """
    global ocr_model
    if ocr_model is None:
        print("Loading OCR model...")
        ocr_model = PaddleOCR(lang="en", use_angle_cls=True, use_static_model=True)
        show_popup("OCR Loaded")
    else:
        print("Unloading OCR model...")
        ocr_model = None
        show_popup("OCR Unloaded")


def capture_screen():
    global ocr_model, current_selector
    if ocr_model is None:
        print("OCR model not loaded!")
        return

    # Clear previous selector if exists
    if current_selector:
        current_selector.close()

    # Create and retain new selector
    current_selector = ScreenSelector()
    current_selector.closed.connect(process_selection)
    current_selector.closed.connect(lambda: cleanup_selector())  # Cleanup on close
    current_selector.show()

def cleanup_selector():
    global current_selector
    current_selector = None

def process_selection(region):
    """ Start OCR processing in a background thread. """
    x1, y1, width, height = region
    threading.Thread(target=run_ocr, args=(x1, y1, width, height), daemon=True).start()


def run_ocr(x1, y1, width, height):
    """ Capture the selected region, apply OCR, and display the result. """
    with mss.mss() as sct:
        screenshot = sct.grab({'left': x1, 'top': y1, 'width': width, 'height': height})
        screenshot_path = 'screenshot.png'
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)

    result = ocr_model.ocr(screenshot_path, cls=True)
    extracted_text = "\n".join([word[1][0] for line in result for word in line])
    pyperclip.copy(extracted_text)

    QMetaObject.invokeMethod(QApplication.instance(),
                             lambda: FloatingTextWindow(extracted_text),
                             Qt.QueuedConnection)


def show_popup(message):
    """ Show a temporary popup message in the main thread. """
    popup = QWidget()
    popup.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    popup.setAttribute(Qt.WA_TranslucentBackground)
    popup.setGeometry(800, 400, 200, 50)

    label = QLabel(message, popup)
    label.setGeometry(0, 0, 200, 50)
    label.setStyleSheet("background-color: black; color: white; border: 2px solid white;")
    label.setAlignment(Qt.AlignCenter)

    popup.show()
    QTimer.singleShot(1000, popup.close)  # Close popup after 1 second


def stop_script():
    """ Terminate the script gracefully. """
    global running, ocr_model
    print("Stopping script...")
    running = False
    if ocr_model:
        ocr_model = None
    sys.exit(0)


def on_press(key):
    """ Handle hotkey press events. """
    global ctrl_pressed, shift_pressed, alt_pressed

    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        ctrl_pressed = True
    elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
        shift_pressed = True
    elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
        alt_pressed = True

    try:
        if key == keyboard.KeyCode.from_char('\\') and ctrl_pressed:
            if alt_pressed:
                comm.stop_signal.emit()
            else:
                comm.capture_signal.emit()
        elif key == keyboard.Key.esc and ctrl_pressed and alt_pressed:
            comm.toggle_ocr_signal.emit()
    except AttributeError:
        pass


def on_release(key):
    """ Handle hotkey release events. """
    global ctrl_pressed, shift_pressed, alt_pressed

    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        ctrl_pressed = False
    elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
        shift_pressed = False
    elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
        alt_pressed = False


def start_hotkey_listener():
    """ Start listening for hotkeys in a separate thread. """
    print("Listening for hotkeys...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    comm.capture_signal.connect(capture_screen)
    comm.toggle_ocr_signal.connect(toggle_ocr_model)
    comm.stop_signal.connect(stop_script)

    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    sys.exit(app.exec_())
