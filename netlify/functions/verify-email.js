// netlify/functions/verify-email.js
// Endpoint untuk memvalidasi apakah email customer sudah menyelesaikan pembelian di Lynk.id

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
        const body = JSON.parse(event.body || "{}");
        const email = (body.email || "").trim().toLowerCase();

        if (!email) {
            return {
                statusCode: 400,
                headers: corsHeaders,
                body: JSON.stringify({ valid: false, message: "Email tidak boleh kosong" })
            };
        }

        // 1. Cek dari Netlify Blobs (Database Bawaan Netlify - Prioritas Utama)
        try {
            const { getStore } = require("@netlify/blobs");
            const store = getStore("buyers");
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

        // 2. Cek dari Supabase Database jika ada env variables (Opsional / Fallback)
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

        // 3. Cek dari Environment Variable ADMIN_EMAILS (Email admin / tester manual)
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
                    name: "Pengguna Terverifikasi"
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
