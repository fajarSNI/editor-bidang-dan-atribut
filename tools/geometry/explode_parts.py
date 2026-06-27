from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsFeature


class ExplodeParts:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(None, 'Pecah Multipart (Explode)', 'Tidak ada layer yang aktif!')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Pecah Multipart (Explode)',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        selected = layer.selectedFeatures()
        if not selected:
            QMessageBox.warning(None, 'Pecah Multipart (Explode)',
                'Tidak ada bidang yang dipilih!\nPilih bidang multipart yang ingin Anda pecah.')
            return

        multipart_features = [f for f in selected if f.geometry().isMultipart()]
        if not multipart_features:
            QMessageBox.information(None, 'Pecah Multipart (Explode)',
                'Semua bidang yang dipilih sudah singlepart (tidak tergabung).')
            return

        total_new = 0
        exploded_count = 0

        for feature in multipart_features:
            geom = feature.geometry()
            parts = geom.asGeometryCollection()
            if len(parts) <= 1:
                continue
            layer.changeGeometry(feature.id(), parts[0])
            for part in parts[1:]:
                new_feature = QgsFeature(feature)
                new_feature.setGeometry(part)
                layer.addFeature(new_feature)
                total_new += 1
            exploded_count += 1

        QMessageBox.information(None, 'Pecah Multipart (Explode)',
            f'Selesai!\n\nBidang diproses : {exploded_count}\n'
            f'Bidang baru ditambahkan : {total_new}\n\nJangan lupa Simpan (Ctrl+S).')
