# Aplikasi Simulasi KPR & Pelunasan Dipercepat Sebagian

Aplikasi lengkap untuk menghitung simulasi cicilan KPR dengan dukungan skema perbankan Indonesia:
- **Bunga Berjenjang (Step-up Rate / Fixed Bertingkat)** — Standar simulasi KPR perbankan.
- **Anuitas Tetap (Fixed Rate)**
- **Efektif (Pokok Tetap / Sliding Rate)**
- **Flat**
- **Pelunasan Dipercepat Sebagian (Extra Payment)** dengan opsi:
  - `KURANGI_TENOR`: Nilai cicilan bulanan tetap, pinjaman lunas jauh lebih cepat dan menghemat bunga secara maksimal.
  - `KURANGI_ANGSURAN`: Tenor pinjaman tetap, nilai cicilan bulanan dihitung ulang menjadi lebih ringan.

---

## 📸 Analisis Data Contoh Simulasi Bank (dari Foto Anda)
Dari gambar tabel prakiraan angsuran yang Anda lampirkan:
- **Plafon Pinjaman**: Rp 676.000.000
- **Tenor**: 180 Bulan (15 Tahun)
- **Skema Bunga Berjenjang**:
  1. **Bulan 1 s/d 36 (Tahun 1–3)**: Suku bunga **5.75%** fixed. Total angsuran: **Rp 5.613.572** / bulan.
  2. **Bulan 37 s/d 72 (Tahun 4–6)**: Suku bunga **8.50%** fixed. Total angsuran dihitung ulang dari sisa saldo: **Rp 6.471.053** / bulan.
  3. **Bulan 73 s/d 180 (Tahun 7–15)**: Suku bunga **10.50%**. Total angsuran dihitung ulang: **Rp 6.993.201** / bulan hingga lunas di bulan ke-180.

Aplikasi ini menggunakan formula matematis yang **100% identik hingga angka satuan Rupiah** dengan standar perbankan tersebut.

---

## 🚀 Cara Menjalankan

