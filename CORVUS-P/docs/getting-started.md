# <span class="corvus-glitch" data-text="Corvus">Corvus</span> Red Edition – Automated Web Security Assessment
> *Precision Auditing. Zero Destruction. Professional Intelligence.*

![Version](https://img.shields.io/badge/version-2.1.0--red-red)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## Daftar Isi
- [Gambaran Umum](#gambaran-umum)
- [Filosofi dan Solusi](#filosofi-dan-solusi)
- [Pengguna Sasaran](#pengguna-sasaran)
- [Batasan Operasional](#batasan-operasional)
- [Skenario Implementasi](#skenario-implementasi)
- [Arsitektur dan Metodologi](#arsitektur-dan-metodologi)
- [Fase Audit](#fase-audit)
- [Format Temuan](#format-temuan)
- [Etika dan Keamanan](#etika-dan-keamanan)
* [Panduan Instalasi](#panduan-instalasi)
- [Referensi API](#referensi-api)
- [Perbandingan Mode](#perbandingan-mode)
- [FAQ](#faq)
- [Lisensi](#lisensi)

---

## Gambaran Umum
Corvus Red Edition adalah platform manajemen audit keamanan web otomatis yang dirancang untuk memberikan visibilitas mendalam terhadap postur risiko aset digital. Dibangun di atas fondasi modular, Corvus menggabungkan berbagai instrumen audit industri ke dalam satu orkestra cerdas untuk menghasilkan laporan kerentanan yang akurat, konsisten, dan dapat ditindaklanjuti.

Sistem ini dirancang khusus untuk audit infrastruktur nyata, mengutamakan stabilitas sistem target di atas segalanya. Tidak seperti alat penyerangan konvensional, Corvus berfokus pada pemetaan risiko berbasis bukti tanpa melakukan tindakan eksploitasi yang merusak.

## Filosofi dan Solusi
Corvus lahir sebagai jawaban atas kompleksitas audit keamanan di lingkungan enterprise yang dinamis.

| Tantangan Audit Manual | Solusi Corvus Red Edition |
| :--- | :--- |
| **Inkonsistensi**: Hasil scan berbeda-beda meski target sama. | **Idempotensi**: Algoritma hashing memastikan hasil yang konsisten dan reproduktif. |
| **Destruktif**: Script agresif dapat menjatuhkan layanan target. | **Non-Destructive**: Hanya menggunakan teknik probing aman tanpa eksploitasi muatan (payload). |
| **Overflow Data**: Temuan duplikat yang membingungkan auditor. | **Deduplikasi Cerdas**: Fingerprinting temuan lintas scan untuk eliminasi redundansi. |
| **Silo Data**: Hasil tool terpisah-pisah. | **Normalisasi Terpusat**: Seluruh data tool dinormalisasi ke format JSON standar. |
| **False Positives**: Scanner sering kali salah menebak kerentanan. | **Agentic AI Deep Validate**: LLM secara otomatis memverifikasi bukti lewat *fetching* DOM langsung ke target. |

## Pengguna Sasaran
Platform ini dirancang untuk profesional yang membutuhkan data keamanan yang valid dan terstruktur.

| Peran | Manfaat Utama |
| :--- | :--- |
| **Security Engineer** | Mengotomatiskan tugas reconnaissance dan discovery yang repetitif. |
| **DevSecOps Team** | Integrasi audit keamanan ke dalam siklus pipeline SDLC (via API). |
| **System Administrator** | Memastikan konfigurasi server (headers, CORS, SSL) tetap aman. |
| **CISO / Head of Security** | Mendapatkan ringkasan risiko infrastruktur secara real-time. |

## Batasan Operasional
Untuk menjaga etika dan stabilitas, Corvus Red Edition beroperasi dalam koridor yang tegas:
1.  **Izin Eksplisit**: Hanya diperbolehkan untuk aset yang telah mendapatkan otorisasi tertulis.
2.  **Blokir IP Privat**: Untuk mencegah SSRF, target yang mengarah ke IP privat internal diblokir secara otomatis:
    *   `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`.
3.  **Batas Kecepatan**: Implementasi *rate limiting* yang ketat (maksimal 5 request per detik pada modul kustom).
4.  **No Exploit**: Tidak melakukan SQL Injection, RCE, atau Brute-Force yang dapat mengubah data atau menjatuhkan sistem target.

## Skenario Implementasi
Corvus Red Edition fleksibel digunakan dalam berbagai fase manajemen risiko:
*   **Audit Rutin**: Scan mingguan untuk memastikan tidak ada perubahan konfigurasi yang tidak diinginkan.
*   **Pre-Deployment**: Melakukan pengecekan akhir sebelum aplikasi naik ke lingkungan produksi.
*   **Asset Discovery**: Mencari subdomain atau endpoint baru yang tidak terdata dalam inventori lama.

**Estimasi Waktu:**
*   **Quick Mode**: ~2-5 menit (Fokus pada headers dan layanan utama).
*   **Normal Mode**: ~10-20 menit (Full discovery dan port scanning).
*   **Deep Mode**: >30 menit (Crawling mendalam dan brute-force direktori aman).

## Arsitektur dan Metodologi
Sistem Corvus bekerja secara asinkron menggunakan arsitektur Worker-Queue berbasis Celery dan Redis.

```text
[ Dashboard UI ] <--> [ Flask API ] <--> [ Redis Queue ] <--> [ Celery Workers ]
                                              |                    |
                                        [ PostgreSQL ]       [ Security Tools ]
```

**Alur Kerja:**
1.  **Request**: Pengguna mengirimkan target melalui Dashboard atau API.
2.  **Orchestration**: Orchestrator membagi scan menjadi beberapa fase modular.
3.  **Execution**: Worker menjalankan tool keamanan aslinya dan menyimpan output mentah.
4.  **Normalization**: Hasil mentah diparsing ke format standar Corvus.
5.  **Deduplication**: Hasil dibandingkan dengan scan sebelumnya untuk menandai duplikasi.
6.  **Reporting**: Data disajikan kembali ke pengguna.

## Fase Audit
Corvus menjalankan 6 fase sistematis untuk memastikan cakupan audit maksimal:

1.  **PHASE 1: RECONNAISSANCE**
    *   Pengumpulan data publik, DNS records, dan pemetaan teknologi (`Wappalyzer`, `Subfinder`).
2.  **PHASE 2: ENUMERATION**
    *   Pemindaian port terbuka dan identifikasi layanan (`Nmap`).
3.  **PHASE 3: DISCOVERY**
    *   Pencarian file/direktori sensitif dan endpoint API (`Ffuf`, `Dirsearch`).
4.  **PHASE 4: VULN SCANNING**
    *   Pendeteksian kerentanan umum berbasis template (`Nuclei`).
5.  **PHASE 5: CUSTOM CHECKS**
    *   Modul internal Corvus untuk audit Header Keamanan, CORS Policy, XXE Potential, dan Rate Limiting.
6.  **PHASE 6: NORMALIZATION & DIFF**
    *   Penyatuan seluruh hasil dan perbandingan dengan baseline scan sebelumnya.

## Format Temuan
Seluruh hasil audit dikonversi ke format JSON standar untuk kemudahan integrasi.

```json
{
  "id": "VULN-2024-001",
  "name": "Missing Security Headers",
  "severity": "MEDIUM",
  "category": "A05:2021-Security Misconfiguration",
  "location": "https://identity.corvus.net",
  "points": [
    "Strict-Transport-Security (HSTS) header is missing",
    "Content-Security-Policy (CSP) is not implemented"
  ],
  "remediation": "Implementasikan header HSTS dan CSP pada konfigurasi Nginx/Apache Anda.",
  "cvss": 5.4,
  "is_duplicate": false,
  "fingerprint": "sha256:7f...a12"
}
```

## Etika dan Keamanan
Corvus Red Edition menjunjung tinggi integritas audit:
*   **Audit Trail**: Setiap aktivitas scan dicatat dengan timestamp lengkap dan snapshot konfigurasi.
*   **Safe Probing**: Hanya melakukan verifikasi keberadaan kerentanan tanpa melakukan "Proof of Concept" yang agresif.
*   **Privacy**: Data scan disimpan secara lokal dan tidak pernah meninggalkan infrastruktur pengguna.

## Panduan Instalasi
Corvus Red Edition dioptimalkan untuk berjalan di lingkungan Docker.

**Prasyarat:**
*   Docker & Docker Compose.
*   RAM minimal 4GB.

**Langkah Instalasi:**
```bash
# 1. Clone Repositori
git clone https://github.com/your-org/corvus-red-edition.git
cd corvus-red-edition

# 2. Konfigurasi Environment
cp .env.example .env

# 3. Jalankan dengan Docker Compose
docker-compose up -d --build

# 4. Akses Dashboard
# Buka http://localhost:5173 di browser Anda.
```

## Referensi API
Corvus menyediakan REST API terdokumentasi untuk integrasi pihak ketiga.

**1. Initiate Scan**
`POST /api/scan`
```json
{
  "target": "example.com",
  "mode": "normal"
}
```

**2. Check Status**
`GET /api/scan/{scan_id}`
```json
{
  "status": "RUNNING",
  "progress": 65,
  "current_step": "Discovery"
}
```

## Perbandingan Mode
| Fitur | Quick | Normal | Deep |
| :--- | :---: | :---: | :---: |
| Subdomain Discovery | ❌ | ✅ | ✅ |
| Port Scanning | ❌ | ✅ | ✅ |
| Crawling & Directory | Basic | Standard | Extreme |
| Custom Safe Checks | ✅ | ✅ | ✅ |
| Deep Nuclei Scan | ❌ | ✅ | ✅ |

## FAQ
**Q: Apakah Corvus Red Edition legal digunakan?**
A: Corvus adalah alat audit. Legalitas penggunaannya bergantung sepenuhnya pada izin yang Anda miliki atas target yang dipindai.

**Q: Mengapa hasil scan saya ditandai sebagai PARTIAL?**
A: Corvus memiliki fitur "Diff Check". Jika jumlah temuan berubah secara drastis (>20%) dibanding scan sebelumnya, sistem menandainya sebagai `PARTIAL` untuk meminta tinjauan manual auditor (mencegah False Negative).

**Q: Apakah saya bisa menambahkan tool baru ke fase audit?**
A: Ya, Corvus dirancang secara modular. Anda dapat memodifikasi modul `executor.py` dan `orchestrator.py` untuk menambah instruksi baru.

## Lisensi
Proyek ini dilisensikan di bawah **MIT License**. Hak Cipta &copy; 2024 Corvus Security Team.
