// netlify/functions/admin-buyers.js
// Endpoint API aman untuk Admin Panel mengelola data pembeli lisensi & ganti password admin via Netlify Blobs

exports.handler = async function(event, context) {
    const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, x-admin-key",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Content-Type": "application/json"
    };

    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 200, headers: corsHeaders, body: "" };
    }

    if (event.httpMethod !== "POST") {
        return {
            statusCode: 405,
            headers: corsHeaders,
            body: JSON.stringify({ error: "Method Not Allowed" })
        };
    }

    try {
        const body = JSON.parse(event.body || "{}");
        const action = body.action || "list";
        const adminKey = event.headers["x-admin-key"] || body.admin_key || "";

        // Siapkan Netlify Blobs Stores
        let buyersStore = null;
        let settingsStore = null;
        try {
            const { getStore } = require("@netlify/blobs");
            buyersStore = getStore("buyers");
            settingsStore = getStore("settings");
        } catch (e) {
            console.warn("Blobs store init notice:", e.message);
        }

        // Tentukan Password Admin Aktif (Cek Blobs 'settings' dulu, jika belum ada cek ENV, default: admin12345)
        let activeAdminPassword = (process.env.ADMIN_PASSWORD || "admin12345").trim();
        if (settingsStore) {
            try {
                const customPass = await settingsStore.get("admin_password");
                if (customPass && customPass.trim()) {
                    activeAdminPassword = customPass.trim();
                }
            } catch (e) {
                console.warn("Failed to read custom admin password:", e.message);
            }
        }

        // 1. Verifikasi Password Admin
        if (adminKey !== activeAdminPassword) {
            return {
                statusCode: 401,
                headers: corsHeaders,
                body: JSON.stringify({ success: false, message: "Password Admin tidak valid." })
            };
        }

        // Jika hanya cek login
        if (action === "login") {
            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({ success: true, message: "Login Admin Berhasil" })
            };
        }

        // 2. Aksi: GANTI PASSWORD ADMIN
        if (action === "change_password") {
            const oldPassword = (body.old_password || "").trim();
            const newPassword = (body.new_password || "").trim();

            if (oldPassword !== activeAdminPassword) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({ success: false, message: "Password lama tidak sesuai." })
                };
            }

            if (!newPassword || newPassword.length < 6) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({ success: false, message: "Password baru minimal 6 karakter." })
                };
            }

            if (newPassword === oldPassword) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({ success: false, message: "Password baru tidak boleh sama dengan password lama." })
                };
            }

            // Simpan password baru ke Netlify Blobs store 'settings'
            if (settingsStore) {
                try {
                    await settingsStore.set("admin_password", newPassword);
                } catch (e) {
                    console.error("Gagal menyimpan password baru ke Netlify Blobs:", e.message);
                }
            }

            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: true,
                    message: "Password Admin berhasil diperbarui!"
                })
            };
        }

        // 3. Aksi: LIST (Ambil Semua Data Pembeli)
        if (action === "list") {
            let buyersList = [];

            // A. Coba dari Netlify Blobs
            if (buyersStore) {
                try {
                    const { blobs } = await buyersStore.list();
                    if (blobs && blobs.length > 0) {
                        for (const b of blobs) {
                            try {
                                const data = await buyersStore.get(b.key, { type: "json" });
                                if (data) buyersList.push(data);
                            } catch (e) {}
                        }
                    }
                } catch (blobsErr) {
                    console.warn("Blobs list error:", blobsErr.message);
                }
            }

            // B. Jika Blobs kosong, coba Supabase (jika ada)
            const supabaseUrl = process.env.SUPABASE_URL;
            const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
            if (buyersList.length === 0 && supabaseUrl && supabaseKey) {
                try {
                    const cleanUrl = supabaseUrl.replace(/\/$/, "");
                    const res = await fetch(`${cleanUrl}/rest/v1/buyers?select=*&order=created_at.desc`, {
                        headers: { "apikey": supabaseKey, "Authorization": `Bearer ${supabaseKey}` }
                    });
                    if (res.ok) {
                        const supaBuyers = await res.json();
                        if (supaBuyers && supaBuyers.length > 0) buyersList = supaBuyers;
                    }
                } catch (e) {}
            }

            // C. Fallback default jika database masih baru dibuat
            if (buyersList.length === 0) {
                const adminEmails = (process.env.ADMIN_EMAILS || "olapoal.artgallery@gmail.com")
                    .split(",")
                    .map((e, idx) => ({
                        id: idx + 1,
                        email: e.trim(),
                        name: "Admin / Pemilik",
                        order_id: "VIP-OWNER",
                        created_at: new Date().toISOString()
                    }));
                buyersList = adminEmails;
            }

            // Urutkan terbaru di atas
            buyersList.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({ success: true, buyers: buyersList })
            };
        }

        // 4. Aksi: ADD (Tambah / Update Pembeli Manual)
        if (action === "add") {
            const email = (body.email || "").trim().toLowerCase();
            const name = (body.name || "Pembeli Manual").trim();
            const orderId = (body.order_id || `MANUAL-${Date.now()}`).trim();
            const phone = (body.phone || "").trim();

            if (!email || !email.includes("@")) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({ success: false, message: "Format email tidak valid." })
                };
            }

            const buyerRecord = {
                email: email,
                name: name,
                phone: phone,
                order_id: orderId,
                created_at: new Date().toISOString()
            };

            // Simpan ke Netlify Blobs
            if (buyersStore) {
                try {
                    await buyersStore.setJSON(email, buyerRecord);
                } catch (e) {
                    console.warn("Blobs save notice:", e.message);
                }
            }

            // Simpan ke Supabase jika tersedia
            const supabaseUrl = process.env.SUPABASE_URL;
            const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
            if (supabaseUrl && supabaseKey) {
                try {
                    const cleanUrl = supabaseUrl.replace(/\/$/, "");
                    await fetch(`${cleanUrl}/rest/v1/buyers`, {
                        method: "POST",
                        headers: {
                            "apikey": supabaseKey,
                            "Authorization": `Bearer ${supabaseKey}`,
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates"
                        },
                        body: JSON.stringify(buyerRecord)
                    });
                } catch (e) {}
            }

            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: true,
                    message: `Akses lisensi berhasil diberikan ke: ${email}`,
                    buyer: buyerRecord
                })
            };
        }

        // 5. Aksi: DELETE (Cabut Lisensi Pembeli)
        if (action === "delete") {
            const email = (body.email || "").trim().toLowerCase();
            if (!email) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({ success: false, message: "Email tidak boleh kosong." })
                };
            }

            if (buyersStore) {
                try {
                    await buyersStore.delete(email);
                } catch (e) {
                    console.warn("Blobs delete notice:", e.message);
                }
            }

            const supabaseUrl = process.env.SUPABASE_URL;
            const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
            if (supabaseUrl && supabaseKey) {
                try {
                    const cleanUrl = supabaseUrl.replace(/\/$/, "");
                    await fetch(`${cleanUrl}/rest/v1/buyers?email=eq.${encodeURIComponent(email)}`, {
                        method: "DELETE",
                        headers: { "apikey": supabaseKey, "Authorization": `Bearer ${supabaseKey}` }
                    });
                } catch (e) {}
            }

            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: true,
                    message: `Akses lisensi untuk ${email} berhasil dihapus permanen.`
                })
            };
        }

        return {
            statusCode: 400,
            headers: corsHeaders,
            body: JSON.stringify({ success: false, message: "Aksi tidak dikenali." })
        };

    } catch (err) {
        return {
            statusCode: 500,
            headers: corsHeaders,
            body: JSON.stringify({ success: false, error: err.message })
        };
    }
};