### Cara 1: Buka Langsung di Web Browser (Paling Praktis, Tanpa Perlu Install Apapun!)
Cukup **klik dua kali (double click)** file:
👉 **[`kalkulator_kpr.html`](file:///G:/My%20Drive/Personal/Project/Aplikasi%20Hitung%20KPR/kalkulator_kpr.html)**
- Langsung terbuka di Google Chrome atau Microsoft Edge.
- Bisa pilih jenis cicilan, atur periode tier suku bunga, dan tambah pelunasan ekstra sebagian.
- Klik tombol **"Download Excel (.xlsx)"** untuk langsung mengunduh file spreadsheet.

---

### Cara 2: Menjalankan Aplikasi Desktop Python (GUI)
1. Buka terminal (PowerShell atau Command Prompt).
2. Pindah ke direktori:
   ```powershell
   cd "G:\My Drive\Personal\Project\Aplikasi Hitung KPR"
   ```
3. Pasang dependensi jika belum:
   ```powershell
   pip install -r requirements.txt
   ```
4. Jalankan aplikasi:
   ```powershell
   python src/main.py
   ```
   *(Akan muncul jendela interaktif Tkinter lengkap dengan form input dan tombol generate Excel).*

---

### Cara 3: Mode Terminal / CLI
Jalankan perhitungan langsung dari command line:
```powershell
python src/main.py --plafon 676000000 --tenor 180 --jenis BERJENJANG --extra "36:50000000:KURANGI_TENOR" --out "Hasil_Simulasi.xlsx"
```

---

## 🔒 Sistem Lisensi Otomatis Lynk.id & Netlify Serverless (Cara A)

Aplikasi web ini telah dilengkapi dengan sistem **Lock Screen Eksklusif** yang terintegrasi secara otomatis dengan pembelian di **Lynk.id**.

### 🌟 Alur Pembelian & Buka Akses Otomatis:
1. **Pembeli Checkout di Lynk.id**: Pembeli memasukkan email dan menyelesaikan pembayaran produk digital Anda di Lynk.id.
2. **Lynk.id Mengirim Webhook**: Lynk.id secara instan mengirim notifikasi pembayaran sukses ke endpoint serverless:
   `https://<nama-aplikasi>.netlify.app/.netlify/functions/lynk-webhook`
3. **Penyimpanan Data Pembeli**: Webhook menyimpan email pembeli ke database Supabase (tabel `buyers`) atau Google Sheets.
4. **Buka Akses Website**:
   - Pembeli membuka website Anda.
   - Layar terkunci (**Lock Screen**) tampil meminta **hanya email**.
   - Pembeli mengetik emailnya, lalu klik **"Buka Akses Aplikasi"**.
   - Netlify Function `verify-email` memvalidasi email pembeli.
   - Jika terdaftar, aplikasi langsung terbuka permanen di browser pembeli (`localStorage`), dan navbar menampilkan badge lisensi aktif:
     `● Lisensi: nama@email.com`

---

### ⚙️ Panduan Konfigurasi:

#### 1. Konfigurasi di Dashboard Lynk.id
- Toko Produk Lynk.id: **[https://lynk.id/olapoal](https://lynk.id/olapoal)**
- **Format Nama Produk**: Berikan awalan **`[KPR]`**, contoh: **`[KPR] Kalkulator KPR Pro`**.
  *(Fungsi: Memastikan script dan webhook hanya memproses pembeli produk KPR, tidak tercampur dengan produk lain di toko Anda).*
- Buka menu **Settings** / **Integrations** / **Webhooks** (jika menggunakan webhook Lynk.id):
  - URL Webhook: `https://<nama-aplikasi>.netlify.app/.netlify/functions/lynk-webhook`
  - Event: `Payment Success` / `Order Paid`.
- Pada pengaturan produk Lynk.id (Thank You / Redirect URL):
  Arahkan pembeli ke URL website Anda:
  `https://<nama-aplikasi>.netlify.app/?email={buyer_email}` *(opsional, jika Lynk.id mendukung parameter email, website akan langsung auto-fill & auto-unlock tanpa pembeli mengetik apa pun!)*

#### 2. Otomasi Membaca Email Masuk Lynk.id via Google Apps Script (100% Gratis)
Jika Lynk.id Anda tidak menggunakan webhook, pasang script otomatis ini di **[script.google.com](https://script.google.com)** (jalan di cloud Google 24 jam nonstop):
```javascript
const NETLIFY_WEBHOOK_URL = "https://<nama-aplikasi-anda>.netlify.app/.netlify/functions/lynk-webhook";

function periksaEmailPembelianLynkId() {
  // Hanya mencari email Lynk.id yang memuat nama produk [KPR]
  const query = 'from:(lynk.id) "[KPR]" -label:KPR-PROCESSED';
  const threads = GmailApp.search(query, 0, 10);
  if (threads.length === 0) return;

  let label = GmailApp.getUserLabelByName("KPR-PROCESSED") || GmailApp.createLabel("KPR-PROCESSED");

  threads.forEach(thread => {
    thread.getMessages().forEach(message => {
      const body = message.getPlainBody();
      const subject = message.getSubject();
      
      // Validasi ketat bahwa ini memang produk [KPR]
      if (subject.includes("[KPR]") || body.includes("[KPR]")) {
        const emailMatches = body.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g);
        if (emailMatches) {
          const buyerEmail = emailMatches.find(e => 
            !e.includes("lynk.id") && !e.includes("google.com") && 
            e.toLowerCase() !== Session.getActiveUser().getEmail().toLowerCase()
          );

          if (buyerEmail) {
            UrlFetchApp.fetch(NETLIFY_WEBHOOK_URL, {
              method: "post",
              contentType: "application/json",
              payload: JSON.stringify({
                customer_email: buyerEmail,
                customer_name: "Pembeli Lynk.id",
                product_name: "[KPR] Kalkulator KPR Pro",
                order_id: "LYNK-" + message.getDate().getTime()
              })
            });
          }
        }
      }
    });
    thread.addLabel(label);
  });
}
```

#### 3. Database Penyimpanan: Netlify Blobs (Bawaan Netlify)
- Sistem sekarang menggunakan **Netlify Blobs** secara otomatis.
- **Tidak perlu setup Supabase lagi!** Data pembeli tersimpan permanen di cloud Netlify Anda dan tidak ada risiko database tertidur (*auto-pause*).

#### 4. Konfigurasi Environment Variables di Netlify
- Masuk ke Dashboard Netlify -> **Site configuration** -> **Environment variables**.
- Tambahkan variabel berikut:
  - `SUPABASE_URL`: `https://xxxx.supabase.co`
  - `SUPABASE_KEY`: `eyJhbGciOi...` (anon key Supabase Anda)
  - `ADMIN_EMAILS`: `email-anda@gmail.com,tester@gmail.com` *(daftar email yang selalu bisa membuka aplikasi tanpa perlu membeli)*
  - `ADMIN_PASSWORD`: `password-rahasia-anda` *(password untuk masuk ke Portal Admin `/admin`, default jika kosong: `admin12345`)*

#### 4. Portal Admin Pengelolaan User (`/admin`)
- Akses melalui URL: **`https://<nama-aplikasi>.netlify.app/admin`** atau buka file **[`admin.html`](file:///G:/My%20Drive/Personal/Project/Aplikasi%20Hitung%20KPR/admin.html)**.
- **Fitur Admin**:
  - 👥 Melihat total pembeli dan daftar seluruh lisensi aktif secara real-time.
  - ➕ Menambahkan pembeli manual (misal: pembeli via transfer bank manual atau WhatsApp).
  - 🔍 Pencarian instan berdasarkan email atau nama pembeli.
  - 🗑️ Mencabut lisensi / menghapus pembeli dengan 1 klik.
  - 🔐 **Ganti Password Admin Langsung**: Dapat mengubah password admin sewaktu-waktu langsung dari dashboard tanpa perlu redeploy Netlify (tersimpan aman di Netlify Blobs).

#### 5. Pengujian Lokal (Local Testing)
- Saat membuka file `index.html`, `kalkulator_kpr.html`, atau `admin.html` langsung dari komputer lokal (`file:///`), sistem mendeteksi mode pengujian lokal dan mengizinkan pengetesan penuh tanpa error koneksi.
