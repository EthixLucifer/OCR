# OCR Project


## Overview
This project is an OCR (Optical Character Recognition) tool that allows users to capture a portion of their screen and extract text from it using the PaddleOCR library. The extracted text is displayed in a floating window and copied to the clipboard.

## Setup

### Prerequisites
- Python 3.6 or higher
- Pip (Python package installer)

### Required Libraries
Install the required libraries using pip:
```bash
pip install paddlepaddle paddleocr pyqt5 mss pyperclip pynput
```

### Running the Project
1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Run the `ocr_capture.py` script:
```bash
python ocr_capture.py
```

## Usage
- **Load/Unload OCR Model**: Press `Ctrl + Alt + Esc` to load or unload the OCR model.
- **Capture Screen Region**: Press `Ctrl + \` to start selecting a screen region. The text within the selected region will be extracted and displayed in a floating window.
- **Stop Script**: Press `Ctrl + Alt + \` to stop the script gracefully.

## File Structure
- `ocr_capture.py`: Main script containing the OCR functionality and GUI components.

## Notes
- Ensure that the PaddleOCR model files are downloaded and available in the expected directory.
- The extracted text is automatically copied to the clipboard for easy pasting.

## License
This project is licensed under the MIT License.

## Acknowledgements
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [PyQt5](https://pypi.org/project/PyQt5/)
- [mss](https://pypi.org/project/mss/)
- [pyperclip](https://pypi.org/project/pyperclip/)
- [pynput](https://pypi.org/project/pynput/)

