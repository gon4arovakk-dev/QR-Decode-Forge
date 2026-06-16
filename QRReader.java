// QRReader.java - Ридер QR-кодов на Java (CLI + Swing GUI)
// Требует ZXing: https://github.com/zxing/zxing/releases
import com.google.zxing.*;
import com.google.zxing.client.j2se.BufferedImageLuminanceSource;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.qrcode.QRCodeReader;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.List;

public class QRReader {
    // ========== ОСНОВНАЯ ЛОГИКА ==========
    public static String decodeQR(BufferedImage image) throws NotFoundException {
        LuminanceSource source = new BufferedImageLuminanceSource(image);
        BinaryBitmap bitmap = new BinaryBitmap(new HybridBinarizer(source));
        QRCodeReader reader = new QRCodeReader();
        Result result = reader.decode(bitmap);
        return result.getText();
    }

    public static String decodeQRFromFile(String path) {
        try {
            BufferedImage image = ImageIO.read(new File(path));
            if (image == null) {
                return null;
            }
            return decodeQR(image);
        } catch (Exception e) {
            return null;
        }
    }

    public static Map<String, String> batchScan(String folder) {
        Map<String, String> results = new LinkedHashMap<>();
        File dir = new File(folder);
        if (!dir.exists() || !dir.isDirectory()) {
            return results;
        }
        String[] extensions = {"png", "jpg", "jpeg", "bmp", "gif"};
        for (File file : dir.listFiles()) {
            if (file.isDirectory()) continue;
            String name = file.getName().toLowerCase();
            boolean isImage = false;
            for (String ext : extensions) {
                if (name.endsWith("." + ext)) {
                    isImage = true;
                    break;
                }
            }
            if (!isImage) continue;
            String data = decodeQRFromFile(file.getAbsolutePath());
            if (data != null) {
                results.put(file.getName(), data);
                System.out.println(file.getName() + ": " + data);
            }
        }
        return results;
    }

    // ========== CLI ==========
    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("--gui")) {
            SwingUtilities.invokeLater(() -> new QRReaderGUI().setVisible(true));
            return;
        }
        // CLI режим
        String image = null, batch = null, output = null;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--image": image = args[++i]; break;
                case "--batch": batch = args[++i]; break;
                case "--output": output = args[++i]; break;
            }
        }
        try {
            if (batch != null) {
                Map<String, String> results = batchScan(batch);
                if (output != null) {
                    StringBuilder sb = new StringBuilder("file,data\n");
                    for (Map.Entry<String, String> e : results.entrySet()) {
                        sb.append(e.getKey()).append(",\"").append(e.getValue()).append("\"\n");
                    }
                    Files.write(Paths.get(output), sb.toString().getBytes());
                    System.out.println("Результаты сохранены в " + output);
                }
            } else if (image != null) {
                String data = decodeQRFromFile(image);
                if (data != null) {
                    System.out.println("📷 QR-код распознан!");
                    System.out.println("Данные: " + data);
                } else {
                    System.out.println("QR-код не найден");
                }
            } else {
                System.out.println("Укажите --image или --batch, или --gui для GUI");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // ========== GUI ==========
    static class QRReaderGUI extends JFrame {
        private JTextArea resultArea;
        private JLabel statusLabel;

        public QRReaderGUI() {
            setTitle("Ридер QR-кодов");
            setSize(600, 500);
            setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            setLayout(new BorderLayout(10, 10));

            JPanel topPanel = new JPanel();
            JButton openBtn = new JButton("📂 Открыть изображение");
            openBtn.addActionListener(e -> openImage());
            topPanel.add(openBtn);
            JButton batchBtn = new JButton("📁 Пакетное сканирование");
            batchBtn.addActionListener(e -> batchScan());
            topPanel.add(batchBtn);
            statusLabel = new JLabel("Готов");
            topPanel.add(statusLabel);
            add(topPanel, BorderLayout.NORTH);

            resultArea = new JTextArea();
            resultArea.setEditable(false);
            add(new JScrollPane(resultArea), BorderLayout.CENTER);

            JButton saveBtn = new JButton("💾 Сохранить результат");
            saveBtn.addActionListener(e -> saveResult());
            add(saveBtn, BorderLayout.SOUTH);
        }

        private void log(String msg) {
            resultArea.append(msg + "\n");
        }

        private void openImage() {
            JFileChooser fc = new JFileChooser();
            fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
                "Images", "png", "jpg", "jpeg", "bmp", "gif"));
            if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                statusLabel.setText("Сканирование...");
                String data = decodeQRFromFile(fc.getSelectedFile().getAbsolutePath());
                statusLabel.setText("Готов");
                if (data != null) {
                    log("📷 QR-код распознан!");
                    log("Данные: " + data);
                    log("-".repeat(40));
                } else {
                    log("QR-код не найден");
                }
            }
        }

        private void batchScan() {
            JFileChooser fc = new JFileChooser();
            fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                statusLabel.setText("Пакетное сканирование...");
                Map<String, String> results = QRReader.batchScan(fc.getSelectedFile().getAbsolutePath());
                statusLabel.setText("Готов");
                log("📁 Обработано " + results.size() + " файлов:");
                for (Map.Entry<String, String> e : results.entrySet()) {
                    log("  " + e.getKey() + ": " + e.getValue());
                }
            }
        }

        private void saveResult() {
            String content = resultArea.getText();
            if (content.isEmpty()) {
                JOptionPane.showMessageDialog(this, "Нет результатов для сохранения");
                return;
            }
            JFileChooser fc = new JFileChooser();
            if (fc.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
                try {
                    Files.write(Paths.get(fc.getSelectedFile().getAbsolutePath()), content.getBytes());
                    JOptionPane.showMessageDialog(this, "Сохранено");
                } catch (IOException e) {
                    JOptionPane.showMessageDialog(this, "Ошибка: " + e.getMessage());
                }
            }
        }
    }
}
