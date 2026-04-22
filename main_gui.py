import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from tkinterdnd2 import DND_FILES, TkinterDnD
import asyncio
import threading
from pathlib import Path

from converter import HTMLToPDFConverter

class GUI(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        # Setup ttkbootstrap theme
        self.style = tb.Style(theme="darkly")
        self.title("ChromiPrint - Perfect HTML to PDF Converter v1.0")
        self.geometry("600x500")
        self.minsize(500, 400)
        
        # Configure grid weight for responsiveness
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.file_paths = []
        self.is_processing = False
        
        self._build_ui()
        
    def _build_ui(self):
        # --- Top Frame: Instructions & Drag/Drop Zone ---
        top_frame = tb.Frame(self, padding=20)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = tb.Label(top_frame, text="Drag & Drop HTML Files Here", font=("Helvetica", 16, "bold"))
        lbl_title.grid(row=0, column=0, pady=(0, 10))
        
        # Drag and drop area
        self.drop_zone = tb.Label(top_frame, text="(Or click to select files)", 
                                  bootstyle="secondary-inverse", 
                                  relief="groove", 
                                  padding=30,
                                  anchor="center")
        self.drop_zone.grid(row=1, column=0, sticky="ew", ipady=20)
        
        # Bind Drag and Drop events
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_zone.bind('<Button-1>', self.on_click_select)
        
        # --- Middle Frame: Selected Files & Progress ---
        mid_frame = tb.Frame(self, padding=(20, 0, 20, 10))
        mid_frame.grid(row=1, column=0, sticky="ew")
        mid_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_status = tb.Label(mid_frame, text="No files selected.")
        self.lbl_status.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.progress_bar = tb.Progressbar(mid_frame, mode="determinate", bootstyle="success")
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.btn_convert = tb.Button(mid_frame, text="Start Conversion", bootstyle="primary", 
                                     command=self.start_conversion, state="disabled")
        self.btn_convert.grid(row=2, column=0, pady=(5, 0))
        
        # --- Bottom Frame: Logs ---
        bot_frame = tb.Frame(self, padding=(20, 0, 20, 20))
        bot_frame.grid(row=2, column=0, sticky="nsew")
        bot_frame.grid_columnconfigure(0, weight=1)
        bot_frame.grid_rowconfigure(0, weight=1)
        
        lbl_log = tb.Label(bot_frame, text="Log Console:")
        lbl_log.grid(row=0, column=0, sticky="w")
        
        self.log_text = tb.Text(bot_frame, wrap="word", height=8, state="disabled", font=("Courier", 9))
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        
        scrollbar = tb.Scrollbar(bot_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(5, 0))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_message("System initialized. Awaiting files...")
        
    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def on_drop(self, event):
        if self.is_processing:
            return
            
        # DND_FILES returns a string of paths, space separated but enclosed in curly braces if there's a space inside.
        files = self.split_dnd_files(event.data)
        self.add_files(files)
        
    def split_dnd_files(self, data):
        """Helper to parse TkinterDnD drop data list."""
        if not data: return []
        import re
        # Find paths enclosed in {} and those that aren't
        res = re.findall(r'\{.*?\}|\S+', data)
        return [p.strip('{}') for p in res]

    def on_click_select(self, event):
        if self.is_processing:
            return
            
        filetypes = (("HTML files", "*.html *.htm"), ("All files", "*.*"))
        filenames = filedialog.askopenfilenames(title="Select HTML files", filetypes=filetypes)
        if filenames:
            self.add_files(filenames)
            
    def add_files(self, files):
        # Filter for HTML/HTM loosely
        valid_files = [f for f in files if f.lower().endswith(('.html', '.htm'))]
        
        if not valid_files:
            messagebox.showwarning("Invalid Files", "Please select HTML (.html, .htm) files only.")
            return
            
        self.file_paths = valid_files
        count = len(self.file_paths)
        self.lbl_status.config(text=f"{count} file(s) selected.")
        self.log_message(f"Added {count} files to the queue.")
        self.btn_convert.config(state="normal")
        self.progress_bar["value"] = 0

    def start_conversion(self):
        if not self.file_paths:
            return
            
        self.is_processing = True
        self.btn_convert.config(state="disabled", text="Converting...")
        self.drop_zone.config(text="Processing...", bootstyle="secondary")
        self.progress_bar["maximum"] = len(self.file_paths)
        self.progress_bar["value"] = 0
        self.log_message("-" * 40)
        
        # Run conversion in a separate thread so GUI doesn't freeze
        conversion_thread = threading.Thread(target=self.run_async_conversion, daemon=True)
        conversion_thread.start()

    def run_async_conversion(self):
        converter = HTMLToPDFConverter(output_dir_name="Converted")
        
        # Creating a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                converter.convert_batch(
                    self.file_paths,
                    progress_callback=self.update_progress,
                    log_callback=self.thread_safe_log
                )
            )
        except Exception as e:
            self.thread_safe_log(f"Critical Error: {str(e)}")
        finally:
            loop.close()
            # Schedule completion UI update on main thread
            self.after(0, self.conversion_complete)

    def update_progress(self, current, total):
        # Need to use after to update GUI from thread
        self.after(0, lambda: self._set_progress(current, total))
        
    def _set_progress(self, current, total):
        self.progress_bar["value"] = current
        self.lbl_status.config(text=f"Converted {current}/{total} files.")
        
    def thread_safe_log(self, message):
        self.after(0, lambda: self.log_message(message))
        
    def conversion_complete(self):
        self.is_processing = False
        self.btn_convert.config(state="normal", text="Start Conversion")
        self.drop_zone.config(text="(Or click to select files)", bootstyle="secondary-inverse")
        self.log_message("All tasks completed.")
        self.log_message("-" * 40)
        messagebox.showinfo("Complete", "Batch HTML to PDF conversion completed!")

if __name__ == "__main__":
    app = GUI()
    app.mainloop()
