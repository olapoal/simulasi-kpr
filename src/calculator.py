"""Modul Kalkulator KPR lengkap dengan berbagai jenis suku bunga, pelunasan dipercepat,
serta pelacakan tanggal jatuh tempo otomatis per bulan.

Mendukung efek pelunasan dipercepat sebagian:
- 'KURANGI_TENOR': Angsuran bulanan tetap sama sesuai standar tier/suku bunga,
  sehingga sisa pokok pinjaman lunas jauh lebih cepat (jangka waktu tenor berkurang nyata!).
- 'KURANGI_ANGSURAN': Tenor tetap hingga akhir, tetapi nilai angsuran bulanan dihitung ulang
  menjadi lebih kecil/ringan.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Optional

def add_months(sourcedate: date, months: int) -> date:
    """Menambah sejumlah bulan ke tanggal dengan penyesuaian hari jatuh tempo."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    max_days = calendar.monthrange(year, month)[1]
    day = min(sourcedate.day, max_days)
    return date(year, month, day)

@dataclass
class TierBunga:
    start_month: int       # Bulan mulai (1-based, misal 1)
    end_month: int         # Bulan selesai (misal 36)
    annual_rate: float     # Suku bunga tahunan dalam persen (misal 5.75)
    name: str = ""         # Nama tier opsional, misal "Fixed Thn 1-3"

@dataclass
class ExtraPayment:
    month: int             # Bulan ke berapa pelunasan dilakukan (1-based)
    amount: float          # Jumlah pelunasan pokok ekstra
    effect: str = "KURANGI_TENOR"  # "KURANGI_TENOR" atau "KURANGI_ANGSURAN"
    note: str = ""         # Keterangan
    multiplier: Optional[float] = None  # Kelipatan angsuran bulanan dinamis (misal 6 = 6x cicilan)

def hitung_pmt(principal: float, monthly_rate: float, remaining_months: int) -> float:
    """Menghitung angsuran bulanan anuitas konstan."""
    if remaining_months <= 0 or principal <= 0:
        return 0.0
    if monthly_rate == 0:
        return principal / remaining_months
    factor = (1 + monthly_rate) ** remaining_months
    return principal * (monthly_rate * factor) / (factor - 1)

