// netlify/functions/verify-email.js
// Endpoint untuk memvalidasi apakah email customer sudah menyelesaikan pembelian di Lynk.id

const { getStore, connectLambda } = require("@netlify/blobs");

// Daftar email yang selalu diverifikasi (Owner & Tester/Pembeli Terverifikasi)
const STATIC_VERIFIED = {
    "alrizal.a.n@gmail.com": {
        name: "Alrizal Akbar Nusantara",
        orderId: "[KPR] LYNK-TEST-ORDER"
    },
    "olapoal.artgallery@gmail.com": {
        name: "Admin / Pemilik",
        orderId: "VIP-OWNER"
    },
    "admin@kpr.com": {
        name: "Super Admin",
        orderId: "VIP-ADMIN"
    }
};

exports.handler = async function(event, context) {
    const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
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
        if (typeof connectLambda === "function") {
            try {
                connectLambda(event);
            } catch (e) {
                console.warn("connectLambda notice:", e.message);
            }
        }

        const body = JSON.parse(event.body || "{}");
        const email = (body.email || "").trim().toLowerCase();

        if (!email) {
            return {
                statusCode: 400,
                headers: corsHeaders,
                body: JSON.stringify({ valid: false, message: "Email tidak boleh kosong" })
            };
        }

        // 1. Cek dari Netlify Blobs (Database Utama)
        let store = null;
        try {
            store = getStore("buyers");
            const buyerData = await store.get(email, { type: "json" });

            if (buyerData) {
                return {
                    statusCode: 200,
                    headers: corsHeaders,
                    body: JSON.stringify({
                        valid: true,
                        email: buyerData.email || email,
                        name: buyerData.name || buyerData.email || email,
                        orderId: buyerData.order_id || "-"
                    })
                };
            }
        } catch (blobsErr) {
            console.warn("Netlify Blobs check notice:", blobsErr.message);
        }

        // 2. Cek dari Google Sheet Database Live
        const GOOGLE_SHEET_ID = (process.env.GOOGLE_SHEET_ID || "1O5MRP-Nov0zJd2LKeWnlUfRcRowlxDMbkcCwnBZWvIo").trim();
        if (GOOGLE_SHEET_ID) {
            try {
                const sheetUrl = `https://docs.google.com/spreadsheets/d/${GOOGLE_SHEET_ID}/export?format=csv`;
                const resSheet = await fetch(sheetUrl);
                if (resSheet.ok) {
                    const csvText = await resSheet.text();
                    const lines = csvText.split(/\r?\n/);
                    for (const line of lines) {
                        const lowerLine = line.toLowerCase();
                        if (lowerLine.includes(email)) {
                            // Coba ambil nama pembeli dari kolom CSV jika ada
                            const cols = line.split(",").map(c => c.replace(/^"|"$/g, "").trim());
                            // Biasanya format: [Timestamp, Nama, Email, Phone, ...]
                            const possibleName = cols.find(c => c && !c.includes("@") && isNaN(c) && c.length > 2) || "Pembeli Terverifikasi";

                            // Auto-sync ke Netlify Blobs agar lebih cepat di request berikutnya
                            if (store) {
                                try {
                                    await store.setJSON(email, {
                                        email: email,
                                        name: possibleName,
                                        order_id: "[KPR] GOOGLE-SHEET-SYNC",
                                        created_at: new Date().toISOString()
                                    });
                                } catch (e) {}
                            }

                            return {
                                statusCode: 200,
                                headers: corsHeaders,
                                body: JSON.stringify({
                                    valid: true,
                                    email: email,
                                    name: possibleName,
                                    orderId: "[KPR] GOOGLE-SHEET-SYNC"
                                })
                            };
                        }
                    }
                }
            } catch (sheetErr) {
                console.warn("Google Sheet sync notice:", sheetErr.message);
            }
        }

        // 3. Cek dari STATIC_VERIFIED (Jaminan instan untuk pembeli terverifikasi)
        if (STATIC_VERIFIED[email]) {
            const staticData = STATIC_VERIFIED[email];

            // Auto-sync ke Netlify Blobs jika store aktif
            if (store) {
                try {
                    await store.setJSON(email, {
                        email: email,
                        name: staticData.name,
                        phone: "",
                        order_id: staticData.orderId,
                        created_at: new Date().toISOString()
                    });
                } catch (e) {}
            }

            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({
                    valid: true,
                    email: email,
                    name: staticData.name,
                    orderId: staticData.orderId
                })
            };
        }

        // 3. Cek dari Supabase Database jika ada env variables (Opsional / Fallback)
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

        if (supabaseUrl && supabaseKey) {
            try {
                const cleanUrl = supabaseUrl.replace(/\/$/, "");
                const endpoint = `${cleanUrl}/rest/v1/buyers?email=eq.${encodeURIComponent(email)}&select=email,name,order_id`;

                const res = await fetch(endpoint, {
                    headers: {
                        "apikey": supabaseKey,
                        "Authorization": `Bearer ${supabaseKey}`
                    }
                });

                if (res.ok) {
                    const rows = await res.json();
                    if (rows && rows.length > 0) {
                        return {
                            statusCode: 200,
                            headers: corsHeaders,
                            body: JSON.stringify({
                                valid: true,
                                email: rows[0].email,
                                name: rows[0].name || rows[0].email,
                                orderId: rows[0].order_id || "-"
                            })
                        };
                    }
                }
            } catch (supaErr) {
                console.warn("Supabase check error:", supaErr);
            }
        }

        // 4. Cek dari Environment Variable ADMIN_EMAILS (Email admin / tester manual)
        const adminEmails = (process.env.ADMIN_EMAILS || "olapoal.artgallery@gmail.com,admin@kpr.com")
            .toLowerCase()
            .split(",")
            .map(e => e.trim());

        if (adminEmails.includes(email)) {
            return {
                statusCode: 200,
                headers: corsHeaders,
                body: JSON.stringify({
                    valid: true,
                    email: email,
                    name: "Pengguna Terverifikasi",
                    orderId: "VIP-ADMIN"
                })
            };
        }

        // Jika tidak ditemukan di database
        return {
            statusCode: 404,
            headers: corsHeaders,
            body: JSON.stringify({
                valid: false,
                message: "Email belum terdaftar sebagai pembeli di Lynk.id."
            })
        };

    } catch (err) {
        return {
            statusCode: 500,
            headers: corsHeaders,
            body: JSON.stringify({ valid: false, error: err.message })
        };
    }
};
