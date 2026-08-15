import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./corvus_red.db"

# Pastikan folder backend bisa di-import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db.database import SessionLocal
from backend.db import models
from backend.core.preprocess import DatasetPreprocessor

def import_local(file_path, label_col, dataset_name):
    if not os.path.exists(file_path):
        print(f"[!] Error: File '{file_path}' tidak ditemukan di folder!")
        return

    # Ambil user pertama yang ada di database untuk dijadikan "owner" dataset ini
    db = SessionLocal()
    user = db.query(models.User).first()
    if not user:
        print("[!] Error: Tidak ada user di database. Silakan buat akun/register terlebih dahulu di web UI Corvus.")
        db.close()
        return
    user_id = user.id
    db.close()

    print(f"\n=======================================================")
    print(f"[*] MEMULAI IMPOR LOKAL (BYPASS BROWSER UPLOAD LIMITS)")
    print(f"=======================================================")
    print(f"[*] File Target   : {file_path}")
    print(f"[*] Nama Dataset  : {dataset_name}")
    print(f"[*] Kolom Label   : {label_col}\n")

    try:
        # Panggil class Preprocessor persis seperti yang dilakukan di backend
        df = DatasetPreprocessor.load_data(file_path)
        df = DatasetPreprocessor.map_labels(df, label_col)
        df = DatasetPreprocessor.extract_features(df)
        df = DatasetPreprocessor.handle_missing(df)
        X_train, X_test, y_train, y_test = DatasetPreprocessor.split_data(df)
        
        # Simpan ke disk dan DB
        dataset_id = DatasetPreprocessor.save_preprocessed(X_train, X_test, y_train, y_test, dataset_name, user_id)
        
        print(f"\n[+] BERHASIL LULUS PREPROCESSING!")
        print(f"[+] Dataset '{dataset_name}' sukses diimpor dan disimpan ke database.")
        print(f"[+] Dataset ID: {dataset_id}")
        print(f"\n[>] Silakan cek halaman 'AI Engine' di Web UI. Dataset Anda sudah muncul dan siap untuk di-Training!")
    except Exception as e:
        print(f"\n[!] TERJADI ERROR SAAT PREPROCESSING: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Penggunaan: python import_dataset.py <nama_file.csv> <kolom_label> \"<Nama Dataset>\"")
        print("Contoh    : python import_dataset.py guide.csv IncidentGrade \"Microsoft GUIDE Raksasa\"")
        sys.exit(1)
    
    file_path = sys.argv[1]
    label_col = sys.argv[2]
    dataset_name = sys.argv[3]
    
    import_local(file_path, label_col, dataset_name)