def hitung_kpr(
    plafon: float,
    tenor_bulan: int,
    start_date: Optional[date] = None,
    jenis_cicilan: str = "BERJENJANG",
    annual_rate: float = 5.75,
    tiers: Optional[List[TierBunga]] = None,
    extra_payments: Optional[List[ExtraPayment]] = None,
) -> Dict[str, Any]:
    """Menghitung jadwal amortisasi lengkap KPR."""
    if start_date is None:
        start_date = date(2025, 5, 28)

    jenis = jenis_cicilan.upper()
    extra_map: Dict[int, ExtraPayment] = {}
    if extra_payments:
        for ep in extra_payments:
            extra_map[ep.month] = ep

    # Setup tiers jika berjenjang
    active_tiers: List[TierBunga] = []
    if jenis == "BERJENJANG":
        if tiers and len(tiers) > 0:
            active_tiers = sorted(tiers, key=lambda t: t.start_month)
        else:
            active_tiers = [
                TierBunga(1, 36, 5.75, "Tahun 1-3 (5.75%)"),
                TierBunga(37, 72, 8.50, "Tahun 4-6 (8.50%)"),
                TierBunga(73, tenor_bulan, 10.50, f"Tahun 7-{tenor_bulan//12} (10.50%)"),
            ]

    def get_rate_for_month(m: int) -> float:
        if jenis == "BERJENJANG":
            for t in active_tiers:
                if t.start_month <= m <= t.end_month:
                    return t.annual_rate
            if active_tiers:
                return active_tiers[-1].annual_rate
            return annual_rate
        return annual_rate

    # LANGKAH 1: Hitung jadwal standar normal (tanpa pelunasan ekstra)
    # Ini penting untuk mendapatkan nilai angsuran bulanan standar di tiap tier perbankan!
    std_pmt_map: Dict[int, float] = {}
    saldo_std = plafon
    curr_std_pmt = 0.0
    curr_tier_idx = -1

    total_bunga_baseline = 0.0
    for m_std in range(1, tenor_bulan + 1):
        rate_mo = (get_rate_for_month(m_std) / 100) / 12
        sisa_tenor_std = tenor_bulan - m_std + 1

        if jenis in ("ANUITAS", "BERJENJANG"):
            if jenis == "BERJENJANG":
                t_idx = -1
                for idx, t in enumerate(active_tiers):
                    if t.start_month <= m_std <= t.end_month:
                        t_idx = idx
                        break
                if t_idx == -1 and active_tiers:
                    t_idx = 0 if m_std < active_tiers[0].start_month else (len(active_tiers) - 1)
                if t_idx != curr_tier_idx:
                    curr_tier_idx = t_idx
                    curr_std_pmt = hitung_pmt(saldo_std, rate_mo, sisa_tenor_std)
            else:
                if m_std == 1:
                    curr_std_pmt = hitung_pmt(saldo_std, rate_mo, sisa_tenor_std)
            std_pmt_map[m_std] = curr_std_pmt
            bunga_std = saldo_std * rate_mo
            pokok_std = curr_std_pmt - bunga_std
            saldo_std -= pokok_std
            total_bunga_baseline += bunga_std
        elif jenis == "FLAT":
            total_bunga_baseline += (plafon * (annual_rate / 100)) / 12
        elif jenis == "EFEKTIF":
            bunga_std = saldo_std * rate_mo
            pokok_std = min(plafon / tenor_bulan if tenor_bulan > 0 else 0.0, saldo_std)
            saldo_std -= pokok_std
            total_bunga_baseline += bunga_std

    # LANGKAH 2: Hitung jadwal aktual dengan pelunasan dipercepat sebagian
    saldo = plafon
    rows: List[Dict[str, Any]] = []

    # Bulan 0 (Akad)
    tgl_akad = add_months(start_date, -1)
    rows.append({
        "bulan": 0,
        "tanggal": tgl_akad.strftime("%d/%m/%Y"),
        "tahun": 0,
        "bulan_ke_tahun": 0,
        "suku_bunga_pa": get_rate_for_month(1),
        "angsuran_pokok": 0.0,
        "angsuran_bunga": 0.0,
        "total_angsuran": 0.0,
        "pelunasan_ekstra": 0.0,
        "saldo_pinjaman": round(saldo, 2),
        "keterangan": "Plafon Awal Pinjaman",
        "is_tier_change": False,
        "is_year_end": False,
    })

    current_pmt = std_pmt_map.get(1, 0.0)
    current_tier_index = -1
    pokok_tetap = plafon / tenor_bulan if tenor_bulan > 0 else 0.0
    bunga_flat_bulanan = (plafon * (annual_rate / 100)) / 12

    # Status apakah pernah dilakukan pelunasan dengan opsi KURANGI_ANGSURAN
    mode_kurangi_angsuran_aktif = False

    m = 1
    total_bunga_terbayar = 0.0
    total_pokok_terbayar = 0.0
    total_ekstra_terbayar = 0.0

    while m <= tenor_bulan and saldo > 0.01:
        rate_pa = get_rate_for_month(m)
        rate_mo = (rate_pa / 100) / 12
        sisa_tenor = tenor_bulan - m + 1
        tgl_jt = add_months(start_date, m - 1)

        is_tier_change = False
        tier_label = ""

        if jenis == "BERJENJANG":
            new_tier_idx = -1
            for idx, t in enumerate(active_tiers):
                if t.start_month <= m <= t.end_month:
                    new_tier_idx = idx
                    tier_label = t.name
                    break
            if new_tier_idx == -1 and active_tiers:
                new_tier_idx = 0 if m < active_tiers[0].start_month else (len(active_tiers) - 1)
                tier_label = active_tiers[new_tier_idx].name
            if new_tier_idx != current_tier_index:
                current_tier_index = new_tier_idx
                is_tier_change = (m > 1)
                if mode_kurangi_angsuran_aktif:
                    # Jika kurangi angsuran, hitung pmt baru dari sisa saldo
                    current_pmt = hitung_pmt(saldo, rate_mo, sisa_tenor)
                else:
                    # JIKA KURANGI TENOR: Angsuran bulanan tetap memakai standar tier!
                    # Ini yang membuat pinjaman lunas LEBIH CEPAT (tenor benar-benar berkurang)!
                    current_pmt = std_pmt_map.get(m, hitung_pmt(saldo, rate_mo, sisa_tenor))
        elif jenis == "ANUITAS":
            if m == 1:
                current_pmt = hitung_pmt(saldo, rate_mo, sisa_tenor)
                tier_label = f"Fixed ({annual_rate}%)"

        if jenis == "FLAT":
            bunga_bln = bunga_flat_bulanan
            pokok_bln = pokok_tetap
            total_angsuran = pokok_bln + bunga_bln
        elif jenis == "EFEKTIF":
            bunga_bln = saldo * rate_mo
            pokok_bln = min(pokok_tetap, saldo)
            total_angsuran = pokok_bln + bunga_bln
        else: # ANUITAS & BERJENJANG
            bunga_bln = saldo * rate_mo
            # Jika saldo tersisa lebih kecil dari porsi pokok reguler, lunaskan di bulan ini!
            if (current_pmt - bunga_bln) >= saldo:
                pokok_bln = saldo
                total_angsuran = pokok_bln + bunga_bln
            else:
                pokok_bln = current_pmt - bunga_bln
                total_angsuran = current_pmt

        extra_obj = extra_map.get(m)
        extra_amt = 0.0
        extra_effect = ""
        if extra_obj:
            if extra_obj.multiplier is not None and extra_obj.multiplier > 0 and current_pmt > 0:
                extra_obj.amount = round(extra_obj.multiplier * current_pmt)
            extra_amt = extra_obj.amount
            extra_effect = extra_obj.effect

        saldo_setelah_reguler = saldo - pokok_bln
        if extra_amt > 0:
            if extra_amt >= saldo_setelah_reguler:
                extra_amt = max(0.0, saldo_setelah_reguler)
                saldo_akhir = 0.0
            else:
                saldo_akhir = saldo_setelah_reguler - extra_amt

            total_ekstra_terbayar += extra_amt

            if extra_effect == "KURANGI_ANGSURAN":
                mode_kurangi_angsuran_aktif = True
                if jenis in ("ANUITAS", "BERJENJANG") and saldo_akhir > 0 and sisa_tenor > 1:
                    next_rate_mo = (get_rate_for_month(m + 1) / 100) / 12
                    current_pmt = hitung_pmt(saldo_akhir, next_rate_mo, sisa_tenor - 1)
            else:
                # KURANGI_TENOR: Angsuran bulanan tetap sama seperti biasa, sehingga tenor memendek!
                pass
        else:
            saldo_akhir = max(0.0, saldo_setelah_reguler)

        total_bunga_terbayar += bunga_bln
        total_pokok_terbayar += pokok_bln
        tahun_ke = ((m - 1) // 12) + 1
        bulan_ke_tahun = ((m - 1) % 12) + 1
        is_year_end = (bulan_ke_tahun == 12)

        ket = []
        if tier_label:
            ket.append(tier_label)
        if extra_amt > 0:
            ket.append(f"Pelunasan ({extra_effect})")
        if saldo_akhir <= 0.01:
            ket.append("🎉 LUNAS")
        elif is_year_end:
            ket.append(f"Thn {tahun_ke}")

        rows.append({
            "bulan": m,
            "tanggal": tgl_jt.strftime("%d/%m/%Y"),
            "tahun": tahun_ke,
            "bulan_ke_tahun": bulan_ke_tahun,
            "suku_bunga_pa": rate_pa,
            "angsuran_pokok": round(pokok_bln, 2),
            "angsuran_bunga": round(bunga_bln, 2),
            "total_angsuran": round(total_angsuran, 2),
            "pelunasan_ekstra": round(extra_amt, 2),
            "saldo_pinjaman": round(saldo_akhir, 2),
            "keterangan": " • ".join(ket),
            "is_tier_change": is_tier_change,
            "is_year_end": is_year_end,
        })

        saldo = saldo_akhir
        m += 1

    actual_months = len(rows) - 1
    hemat_bulan = max(0, tenor_bulan - actual_months)

    summary = {
        "plafon": plafon,
        "tanggal_awal_angsuran": start_date.strftime("%d/%m/%Y"),
        "tanggal_pelunasan_terakhir": rows[-1]["tanggal"] if rows else "",
        "tenor_rencana_bulan": tenor_bulan,
        "tenor_aktual_bulan": actual_months,
        "jenis_cicilan": jenis,
        "total_pokok_terbayar": round(total_pokok_terbayar, 2),
        "total_ekstra_terbayar": round(total_ekstra_terbayar, 2),
        "total_bunga_terbayar": round(total_bunga_terbayar, 2),
        "total_bunga_baseline": round(total_bunga_baseline, 2),
        "hemat_bunga_rp": round(max(0.0, total_bunga_baseline - total_bunga_terbayar), 2),
        "total_pembayaran_keseluruhan": round(total_pokok_terbayar + total_ekstra_terbayar + total_bunga_terbayar, 2),
        "hemat_bulan": hemat_bulan,
        "sisa_saldo_akhir": round(saldo, 2),
    }

    return {
        "rows": rows,
        "summary": summary,
        "tiers": active_tiers if jenis == "BERJENJANG" else [],
    }
