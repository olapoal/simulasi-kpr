// netlify/functions/lynk-webhook.js
// Endpoint ini menerima notifikasi saat customer selesai membayar di Lynk.id

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
        const payload = JSON.parse(event.body || "{}");
        console.log("Lynk.id webhook incoming payload:", JSON.stringify(payload));

        // Ekstraksi data customer dari berbagai format payload Lynk.id
        const email = (
            payload.customer_email ||
            payload.email ||
            payload.data?.customer_email ||
            payload.data?.email ||
            payload.buyer_email ||
            payload.customer?.email ||
            ""
        ).trim().toLowerCase();

        const name = (
            payload.customer_name ||
            payload.name ||
            payload.data?.customer_name ||
            payload.data?.name ||
            payload.customer?.name ||
            "Pembeli Lynk.id"
        );

        const orderId = (
            payload.order_id ||
            payload.transaction_id ||
            payload.id ||
            payload.data?.order_id ||
            payload.data?.id ||
            `LYNK-${Date.now()}`
        );

        const phone = (
            payload.customer_phone ||
            payload.phone ||
            payload.data?.customer_phone ||
            payload.data?.phone ||
            ""
        );

        const productName = (
            payload.product_name ||
            payload.product ||
            payload.title ||
            payload.item_name ||
            payload.data?.product_name ||
            payload.data?.title ||
            ""
        );

        // Filter Proteksi Multi-Produk: Jika ada nama produk tapi bukan produk [KPR], lewati transaksi ini
        if (productName && !productName.toUpperCase().includes("[KPR]") && !productName.toLowerCase().includes("kpr")) {
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
            created_at: new Date().toISOString()
        };

        // 1. Simpan ke Netlify Blobs (Database Bawaan Netlify - Prioritas Utama)
        let savedToBlobs = false;
        try {
            const { getStore } = require("@netlify/blobs");
            const store = getStore("buyers");
            await store.setJSON(email, buyerRecord);
            savedToBlobs = true;
            console.log(`Berhasil menyimpan ${email} ke Netlify Blobs`);
        } catch (blobsErr) {
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
            body: JSON.stringify({ error: err.message })
        };
    }
};
