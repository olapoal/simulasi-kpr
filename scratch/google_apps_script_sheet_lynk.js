/**
 * GOOGLE APPS SCRIPT: AUTO-SYNC LYNK.ID KE GOOGLE SHEET & WEBSITE SIMULASI KPR
 * 
 * Script ini dipasang langsung di dalam file Google Spreadsheet Anda:
 * 1. Menulis data pembeli baru secara otomatis ke baris spreadsheet ini.
 * 2. Mengaktifkan lisensi pembeli di website https://simulasi-kpr.netlify.app/
 * 3. Berjalan otomatis setiap 1 menit.
 */

const WEBHOOK_URL = "https://simulasi-kpr.netlify.app/.netlify/functions/lynk-webhook";
const PROCESSED_LABEL = "Lynk-Processed";

function setupSheetHeader() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Tanggal & Waktu", "Nama Pembeli", "Email Pembeli", "No. WhatsApp", "Nama Produk", "Status Akses"]);
    sheet.getRange("A1:F1").setFontWeight("bold").setBackground("#10b981").setFontColor("#ffffff");
    sheet.setFrozenRows(1);
  }
}

function syncLynkOrders() {
  setupSheetHeader();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  // Pastikan label Gmail ada
  let label = GmailApp.getUserLabelByName(PROCESSED_LABEL);
  if (!label) {
    label = GmailApp.createLabel(PROCESSED_LABEL);
  }

  // Cari email penjualan Lynk.id yang belum diproses
  const query = 'from:notification@lynk.id "Order from" -label:' + PROCESSED_LABEL;
  const threads = GmailApp.search(query, 0, 20);

  Logger.log("Menemukan " + threads.length + " thread email Lynk.id baru.");

  for (let i = 0; i < threads.length; i++) {
    const thread = threads[i];
    const messages = thread.getMessages();

    for (let j = 0; j < messages.length; j++) {
      const msg = messages[j];
      const body = msg.getPlainBody();
      const date = msg.getDate();

      // Ekstraksi data pembeli
      const nameMatch = body.match(/Order from\s+([^,\r\n]+)/i);
      const emailMatch = body.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      const phoneMatch = body.match(/(\+?[0-9]{10,16})/);
      const itemMatch = body.match(/ITEMS\s*[\r\n]+([^\r\n]+)/i);

      if (emailMatch && emailMatch[1]) {
        const customerEmail = emailMatch[1].trim().toLowerCase();
        const customerName = nameMatch ? nameMatch[1].trim() : "Pembeli Lynk.id";
        const customerPhone = phoneMatch ? phoneMatch[1].trim() : "";
        const productName = itemMatch ? itemMatch[1].trim() : "[KPR] Aplikasi Simulasi Hitung KPR";

        // Filter: Hanya proses jika produk KPR
        if (!productName.toLowerCase().includes("kpr")) {
          Logger.log("Bukan produk KPR, dilewati: " + productName);
          continue;
        }

        Logger.log("Memproses Order: " + customerName + " (" + customerEmail + ")");

        // 1. Tulis ke baris Google Sheet
        sheet.appendRow([
          Utilities.formatDate(date, "Asia/Jakarta", "yyyy-MM-dd HH:mm:ss"),
          customerName,
          customerEmail,
          customerPhone,
          productName,
          "Aktif"
        ]);

        // 2. Kirim sinyal Webhook ke Netlify website
        try {
          const payload = {
            customer_name: customerName,
            customer_email: customerEmail,
            customer_phone: customerPhone,
            product_name: productName,
            order_id: "GMAIL-" + msg.getId()
          };

          const options = {
            method: "post",
            contentType: "application/json",
            payload: JSON.stringify(payload),
            muteHttpExceptions: true
          };

          UrlFetchApp.fetch(WEBHOOK_URL, options);
          Logger.log("Akses lisensi berhasil diaktifkan di website untuk: " + customerEmail);
        } catch (err) {
          Logger.log("Webhook call note: " + err.toString());
        }
      }
    }

    // Tandai email dengan label Lynk-Processed agar tidak diproses ulang
    thread.addLabel(label);
  }
}
