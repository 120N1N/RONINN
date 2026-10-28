# Corvus - Automated Pentest & Vulnerability Analysis Platform

Corvus is a sophisticated security orchestration platform designed for automated vulnerability scanning, mapping (OWASP), and risk analysis.

## Features
- **Multi-Tool Orchestration**: Seamless integration of Recon, Discovery, Fuzzing, and Scanning tools.
- **Real-time Monitoring**: WebSocket-based progress updates.
- **Agentic AI Deep Validate**: LLM-powered automatic fetching and DOM validation for Client-Side vulnerabilities to eliminate False Positives.
- **Vulnerability Analysis**: Automatic deduplication and normalization of findings with LLM assistance.
- **Per-User API Keys**: Secure, isolated LLM API key management for individual authenticated users.
- **JS Secret Extraction**: Deep parsing of JavaScript files for leaked secrets.
- **Modern Stack**: FastAPI, Celery, Redis, PostgreSQL, and React.
- **Dockerized**: One-command deployment.

## Tool Stack
- **Recon**: subfinder, assetfinder, httpx
- **Discovery**: gau, katana, jsfinder
- **Scanning**: nuclei, dalfox, sqlmap
- **Validation**: Playwright/Requests (Agentic Fetcher)
- **Custom**: JS Secret Extraction engine

## Cara Menjalankan Aplikasi (Panduan Pemula)

Aplikasi Corvus ini terbagi menjadi dua bagian utama:
1. **Backend (API & Worker)**: Mesin utama yang bekerja di belakang layar untuk memproses data, database, dan pemindaian keamanan.
2. **Frontend (Web)**: Tampilan antarmuka yang Anda lihat dan klik di browser.

Anda bisa memilih **salah satu** dari dua cara di bawah ini untuk menyalakan aplikasi: **Cara Otomatis (Docker)** atau **Cara Manual (Standalone)**.

---

### Cara 1: Menjalankan Secara Otomatis dengan Docker (Sangat Direkomendasikan)
Cara ini paling mudah karena Docker akan otomatis menyalakan Frontend, Backend, dan Database sekaligus di dalam "wadah" virtual. Anda tidak perlu repot menginstal komponen satu per satu.

1. Pastikan aplikasi **Docker** dan **Docker Compose** sudah terinstal dan berjalan di komputer Anda.
2. Buka terminal (Command Prompt/PowerShell/Bash) dan masuk ke folder tempat file ini berada.
3. Nyalakan aplikasi sesuai sistem operasi Anda:
   - **Bagi pengguna Linux / macOS / WSL**:
     Jalankan script otomatis ini:
     ```bash
     bash setup.sh
     ```
   - **Bagi pengguna Windows (Manual Docker Compose)**:
     Jalankan dua perintah ini secara berurutan:
     ```bash
     docker-compose up -d --build
     docker-compose exec api alembic upgrade head || docker-compose exec api python migrate.py
     ```
4. **Selesai!** Anda bisa mengakses aplikasi melalui browser:
   - Tampilan Web (Frontend): `http://localhost` (Docker menyetelnya di port 80)
   - Dokumentasi API Backend: `http://localhost:8000/api/docs`

---

### Cara 2: Menjalankan Secara Manual (Standalone / Tanpa Docker)
Gunakan cara ini jika Anda ingin memodifikasi kode (sebagai developer) atau sistem Anda tidak mendukung Docker. Anda harus menyalakan Backend dan Frontend di jendela terminal yang terpisah.

#### A. Menyalakan Backend
1. Pastikan **Python** sudah terinstal.
2. Buka terminal dan install pustaka yang dibutuhkan: 
   `pip install -r requirements.txt`
3. (Opsional) Jalankan migrasi database jika diperlukan oleh sistem FastAPI.
4. **Nyalakan Server API**: 
   `python -m backend.app`
5. **Nyalakan Celery Worker** (Buka **Terminal Baru**): 
   `celery -A backend.queue.celery_app worker --loglevel=info`

#### B. Menyalakan Frontend
1. Pastikan **Node.js** sudah terinstal.
2. Buka **Terminal Baru** dan masuk ke folder frontend: 
   `cd frontend`
3. Install package yang dibutuhkan: 
   `npm install`
4. Nyalakan server tampilan web: 
   `npm run dev`
5. Frontend biasanya bisa diakses di `http://localhost:5173` atau `http://localhost:3000` sesuai info di terminal.

---

### Cara Khusus: Menjalankan di VPS (Virtual Private Server) atau WSL
Jika Anda ingin mengonlinekan Corvus di VPS (seperti Ubuntu/Debian di AWS, DigitalOcean, dll) atau menggunakan **WSL** di Windows, langkah-langkahnya pada dasarnya sama persis dengan **Cara 1 (Docker)**.

**Langkah-langkah Komplit di VPS (Ubuntu/Debian) / WSL:**
Cukup *copy-paste* perintah di bawah ini secara berurutan ke terminal Anda agar bebas error:

1. **Update sistem dan install Git & Docker:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install git docker.io docker-compose -y
   ```

2. **Nyalakan layanan Docker dan cek versinya (Verifikasi):**
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   docker --version
   docker-compose --version
   ```
   *(Pastikan tidak ada error dan versi Docker muncul di layar)*

3. **Unduh (clone) repository Corvus dan masuk ke foldernya:**
   ```bash
   git clone https://github.com/DRL-GITHUB/RONINN.git
   cd RONINN/CORVUS-P
   ```
   *(Catatan: Sesuaikan link `git clone` dengan link repository asli Anda jika berbeda)*

4. **Jalankan script instalasi otomatis:**
   ```bash
   bash setup.sh
   ```

5. **Selesai! Aplikasi sedang berjalan.** 
   - **Di WSL:** Buka browser Windows Anda dan kunjungi `http://localhost`
   - **Di VPS:** Buka browser dan kunjungi Alamat IP VPS Anda (contoh: `http://192.168.1.50`)

**Tips Khusus Pengguna VPS (Cara Update):**
Jika ada pembaruan kode terbaru, Anda tidak perlu menginstal ulang dari awal. Cukup jalankan script pembaruan yang sudah kami sediakan:
```bash
bash update_vps.sh
```
Script ini otomatis akan menarik kode baru, mengatur API Key bawaan (Dual-LLM), dan merestart server Anda dengan bersih.

## Ethical Use
Corvus is intended for authorized security testing only. Scanning targets without explicit permission is illegal and unethical.

## 📚 Documentation
Corvus Red Edition uses MkDocs Material for professional documentation.

### Build Documentation
```bash
pip install mkdocs-material
mkdocs build
```

### Serve Locally
```bash
mkdocs serve
```
The documentation will be available at `http://127.0.0.1:8000`.

## License
MIT License
