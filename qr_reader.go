// qr_reader.go - Ридер QR-кодов на Go (CLI)
// Установка: go get -u github.com/makiuchi-d/gozxing
package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"image"
	_ "image/gif"
	_ "image/jpeg"
	_ "image/png"
	"os"
	"path/filepath"
	"strings"

	"github.com/makiuchi-d/gozxing"
	"github.com/makiuchi-d/gozxing/qrcode"
)

func main() {
	var imagePath, batchPath, outputPath string
	flag.StringVar(&imagePath, "image", "", "Путь к изображению")
	flag.StringVar(&batchPath, "batch", "", "Папка для пакетного сканирования")
	flag.StringVar(&outputPath, "output", "", "Файл для сохранения результатов (CSV)")
	flag.Parse()

	if batchPath != "" {
		batchScan(batchPath, outputPath)
	} else if imagePath != "" {
		decodeImage(imagePath)
	} else {
		fmt.Println("Укажите --image или --batch")
	}
}

func decodeImage(path string) {
	file, err := os.Open(path)
	if err != nil {
		fmt.Printf("Ошибка открытия %s: %v\n", path, err)
		return
	}
	defer file.Close()

	img, _, err := image.Decode(file)
	if err != nil {
		fmt.Printf("Ошибка декодирования %s: %v\n", path, err)
		return
	}

	bmp, err := gozxing.NewBinaryBitmapFromImage(img)
	if err != nil {
		fmt.Printf("Ошибка создания битмапа: %v\n", err)
		return
	}

	qrReader := qrcode.NewQRCodeReader()
	result, err := qrReader.Decode(bmp, nil)
	if err != nil {
		fmt.Println("QR-код не найден")
		return
	}

	fmt.Printf("📷 QR-код распознан!\n")
	fmt.Printf("Данные: %s\n", result.GetText())
	fmt.Printf("Формат: %s\n", result.GetBarcodeFormat())
}

func batchScan(folder, output string) {
	entries, err := os.ReadDir(folder)
	if err != nil {
		fmt.Printf("Ошибка чтения папки: %v\n", err)
		return
	}

	var results [][]string
	extensions := map[string]bool{".png": true, ".jpg": true, ".jpeg": true, ".bmp": true, ".gif": true}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		ext := strings.ToLower(filepath.Ext(entry.Name()))
		if !extensions[ext] {
			continue
		}
		fullPath := filepath.Join(folder, entry.Name())
		file, err := os.Open(fullPath)
		if err != nil {
			continue
		}
		img, _, err := image.Decode(file)
		file.Close()
		if err != nil {
			continue
		}
		bmp, err := gozxing.NewBinaryBitmapFromImage(img)
		if err != nil {
			continue
		}
		qrReader := qrcode.NewQRCodeReader()
		result, err := qrReader.Decode(bmp, nil)
		if err == nil {
			results = append(results, []string{entry.Name(), result.GetText()})
			fmt.Printf("%s: %s\n", entry.Name(), result.GetText())
		}
	}

	if output != "" && len(results) > 0 {
		f, err := os.Create(output)
		if err != nil {
			fmt.Printf("Ошибка создания файла: %v\n", err)
			return
		}
		defer f.Close()
		writer := csv.NewWriter(f)
		writer.Write([]string{"file", "data"})
		writer.WriteAll(results)
		writer.Flush()
		fmt.Printf("Результаты сохранены в %s\n", output)
	}
}
