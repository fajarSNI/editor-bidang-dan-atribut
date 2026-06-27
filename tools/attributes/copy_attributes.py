from qgis.PyQt.QtWidgets import QMessageBox, QInputDialog


class CopyAttributes:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(None, 'Salin Atribut ke Pilihan', 'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if len(selected) < 2:
            QMessageBox.warning(None, 'Salin Atribut ke Pilihan',
                'Pilih minimal 2 bidang.\n'
                '(1 sumber + 1 atau lebih target)')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Salin Atribut ke Pilihan',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        # Let user pick which feature is the source
        options = []
        for f in selected:
            # Build a short label from common identifier fields
            for candidate in ['NOMOR', 'NOP', 'Id', 'id', 'FID']:
                val = f[candidate] if candidate in [fld.name() for fld in layer.fields()] else None
                if val is not None:
                    options.append(f'FID {f.id()} — {candidate}: {val}')
                    break
            else:
                options.append(f'FID {f.id()}')

        source_label, ok = QInputDialog.getItem(
            None, 'Salin Atribut ke Pilihan',
            'Pilih bidang SUMBER (atribut akan disalin DARI bidang ini):',
            options, 0, False
        )
        if not ok:
            return

        source_index = options.index(source_label)
        source_feat = selected[source_index]
        target_feats = [f for i, f in enumerate(selected) if i != source_index]

        fields = layer.fields()
        source_attrs = {field.name(): source_feat[field.name()] for field in fields}

        for target in target_feats:
            for field in fields:
                idx = layer.fields().indexOf(field.name())
                layer.changeAttributeValue(target.id(), idx, source_attrs[field.name()])

        QMessageBox.information(None, 'Salin Atribut ke Pilihan',
            f'Selesai! Atribut disalin ke {len(target_feats)} bidang.\n'
            f'Jangan lupa Simpan (Ctrl+S).')
