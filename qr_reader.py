"""
qr_reader.py - Ридер QR-кодов на Python (CLI + Tkinter GUI)
Поддерживает: чтение из изображений, PDF, пакетное сканирование.
Использует библиотеки: zxing-cpp, pillow, opencv-python.
"""
import argparse
import os
import sys
import json
import csv
from pathlib import Path
from PIL import Image
import zxingcpp
import cv2

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# ========== ОСНОВНАЯ ЛОГИКА ==========
class QRReader:
    def __init__(self):
        self.results = []

    def read_from_image(self, image_path):
        """Декодирует QR-код из изображения"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            # Конвертируем в оттенки серого для лучшего распознавания
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Используем zxing-cpp для распознавания
            barcodes = zxingcpp.read_barcodes(gray)
            results = []
            for barcode in barcodes:
                results.append({
                    'text': barcode.text,
                    'format': str(barcode.format),
                    'position': barcode.position if hasattr(barcode, 'position') else None
                })
            return results
        except Exception as e:
            print(f"Ошибка при чтении {image_path}: {e}")
            return None

    def read_batch(self, folder_path, output=None):
        """Пакетное сканирование всех изображений в папке"""
        self.results = []
        extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        files = [f for f in Path(folder_path).iterdir() if f.suffix.lower() in extensions]
        for file in files:
            result = self.read_from_image(str(file))
            if result:
                for item in result:
                    self.results.append({
                        'file': file.name,
                        'data': item['text'],
                        'format': item['format']
                    })
        if output:
            self.export_results(output)
        return self.results

    def export_results(self, output_path):
        """Экспорт результатов в CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'data', 'format'])
            writer.writeheader()
            writer.writerows(self.results)

# ========== CLI ==========
def cli():
    parser = argparse.ArgumentParser(description="Ридер QR-кодов")
    parser.add_argument("--image", "-i", help="Путь к изображению")
    parser.add_argument("--batch", "-b", help="Папка для пакетного сканирования")
    parser.add_argument("--output", "-o", help="Файл для сохранения результатов (CSV)")
    parser.add_argument("--gui", action="store_true", help="Запустить GUI")
    args = parser.parse_args()

    if args.gui and GUI_AVAILABLE:
        root = tk.Tk()
        app = QRReaderGUI(root)
        root.mainloop()
        return

    reader = QRReader()
    if args.batch:
        results = reader.read_batch(args.batch, args.output)
        for r in results:
            print(f"{r['file']}: {r['data']}")
        print(f"\nОбработано {len(results)} файлов")
    elif args.image:
        results = reader.read_from_image(args.image)
        if results:
            for r in results:
                print(f"📷 QR-код распознан!")
                print(f"Данные: {r['text']}")
                print(f"Формат: {r['format']}")
        else:
            print("QR-код не найден")
    else:
        parser.print_help()

# ========== GUI ==========
if GUI_AVAILABLE:
    class QRReaderGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Ридер QR-кодов")
            self.root.geometry("700x600")
            self.root.resizable(True, True)
            self.reader = QRReader()
            self.create_widgets()

        def create_widgets(self):
            # Верхняя панель
            top_frame = tk.Frame(self.root)
            top_frame.pack(fill=tk.X, padx=10, pady=10)
            tk.Button(top_frame, text="📂 Открыть изображение", command=self.open_image,
                      bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(top_frame, text="📁 Пакетное сканирование", command=self.batch_scan,
                      bg="#2ecc71", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(top_frame, text="📋 Вставить из буфера", command=self.from_clipboard,
                      bg="#f39c12", fg="white").pack(side=tk.LEFT, padx=5)
            self.status_label = tk.Label(top_frame, text="Готов", fg="gray")
            self.status_label.pack(side=tk.RIGHT)

            # Результаты
            self.result_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20)
            self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.result_text.config(state='disabled')

            # Кнопка экспорта
            export_frame = tk.Frame(self.root)
            export_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Button(export_frame, text="💾 Сохранить результат", command=self.save_result,
                      bg="#9b59b6", fg="white").pack(side=tk.RIGHT)

        def log(self, message):
            self.result_text.config(state='normal')
            self.result_text.insert(tk.END, message + "\n")
            self.result_text.see(tk.END)
            self.result_text.config(state='disabled')

        def open_image(self):
            path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
            if path:
                self.status_label.config(text="Сканирование...", fg="blue")
                results = self.reader.read_from_image(path)
                self.status_label.config(text="Готов", fg="gray")
                if results:
                    for r in results:
                        self.log(f"📷 QR-код распознан!")
                        self.log(f"Данные: {r['text']}")
                        self.log(f"Формат: {r['format']}")
                        self.log("-" * 40)
                else:
                    self.log("QR-код не найден")

        def batch_scan(self):
            folder = filedialog.askdirectory()
            if folder:
                self.status_label.config(text="Пакетное сканирование...", fg="blue")
                results = self.reader.read_batch(folder)
                self.status_label.config(text="Готов", fg="gray")
                self.log(f"📁 Обработано {len(results)} файлов:")
                for r in results:
                    self.log(f"  {r['file']}: {r['data']}")

        def from_clipboard(self):
            try:
                from PIL import ImageGrab
                img = ImageGrab.grabclipboard()
                if img is None:
                    self.log("Буфер обмена пуст или не содержит изображения")
                    return
                # Сохраняем временно и сканируем
                temp_path = "temp_clipboard.png"
                img.save(temp_path)
                results = self.reader.read_from_image(temp_path)
                os.remove(temp_path)
                if results:
                    for r in results:
                        self.log(f"📷 QR-код из буфера обмена:")
                        self.log(f"Данные: {r['text']}")
                else:
                    self.log("QR-код не найден в буфере обмена")
            except Exception as e:
                self.log(f"Ошибка: {e}")

        def save_result(self):
            content = self.result_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Нет данных", "Нет результатов для сохранения")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")]
            )
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Сохранено", f"Сохранено в {path}")

if __name__ == "__main__":
    cli()
