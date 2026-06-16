// QRReader.cs - Ридер QR-кодов на C# (CLI + WinForms)
// Требует ZXing.Net: Install-Package ZXing.Net
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using ZXing;

namespace QRReader
{
    public class QRReader
    {
        // ========== ОСНОВНАЯ ЛОГИКА ==========
        public static string DecodeQR(Bitmap image)
        {
            var reader = new BarcodeReader();
            var result = reader.Decode(image);
            return result?.Text;
        }

        public static string DecodeQRFromFile(string path)
        {
            try
            {
                using (var image = new Bitmap(path))
                {
                    return DecodeQR(image);
                }
            }
            catch
            {
                return null;
            }
        }

        public static Dictionary<string, string> BatchScan(string folder)
        {
            var results = new Dictionary<string, string>();
            var dir = new DirectoryInfo(folder);
            if (!dir.Exists) return results;
            var extensions = new[] { ".png", ".jpg", ".jpeg", ".bmp", ".gif" };
            foreach (var file in dir.GetFiles())
            {
                if (!extensions.Contains(file.Extension.ToLower())) continue;
                var data = DecodeQRFromFile(file.FullName);
                if (data != null)
                {
                    results[file.Name] = data;
                    Console.WriteLine($"{file.Name}: {data}");
                }
            }
            return results;
        }

        // ========== CLI ==========
        static void Main(string[] args)
        {
            if (args.Length > 0 && args[0] == "--gui")
            {
                Application.EnableVisualStyles();
                Application.Run(new QRReaderGUI());
                return;
            }
            // CLI режим
            string image = null, batch = null, output = null;
            for (int i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--image": image = args[++i]; break;
                    case "--batch": batch = args[++i]; break;
                    case "--output": output = args[++i]; break;
                }
            }
            try
            {
                if (batch != null)
                {
                    var results = BatchScan(batch);
                    if (output != null)
                    {
                        var lines = new List<string> { "file,data" };
                        lines.AddRange(results.Select(kv => $"{kv.Key},\"{kv.Value}\""));
                        File.WriteAllLines(output, lines);
                        Console.WriteLine($"Результаты сохранены в {output}");
                    }
                }
                else if (image != null)
                {
                    var data = DecodeQRFromFile(image);
                    if (data != null)
                    {
                        Console.WriteLine("📷 QR-код распознан!");
                        Console.WriteLine($"Данные: {data}");
                    }
                    else
                    {
                        Console.WriteLine("QR-код не найден");
                    }
                }
                else
                {
                    Console.WriteLine("Укажите --image или --batch, или --gui для GUI");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Ошибка: {ex.Message}");
            }
        }

        // ========== GUI ==========
        public class QRReaderGUI : Form
        {
            private TextBox resultBox;
            private Label statusLabel;

            public QRReaderGUI()
            {
                Text = "Ридер QR-кодов";
                Size = new Size(600, 500);
                StartPosition = FormStartPosition.CenterScreen;

                var topPanel = new FlowLayoutPanel { Dock = DockStyle.Top, Padding = new Padding(5) };
                var openBtn = new Button { Text = "📂 Открыть изображение", AutoSize = true };
                openBtn.Click += (s, e) => OpenImage();
                topPanel.Controls.Add(openBtn);
                var batchBtn = new Button { Text = "📁 Пакетное сканирование", AutoSize = true };
                batchBtn.Click += (s, e) => BatchScan();
                topPanel.Controls.Add(batchBtn);
                statusLabel = new Label { Text = "Готов", AutoSize = true };
                topPanel.Controls.Add(statusLabel);
                Controls.Add(topPanel);

                resultBox = new TextBox { Multiline = true, Dock = DockStyle.Fill, ReadOnly = true, ScrollBars = ScrollBars.Vertical };
                Controls.Add(resultBox);

                var saveBtn = new Button { Text = "💾 Сохранить результат", Dock = DockStyle.Bottom, Height = 30 };
                saveBtn.Click += (s, e) => SaveResult();
                Controls.Add(saveBtn);
            }

            private void Log(string msg)
            {
                resultBox.AppendText(msg + Environment.NewLine);
            }

            private void OpenImage()
            {
                var ofd = new OpenFileDialog { Filter = "Image files|*.png;*.jpg;*.jpeg;*.bmp;*.gif" };
                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    statusLabel.Text = "Сканирование...";
                    var data = DecodeQRFromFile(ofd.FileName);
                    statusLabel.Text = "Готов";
                    if (data != null)
                    {
                        Log("📷 QR-код распознан!");
                        Log($"Данные: {data}");
                        Log(new string('-', 40));
                    }
                    else
                    {
                        Log("QR-код не найден");
                    }
                }
            }

            private void BatchScan()
            {
                using (var fbd = new FolderBrowserDialog())
                {
                    if (fbd.ShowDialog() == DialogResult.OK)
                    {
                        statusLabel.Text = "Пакетное сканирование...";
                        var results = QRReader.BatchScan(fbd.SelectedPath);
                        statusLabel.Text = "Готов";
                        Log($"📁 Обработано {results.Count} файлов:");
                        foreach (var kv in results)
                        {
                            Log($"  {kv.Key}: {kv.Value}");
                        }
                    }
                }
            }

            private void SaveResult()
            {
                if (string.IsNullOrEmpty(resultBox.Text))
                {
                    MessageBox.Show("Нет результатов для сохранения");
                    return;
                }
                var sfd = new SaveFileDialog { Filter = "Text files|*.txt|CSV files|*.csv", DefaultExt = "txt" };
                if (sfd.ShowDialog() == DialogResult.OK)
                {
                    File.WriteAllText(sfd.FileName, resultBox.Text);
                    MessageBox.Show("Сохранено");
                }
            }
        }
    }
}
