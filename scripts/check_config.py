RTS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "11", "12", "13", "14"]
REFERENCES = {
    "SDN Jembatan Besi": (-6.153027, 106.798433),
    "Sekretariat Pos RW 06": (-6.153560, 106.798694),
}
assert len(RTS) == 13 and "10" not in RTS
assert all(-90 <= lat <= 90 and -180 <= lng <= 180 for lat, lng in REFERENCES.values())
print("Konfigurasi RW 06 valid: 13 RT dan 2 titik referensi peta.")
print("Catatan: titik referensi bukan batas wilayah dan bukan pusat administratif.")
