"""Modul ekspor hasil simulasi KPR ke format Excel (.xlsx) dengan tanggal jatuh tempo perbankan.
"""

from typing import Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def export_to_excel(result_data: Dict[str, Any], file_path: str, nama_bank: str = "Bank") -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Simulasi KPR"
    ws.views.sheetView[0].showGridLines = True

    summary = result_data.get("summary", {})
    rows = result_data.get("rows", [])

    COLOR_HEADER_BG = "8B0000"
    COLOR_HEADER_FG = "FFFFFF"
    COLOR_TIER_BG = "1F497D"
    COLOR_TIER_FG = "FFFFFF"
    COLOR_EXTRA_BG = "D9EAD3"
    COLOR_YEAR_BG = "F3F3F3"
    COLOR_TOTAL_BG = "D9D9D9"

    font_title = Font(name="Calibri", size=16, bold=True, color="8B0000")
    font_sub = Font(name="Calibri", size=11, bold=True)
    font_header = Font(name="Calibri", size=10, bold=True, color=COLOR_HEADER_FG)
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)

    fill_header = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
    fill_tier = PatternFill(start_color=COLOR_TIER_BG, end_color=COLOR_TIER_BG, fill_type="solid")
    fill_extra = PatternFill(start_color=COLOR_EXTRA_BG, end_color=COLOR_EXTRA_BG, fill_type="solid")
    fill_year = PatternFill(start_color=COLOR_YEAR_BG, end_color=COLOR_YEAR_BG, fill_type="solid")
    fill_total = PatternFill(start_color=COLOR_TOTAL_BG, end_color=COLOR_TOTAL_BG, fill_type="solid")

    thin_border_side = Side(style="thin", color="CCCCCC")
    double_bottom_side = Side(style="double", color="000000")

    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_total = Border(top=thin_border_side, bottom=double_bottom_side)

    # 1. Judul Dokumen
    ws.merge_cells("A1:H1")
    ws["A1"] = f"Prakiraan Angsuran Bunga + Pokok KPR {nama_bank}".strip()
    ws["A1"].font = font_title
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # 2. Ringkasan Parameter Pinjaman
    ws["A3"] = "Ringkasan Pinjaman:"
    ws["A3"].font = font_sub

    info_data = [
        ("Plafon Pinjaman", summary.get("plafon", 0), "Rp #,##0"),
        ("Tanggal Awal Angsuran", summary.get("tanggal_awal_angsuran", "-"), "@"),
        ("Estimasi Tanggal Lunas", summary.get("tanggal_pelunasan_terakhir", "-"), "@"),
        ("Jenis Perhitungan", summary.get("jenis_cicilan", ""), "@"),
        ("Tenor Rencana", f"{summary.get('tenor_rencana_bulan', 0)} Bulan ({summary.get('tenor_rencana_bulan', 0)//12} Tahun)", "@"),
        ("Tenor Aktual", f"{summary.get('tenor_aktual_bulan', 0)} Bulan (Hemat {summary.get('hemat_bulan', 0)} Bulan!)", "@"),
        ("Total Pokok Terbayar", summary.get("total_pokok_terbayar", 0), "Rp #,##0"),
        ("Total Pelunasan Ekstra", summary.get("total_ekstra_terbayar", 0), "Rp #,##0"),
        ("Total Bunga Terbayar", summary.get("total_bunga_terbayar", 0), "Rp #,##0"),
        ("Total Keseluruhan", summary.get("total_pembayaran_keseluruhan", 0), "Rp #,##0"),
    ]

    for idx, (label, val, fmt) in enumerate(info_data):
        r = 4 + idx
        ws.cell(row=r, column=1, value=label).font = font_bold
        val_cell = ws.cell(row=r, column=2, value=val)
        val_cell.font = font_regular
        if fmt != "@":
            val_cell.number_format = fmt
        val_cell.alignment = Alignment(horizontal="right" if fmt != "@" else "left")

    start_row_table = 4 + len(info_data) + 2

    # 3. Header Tabel
    headers = [
        "Bulan",
        "Tgl Jatuh Tempo",
        "Suku Bunga (% p.a.)",
        "Angsuran Pokok",
        "Angsuran Bunga",
        "Total Angsuran",
        "Pelunasan Ekstra",
        "Saldo Pinjaman",
        "Keterangan / Tier",
    ]

    ws.row_dimensions[start_row_table].height = 25
    for c_idx, h_text in enumerate(headers, 1):
        cell = ws.cell(row=start_row_table, column=c_idx, value=h_text)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 4. Baris Data
    curr_r = start_row_table + 1
    rupiah_fmt = "Rp #,##0"
    rate_fmt = "0.00%"

    for row_data in rows:
        m = row_data["bulan"]
        tgl = row_data["tanggal"]
        rate = row_data["suku_bunga_pa"] / 100
        pokok = row_data["angsuran_pokok"]
        bunga = row_data["angsuran_bunga"]
        total = row_data["total_angsuran"]
        ekstra = row_data["pelunasan_ekstra"]
        saldo = row_data["saldo_pinjaman"]
        ket = row_data["keterangan"]

        ws.row_dimensions[curr_r].height = 20

        c1 = ws.cell(row=curr_r, column=1, value=m)
        c2 = ws.cell(row=curr_r, column=2, value=tgl)
        c3 = ws.cell(row=curr_r, column=3, value=rate)
        c4 = ws.cell(row=curr_r, column=4, value=pokok)
        c5 = ws.cell(row=curr_r, column=5, value=bunga)
        c6 = ws.cell(row=curr_r, column=6, value=total)
        c7 = ws.cell(row=curr_r, column=7, value=ekstra)
        c8 = ws.cell(row=curr_r, column=8, value=saldo)
        c9 = ws.cell(row=curr_r, column=9, value=ket)

        c1.alignment = Alignment(horizontal="center")
        c2.alignment = Alignment(horizontal="center")
        c3.alignment = Alignment(horizontal="center")
        c3.number_format = rate_fmt

        for c in (c4, c5, c6, c7, c8):
            c.number_format = rupiah_fmt
            c.alignment = Alignment(horizontal="right")

        c9.alignment = Alignment(horizontal="left")

        for c in (c1, c2, c3, c4, c5, c6, c7, c8, c9):
            c.border = border_cell
            c.font = font_regular

        if m == 0:
            c1.font = font_bold
            c8.font = font_bold
            c9.font = font_bold
        elif row_data.get("is_tier_change"):
            for c in (c1, c2, c3, c4, c5, c6, c7, c8, c9):
                c.fill = fill_tier
                c.font = Font(name="Calibri", size=10, bold=True, color=COLOR_TIER_FG)
        elif ekstra > 0:
            for c in (c1, c2, c3, c4, c5, c6, c7, c8, c9):
                c.fill = fill_extra
                c.font = Font(name="Calibri", size=10, bold=True)
        elif row_data.get("is_year_end"):
            for c in (c1, c2, c3, c4, c5, c6, c7, c8, c9):
                c.fill = fill_year
                c.font = font_bold

        curr_r += 1

    # 5. Baris Total
    ws.row_dimensions[curr_r].height = 22
    total_lbl = ws.cell(row=curr_r, column=1, value="TOTAL")
    total_lbl.font = font_bold
    total_lbl.alignment = Alignment(horizontal="center")
    total_lbl.fill = fill_total

    ws.cell(row=curr_r, column=2, value="").fill = fill_total
    ws.cell(row=curr_r, column=3, value="").fill = fill_total

    for col_idx in (4, 5, 6, 7):
        col_letter = get_column_letter(col_idx)
        sum_formula = f"=SUM({col_letter}{start_row_table + 1}:{col_letter}{curr_r - 1})"
        cell = ws.cell(row=curr_r, column=col_idx, value=sum_formula)
        cell.font = font_bold
        cell.number_format = rupiah_fmt
        cell.alignment = Alignment(horizontal="right")
        cell.fill = fill_total
        cell.border = border_total

    ws.cell(row=curr_r, column=8, value=0).number_format = rupiah_fmt
    ws.cell(row=curr_r, column=8).alignment = Alignment(horizontal="right")
    ws.cell(row=curr_r, column=8).font = font_bold
    ws.cell(row=curr_r, column=8).fill = fill_total

    ws.cell(row=curr_r, column=9, value="Lunas").font = font_bold
    ws.cell(row=curr_r, column=9).fill = fill_total

    # 6. Auto Width
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len and "\n" not in val_str:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["I"].width = 35

    wb.save(file_path)
