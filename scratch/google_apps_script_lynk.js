/**
 * GOOGLE APPS SCRIPT: AUTO-SYNC EMAIL NOTIFIKASI LYNK.ID KE SIMULASI KPR
 * 
 * Fungsi script ini:
 * 1. Berjalan otomatis setiap 1 menit di Google Apps Script (gratis di akun Gmail Anda).
 * 2. Memeriksa email masuk dari "notification@lynk.id" dengan subject "Sales notification".
 * 3. Mengambil data Pembeli: Nama, Email, No. HP, dan Nama Produk.
 * 4. Mengirimkan data via POST Webhook ke https://simulasi-kpr.netlify.app/.netlify/functions/lynk-webhook
 * 5. Memberi label "Lynk-Processed" pada email tersebut agar tidak diproses ulang.
 * 
 * CARA PEMASANGAN (HANYA 2 MENIT):
 * 1. Buka https://script.google.com/ di browser Anda (login dengan akun Gmail olapoal.artgallery@gmail.com).
 * 2. Klik tombol "New project" (Proyek baru).
 * 3. Hapus semua kode default di editor, lalu paste SELURUH kode di file ini.
 * 4. Beri nama proyek di kiri atas, misal: "Lynk KPR Auto Sync".
 * 5. Klik icon disket "Save" (Simpan).
 * 6. Jalankan fungsi "syncLynkOrders" sekali dengan mengklik tombol "Run" (Jalankan) di atas.
 *    - Google akan meminta izin akses Gmail (Review permissions -> Pilih akun -> Advanced -> Go to Lynk KPR Auto Sync -> Allow).
 * 7. Untuk otomatisasi setiap 1 menit:
 *    - Di menu sebelah kiri, klik icon jam ("Triggers" / Pemicu).
 *    - Klik tombol biru "+ Add Trigger" di kanan bawah.
 *    - Choose which function to run: syncLynkOrders
 *    - Select event source: Time-driven (Berdasarkan waktu)
 *    - Select type of time based trigger: Minutes timer (Pengatur waktu menit)
 *    - Select minute interval: Every minute (Setiap menit)
 *    - Klik "Save".
 * Selesai! Mulai sekarang, setiap ada order dari Lynk.id, akun pembeli langsung aktif otomatis!
 */

const WEBHOOK_URL = "https://simulasi-kpr.netlify.app/.netlify/functions/lynk-webhook";
const PROCESSED_LABEL = "Lynk-Processed";

function syncLynkOrders() {
  // Pastikan label ada
  let label = GmailApp.getUserLabelByName(PROCESSED_LABEL);
  if (!label) {
    label = GmailApp.createLabel(PROCESSED_LABEL);
  }

  // Cari email dari notification@lynk.id yang belum diberi label Lynk-Processed
  const query = 'from:notification@lynk.id "Order from" -label:' + PROCESSED_LABEL;
  const threads = GmailApp.search(query, 0, 15);

  Logger.log("Menemukan " + threads.length + " thread email Lynk.id baru.");

  for (let i = 0; i < threads.length; i++) {
    const thread = threads[i];
    const messages = thread.getMessages();

    for (let j = 0; j < messages.length; j++) {
      const msg = messages[j];
      const body = msg.getPlainBody();

      // Ekstraksi data pembeli menggunakan regex
      const nameMatch = body.match(/Order from\s+([^,\r\n]+)/i);
      const emailMatch = body.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      const phoneMatch = body.match(/(\+?[0-9]{10,16})/);
      const itemMatch = body.match(/ITEMS\s*[\r\n]+([^\r\n]+)/i);

      if (emailMatch && emailMatch[1]) {
        const customerEmail = emailMatch[1].trim().toLowerCase();
        const customerName = nameMatch ? nameMatch[1].trim() : "Pembeli Lynk.id";
        const customerPhone = phoneMatch ? phoneMatch[1].trim() : "";
        const productName = itemMatch ? itemMatch[1].trim() : "[KPR] Aplikasi Simulasi Hitung KPR";
        const messageId = msg.getId();

        Logger.log("Memproses Order: " + customerName + " (" + customerEmail + ")");

        // Siapkan payload webhook
        const payload = {
          customer_name: customerName,
          customer_email: customerEmail,
          customer_phone: customerPhone,
          product_name: productName,
          order_id: "GMAIL-" + messageId
        };

        try {
          const options = {
            method: "post",
            contentType: "application/json",
            payload: JSON.stringify(payload),
            muteHttpExceptions: true
          };

          const response = UrlFetchApp.fetch(WEBHOOK_URL, options);
          const responseCode = response.getResponseCode();
          const responseText = response.getContentText();

          Logger.log("Webhook Response (" + responseCode + "): " + responseText);

          if (responseCode === 200) {
            Logger.log("Akses berhasil diaktifkan untuk: " + customerEmail);
          } else {
            Logger.warn("Webhook warning untuk " + customerEmail + ": " + responseText);
          }
        } catch (err) {
          Logger.log("Error saat memanggil webhook: " + err.toString());
        }
      }
    }

    // Tandai thread dengan label agar tidak diproses ulang
    thread.addLabel(label);
  }
}
