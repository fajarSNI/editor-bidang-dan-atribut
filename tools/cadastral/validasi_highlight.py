from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QScrollArea, QWidget, QCheckBox
)
from qgis.core import QgsRuleBasedRenderer, QgsFillSymbol, QgsExpression
import re


class ValidasiDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Validasi & Sorot Kolom Kosong')
        self.setMinimumWidth(380)
        self.setMinimumHeight(400)
        self.fields = fields
        self.checks = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            'Pilih kolom wajib yang ingin diperiksa.\n'
            'Bidang dengan nilai kosong (NULL) pada kolom wajib akan disorot MERAH.\n'
            'Bidang yang semua kolom wajibnya terisi akan disorot HIJAU.'
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QVBoxLayout(container)

        for field in self.fields:
            chk = QCheckBox(field.name())
            self.checks[field.name()] = chk
            form_layout.addWidget(chk)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton('Jalankan Validasi')
        btn_cancel = QPushButton('Batal')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def get_selected_fields(self):
        return [name for name, chk in self.checks.items() if chk.isChecked()]


class ValidasiHighlight:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()

        if not layer:
            QMessageBox.warning(None, 'Validasi Bidang', 'Tidak ada layer yang aktif!')
            return

        dialog = ValidasiDialog(layer.fields())
        if dialog.exec_() != QDialog.Accepted:
            return

        mandatory_fields = dialog.get_selected_fields()
        if not mandatory_fields:
            QMessageBox.warning(None, 'Validasi Bidang',
                'Tidak ada kolom yang dipilih! Centang minimal satu kolom.')
            return

        # Build null expression: feature is invalid if ANY mandatory field is NULL or empty
        null_conditions = []
        for field in mandatory_fields:
            null_conditions.append(f'"{field}" IS NULL OR "{field}" = \'\'')
        null_expr = ' OR '.join(null_conditions)

        # Build rule-based renderer
        renderer = QgsRuleBasedRenderer(QgsFillSymbol())
        root_rule = renderer.rootRule()

        # Remove default rule
        for child in root_rule.children():
            root_rule.removeChild(child)

        # RED rule — has null in mandatory fields
        red_symbol = QgsFillSymbol.createSimple({
            'color': '220,50,50,200',
            'outline_color': '180,0,0,255',
            'outline_width': '0.5'
        })
        red_rule = QgsRuleBasedRenderer.Rule(red_symbol)
        red_rule.setLabel('Kolom wajib kosong')
        red_rule.setFilterExpression(null_expr)
        root_rule.appendChild(red_rule)

        # GREEN rule — all mandatory fields filled
        green_symbol = QgsFillSymbol.createSimple({
            'color': '50,180,50,200',
            'outline_color': '0,120,0,255',
            'outline_width': '0.5'
        })
        green_rule = QgsRuleBasedRenderer.Rule(green_symbol)
        green_rule.setLabel('Lengkap')
        green_rule.setFilterExpression(f'NOT ({null_expr})')
        root_rule.appendChild(green_rule)

        layer.setRenderer(renderer)
        layer.triggerRepaint()

        # Count stats
        null_count = sum(
            1 for f in layer.getFeatures()
            if any(f[field] is None or str(f[field]).strip() == '' for field in mandatory_fields)
        )
        total = layer.featureCount()
        complete = total - null_count

        QMessageBox.information(None, 'Validasi Bidang',
            f'Validasi selesai!\n\n'
            f'Total bidang    : {total}\n'
            f'Lengkap (hijau) : {complete}\n'
            f'Kosong (merah)  : {null_count}\n\n'
            f'Kolom dicek: {", ".join(mandatory_fields)}')
