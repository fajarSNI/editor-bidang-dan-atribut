from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QCheckBox
)


class BatchRenameDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Ubah Nama Nilai Massal')
        self.setMinimumWidth(380)
        self._build_ui(fields)

    def _build_ui(self, fields):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Pencarian pada kolom:'))
        self.field_combo = QComboBox()
        for f in fields:
            self.field_combo.addItem(f.name())
        layout.addWidget(self.field_combo)

        layout.addWidget(QLabel('Cari (Find):'))
        self.find_input = QLineEdit()
        layout.addWidget(self.find_input)

        layout.addWidget(QLabel('Ganti dengan (Replace):'))
        self.replace_input = QLineEdit()
        layout.addWidget(self.replace_input)

        self.selected_only_chk = QCheckBox(
            'Terapkan hanya pada bidang terpilih')
        layout.addWidget(self.selected_only_chk)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Ganti Semua')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def get_values(self):
        return (
            self.field_combo.currentText(),
            self.find_input.text(),
            self.replace_input.text(),
            self.selected_only_chk.isChecked()
        )


class BatchRename:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Ubah Nama Massal',
                'Tidak ada layer yang aktif!')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Ubah Nama Massal',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        dialog = BatchRenameDialog(layer.fields())
        if dialog.exec_() != QDialog.Accepted:
            return

        field_name, find_val, replace_val, selected_only = dialog.get_values()
        if not find_val:
            QMessageBox.warning(
                None,
                'Ubah Nama Massal',
                'Nilai pencarian (Cari) tidak boleh kosong!')
            return

        fields = layer.fields()
        idx = fields.indexOf(field_name)
        if idx < 0:
            QMessageBox.warning(
                None,
                'Ubah Nama Massal',
                f'Kolom "{field_name}" tidak ditemukan!')
            return

        features = layer.selectedFeatures() if selected_only else layer.getFeatures()
        count = 0
        for feature in features:
            current_val = str(
                feature[field_name]) if feature[field_name] else ''
            if find_val in current_val:
                new_val = current_val.replace(find_val, replace_val)
                layer.changeAttributeValue(feature.id(), idx, new_val)
                count += 1

        QMessageBox.information(None, 'Ubah Nama Massal',
                                f'Selesai! Mengganti "{find_val}" → "{replace_val}" pada {count} bidang.\n'
                                f'Jangan lupa Simpan (Ctrl+S).')
