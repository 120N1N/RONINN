#!/bin/bash
# ==========================================
# CORVUS DUAL-LLM VPS UPDATE SCRIPT
# ==========================================

echo "[*] Memulai pembaruan sistem Corvus ke arsitektur Dual-LLM..."

# 1. Menarik pembaruan kode terbaru dari Git
echo "[*] Menarik kode terbaru dari repository..."
git pull origin main

# 2. Menambahkan API Keys ke .env jika belum ada
echo "[*] Memeriksa konfigurasi .env..."

if ! grep -q "QWEN_API_KEY" .env; then
    echo 'QWEN_API_KEY="sk-ws-H.DMRYRDI.qQbv.MEYCIQC7R_HrkxD4jNeCVZ8SnnlUMcLTbIewYjPnsD4sNTRpgAIhALCkEr9QleWFQw81Wrt7hrN5y99HqEccx94pFQyY-7ET"' >> .env
    echo "  [+] QWEN_API_KEY berhasil ditambahkan."
fi

if ! grep -q "GEMINI_API_KEY" .env; then
    echo 'GEMINI_API_KEY="AQ.Ab8RN6JZbNVw3HZPz9FDy5Xkj25gLbAqxpUyYqg5GCs-kyyoxA"' >> .env
    echo "  [+] GEMINI_API_KEY berhasil ditambahkan."
fi

# 3. Build & Restart Docker
echo "[*] Menghentikan kontainer lama..."
docker-compose down

echo "[*] Membersihkan cache build lama (opsional)..."
docker builder prune -f

echo "[*] Melakukan build ulang dan menjalankan kontainer baru..."
docker-compose up -d --build

echo ""
echo "[SUCCESS] Pembaruan selesai! Corvus Dual-LLM sekarang aktif di VPS Anda."
echo "[INFO] Gunakan perintah 'docker-compose logs -f api' untuk melihat log server secara real-time."
