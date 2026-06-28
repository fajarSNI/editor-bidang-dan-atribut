from qgis.PyQt.QtWidgets import QMessageBox


class SwapAttributes:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Tukar Atribut (Swap)',
                'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if len(selected) != 2:
            QMessageBox.warning(
                None,
                'Tukar Atribut (Swap)',
                f'Pilih tepat 2 bidang.\nSaat ini terpilih: {
                    len(selected)}')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Tukar Atribut (Swap)',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        feat_a, feat_b = selected[0], selected[1]
        fields = layer.fields()

        # Collect attributes from both features
        attrs_a = {field.name(): feat_a[field.name()] for field in fields}
        attrs_b = {field.name(): feat_b[field.name()] for field in fields}

        # Swap — write B's attrs to A, and A's attrs to B
        for field in fields:
            name = field.name()
            idx = layer.fields().indexOf(name)
            layer.changeAttributeValue(feat_a.id(), idx, attrs_b[name])
            layer.changeAttributeValue(feat_b.id(), idx, attrs_a[name])

        QMessageBox.information(
            None,
            'Tukar Atribut (Swap)',
            'Atribut berhasil ditukar!\nJangan lupa Simpan (Ctrl+S).')
