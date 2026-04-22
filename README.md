# Batch HTML to PDF Converter

A high-fidelity batch HTML to PDF conversion tool with a modern GUI.

## Features
- **Modern UI**: Built with `ttkbootstrap` for a premium dark mode look.
- **Drag & Drop**: Easily add files by dragging them into the application.
- **High Fidelity**: Uses Playwright (Chromium) to ensure CSS and JavaScript are rendered perfectly.
- **Batch Processing**: Convert multiple files at once.
- **Auto-organization**: Converted PDFs are saved in a `Converted` folder next to the source files.

## Installation

1. Clone the repository.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the Playwright browser engine:
   ```bash
   playwright install chromium
   ```

## Usage

Run the application using:
```bash
python main_gui.py
```

## Requirements
- Python 3.8+
- Playwright
- ttkbootstrap
- tkinterdnd2
