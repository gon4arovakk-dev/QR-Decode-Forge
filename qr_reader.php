<?php
// qr_reader.php - Ридер QR-кодов на PHP (CLI + веб)
// Требует: composer require khanamiryan/qrcode-detector-decoder
// CLI: php qr_reader.php --image=qr.png
// Веб: откройте в браузере

if (php_sapi_name() === 'cli') {
    // CLI режим
    $options = getopt("", ["image:", "batch:", "output:"]);
    $image = $options['image'] ?? null;
    $batch = $options['batch'] ?? null;
    $output = $options['output'] ?? null;

    require_once 'vendor/autoload.php';
    use Zxing\QrReader;

    function decodeQR($path) {
        try {
            $reader = new QrReader($path);
            return $reader->text();
        } catch (Exception $e) {
            return null;
        }
    }

    if ($batch) {
        $results = [];
        $files = glob($batch . '/*.{png,jpg,jpeg,bmp,gif}', GLOB_BRACE);
        foreach ($files as $file) {
            $data = decodeQR($file);
            if ($data) {
                $name = basename($file);
                $results[$name] = $data;
                echo "$name: $data\n";
            }
        }
        if ($output) {
            $csv = "file,data\n";
            foreach ($results as $name => $data) {
                $csv .= "$name,\"$data\"\n";
            }
            file_put_contents($output, $csv);
            echo "Результаты сохранены в $output\n";
        }
    } elseif ($image) {
        $data = decodeQR($image);
        if ($data) {
            echo "📷 QR-код распознан!\n";
            echo "Данные: $data\n";
        } else {
            echo "QR-код не найден\n";
        }
    } else {
        echo "Укажите --image или --batch\n";
    }
    exit;
}

// ========== ВЕБ-ИНТЕРФЕЙС ==========
require_once 'vendor/autoload.php';
use Zxing\QrReader;

$result = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['qr_image'])) {
    $file = $_FILES['qr_image'];
    if ($file['error'] === UPLOAD_ERR_OK) {
        try {
            $reader = new QrReader($file['tmp_name']);
            $result = $reader->text();
            if (!$result) {
                $error = "QR-код не найден";
            }
        } catch (Exception $e) {
            $error = "Ошибка: " . $e->getMessage();
        }
    } else {
        $error = "Ошибка загрузки файла";
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ридер QR-кодов (PHP)</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7fb; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { display: flex; align-items: center; gap: 10px; }
        .drop-zone { border: 2px dashed #ccc; border-radius: 16px; padding: 40px; text-align: center; margin: 20px 0; cursor: pointer; transition: 0.2s; }
        .drop-zone:hover { border-color: #3498db; background: #f0f8ff; }
        .drop-zone.dragover { border-color: #2ecc71; background: #e8f5e9; }
        input[type="file"] { display: none; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; }
        .result { background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; }
        .error { background: #ffebee; padding: 15px; border-radius: 8px; margin: 20px 0; color: #c62828; }
        .batch-upload { margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
    </style>
</head>
<body>
<div class="container">
    <h1>📷 Ридер QR-кодов</h1>
    <p>Загрузите изображение с QR-кодом для распознавания.</p>

    <form method="POST" enctype="multipart/form-data" id="uploadForm">
        <div class="drop-zone" id="dropZone">
            <p>📁 Перетащите файл сюда или нажмите для выбора</p>
            <input type="file" name="qr_image" id="fileInput" accept="image/*">
        </div>
        <button type="submit">🔍 Распознать</button>
    </form>

    <?php if ($result): ?>
        <div class="result">
            <strong>📷 QR-код распознан!</strong><br>
            <strong>Данные:</strong> <?= htmlspecialchars($result) ?>
        </div>
    <?php elseif ($error): ?>
        <div class="error"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <div class="batch-upload">
        <h3>📁 Пакетное сканирование</h3>
        <p>Загрузите ZIP-архив с изображениями или укажите папку через CLI.</p>
        <small>CLI: php qr_reader.php --batch=/path/to/images --output=results.csv</small>
    </div>
</div>

<script>
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            document.getElementById('uploadForm').submit();
        }
    });
</script>
</body>
</html>
