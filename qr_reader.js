// qr_reader.js - Ридер QR-кодов на JavaScript (Node.js CLI + браузер)
// Для Node.js: npm install jsqr canvas
// Для браузера: используйте библиотеку jsQR или @zxing/browser

// ========== CLI (Node.js) ==========
if (typeof require !== 'undefined' && require.main === module) {
    const fs = require('fs');
    const path = require('path');
    const { createCanvas, loadImage } = require('canvas');
    const jsQR = require('jsqr');
    const { program } = require('commander');

    program
        .option('-i, --image <path>', 'Путь к изображению')
        .option('-b, --batch <path>', 'Папка для пакетного сканирования')
        .option('-o, --output <path>', 'Файл для сохранения результатов')
        .parse(process.argv);

    const opts = program.opts();

    async function decodeQR(imagePath) {
        try {
            const image = await loadImage(imagePath);
            const canvas = createCanvas(image.width, image.height);
            const ctx = canvas.getContext('2d');
            ctx.drawImage(image, 0, 0);
            const imageData = ctx.getImageData(0, 0, image.width, image.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            if (code) {
                return { text: code.data, format: 'QR Code' };
            }
            return null;
        } catch (err) {
            console.error(`Ошибка чтения ${imagePath}: ${err.message}`);
            return null;
        }
    }

    async function batchScan(folder) {
        const files = fs.readdirSync(folder).filter(f => 
            /\.(png|jpg|jpeg|bmp|gif)$/i.test(f)
        );
        const results = [];
        for (const file of files) {
            const fullPath = path.join(folder, file);
            const result = await decodeQR(fullPath);
            if (result) {
                results.push({ file, data: result.text });
                console.log(`${file}: ${result.text}`);
            }
        }
        if (opts.output) {
            const csv = ['file,data', ...results.map(r => `${r.file},"${r.data}"`)].join('\n');
            fs.writeFileSync(opts.output, csv);
            console.log(`Результаты сохранены в ${opts.output}`);
        }
        return results;
    }

    async function main() {
        if (opts.batch) {
            await batchScan(opts.batch);
        } else if (opts.image) {
            const result = await decodeQR(opts.image);
            if (result) {
                console.log(`📷 QR-код распознан!`);
                console.log(`Данные: ${result.text}`);
                console.log(`Формат: ${result.format}`);
            } else {
                console.log('QR-код не найден');
            }
        } else {
            console.log('Укажите --image или --batch');
        }
    }

    main();
}

// ========== Браузерная версия ==========
if (typeof window !== 'undefined') {
    // Используем библиотеку jsQR для браузера
    // Подключите: <script src="https://cdn.jsdelivr.net/npm/jsqr/dist/jsQR.js"></script>
    window.decodeQRFromImage = function(imageData) {
        const code = jsQR(imageData.data, imageData.width, imageData.height);
        if (code) {
            return code.data;
        }
        return null;
    };

    // Функция для чтения из файла
    window.readQRFromFile = function(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    const imageData = ctx.getImageData(0, 0, img.width, img.height);
                    const result = decodeQRFromImage(imageData);
                    resolve(result);
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    };

    // Функция для чтения из видеопотока
    window.startCamera = function(videoElement, onResult) {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => {
                videoElement.srcObject = stream;
                videoElement.setAttribute('playsinline', true);
                videoElement.play();
                // Запускаем сканирование кадров
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                function scanFrame() {
                    if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                        canvas.width = videoElement.videoWidth;
                        canvas.height = videoElement.videoHeight;
                        ctx.drawImage(videoElement, 0, 0);
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const result = decodeQRFromImage(imageData);
                        if (result) {
                            onResult(result);
                            return;
                        }
                    }
                    requestAnimationFrame(scanFrame);
                }
                scanFrame();
            })
            .catch(err => {
                console.error('Ошибка доступа к камере:', err);
            });
    };
}
