from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsGeometry, QgsPointXY


class AutoClosePolygon:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(None, 'Tutup Poligon Otomatis', 'Tidak ada layer yang aktif!')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Tutup Poligon Otomatis',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        selected = layer.selectedFeatures()
        features = selected if selected else list(layer.getFeatures())

        if not features:
            QMessageBox.warning(None, 'Tutup Poligon Otomatis', 'Tidak ada bidang yang ditemukan!')
            return

        fixed_count = 0
        for feature in features:
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            # makeValid closes unclosed rings and fixes other issues
            valid_geom = geom.makeValid()
            if valid_geom and valid_geom != geom:
                layer.changeGeometry(feature.id(), valid_geom)
                fixed_count += 1

        scope = f'{len(selected)} bidang terpilih' if selected else 'semua bidang'
        QMessageBox.information(None, 'Tutup Poligon Otomatis',
            f'Selesai! Memeriksa {scope}.\n'
            f'Diperbaiki/ditutup: {fixed_count} poligon.\n'
            f'Jangan lupa Simpan (Ctrl+S).')
