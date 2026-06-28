from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QWidget, QMessageBox
)
from qgis.PyQt.QtCore import Qt


class QuickFieldFillDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Isi Kolom Cepat')
        self.setMinimumWidth(400)
        self.fields = fields
        self.inputs = {}
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(
            'Isi kolom yang ingin Anda perbarui.\nBiarkan kosong untuk melewatkan kolom tersebut.'
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QVBoxLayout(container)

        for field in self.fields:
            row = QHBoxLayout()
            label = QLabel(field.name())
            label.setFixedWidth(160)
            line = QLineEdit()
            line.setPlaceholderText('(biarkan kosong untuk lewat)')
            self.inputs[field.name()] = line
            row.addWidget(label)
            row.addWidget(line)
            form_layout.addLayout(row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Perbarui Pilihan')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        main_layout.addLayout(btn_row)

    def get_values(self):
        """Return dict of {field_name: value} for non-empty inputs only."""
        return {
            name: widget.text()
            for name, widget in self.inputs.items()
            if widget.text().strip() != ''
        }


class QuickFieldFill:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(
                None,
                'Isi Kolom Cepat',
                'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if not selected:
            QMessageBox.warning(
                None,
                'Isi Kolom Cepat',
                'Tidak ada bidang yang dipilih! Pilih bidang yang ingin Anda perbarui.')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                None, 'Isi Kolom Cepat',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        dialog = QuickFieldFillDialog(layer.fields())
        if dialog.exec_() != QDialog.Accepted:
            return

        values = dialog.get_values()
        if not values:
            QMessageBox.information(
                None,
                'Isi Kolom Cepat',
                'Tidak ada kolom yang diisi, tidak ada yang diperbarui.')
            return

        fields = layer.fields()
        for feature in selected:
            for field_name, value in values.items():
                idx = fields.indexOf(field_name)
                if idx >= 0:
                    layer.changeAttributeValue(feature.id(), idx, value)

        QMessageBox.information(
            None, 'Isi Kolom Cepat', f'Selesai! Memperbarui {
                len(values)} kolom untuk {
                len(selected)} bidang.\n' f'Jangan lupa Simpan (Ctrl+S).')
