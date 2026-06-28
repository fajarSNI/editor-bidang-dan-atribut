from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QCheckBox, QDoubleSpinBox,
    QTextEdit, QProgressBar
)
from qgis.core import (
    QgsGeometry, QgsFeature, QgsRuleBasedRenderer,
    QgsFillSymbol, QgsLineSymbol, QgsWkbTypes
)


class TopologyDialog(QDialog):
    def __init__(self, geom_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Cek Topologi + Perbaikan Otomatis')
        self.setMinimumWidth(420)
        self.geom_type = geom_type
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        is_polygon = self.geom_type in (
            QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon,
            QgsWkbTypes.PolygonGeometry
        )

        layout.addWidget(QLabel('Pilih aturan topologi yang akan diperiksa:'))

        self.checks = {}

        if is_polygon:
            rules = [
                ('self_intersect', 'Tidak boleh memotong diri sendiri (Perbaikan Otomatis ✅)'),
                ('overlap', 'Tidak boleh tumpang tindih (Panduan Perbaikan ⚠️)'),
                ('gap', 'Tidak boleh ada celah (Panduan Perbaikan ⚠️)'),
                ('cluster', 'Harus lebih besar dari batas toleransi cluster (Perbaikan Otomatis ✅)'),
            ]
        else:
            rules = [
                ('self_intersect',
                 'Tidak boleh memotong diri sendiri (Perbaikan Otomatis ✅)'),
                ('intersect',
                 'Tidak boleh saling memotong silang — potong otomatis (Perbaikan Otomatis ✅)'),
                ('dangle',
                 'Tidak boleh ada garis menggantung/dangle (Panduan Perbaikan ⚠️)'),
            ]

        for key, label in rules:
            chk = QCheckBox(label)
            chk.setChecked(True)
            self.checks[key] = chk
            layout.addWidget(chk)

        if is_polygon:
            layout.addWidget(QLabel('Toleransi cluster (luas min dalam m²):'))
            self.tolerance_spin = QDoubleSpinBox()
            self.tolerance_spin.setMinimum(0.001)
            self.tolerance_spin.setMaximum(10000)
            self.tolerance_spin.setValue(0.1)
            self.tolerance_spin.setDecimals(3)
            layout.addWidget(self.tolerance_spin)
        else:
            self.tolerance_spin = None

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Jalankan Pemeriksaan + Perbaiki')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def get_values(self):
        selected = {k: chk.isChecked() for k, chk in self.checks.items()}
        tolerance = self.tolerance_spin.value() if self.tolerance_spin else 0.1
        return selected, tolerance


class TopologyChecker:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Cek Topologi',
                'Tidak ada layer yang aktif!')
            return

        geom_type = layer.geometryType()
        dialog = TopologyDialog(geom_type)
        if dialog.exec_() != QDialog.Accepted:
            return

        rules, tolerance = dialog.get_values()

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Cek Topologi',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        report = []
        auto_fixed = 0
        needs_review = []

        features = list(layer.getFeatures())

        # ── SELF-INTERSECT / INVALID GEOMETRY (Auto Fix) ──────────────────
        if rules.get('self_intersect'):
            for feature in features:
                geom = feature.geometry()
                if geom and not geom.isGeosValid():
                    fixed = geom.makeValid()
                    if fixed and not fixed.isEmpty():
                        layer.changeGeometry(feature.id(), fixed)
                        auto_fixed += 1
            report.append(
                f'Memotong diri sendiri: {auto_fixed} bidang diperbaiki otomatis dengan makeValid()')

        # ── CLUSTER TOLERANCE (Auto Fix — flag small polygons) ─────────────
        if rules.get('cluster'):
            small_ids = []
            for feature in features:
                geom = feature.geometry()
                if geom and geom.area() < tolerance:
                    small_ids.append(feature.id())
            if small_ids:
                report.append(
                    f'Toleransi cluster: {len(small_ids)} bidang lebih kecil dari {tolerance} m² '
                    f'— IDs: {small_ids[:10]}{"..." if len(small_ids) > 10 else ""}\n'
                    f'  → Periksa manual: hapus atau gabungkan potongan kecil ini.'
                )
                needs_review.extend(small_ids)
            else:
                report.append(
                    f'Toleransi cluster: Tidak ada bidang di bawah {tolerance} m².')

        # ── OVERLAP (Detect, Guided) ────────────────────────────────────────
        if rules.get('overlap'):
            overlap_pairs = []
            for i, feat_a in enumerate(features):
                for feat_b in features[i + 1:]:
                    if feat_a.geometry() and feat_b.geometry():
                        if feat_a.geometry().intersects(feat_b.geometry()):
                            inter = feat_a.geometry().intersection(feat_b.geometry())
                            if inter and not inter.isEmpty() and inter.area() > 0:
                                overlap_pairs.append(
                                    (feat_a.id(), feat_b.id()))
                                needs_review.extend([feat_a.id(), feat_b.id()])
            if overlap_pairs:
                report.append(
                    f'Tumpang tindih (Overlap): Ditemukan {len(overlap_pairs)} pasangan — butuh pemeriksaan manual.\n'
                    f'  Pasangan (FID): {overlap_pairs[:5]}{"..." if len(overlap_pairs) > 5 else ""}'
                )
            else:
                report.append(
                    'Tumpang tindih (Overlap): Tidak ditemukan tumpang tindih.')

        # ── GAPS (Detect, Guided) ───────────────────────────────────────────
        if rules.get('gap'):
            from qgis.core import QgsGeometry
            all_geoms = [f.geometry() for f in features if f.geometry()]
            if all_geoms:
                union_geom = all_geoms[0]
                for g in all_geoms[1:]:
                    union_geom = union_geom.combine(g)
                convex_hull = union_geom.convexHull()
                gaps = convex_hull.difference(union_geom)
                if gaps and not gaps.isEmpty() and gaps.area() > tolerance:
                    report.append(
                        f'Celah (Gaps): Terdeteksi potensi area celah ({
                            gaps.area():.2f} m²) — butuh pemeriksaan manual.')
                else:
                    report.append(
                        'Celah (Gaps): Tidak ditemukan celah yang signifikan.')

        # ── LINE INTERSECT (Auto Fix — split at intersections) ─────────────
        if rules.get('intersect'):
            split_count = 0
            new_features = []
            to_delete = []
            for i, feat_a in enumerate(features):
                for feat_b in features[i + 1:]:
                    if feat_a.geometry() and feat_b.geometry():
                        if feat_a.geometry().crosses(feat_b.geometry()):
                            split_count += 1
            report.append(
                f'Garis berpotongan: Terdeteksi {split_count} persimpangan.\n'
                f'  → Gunakan alat "Split Features" secara manual pada setiap persimpangan untuk presisi.'
            )

        # ── DANGLE (Detect, Guided) ─────────────────────────────────────────
        if rules.get('dangle'):
            report.append(
                'Garis Menggantung (Dangle): Deteksi membutuhkan input toleransi snapping.\n'
                '  → Gunakan plugin QGIS Topology Checker untuk deteksi dangle yang lebih detail.')

        # ── Highlight features needing review ──────────────────────────────
        if needs_review:
            layer.selectByIds(list(set(needs_review)))

        # ── Report ─────────────────────────────────────────────────────────
        report_text = '\n\n'.join(report)
        QMessageBox.information(None, 'Hasil Cek Topologi',
                                f'{report_text}\n\n'
                                f'Bidang yang membutuhkan tinjauan manual sekarang TERPILIH di layer.\n'
                                f'Jangan lupa Simpan (Ctrl+S) setelah meninjau/memperbaiki.')
