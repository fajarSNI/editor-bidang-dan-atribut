from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QCheckBox, QDoubleSpinBox
)
from qgis.core import QgsDistanceArea, QgsProject


class HitungLuasDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hitung Luas Otomatis')
        self.setMinimumWidth(360)
        self._build_ui(fields)

    def _build_ui(self, fields):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Kolom target (untuk menyimpan nilai luas):'))
        self.field_combo = QComboBox()
        for f in fields:
            self.field_combo.addItem(f.name())
        # Default to LUAS_BUMI if exists
        for i, f in enumerate(fields):
            if 'LUAS' in f.name().upper():
                self.field_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.field_combo)

        layout.addWidget(QLabel('Pembulatan (jumlah desimal):'))
        self.round_spin = QDoubleSpinBox()
        self.round_spin.setDecimals(0)
        self.round_spin.setMinimum(0)
        self.round_spin.setMaximum(6)
        self.round_spin.setValue(2)
        layout.addWidget(self.round_spin)

        self.selected_only_chk = QCheckBox('Terapkan hanya pada bidang terpilih')
        self.selected_only_chk.setChecked(True)
        layout.addWidget(self.selected_only_chk)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Hitung & Perbarui')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def get_values(self):
        return (
            self.field_combo.currentText(),
            int(self.round_spin.value()),
            self.selected_only_chk.isChecked()
        )


class HitungLuas:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(None, 'Hitung Luas', 'Tidak ada layer yang aktif!')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Hitung Luas',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        dialog = HitungLuasDialog(layer.fields())
        if dialog.exec_() != QDialog.Accepted:
            return

        field_name, decimals, selected_only = dialog.get_values()
        idx = layer.fields().indexOf(field_name)
        if idx < 0:
            QMessageBox.warning(None, 'Hitung Luas', f'Kolom "{field_name}" tidak ditemukan!')
            return

        # Use QGIS distance area for accurate calculation
        da = QgsDistanceArea()
        da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())

        features = layer.selectedFeatures() if selected_only else layer.getFeatures()
        count = 0
        for feature in features:
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                area = da.measureArea(geom)
                area_rounded = round(area, decimals)
                layer.changeAttributeValue(feature.id(), idx, area_rounded)
                count += 1

        QMessageBox.information(None, 'Hitung Luas',
            f'Selesai! Memperbarui "{field_name}" pada {count} bidang.\n'
            f'Jangan lupa Simpan (Ctrl+S).')
