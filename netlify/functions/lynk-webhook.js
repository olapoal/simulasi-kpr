// netlify/functions/lynk-webhook.js
// Endpoint ini menerima notifikasi saat customer selesai membayar di Lynk.id

const { getStore, connectLambda } = require("@netlify/blobs");

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
        if (typeof connectLambda === "function") {
            try {
                connectLambda(event);
            } catch (e) {
                console.warn("connectLambda notice:", e.message);
            }
        }

        const payload = JSON.parse(event.body || "{}");
        console.log("Lynk.id webhook incoming payload:", JSON.stringify(payload));

        // Ekstraksi data customer dari berbagai format payload Lynk.id (Webhook resmi Lynk.id maupun GAS forwarder)
        const msgData = payload.data?.message_data || payload.data || {};
        const customer = msgData.customer || payload.customer || {};

        const email = (
            customer.email ||
            payload.customer_email ||
            payload.email ||
            msgData.customer_email ||
            msgData.email ||
            payload.buyer_email ||
            ""
        ).trim().toLowerCase();

        const name = (
            customer.name ||
            payload.customer_name ||
            payload.name ||
            msgData.customer_name ||
            msgData.name ||
            payload.buyer_name ||
            "Pembeli Lynk.id"
        );

        const phone = (
            customer.phone ||
            payload.customer_phone ||
            payload.phone ||
            msgData.customer_phone ||
            msgData.phone ||
            ""
        );

        const orderId = (
            msgData.refId ||
            payload.order_id ||
            payload.transaction_id ||
            payload.id ||
            msgData.order_id ||
            msgData.id ||
            `LYNK-${Date.now()}`
        );

        // Ekstraksi Produk
        let productName = (
            payload.product_name ||
            payload.product ||
            payload.title ||
            payload.item_name ||
            msgData.product_name ||
            msgData.title ||
            ""
        );

        // Cek jika produk ada di array items (format resmi Lynk.id)
        const items = msgData.items || payload.items;
        if (Array.isArray(items) && items.length > 0) {
            const titles = items.map(it => it.title || it.name || "").filter(Boolean);
            if (titles.length > 0) {
                productName = titles.join(", ");
            }
        }

        // Filter Proteksi Multi-Produk:
        // Jika nama produk disebutkan dan sama sekali tidak berkaitan dengan KPR / Simulasi / Aplikasi, lewati transaksi
        if (productName) {
            const pLower = productName.toLowerCase();
            const isKprProduct = pLower.includes("kpr") || pLower.includes("simulasi") || pLower.includes("aplikasi") || pLower.includes("hitung");
            if (!isKprProduct) {
                console.log(`Transaksi diabaikan karena bukan produk KPR: ${productName}`);
                return {
                    statusCode: 200,
                    headers: corsHeaders,
                    body: JSON.stringify({
                        success: false,
                        ignored: true,
                        message: `Transaksi diabaikan: produk '${productName}' bukan produk KPR.`
                    })
                };
            }
        }

        if (!email || !email.includes("@")) {
            return {
                statusCode: 400,
                headers: corsHeaders,
                body: JSON.stringify({ error: "Email customer tidak valid dalam payload Lynk.id" })
            };
        }

        const buyerRecord = {
            email: email,
            name: name,
            phone: phone,
            order_id: productName ? `[KPR] ${orderId}` : String(orderId),
            product_name: productName || "[KPR] Aplikasi Simulasi Hitung KPR",
            created_at: new Date().toISOString()
        };

        // 1. Simpan ke Netlify Blobs (Database Utama Bawaan Netlify)
        let savedToBlobs = false;
        let blobsErrorMessage = "";
        try {
            const store = getStore("buyers");
            await store.setJSON(email, buyerRecord);
            savedToBlobs = true;
            console.log(`Berhasil menyimpan ${email} ke Netlify Blobs`);
        } catch (blobsErr) {
            blobsErrorMessage = blobsErr ? blobsErr.message : "unknown";
            console.warn("Netlify Blobs write notice:", blobsErr.message);
        }

        // 2. Simpan ke Supabase jika konfigurasi tersedia (Opsional)
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

        if (supabaseUrl && supabaseKey) {
            try {
                const cleanUrl = supabaseUrl.replace(/\/$/, "");
                const endpoint = `${cleanUrl}/rest/v1/buyers`;

                await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "apikey": supabaseKey,
                        "Authorization": `Bearer ${supabaseKey}`,
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates"
                    },
                    body: JSON.stringify(buyerRecord)
                });
            } catch (supaErr) {
                console.warn("Supabase insert warning:", supaErr);
            }
        }

        return {
            statusCode: 200,
            headers: corsHeaders,
            body: JSON.stringify({
                success: true,
                message: `Akses berhasil diaktifkan untuk email: ${email}`,
                email: email,
                orderId: orderId,
                storage: savedToBlobs ? "Netlify Blobs" : "Fallback"
            })
        };

    } catch (err) {
        console.error("Lynk.id webhook processing error:", err);
        return {
            statusCode: 500,
            headers: corsHeaders,
            body: JSON.stringify({ error: "Internal Server Error", details: err.message })
        };
    }
};
