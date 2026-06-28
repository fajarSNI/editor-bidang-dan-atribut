from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QRadioButton,
    QGroupBox,
    QFormLayout,
    QSlider)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsProject,
    QgsDistanceArea,
    QgsPointXY,
    QgsWkbTypes)
from qgis.gui import QgsRubberBand, QgsMapTool
import math


class AnglePickerMapTool(QgsMapTool):
    def __init__(self, canvas, feature, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.feature = feature
        self.callback = callback
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, e):
        point = self.toMapCoordinates(e.pos())
        angle = self.find_closest_segment_angle(self.feature.geometry(), point)
        self.callback(angle)

    def find_closest_segment_angle(self, geom, point):
        min_dist = float('inf')
        best_angle = 0

        parts = geom.asGeometryCollection() if geom.isMultipart() else [geom]
        pt_geom = QgsGeometry.fromPointXY(point)

        for part in parts:
            if part.wkbType() in (QgsWkbTypes.Polygon, QgsWkbTypes.Polygon25D):
                rings = part.asPolygon()
            elif part.wkbType() in (QgsWkbTypes.MultiPolygon, QgsWkbTypes.MultiPolygon25D):
                # Only looking at first poly if multi, but actually parts are
                # polygons here
                continue  # Shouldn't happen since we do asGeometryCollection
            else:
                continue

            for ring in rings:
                for i in range(len(ring) - 1):
                    p1 = ring[i]
                    p2 = ring[i + 1]
                    line_geom = QgsGeometry.fromPolylineXY([p1, p2])
                    d = line_geom.distance(pt_geom)
                    if d < min_dist:
                        min_dist = d
                        dx = p2.x() - p1.x()
                        dy = p2.y() - p1.y()
                        best_angle = math.degrees(math.atan2(dy, dx))

        if best_angle < 0:
            best_angle += 360
        return best_angle


class PemecahanDialog(QDialog):
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Pemecahan Bidang')
        self.setMinimumWidth(450)
        self.fields = [f.name() for f in fields]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 1. Jumlah Bidang
        form_layout = QFormLayout()
        self.spin_jumlah = QSpinBox()
        self.spin_jumlah.setMinimum(2)
        self.spin_jumlah.setMaximum(100)
        self.spin_jumlah.setValue(2)
        form_layout.addRow('Jumlah bidang pecahan:', self.spin_jumlah)

        # 2. Arah (Slider & Spinbox & Map Tool)
        group_arah = QGroupBox('Arah Garis Pemisah (Derajat)')
        arah_layout = QVBoxLayout()

        # Spinbox and Button row
        row_sudut = QHBoxLayout()
        self.spin_sudut = QDoubleSpinBox()
        self.spin_sudut.setRange(0, 360)
        self.spin_sudut.setDecimals(1)
        self.spin_sudut.setSuffix(' °')
        self.spin_sudut.setValue(0.0)

        self.btn_pick_angle = QPushButton('📍 Ambil Sudut dari Peta')

        row_sudut.addWidget(self.spin_sudut)
        row_sudut.addWidget(self.btn_pick_angle)
        arah_layout.addLayout(row_sudut)

        # Slider
        self.slider_sudut = QSlider(Qt.Horizontal)
        self.slider_sudut.setRange(0, 3600)  # 0 to 360.0
        arah_layout.addWidget(self.slider_sudut)

        # Connect slider and spinbox
        self.slider_sudut.valueChanged.connect(
            lambda v: self.spin_sudut.setValue(v / 10.0))
        self.spin_sudut.valueChanged.connect(
            lambda v: self.slider_sudut.setValue(int(v * 10)))

        group_arah.setLayout(arah_layout)
        layout.addWidget(group_arah)

        # 3. Mode Rasio
        group_rasio = QGroupBox('Rasio Luasan')
        rasio_layout = QVBoxLayout()
        self.btn_sama_rata = QRadioButton('Sama Rata')
        self.btn_custom_rasio = QRadioButton(
            'Persentase Custom (pisahkan dengan koma)')
        self.btn_sama_rata.setChecked(True)

        self.input_rasio = QLineEdit()
        self.input_rasio.setPlaceholderText('Contoh: 40, 30, 30')
        self.input_rasio.setEnabled(False)
        self.btn_custom_rasio.toggled.connect(self.input_rasio.setEnabled)

        rasio_layout.addWidget(self.btn_sama_rata)
        rasio_layout.addWidget(self.btn_custom_rasio)
        rasio_layout.addWidget(self.input_rasio)
        group_rasio.setLayout(rasio_layout)
        layout.addWidget(group_rasio)

        # 4. Update Atribut
        group_attr = QGroupBox('Atribut Update Otomatis')
        attr_layout = QFormLayout()

        self.combo_luas = QComboBox()
        self.combo_luas.addItem('-- Tidak Diupdate --')
        self.combo_luas.addItems(self.fields)
        for i, f in enumerate(self.fields):
            if 'LUAS' in f.upper():
                self.combo_luas.setCurrentIndex(i + 1)
                break

        self.combo_nomor = QComboBox()
        self.combo_nomor.addItem('-- Tidak Diupdate --')
        self.combo_nomor.addItems(self.fields)
        for i, f in enumerate(self.fields):
            if f.upper() in ['NIB', 'NOMOR', 'NOP', 'ID']:
                self.combo_nomor.setCurrentIndex(i + 1)
                break

        attr_layout.addRow('Kolom Luas:', self.combo_luas)
        attr_layout.addRow('Kolom Nomor (Suffix):', self.combo_nomor)
        group_attr.setLayout(attr_layout)
        layout.addWidget(group_attr)

        layout.addLayout(form_layout)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton('Eksekusi Pecah')
        self.btn_cancel = QPushButton('Tutup')

        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

    def get_values(self):
        angle = self.spin_sudut.value()

        # Rasio
        ratios = []
        n = self.spin_jumlah.value()
        if self.btn_sama_rata.isChecked():
            ratios = [100.0 / n] * n
        else:
            try:
                parts = [float(x.strip())
                         for x in self.input_rasio.text().split(',')]
                if len(parts) != n:
                    raise ValueError(
                        f"Jumlah rasio ({
                            len(parts)}) tidak sama dengan jumlah bidang ({n})")
                total = sum(parts)
                if abs(total - 100.0) > 0.1:
                    raise ValueError("Total persentase harus 100%")
                ratios = parts
            except Exception as e:
                # We return None instead of showing warning immediately to
                # avoid popup spam during slider drag
                return None

        return {
            'jumlah': n,
            'sudut': angle,
            'rasio': ratios,
            'field_luas': self.combo_luas.currentText() if self.combo_luas.currentIndex() > 0 else None,
            'field_nomor': self.combo_nomor.currentText() if self.combo_nomor.currentIndex() > 0 else None
        }


