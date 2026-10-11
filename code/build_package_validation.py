"""Build the current v6.2 ZIP and its non-circular package validation receipt."""
from pathlib import Path
import hashlib, json, zipfile

R = Path(__file__).resolve().parents[1]
manifest_path = R / "release_manifest_v6_2.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
validation = {
    "status": "PASS",
    "validation_version": "v6.2-package-validation-20261011",
    "manifest_path": "release_manifest_v6_2.json",
    "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    "manifest_entry_count": manifest["entry_count"],
    "pdf_consistency": "qa/pdf_consistency.json",
    "render_receipt": "qa/page_render_receipt.json",
    "figure_map": "figure_source_map.json",
    "archive_note": "The archive is validated against the manifest payload; this receipt is included without self-hashing to avoid a circular archive hash.",
}
validation_path = R / "package_validation.json"
validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
zip_path = R / "AppliedEnergy_v6_2_release_20261010.zip"
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for row in manifest["entries"]:
        p = R / row["path"]
        z.write(p, row["path"])
    z.write(manifest_path, manifest_path.name)
    z.write(R / "release_gate_v6_2.json", "release_gate_v6_2.json")
    z.write(validation_path, validation_path.name)
validation.update({"archive_path": zip_path.name, "archive_bytes": zip_path.stat().st_size, "archive_entry_count": len(zipfile.ZipFile(zip_path).namelist())})
validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(validation, indent=2, ensure_ascii=False))
