"""Antarmuka Pengguna Grafis (GUI) Modern untuk Aplikasi Hitung KPR.
Desain One-View Full Width dengan Kolom Tier & Pelunasan yang Sangat Lebar & Jelas.
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date

from calculator import hitung_kpr, TierBunga, ExtraPayment
from excel_exporter import export_to_excel

class AplikasiKPR(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kalkulator KPR Pro — Bunga Berjenjang & Pelunasan Sebagian")
        self.geometry("1420x940")
        self.minsize(1150, 780)
        self.configure(bg="#0B0F19")

        self.simulasi_result = None
        self._setup_custom_styles()
        self.buat_widgets()

    def _setup_custom_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.c_bg = "#0B0F19"
        self.c_card = "#111827"
        self.c_text = "#F9FAFB"
        self.c_border = "#374151"

        self.style.configure(".", background=self.c_bg, foreground=self.c_text, font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.c_bg)

        self.style.configure(
            "TLabelframe",
            background=self.c_card,
            foreground="#60A5FA",
            relief="solid",
            borderwidth=1
        )
        self.style.configure(
            "TLabelframe.Label",
            background=self.c_card,
            foreground="#60A5FA",
            font=("Segoe UI", 10, "bold")
        )

        self.style.configure(
            "Treeview",
            background="#111827",
            foreground="#F3F4F6",
            fieldbackground="#111827",
            rowheight=26,
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Treeview.Heading",
            background="#1E293B",
            foreground="#CBD5E1",
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        self.style.map("Treeview", background=[("selected", "#2563EB")])

    def buat_widgets(self):
        # 1. Navbar Top
        top_bar = tk.Frame(self, bg="#111827", height=58, highlightthickness=1, highlightbackground="#1F2937")
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        brand_frame = tk.Frame(top_bar, bg="#111827")
        brand_frame.pack(side=tk.LEFT, padx=20)

        # Coba load logo image
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        self.logo_img = None
        if os.path.exists(logo_path):
            try:
                # Tkinter native PNG support in Python 3.4+
                raw_img = tk.PhotoImage(file=logo_path)
                # Subsample agar proporsional di navbar (tinggi ~38px)
                factor = max(1, raw_img.height() // 38)
                self.logo_img = raw_img.subsample(factor, factor)
                lbl_icon = tk.Label(brand_frame, image=self.logo_img, bg="#111827", padx=0, pady=0)
                lbl_icon.pack(side=tk.LEFT, padx=(0, 10))
            except Exception:
                lbl_icon = tk.Label(brand_frame, text="🏠", font=("Segoe UI", 18), bg="#111827", fg="#60A5FA")
                lbl_icon.pack(side=tk.LEFT, padx=(0, 8))
        else:
            lbl_icon = tk.Label(brand_frame, text="🏠", font=("Segoe UI", 18), bg="#111827", fg="#60A5FA")
            lbl_icon.pack(side=tk.LEFT, padx=(0, 8))

        title_frame = tk.Frame(brand_frame, bg="#111827")
        title_frame.pack(side=tk.LEFT)
        tk.Label(title_frame, text="SIMULASI KPR PRO (ONE VIEW)", font=("Segoe UI", 13, "bold"), fg="#FFFFFF", bg="#111827").pack(anchor="w")
        tk.Label(title_frame, text="Kolom Lebar & Jelas • Cukup Scroll ke Bawah", font=("Segoe UI", 8), fg="#9CA3AF", bg="#111827").pack(anchor="w")

        # Top action buttons
        btn_excel_top = tk.Button(
            top_bar,
            text="📊 Download Excel (.xlsx)",
            font=("Segoe UI", 9, "bold"),
            bg="#10B981",
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.generate_excel
        )
        btn_excel_top.pack(side=tk.RIGHT, padx=(6, 20))

        btn_hapus_top = tk.Button(
            top_bar,
            text="🗑️ Hapus Semua Data",
            font=("Segoe UI", 9, "bold"),
            bg="#374151",
            fg="#FCA5A5",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.hapus_semua_data
        )
        btn_hapus_top.pack(side=tk.RIGHT, padx=4)

        btn_save_json = tk.Button(
            top_bar,
            text="💾 Simpan .json",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.export_json
        )
        btn_save_json.pack(side=tk.RIGHT, padx=4)

        btn_open_json = tk.Button(
            top_bar,
            text="📂 Open (.json)",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.import_json
        )
        btn_open_json.pack(side=tk.RIGHT, padx=4)

        btn_trakteer = tk.Button(
            top_bar,
            text="☕ Donasi",
            font=("Segoe UI", 9, "bold"),
            bg="#BE1E2D",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.buka_trakteer
        )
        btn_trakteer.pack(side=tk.RIGHT, padx=4)

        # 2. Main Content Container
        main_content = tk.Frame(self, bg=self.c_bg)
        main_content.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # --- Bagian Atas: Form Konfigurasi ---
        top_config_frame = tk.Frame(main_content, bg=self.c_card, highlightthickness=1, highlightbackground=self.c_border, padx=16, pady=12)
        top_config_frame.pack(fill=tk.X, pady=(0, 10))

        # Baris Header & Tombol Hitung
        f_top_header = tk.Frame(top_config_frame, bg=self.c_card)
        f_top_header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(f_top_header, text="⚙️ KONFIGURASI PARAMETER PINJAMAN & PELUNASAN DIPERCEPAT", font=("Segoe UI", 11, "bold"), fg="#60A5FA", bg=self.c_card).pack(side=tk.LEFT)

        btn_hitung = tk.Button(
            f_top_header,
            text="⚡ HITUNG ULANG SIMULASI",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="white",
            relief="flat",
            padx=18,
            pady=5,
            cursor="hand2",
            command=self.hitung_dan_tampilkan
        )
        btn_hitung.pack(side=tk.RIGHT)

        # BARIS 1: Parameter Pokok (Proporsi Optimal)
        f_param_row = tk.Frame(top_config_frame, bg="#1E293B", padx=12, pady=10, highlightthickness=1, highlightbackground="#334155")
        f_param_row.pack(fill=tk.X, pady=(0, 10))

        f_param_row.grid_columnconfigure(0, weight=10)
        f_param_row.grid_columnconfigure(1, weight=12)
        f_param_row.grid_columnconfigure(2, weight=7)
        f_param_row.grid_columnconfigure(3, weight=8)
        f_param_row.grid_columnconfigure(4, weight=18)

        tk.Label(f_param_row, text="Bank / Label:", bg="#1E293B", fg="#CBD5E1", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", padx=6)
        self.ent_bank = tk.Entry(f_param_row, bg="#0F172A", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        self.ent_bank.insert(0, "KPR Bank")
        self.ent_bank.grid(row=1, column=0, sticky="ew", padx=6, pady=(3, 0))

        tk.Label(f_param_row, text="Plafon Pokok (Rp):", bg="#1E293B", fg="#CBD5E1", font=("Segoe UI", 8, "bold")).grid(row=0, column=1, sticky="w", padx=6)
        self.ent_plafon = tk.Entry(f_param_row, bg="#0F172A", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9, "bold"))
        self.ent_plafon.insert(0, "676000000")
        self.ent_plafon.grid(row=1, column=1, sticky="ew", padx=6, pady=(3, 0))

        tk.Label(f_param_row, text="Tenor (Bulan):", bg="#1E293B", fg="#CBD5E1", font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w", padx=6)
        self.ent_tenor = tk.Entry(f_param_row, bg="#0F172A", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        self.ent_tenor.insert(0, "180")
        self.ent_tenor.grid(row=1, column=2, sticky="ew", padx=6, pady=(3, 0))

        tk.Label(f_param_row, text="Tgl Jatuh Tempo 1:", bg="#1E293B", fg="#CBD5E1", font=("Segoe UI", 8, "bold")).grid(row=0, column=3, sticky="w", padx=6)
        self.ent_start_date = tk.Entry(f_param_row, bg="#0F172A", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        self.ent_start_date.insert(0, "28/05/2025")
        self.ent_start_date.grid(row=1, column=3, sticky="ew", padx=6, pady=(3, 0))

        tk.Label(f_param_row, text="Skema Suku Bunga:", bg="#1E293B", fg="#CBD5E1", font=("Segoe UI", 8, "bold")).grid(row=0, column=4, sticky="w", padx=6)
        self.cb_jenis = ttk.Combobox(
            f_param_row,
            values=["Bunga Berjenjang", "Anuitas Tetap", "Efektif", "Flat"],
            state="readonly"
        )
        self.cb_jenis.current(0)
        self.cb_jenis.grid(row=1, column=4, sticky="ew", padx=6, pady=(3, 0))

        # BARIS 2: SPLIT 50% : 50% LEGA UNTUK TIER & PELUNASAN SEBAGIAN
        f_split_row = tk.Frame(top_config_frame, bg=self.c_card)
        f_split_row.pack(fill=tk.X)

        # KIRI: 2. PERIODE BUNGA BERJENJANG (KOLOM LEGA)
        panel_tier = tk.Frame(f_split_row, bg="#1E293B", padx=12, pady=10, highlightthickness=1, highlightbackground="#334155")
        panel_tier.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        f_t_head = tk.Frame(panel_tier, bg="#1E293B")
        f_t_head.pack(fill=tk.X, pady=(0, 6))
        tk.Label(f_t_head, text="2. PERIODE BUNGA BERJENJANG", font=("Segoe UI", 9, "bold"), fg="#60A5FA", bg="#1E293B").pack(side=tk.LEFT)
        tk.Button(f_t_head, text="+ Tambah Periode", bg="#2563EB", fg="white", relief="flat", font=("Segoe UI", 8, "bold"), padx=8, command=self._popup_tambah_tier).pack(side=tk.RIGHT)

        cols_tier = ("start", "end", "rate", "label")
        self.tree_tier = ttk.Treeview(panel_tier, columns=cols_tier, show="headings", height=3)
        self.tree_tier.heading("start", text="Mulai Bln")
        self.tree_tier.heading("end", text="S/D Bln")
        self.tree_tier.heading("rate", text="Bunga (% p.a.)")
        self.tree_tier.heading("label", text="Keterangan / Tier")

        self.tree_tier.column("start", width=75, anchor="center")
        self.tree_tier.column("end", width=75, anchor="center")
        self.tree_tier.column("rate", width=105, anchor="center")
        self.tree_tier.column("label", width=220, anchor="w")
        self.tree_tier.pack(fill=tk.BOTH, expand=True)

        self.tree_tier.insert("", tk.END, values=(1, 36, "5.75", "Tahun 1-3 (5.75% Fixed)"))
        self.tree_tier.insert("", tk.END, values=(37, 72, "8.50", "Tahun 4-6 (8.50% Fixed)"))
        self.tree_tier.insert("", tk.END, values=(73, 180, "10.50", "Tahun 7-15 (10.50% Floating)"))

        # KANAN: 3. PELUNASAN DIPERCEPAT SEBAGIAN (KOLOM LEGA)
        panel_extra = tk.Frame(f_split_row, bg="#1E293B", padx=12, pady=10, highlightthickness=1, highlightbackground="#334155")
        panel_extra.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        f_e_head = tk.Frame(panel_extra, bg="#1E293B")
        f_e_head.pack(fill=tk.X, pady=(0, 6))
        tk.Label(f_e_head, text="3. PELUNASAN DIPERCEPAT SEBAGIAN", font=("Segoe UI", 9, "bold"), fg="#34D399", bg="#1E293B").pack(side=tk.LEFT)
        tk.Button(f_e_head, text="+ Tambah Pelunasan", bg="#10B981", fg="white", relief="flat", font=("Segoe UI", 8, "bold"), padx=8, command=self._popup_tambah_extra).pack(side=tk.RIGHT)

        cols_extra = ("month", "mult", "amount", "effect")
        self.tree_extra = ttk.Treeview(panel_extra, columns=cols_extra, show="headings", height=3)
        self.tree_extra.heading("month", text="Bln Ke")
        self.tree_extra.heading("mult", text="x Angsuran")
        self.tree_extra.heading("amount", text="Pokok Murni (Rp)")
        self.tree_extra.heading("effect", text="Efek Pada Pinjaman")

        self.tree_extra.column("month", width=65, anchor="center")
        self.tree_extra.column("mult", width=75, anchor="center")
        self.tree_extra.column("amount", width=155, anchor="e")
        self.tree_extra.column("effect", width=200, anchor="center")
        self.tree_extra.pack(fill=tk.BOTH, expand=True)

        self.tree_extra.insert("", tk.END, values=(18, "6x", "33,681,432", "KURANGI_TENOR (Hemat Bunga)"))

        # Info Box Efek Pelunasan Dinamis
        self.frame_extra_info = tk.Frame(panel_extra, bg="#0F172A", highlightthickness=1, highlightbackground="#F59E0B", padx=8, pady=4)
        self.frame_extra_info.pack(fill=tk.X, pady=(6, 0))
        self.lbl_extra_info = tk.Label(self.frame_extra_info, text="", font=("Segoe UI", 8), fg="#FDE68A", bg="#0F172A", wraplength=450, justify=tk.LEFT)
        self.lbl_extra_info.pack(fill=tk.X)

        # --- Bagian Tengah: Stat Bento Metrics Bar ---
        stats_bar = tk.Frame(main_content, bg=self.c_bg)
        stats_bar.pack(fill=tk.X, pady=(0, 10))

        s1 = tk.Frame(stats_bar, bg="#111827", padx=14, pady=10, highlightthickness=1, highlightbackground="#374151")
        s1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        tk.Label(s1, text="CICILAN AWAL (BLN 1)", font=("Segoe UI", 8, "bold"), fg="#9CA3AF", bg="#111827").pack(anchor="w")
        self.val_pmt1 = tk.Label(s1, text="Rp 0", font=("Segoe UI", 14, "bold"), fg="#60A5FA", bg="#111827")
        self.val_pmt1.pack(anchor="w")

        s2 = tk.Frame(stats_bar, bg="#111827", padx=14, pady=10, highlightthickness=1, highlightbackground="#374151")
        s2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(s2, text="TENOR AKTUAL & HEMAT", font=("Segoe UI", 8, "bold"), fg="#9CA3AF", bg="#111827").pack(anchor="w")
        self.val_tenor = tk.Label(s2, text="0 Bulan", font=("Segoe UI", 14, "bold"), fg="#34D399", bg="#111827")
        self.val_tenor.pack(anchor="w")

        s3 = tk.Frame(stats_bar, bg="#111827", padx=14, pady=10, highlightthickness=1, highlightbackground="#374151")
        s3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(s3, text="TOTAL BUNGA TERBAYAR", font=("Segoe UI", 8, "bold"), fg="#9CA3AF", bg="#111827").pack(anchor="w")
        self.val_bunga = tk.Label(s3, text="Rp 0", font=("Segoe UI", 14, "bold"), fg="#FBBF24", bg="#111827")
        self.val_bunga.pack(anchor="w")

        s4 = tk.Frame(stats_bar, bg="#111827", padx=14, pady=10, highlightthickness=1, highlightbackground="#059669")
        s4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(s4, text="TOTAL HEMAT PELUNASAN", font=("Segoe UI", 8, "bold"), fg="#6EE7B7", bg="#111827").pack(anchor="w")
        self.val_hemat = tk.Label(s4, text="Rp 0", font=("Segoe UI", 14, "bold"), fg="#34D399", bg="#111827")
        self.val_hemat.pack(anchor="w")

        s5 = tk.Frame(stats_bar, bg="#111827", padx=14, pady=10, highlightthickness=1, highlightbackground="#374151")
        s5.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        tk.Label(s5, text="TOTAL KESELURUHAN", font=("Segoe UI", 8, "bold"), fg="#9CA3AF", bg="#111827").pack(anchor="w")
        self.val_total = tk.Label(s5, text="Rp 0", font=("Segoe UI", 14, "bold"), fg="#A78BFA", bg="#111827")
        self.val_total.pack(anchor="w")

        # --- Bagian Bawah: TABEL AMORTISASI FULL WIDTH ---
        table_container = tk.Frame(main_content, bg=self.c_card, highlightthickness=1, highlightbackground=self.c_border, padx=10, pady=8)
        table_container.pack(fill=tk.BOTH, expand=True)

        cols_table = ("bulan", "tanggal", "rate", "pokok", "bunga", "total", "ekstra", "saldo", "ket")
        self.tree_schedule = ttk.Treeview(table_container, columns=cols_table, show="headings")

        self.tree_schedule.heading("bulan", text="Bln")
        self.tree_schedule.heading("tanggal", text="Jatuh Tempo")
        self.tree_schedule.heading("rate", text="Bunga")
        self.tree_schedule.heading("pokok", text="Angsuran Pokok (Rp)")
        self.tree_schedule.heading("bunga", text="Angsuran Bunga (Rp)")
        self.tree_schedule.heading("total", text="Total Angsuran (Rp)")
        self.tree_schedule.heading("ekstra", text="Pelunasan Ekstra (Rp)")
        self.tree_schedule.heading("saldo", text="Sisa Saldo Pokok (Rp)")
        self.tree_schedule.heading("ket", text="Keterangan")

        self.tree_schedule.column("bulan", width=45, anchor="center")
        self.tree_schedule.column("tanggal", width=105, anchor="center")
        self.tree_schedule.column("rate", width=70, anchor="center")
        self.tree_schedule.column("pokok", width=145, anchor="e")
        self.tree_schedule.column("bunga", width=145, anchor="e")
        self.tree_schedule.column("total", width=155, anchor="e")
        self.tree_schedule.column("ekstra", width=145, anchor="e")
        self.tree_schedule.column("saldo", width=165, anchor="e")
        self.tree_schedule.column("ket", width=180, anchor="w")

        self.tree_schedule.tag_configure("tier_change", background="#1E293B", foreground="#93C5FD", font=("Segoe UI", 9, "bold"))
        self.tree_schedule.tag_configure("extra_row", background="#064E3B", foreground="#6EE7B7", font=("Segoe UI", 9, "bold"))
        self.tree_schedule.tag_configure("year_end", background="#172033")

        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree_schedule.yview)
        self.tree_schedule.configure(yscrollcommand=scroll_y.set)

        self.tree_schedule.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def _popup_tambah_tier(self):
        w = tk.Toplevel(self)
        w.title("Tambah Periode Suku Bunga")
        w.geometry("340x230")
        w.configure(bg="#111827")
        w.transient(self)
        w.grab_set()

        tk.Label(w, text="Mulai Bln:", bg="#111827", fg="white").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        ent_s = tk.Entry(w, bg="#1F2937", fg="white")
        ent_s.grid(row=0, column=1, padx=12, pady=6)

        tk.Label(w, text="S/D Bln:", bg="#111827", fg="white").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ent_e = tk.Entry(w, bg="#1F2937", fg="white")
        ent_e.grid(row=1, column=1, padx=12, pady=6)

        tk.Label(w, text="Bunga (% p.a.):", bg="#111827", fg="white").grid(row=2, column=0, padx=12, pady=6, sticky="w")
        ent_r = tk.Entry(w, bg="#1F2937", fg="white")
        ent_r.grid(row=2, column=1, padx=12, pady=6)

        tk.Label(w, text="Keterangan:", bg="#111827", fg="white").grid(row=3, column=0, padx=12, pady=6, sticky="w")
        ent_l = tk.Entry(w, bg="#1F2937", fg="white")
        ent_l.grid(row=3, column=1, padx=12, pady=6)

        def simpan():
            try:
                s = int(ent_s.get())
                e = int(ent_e.get())
                r = float(ent_r.get())
                lbl = ent_l.get().strip() or f"Bln {s}-{e}"
                self.tree_tier.insert("", tk.END, values=(s, e, f"{r:.2f}", lbl))
                w.destroy()
            except ValueError:
                messagebox.showerror("Error", "Harap isi angka dengan benar.")

        tk.Button(w, text="Simpan Periode", bg="#2563EB", fg="white", relief="flat", padx=14, pady=5, command=simpan).grid(row=4, column=0, columnspan=2, pady=12)

    def _popup_tambah_extra(self):
        w = tk.Toplevel(self)
        w.title("Tambah Pelunasan Ekstra")
        w.geometry("380x280")
        w.configure(bg="#111827")
        w.transient(self)
        w.grab_set()

        tk.Label(w, text="Bulan Ke:", bg="#111827", fg="white").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        ent_m = tk.Entry(w, bg="#1F2937", fg="white")
        ent_m.insert(0, "18")
        ent_m.grid(row=0, column=1, padx=12, pady=6)

        tk.Label(w, text="Kali Angsuran (x):", bg="#111827", fg="white").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ent_mult = tk.Entry(w, bg="#1F2937", fg="white")
        ent_mult.grid(row=1, column=1, padx=12, pady=6)

        tk.Label(w, text="Pokok Murni (Rp):", bg="#111827", fg="white").grid(row=2, column=0, padx=12, pady=6, sticky="w")
        ent_a = tk.Entry(w, bg="#1F2937", fg="white")
        ent_a.grid(row=2, column=1, padx=12, pady=6)

        def on_mult_change(event=None):
            try:
                mult_txt = ent_mult.get().strip()
                if not mult_txt:
                    return
                mult_val = float(mult_txt)
                m_txt = ent_m.get().strip()
                m_val = int(m_txt) if m_txt else 1
                pmt = 0.0
                if hasattr(self, 'simulasi_result') and self.simulasi_result and "rows" in self.simulasi_result:
                    for r in self.simulasi_result["rows"]:
                        if r["bulan"] == m_val:
                            pmt = r["total_angsuran"]
                            break
                    if pmt <= 0 and len(self.simulasi_result["rows"]) > 1:
                        pmt = self.simulasi_result["rows"][1]["total_angsuran"]
                if mult_val > 0 and pmt > 0:
                    calculated = round(mult_val * pmt)
                    ent_a.delete(0, tk.END)
                    ent_a.insert(0, f"{calculated:,.0f}")
            except (ValueError, TypeError):
                pass

        ent_mult.bind("<KeyRelease>", on_mult_change)
        ent_m.bind("<KeyRelease>", on_mult_change)

        tk.Label(w, text="Efek Pelunasan:", bg="#111827", fg="white").grid(row=3, column=0, padx=12, pady=6, sticky="w")
        cb_eff = ttk.Combobox(w, values=["-- Pilih Efek --", "KURANGI_TENOR", "KURANGI_ANGSURAN"], state="readonly")
        cb_eff.current(0)
        cb_eff.grid(row=3, column=1, padx=12, pady=6)

        def simpan():
            try:
                m = int(ent_m.get())
                amt_str = ent_a.get().replace(",", "").replace(".", "").replace("Rp", "").strip()
                amt = float(amt_str)
                mult_val = ent_mult.get().strip()
                mult_display = f"{mult_val}x" if mult_val else "-"
                eff = cb_eff.get()
                if not eff or eff == "-- Pilih Efek --":
                    messagebox.showwarning("Pilih Efek", "Harap pilih Efek Pada Pinjaman (KURANGI_TENOR atau KURANGI_ANGSURAN).")
                    return
                self.tree_extra.insert("", tk.END, values=(m, mult_display, f"{amt:,.0f}", eff))
                self._sort_tree_extra()
                w.destroy()
                self.hitung_dan_tampilkan()
            except ValueError:
                messagebox.showerror("Error", "Harap isi angka dengan benar.")

        tk.Button(w, text="Simpan Pelunasan", bg="#10B981", fg="white", relief="flat", padx=14, pady=5, command=simpan).grid(row=4, column=0, columnspan=2, pady=12)

    def _sort_tree_extra(self):
        items = []
        for item in self.tree_extra.get_children():
            vals = self.tree_extra.item(item, "values")
            items.append(vals)
        try:
            items.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else 999999)
        except (ValueError, TypeError):
            pass
        for item in self.tree_extra.get_children():
            self.tree_extra.delete(item)
        for vals in items:
            self.tree_extra.insert("", tk.END, values=vals)

    def _extract_installment_periods(self, rows):
        if not rows or len(rows) <= 1:
            return []
        periods = []
        cur = None
        for i in range(1, len(rows)):
            r = rows[i]
            is_last = (i == len(rows) - 1)
            is_new = False
            if not cur:
                is_new = True
            else:
                rate_changed = abs(r["suku_bunga_pa"] - cur["rate"]) > 0.001
                prev_row = rows[i - 1]
                had_extra = prev_row.get("pelunasan_ekstra", 0) > 0 and abs(r["total_angsuran"] - cur["pmt"]) > 100
                pmt_changed = (not is_last) and abs(r["total_angsuran"] - cur["pmt"]) > 500
                if r.get("is_tier_change") or rate_changed or had_extra or pmt_changed:
                    is_new = True

            if is_new:
                if cur:
                    cur["end_month"] = rows[i - 1]["bulan"]
                    periods.append(cur)
                cur = {
                    "start_month": r["bulan"],
                    "end_month": r["bulan"],
                    "rate": r["suku_bunga_pa"],
                    "pmt": r["total_angsuran"],
                    "extras": []
                }
            else:
                cur["end_month"] = r["bulan"]

            if r.get("pelunasan_ekstra", 0) > 0:
                cur["extras"].append({"bulan": r["bulan"], "amount": r["pelunasan_ekstra"]})

        if cur:
            cur["end_month"] = rows[-1]["bulan"]
            cur["is_lunas"] = True
            periods.append(cur)
        return periods

    def _parse_start_date(self) -> date:
        raw = self.ent_start_date.get().strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
        return date(2025, 5, 28)

    def _ambil_data_input(self):
        plafon_str = self.ent_plafon.get().replace(",", "").replace(".", "").strip()
        plafon = float(plafon_str)
        tenor = int(self.ent_tenor.get().strip())
        start_date = self._parse_start_date()

        jenis_raw = self.cb_jenis.get()
        if "Berjenjang" in jenis_raw:
            jenis = "BERJENJANG"
        elif "Anuitas" in jenis_raw:
            jenis = "ANUITAS"
        elif "Efektif" in jenis_raw:
            jenis = "EFEKTIF"
        else:
            jenis = "FLAT"

        annual_rate = 7.5

        tiers = []
        if jenis == "BERJENJANG":
            for item in self.tree_tier.get_children():
                vals = self.tree_tier.item(item, "values")
                s = int(vals[0])
                e = int(vals[1])
                r = float(vals[2])
                name = str(vals[3])
                tiers.append(TierBunga(s, e, r, name))

        self._sort_tree_extra()
        extras = []
        for item in self.tree_extra.get_children():
            vals = self.tree_extra.item(item, "values")
            m = int(vals[0])
            mult_str = str(vals[1]).replace("x", "").strip() if str(vals[1]) != "-" else ""
            mult_val = float(mult_str) if mult_str else None
            amt = float(str(vals[2]).replace(",", "").replace(".", "").replace("Rp", "").strip())
            eff = str(vals[3])
            extras.append(ExtraPayment(m, amt, eff, multiplier=mult_val))

        return plafon, tenor, start_date, jenis, annual_rate, tiers, extras

    def hitung_dan_tampilkan(self):
        try:
            plafon, tenor, start_date, jenis, annual_rate, tiers, extras = self._ambil_data_input()
            res = hitung_kpr(
                plafon=plafon,
                tenor_bulan=tenor,
                start_date=start_date,
                jenis_cicilan=jenis,
                annual_rate=annual_rate,
                tiers=tiers,
                extra_payments=extras
            )
            self.simulasi_result = res
            summary = res["summary"]
            rows = res["rows"]

            angsuran_bln1 = rows[1]["total_angsuran"] if len(rows) > 1 else 0.0
            self.val_pmt1.config(text=f"Rp {angsuran_bln1:,.0f}")
            self.val_tenor.config(text=f"{summary['tenor_aktual_bulan']} Bln (Hemat {summary['hemat_bulan']} Bln)")
            self.val_bunga.config(text=f"Rp {summary['total_bunga_terbayar']:,.0f}")
            self.val_hemat.config(text=f"Rp {summary.get('hemat_bunga_rp', 0):,.0f}")
            self.val_total.config(text=f"Rp {summary['total_pembayaran_keseluruhan']:,.0f}")

            # Perbarui nilai nominal di tree_extra jika ada kelipatan otomatis dinamis
            for idx, item in enumerate(self.tree_extra.get_children()):
                if idx < len(extras):
                    ex = extras[idx]
                    vals = list(self.tree_extra.item(item, "values"))
                    vals[2] = f"{ex.amount:,.0f}"
                    self.tree_extra.item(item, values=vals)

            # Update callout dinamis pelunasan & proyeksi angsuran per tahun
            periods = self._extract_installment_periods(rows)
            period_lines = []
            for p in periods:
                s_yr = ((p["start_month"] - 1) // 12) + 1
                e_yr = ((p["end_month"] - 1) // 12) + 1
                yr_txt = f"Tahun {s_yr}" if s_yr == e_yr else f"Tahun {s_yr}-{e_yr}"
                bln_txt = f"Bln {p['start_month']}-{p['end_month']}"
                extra_txt = f" [⚡ Pelunasan Bln {p['extras'][0]['bulan']}]" if p["extras"] else ""
                lunas_txt = " (Lunas!)" if p.get("is_lunas") and summary.get("hemat_bulan", 0) > 0 else ""
                period_lines.append(f"• {yr_txt} ({bln_txt}, {p['rate']:.2f}%): Rp {p['pmt']:,.0f}/bln{extra_txt}{lunas_txt}")
            period_str = "\n".join(period_lines)

            if not extras or summary.get("total_ekstra_terbayar", 0) <= 0:
                self.frame_extra_info.config(highlightbackground="#475569")
                info_header = f"💡 Belum ada pelunasan sebagian aktif. Tenor pinjaman {summary['tenor_rencana_bulan']} bulan."
                self.lbl_extra_info.config(text=f"{info_header}\n\n📅 Proyeksi Angsuran per Periode / Tahun:\n{period_str}", fg="#CBD5E1")
            else:
                has_tenor = any(x.get("effect") == "KURANGI_TENOR" for x in extras.values())
                has_angsuran = any(x.get("effect") == "KURANGI_ANGSURAN" for x in extras.values())
                if has_tenor and not has_angsuran:
                    self.frame_extra_info.config(highlightbackground="#10B981")
                    info_header = f"💡 Efek Kurangi Tenor: Pinjaman selesai LEBIH AWAL {summary['hemat_bulan']} Bulan (lunas bulan ke-{summary['tenor_aktual_bulan']}!). Hemat bunga: Rp {summary.get('hemat_bunga_rp', 0):,.0f}."
                    self.lbl_extra_info.config(text=f"{info_header}\n\n📅 Proyeksi Angsuran per Periode / Tahun:\n{period_str}", fg="#A7F3D0")
                elif has_angsuran and not has_tenor:
                    self.frame_extra_info.config(highlightbackground="#3B82F6")
                    info_header = f"💡 Efek Kurangi Angsuran: Tenor tetap ({summary['tenor_aktual_bulan']} bulan), angsuran lebih ringan. Hemat bunga: Rp {summary.get('hemat_bunga_rp', 0):,.0f}."
                    self.lbl_extra_info.config(text=f"{info_header}\n\n📅 Proyeksi Angsuran per Periode / Tahun:\n{period_str}", fg="#BFDBFE")
                else:
                    self.frame_extra_info.config(highlightbackground="#F59E0B")
                    info_header = f"💡 Efek Kombinasi: Pinjaman lunas di bulan ke-{summary['tenor_aktual_bulan']} (hemat {summary['hemat_bulan']} bln). Hemat bunga: Rp {summary.get('hemat_bunga_rp', 0):,.0f}."
                    self.lbl_extra_info.config(text=f"{info_header}\n\n📅 Proyeksi Angsuran per Periode / Tahun:\n{period_str}", fg="#FDE68A")

            for item in self.tree_schedule.get_children():
                self.tree_schedule.delete(item)

            for r in rows:
                tag = ""
                if r.get("is_tier_change"):
                    tag = "tier_change"
                elif r["pelunasan_ekstra"] > 0:
                    tag = "extra_row"
                elif r.get("is_year_end"):
                    tag = "year_end"

                self.tree_schedule.insert(
                    "",
                    tk.END,
                    values=(
                        r["bulan"],
                        r["tanggal"],
                        f"{r['suku_bunga_pa']:.2f}%",
                        f"{r['angsuran_pokok']:,.0f}",
                        f"{r['angsuran_bunga']:,.0f}",
                        f"{r['total_angsuran']:,.0f}",
                        f"{r['pelunasan_ekstra']:,.0f}" if r["pelunasan_ekstra"] > 0 else "-",
                        f"{r['saldo_pinjaman']:,.0f}",
                        r["keterangan"],
                    ),
                    tags=(tag,) if tag else ()
                )

        except Exception as e:
            messagebox.showerror("Error Perhitungan", f"Terjadi kesalahan: {str(e)}")

    def generate_excel(self):
        if not self.simulasi_result:
            self.hitung_dan_tampilkan()
            if not self.simulasi_result:
                return

        nama_bank = self.ent_bank.get().strip() or "Bank"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=f"Simulasi_KPR_{nama_bank.replace(' ', '_')}.xlsx"
        )
        if file_path:
            try:
                export_to_excel(self.simulasi_result, file_path, nama_bank=nama_bank)
                messagebox.showinfo("Berhasil", f"Jadwal simulasi KPR berhasil diekspor ke:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Gagal Ekspor", f"Gagal mengekspor file: {str(e)}")

    def export_json(self):
        try:
            nama_bank = self.ent_bank.get().strip() or "Simulasi_KPR"
            plafon = self.ent_plafon.get().strip()
            tenor = self.ent_tenor.get().strip()
            tgl = self.ent_start_date.get().strip()
            skema = self.cbo_jenis.get().strip()

            tiers = []
            for item in self.tree_tier.get_children():
                vals = self.tree_tier.item(item)["values"]
                tiers.append({
                    "start": vals[0],
                    "end": vals[1],
                    "rate": vals[2],
                    "name": vals[3]
                })

            extras = []
            for item in self.tree_extra.get_children():
                vals = self.tree_extra.item(item)["values"]
                eff = "KURANGI_TENOR" if "Tenor" in str(vals[3]) else "KURANGI_ANGSURAN"
                extras.append({
                    "month": vals[0],
                    "multiplier": str(vals[1]).replace("x", "").strip() if str(vals[1]) != "-" else "",
                    "amount": vals[2],
                    "effect": eff
                })

            data = {
                "app": "Simulasi KPR Pro",
                "version": "1.0",
                "bankName": nama_bank,
                "plafon": plafon,
                "tenor": tenor,
                "startDate": tgl,
                "jenisCicilan": "BERJENJANG" if "Berjenjang" in skema else "ANUITAS",
                "singleRate": self.ent_single_rate.get().strip(),
                "tiers": tiers,
                "extras": extras,
                "exportedAt": datetime.now().isoformat()
            }

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                initialfile=f"KPR_{nama_bank.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.json"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Berhasil", f"Data konfigurasi simulasi KPR berhasil disimpan ke:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Gagal Simpan JSON", f"Terjadi kesalahan: {str(e)}")

    def import_json(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "bankName" in data:
                self.ent_bank.delete(0, tk.END)
                self.ent_bank.insert(0, data["bankName"])
            if "plafon" in data:
                self.ent_plafon.delete(0, tk.END)
                self.ent_plafon.insert(0, str(data["plafon"]))
            if "tenor" in data:
                self.ent_tenor.delete(0, tk.END)
                self.ent_tenor.insert(0, str(data["tenor"]))
            if "startDate" in data:
                self.ent_start_date.delete(0, tk.END)
                self.ent_start_date.insert(0, data["startDate"])

            if "tiers" in data and isinstance(data["tiers"], list):
                for item in self.tree_tier.get_children():
                    self.tree_tier.delete(item)
                for t in data["tiers"]:
                    self.tree_tier.insert("", tk.END, values=(t.get("start"), t.get("end"), t.get("rate"), t.get("name", "")))

            if "extras" in data and isinstance(data["extras"], list):
                for item in self.tree_extra.get_children():
                    self.tree_extra.delete(item)
                for e in data["extras"]:
                    eff_txt = "Kurangi Tenor" if e.get("effect") == "KURANGI_TENOR" else "Kurangi Angsuran"
                    mult_val = e.get("multiplier", "")
                    mult_txt = f"{mult_val}x" if mult_val else "-"
                    self.tree_extra.insert("", tk.END, values=(e.get("month"), mult_txt, e.get("amount"), eff_txt))
                self._sort_tree_extra()

            self.hitung_dan_tampilkan()
            messagebox.showinfo("Berhasil", f"Data berhasil dimuat dari:\n{os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Gagal Buka JSON", f"Gagal membaca file JSON: {str(e)}")

    def buka_trakteer(self):
        url = "https://trakteer.id/olapoal.artgallery/tip"
        try:
            import webbrowser
            webbrowser.open_new_tab(url)
        except Exception:
            messagebox.showinfo("Donasi Pengembang", f"Silakan kunjungi halaman donasi Trakteer kami di:\n{url}")

    def hapus_semua_data(self):
        # Custom Modern Fintech Modal Dialog
        dlg = tk.Toplevel(self)
        dlg.title("Konfirmasi Hapus Data")
        dlg.geometry("450x330")
        dlg.configure(bg="#0F172A")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        # Center dialog relative to main window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 225
        y = self.winfo_y() + (self.winfo_height() // 2) - 165
        dlg.geometry(f"+{max(0, x)}+{max(0, y)}")

        card = tk.Frame(dlg, bg="#1E293B", padx=20, pady=18, highlightthickness=1, highlightbackground="#EF4444")
        card.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Header Icon & Title
        tk.Label(card, text="🗑️", font=("Segoe UI", 26), fg="#EF4444", bg="#1E293B").pack(pady=(0, 4))
        tk.Label(card, text="Hapus Semua Data Simulasi?", font=("Segoe UI", 12, "bold"), fg="#F8FAFC", bg="#1E293B").pack(pady=(0, 6))
        tk.Label(
            card,
            text="Seluruh parameter pinjaman, suku bunga berjenjang,\ndan jadwal pelunasan dipercepat akan dikosongkan.",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#1E293B",
            justify=tk.CENTER
        ).pack(pady=(0, 12))

        # Tip Box
        f_tip = tk.Frame(card, bg="#111827", padx=10, pady=8, highlightthickness=1, highlightbackground="#F59E0B")
        f_tip.pack(fill=tk.X, pady=(0, 16))
        tk.Label(
            f_tip,
            text="💡 Tip: Anda dapat mencadangkan simulasi dengan tombol 'Simpan .json' sebelum menghapus.",
            font=("Segoe UI", 8),
            fg="#FDE68A",
            bg="#111827",
            wraplength=380,
            justify=tk.LEFT
        ).pack()

        # Action Buttons
        f_btns = tk.Frame(card, bg="#1E293B")
        f_btns.pack(fill=tk.X)

        def batal():
            dlg.destroy()

        def konfirmasi():
            dlg.destroy()
            self._eksekusi_hapus_data()

        btn_cancel = tk.Button(
            f_btns,
            text="Batal",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#F8FAFC",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=6,
            command=batal
        )
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_confirm = tk.Button(
            f_btns,
            text="🗑️ Ya, Hapus Semua Data",
            font=("Segoe UI", 9, "bold"),
            bg="#EF4444",
            fg="#FFFFFF",
            activebackground="#DC2626",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=6,
            command=konfirmasi
        )
        btn_confirm.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

        dlg.bind("<Escape>", lambda e: batal())

    def _eksekusi_hapus_data(self):
        self.ent_bank.delete(0, tk.END)
        self.ent_bank.insert(0, "KPR Bank")
        self.ent_plafon.delete(0, tk.END)
        self.ent_tenor.delete(0, tk.END)
        self.ent_tenor.insert(0, "180")
        for item in self.tree_tier.get_children():
            self.tree_tier.delete(item)
        self.tree_tier.insert("", tk.END, values=(1, 36, "5.75", "Tahun 1-3 (5.75% Fixed)"))
        self.tree_tier.insert("", tk.END, values=(37, 72, "8.50", "Tahun 4-6 (8.50% Fixed)"))
        self.tree_tier.insert("", tk.END, values=(73, 180, "10.50", "Tahun 7-15 (10.50% Floating)"))
        for item in self.tree_extra.get_children():
            self.tree_extra.delete(item)
        for item in self.tree_schedule.get_children():
            self.tree_schedule.delete(item)
        self.val_pmt1.config(text="Rp 0")
        self.val_tenor.config(text="0 Bulan")
        self.val_bunga.config(text="Rp 0")
        self.val_hemat.config(text="Rp 0")
        self.val_total.config(text="Rp 0")
        self.frame_extra_info.config(highlightbackground="#475569")
        self.lbl_extra_info.config(text="💡 Belum ada pelunasan sebagian aktif.", fg="#94A3B8")
        self.simulasi_result = None

if __name__ == "__main__":
    app = AplikasiKPR()
    app.mainloop()