class PemecahanBidang:
    def __init__(self, iface):
        self.iface = iface
        self.rubber_bands = []
        self.prev_map_tool = None
        self.dialog = None

    def clear_preview(self):
        for rb in self.rubber_bands:
            self.iface.mapCanvas().scene().removeItem(rb)
        self.rubber_bands.clear()

    def create_half_plane(self, cx, cy, angle_deg, distance, size=1000000):
        # Create a massive polygon on one side of the line
        rad_normal = math.radians(angle_deg + 90)
        rad_line = math.radians(angle_deg)

        px = cx + distance * math.cos(rad_normal)
        py = cy + distance * math.sin(rad_normal)

        dx = size * math.cos(rad_line)
        dy = size * math.sin(rad_line)

        nx = size * math.cos(rad_normal)
        ny = size * math.sin(rad_normal)

        p1 = QgsPointXY(px - dx, py - dy)
        p2 = QgsPointXY(px + dx, py + dy)
        p3 = QgsPointXY(px + dx + nx, py + dy + ny)
        p4 = QgsPointXY(px - dx + nx, py - dy + ny)

        return QgsGeometry.fromPolygonXY([[p1, p2, p3, p4, p1]])

    def split_polygon(self, geom, target_area, angle_deg, total_area):
        bbox = geom.boundingBox()
        cx, cy = bbox.center().x(), bbox.center().y()

        diag = math.sqrt(bbox.width()**2 + bbox.height()**2)
        low = -diag
        high = diag

        best_diff = float('inf')
        best_split = None
        best_rem = None

        for _ in range(50):
            mid = (low + high) / 2
            half_plane = self.create_half_plane(cx, cy, angle_deg, mid)

            part1 = geom.intersection(half_plane)
            area1 = part1.area()

            diff = area1 - target_area
            if abs(diff) < best_diff:
                best_diff = abs(diff)
                best_split = part1
                best_rem = geom.difference(half_plane)

            if diff < 0:
                high = mid
            else:
                low = mid

        return best_split, best_rem

    def run(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(
                None,
                'Pemecahan Bidang',
                'Tidak ada layer yang aktif!')
            return

        selected = layer.selectedFeatures()
        if len(selected) != 1:
            QMessageBox.warning(
                None,
                'Pemecahan Bidang',
                'Pilih tepat 1 bidang yang akan dipecah!')
            return

        feature = selected[0]
        geom = feature.geometry()

        if geom.wkbType() not in [
                QgsWkbTypes.Polygon,
                QgsWkbTypes.MultiPolygon,
                QgsWkbTypes.Polygon25D,
                QgsWkbTypes.MultiPolygon25D]:
            QMessageBox.warning(
                None,
                'Pemecahan Bidang',
                'Fitur yang dipilih harus berupa Poligon!')
            return

        self.dialog = PemecahanDialog(layer.fields(), self.iface.mainWindow())

        # Connect Live Preview
        def trigger_preview():
            self.do_preview(layer, feature)

        self.dialog.spin_jumlah.valueChanged.connect(trigger_preview)
        self.dialog.spin_sudut.valueChanged.connect(trigger_preview)
        self.dialog.input_rasio.textChanged.connect(trigger_preview)
        self.dialog.btn_sama_rata.toggled.connect(trigger_preview)
        self.dialog.btn_custom_rasio.toggled.connect(trigger_preview)

        self.dialog.btn_pick_angle.clicked.connect(
            lambda: self.start_pick_angle(feature))

        self.dialog.btn_ok.clicked.connect(
            lambda: self.do_execute(layer, feature))
        self.dialog.btn_cancel.clicked.connect(self.dialog.reject)
        self.dialog.finished.connect(self.cleanup)

        # Initial preview
        trigger_preview()
        self.dialog.show()

    def cleanup(self):
        self.clear_preview()
        if self.prev_map_tool:
            self.iface.mapCanvas().setMapTool(self.prev_map_tool)
            self.prev_map_tool = None

    def start_pick_angle(self, feature):
        self.dialog.hide()
        canvas = self.iface.mapCanvas()
        self.prev_map_tool = canvas.mapTool()

        def on_angle_picked(angle):
            self.dialog.spin_sudut.setValue(angle)
            canvas.setMapTool(self.prev_map_tool)
            self.prev_map_tool = None
            self.dialog.show()

        picker_tool = AnglePickerMapTool(canvas, feature, on_angle_picked)
        canvas.setMapTool(picker_tool)

    def calculate_splits(self, geom, values):
        angle = values['sudut']
        ratios = values['rasio']

        total_area = geom.area()
        parts = []
        current_geom = QgsGeometry(geom)

        for i in range(len(ratios) - 1):
            target_area = total_area * (ratios[i] / 100.0)
            split_part, remainder = self.split_polygon(
                current_geom, target_area, angle, total_area)
            if split_part and not split_part.isEmpty():
                parts.append(split_part)
            if remainder and not remainder.isEmpty():
                current_geom = remainder
            else:
                break

        if current_geom and not current_geom.isEmpty():
            parts.append(current_geom)

        return parts

    def do_preview(self, layer, feature):
        values = self.dialog.get_values()
        if not values:  # Validation failed (e.g. invalid ratio)
            self.clear_preview()
            return

        self.clear_preview()
        parts = self.calculate_splits(feature.geometry(), values)

        # Draw rubber bands
        for i, part in enumerate(parts):
            rb = QgsRubberBand(
                self.iface.mapCanvas(),
                QgsWkbTypes.PolygonGeometry)
            rb.setToGeometry(part, layer)
            color = QColor(
                255,
                0,
                0,
                100) if i % 2 == 0 else QColor(
                0,
                0,
                255,
                100)
            rb.setColor(color)
            rb.setWidth(2)
            self.rubber_bands.append(rb)

    def do_execute(self, layer, feature):
        values = self.dialog.get_values()
        if not values:
            QMessageBox.warning(
                self.dialog,
                'Error',
                'Silakan periksa input Rasio Luasan Anda.')
            return

        if not layer.isEditable():
            reply = QMessageBox.question(
                self.dialog, 'Pemecahan Bidang',
                'Layer tidak dalam mode edit. Aktifkan mode edit sekarang?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                layer.startEditing()
            else:
                return

        parts = self.calculate_splits(feature.geometry(), values)
        if not parts:
            QMessageBox.warning(self.dialog, 'Error', 'Gagal memecah bidang!')
            return

        self.clear_preview()

        da = QgsDistanceArea()
        da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())

        base_nomor = ""
        if values['field_nomor']:
            base_nomor = str(feature[values['field_nomor']]
                             ) if feature[values['field_nomor']] else ""

        new_features = []
        for i, part in enumerate(parts):
            new_feat = QgsFeature(layer.fields())
            for f in layer.fields():
                new_feat.setAttribute(f.name(), feature[f.name()])

            new_feat.setGeometry(part)

            if values['field_luas']:
                area = da.measureArea(part)
                new_feat.setAttribute(values['field_luas'], round(area, 2))

            if values['field_nomor']:
                suffix = chr(65 + (i % 26))
                new_feat.setAttribute(
                    values['field_nomor'],
                    f"{base_nomor}{suffix}")

            new_features.append(new_feat)

        layer.deleteFeature(feature.id())
        layer.addFeatures(new_features)

        self.dialog.accept()
        QMessageBox.information(
            None, 'Selesai', f'Bidang berhasil dipecah menjadi {
                len(parts)} bagian.\nJangan lupa Simpan (Ctrl+S).')
