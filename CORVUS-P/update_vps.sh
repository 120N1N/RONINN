#!/bin/bash
# ==========================================
# CORVUS DUAL-LLM VPS UPDATE SCRIPT
# ==========================================

echo "[*] Memulai pembaruan sistem Corvus ke arsitektur Dual-LLM..."

# 1. Menarik pembaruan kode terbaru dari Git
echo "[*] Menarik kode terbaru dari repository..."
git pull origin main

# 2. Environment Variables Configuration
echo "[*] Memeriksa konfigurasi .env... Pastikan API Keys telah diatur secara aman."

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
