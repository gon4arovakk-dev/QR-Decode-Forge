// qr_reader.rs - Ридер QR-кодов на Rust (CLI)
// Зависимости: rqrr, image, clap
use clap::{Arg, App};
use image::{GenericImageView, ImageFormat};
use rqrr::PreparedImage;
use std::fs;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let matches = App::new("QR Reader")
        .arg(Arg::with_name("image").short("i").long("image").takes_value(true).help("Путь к изображению"))
        .arg(Arg::with_name("batch").short("b").long("batch").takes_value(true).help("Папка для пакетного сканирования"))
        .arg(Arg::with_name("output").short("o").long("output").takes_value(true).help("Файл для сохранения результатов"))
        .get_matches();

    if let Some(batch) = matches.value_of("batch") {
        batch_scan(batch, matches.value_of("output"))?;
    } else if let Some(image) = matches.value_of("image") {
        decode_image(image)?;
    } else {
        println!("Укажите --image или --batch");
    }
    Ok(())
}

fn decode_image(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let img = image::open(path)?;
    let (width, height) = img.dimensions();
    let gray = img.to_luma8();

    let prepared = PreparedImage::prepare(gray);
    let results = prepared.detect_codes()?;

    if results.is_empty() {
        println!("QR-код не найден");
        return Ok(());
    }

    for result in results {
        println!("📷 QR-код распознан!");
        println!("Данные: {}", result.data());
    }
    Ok(())
}

fn batch_scan(folder: &str, output: Option<&str>) -> Result<(), Box<dyn std::error::Error>> {
    let extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif"];
    let mut results = Vec::new();

    for entry in fs::read_dir(folder)? {
        let entry = entry?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
        let ext = format!(".{}", ext.to_lowercase());
        if !extensions.contains(&ext.as_str()) {
            continue;
        }

        if let Ok(img) = image::open(&path) {
            let gray = img.to_luma8();
            let prepared = PreparedImage::prepare(gray);
            if let Ok(codes) = prepared.detect_codes() {
                for code in codes {
                    let name = path.file_name().unwrap().to_string_lossy();
                    println!("{}: {}", name, code.data());
                    results.push((name.to_string(), code.data().to_string()));
                }
            }
        }
    }

    if let Some(out) = output {
        use std::io::Write;
        let mut file = fs::File::create(out)?;
        writeln!(file, "file,data")?;
        for (name, data) in results {
            writeln!(file, "{},\"{}\"", name, data)?;
        }
        println!("Результаты сохранены в {}", out);
    }
    Ok(())
}
