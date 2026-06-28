from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QClipboard
from qgis.PyQt.QtWidgets import QApplication


class CopyCoordinates:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Salin Koordinat',
                'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if not selected:
            QMessageBox.warning(
                None,
                'Salin Koordinat',
                'Tidak ada bidang yang dipilih! Pilih bidang terlebih dahulu.')
            return

        lines = []
        for feature in selected:
            centroid = feature.geometry().centroid().asPoint()
            # Try to get a label from common ID fields
            label = f'FID {feature.id()}'
            for candidate in ['NOMOR', 'NOP', 'Id', 'id']:
                if candidate in [f.name() for f in layer.fields()]:
                    val = feature[candidate]
                    if val:
                        label = f'{candidate}: {val}'
                        break
            lines.append(
                f'{label}\tX: {
                    centroid.x():.6f}\tY: {
                    centroid.y():.6f}')

        text = '\n'.join(lines)
        QApplication.clipboard().setText(text)

        QMessageBox.information(
            None, 'Salin Koordinat', f'Menyalin koordinat dari {
                len(selected)} bidang ke clipboard.\n\n{text}')
