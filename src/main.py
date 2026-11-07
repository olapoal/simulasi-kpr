"""Entry point utama Aplikasi Hitung KPR.
Menjalankan GUI secara default jika tanpa argumen, atau menjalankan CLI jika argumen diberikan.
"""

import sys
import argparse
from datetime import datetime

def jalankan_gui():
    try:
        from gui import AplikasiKPR
        app = AplikasiKPR()
        app.mainloop()
    except Exception as e:
        print(f"Error membuka GUI: {e}")
        print("Menjalankan dalam mode CLI...")
        jalankan_cli_default()

def parse_extra_cli(s: str):
    from calculator import ExtraPayment
    extras = []
    if not s:
        return extras
    # Format: "bulan:nominal[:efek],bulan:nominal[:efek]"
    # contoh: "36:50000000:KURANGI_TENOR,48:25000000:KURANGI_ANGSURAN"
    for part in s.split(','):
        if not part.strip():
            continue
        tokens = part.split(':')
        m = int(tokens[0].strip())
        amt = float(tokens[1].strip())
        eff = tokens[2].strip() if len(tokens) > 2 else "KURANGI_TENOR"
        extras.append(ExtraPayment(month=m, amount=amt, effect=eff))
    return extras

def jalankan_cli(args):
    from calculator import hitung_kpr, TierBunga
    from excel_exporter import export_to_excel

    tiers = []
    if args.tiers:
        # Format: "1:36:5.75:Thn 1-3,37:72:8.50:Thn 4-6,73:180:10.50:Thn 7-15"
        for t_str in args.tiers.split(','):
            tokens = t_str.split(':')
            s = int(tokens[0].strip())
            e = int(tokens[1].strip())
            r = float(tokens[2].strip())
            lbl = tokens[3].strip() if len(tokens) > 3 else f"Bln {s}-{e}"
            tiers.append(TierBunga(s, e, r, lbl))

    extras = parse_extra_cli(args.extra)

    res = hitung_kpr(
        plafon=args.plafon,
        tenor_bulan=args.tenor,
        jenis_cicilan=args.jenis,
        annual_rate=args.rate,
        tiers=tiers,
        extra_payments=extras
    )

    export_to_excel(res, args.out, nama_bank=args.bank)
    summary = res["summary"]
    print("=" * 60)
    print(f"SIMULASI KPR {args.bank.upper()} BERHASIL DI-GENERATE")
    print("=" * 60)
    print(f"Plafon Pinjaman         : Rp {summary['plafon']:,.0f}")
    print(f"Jenis Cicilan           : {summary['jenis_cicilan']}")
    print(f"Tenor Rencana           : {summary['tenor_rencana_bulan']} Bulan")
    print(f"Tenor Aktual            : {summary['tenor_aktual_bulan']} Bulan (Hemat {summary['hemat_bulan']} Bulan!)")
    print(f"Total Bunga Terbayar    : Rp {summary['total_bunga_terbayar']:,.0f}")
    print(f"Total Seluruh Bayar     : Rp {summary['total_pembayaran_keseluruhan']:,.0f}")
    print(f"File Excel Tersimpan Di : {args.out}")
    print("=" * 60)

def jalankan_cli_default():
    from calculator import hitung_kpr
    from excel_exporter import export_to_excel
    # Contoh default simulasi KPR Bank
    res = hitung_kpr(
        plafon=676000000,
        tenor_bulan=180,
        jenis_cicilan="BERJENJANG"
    )
    export_to_excel(res, "Simulasi_KPR_Contoh.xlsx", nama_bank="KPR Bank")
    print("Simulasi KPR Contoh berhasil disimpan ke 'Simulasi_KPR_Contoh.xlsx'.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Tanpa parameter -> Buka GUI
        jalankan_gui()
    else:
        parser = argparse.ArgumentParser(description="Kalkulator KPR & Pelunasan Dipercepat")
        parser.add_argument("--gui", action="store_true", help="Buka antarmuka grafis (GUI)")
        parser.add_argument("--plafon", type=float, default=676000000, help="Jumlah pinjaman pokok (Rp)")
        parser.add_argument("--tenor", type=int, default=180, help="Tenor pinjaman dalam bulan")
        parser.add_argument("--jenis", type=str, default="BERJENJANG", choices=["BERJENJANG", "ANUITAS", "EFEKTIF", "FLAT"], help="Jenis cicilan bunga")
        parser.add_argument("--rate", type=float, default=7.5, help="Suku bunga tahunan (persen) jika non-berjenjang")
        parser.add_argument("--tiers", type=str, default="", help="Konfigurasi tier berjenjang 'mulai:selesai:bunga:nama,...'")
        parser.add_argument("--extra", type=str, default="", help="Pelunasan ekstra 'bulan:nominal:efek,...'")
        parser.add_argument("--bank", type=str, default="KPR Bank", help="Nama bank untuk label Excel")
        parser.add_argument("--out", type=str, default="Simulasi_KPR.xlsx", help="Nama file output Excel")

        args = parser.parse_args()
        if args.gui:
            jalankan_gui()
        else:
            jalankan_cli(args)
