from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QMessageBox
)


def generate_suffix(n):
    """Generate Excel-style suffix: A, B, ..., Z, AA, AB, ..."""
    result = ''
    while n >= 0:
        result = chr(65 + (n % 26)) + result
        n = n // 26 - 1
    return result


class AutoSuffixDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Penomoran Akhiran Otomatis')
        self.setMinimumWidth(380)
        self._build_ui(fields)

    def _build_ui(self, fields):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Kolom yang diperbarui:'))
        self.field_combo = QComboBox()
        for f in fields:
            self.field_combo.addItem(f.name())
        # Default to NOMOR if exists
        for i, f in enumerate(fields):
            if f.name().upper() == 'NOMOR':
                self.field_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.field_combo)

        layout.addWidget(QLabel('Nomor dasar (misal 001):'))
        self.base_input = QLineEdit()
        self.base_input.setPlaceholderText('misal 001')
        layout.addWidget(self.base_input)

        layout.addWidget(QLabel(
            'Bidang yang dipilih akan diberi nomor:\n'
            '  001A, 001B, 001C, ... 001Z, 001AA, 001AB, ...\n'
            'sesuai urutan dalam tabel atribut.'
        ))

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Terapkan')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def get_values(self):
        return self.field_combo.currentText(), self.base_input.text().strip()


class AutoSuffixNomor:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Penomoran Akhiran',
                'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if not selected:
            QMessageBox.warning(
                None,
                'Penomoran Akhiran',
                'Tidak ada bidang yang dipilih! Pilih bidang hasil pemecahan.')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Penomoran Akhiran',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        dialog = AutoSuffixDialog(layer.fields())
        if dialog.exec_() != QDialog.Accepted:
            return

        field_name, base_number = dialog.get_values()
        if not base_number:
            QMessageBox.warning(
                None,
                'Penomoran Akhiran',
                'Nomor dasar tidak boleh kosong!')
            return

        fields = layer.fields()
        idx = fields.indexOf(field_name)
        if idx < 0:
            QMessageBox.warning(
                None,
                'Penomoran Akhiran',
                f'Kolom "{field_name}" tidak ditemukan!')
            return

        for i, feature in enumerate(selected):
            suffix = generate_suffix(i)
            new_value = f'{base_number}{suffix}'
            layer.changeAttributeValue(feature.id(), idx, new_value)

        QMessageBox.information(
            None, 'Penomoran Akhiran', f'Selesai! Menambahkan akhiran ke {
                len(selected)} bidang.\n' f'Contoh: {base_number}A → {base_number}{
                generate_suffix(
                    len(selected) - 1)}\n' f'Jangan lupa Simpan (Ctrl+S).')
