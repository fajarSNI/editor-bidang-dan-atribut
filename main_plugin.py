import os
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolBar
from qgis.PyQt.QtGui import QIcon

from .tools.geometry.explode_parts import ExplodeParts
from .tools.attributes.swap_attributes import SwapAttributes
from .tools.attributes.copy_attributes import CopyAttributes
from .tools.attributes.quick_field_fill import QuickFieldFill
from .tools.attributes.batch_rename import BatchRename
from .tools.attributes.auto_suffix_nomor import AutoSuffixNomor
from .tools.attributes.copy_coordinates import CopyCoordinates
from .tools.geometry.auto_close_polygon import AutoClosePolygon
from .tools.geometry.pemecahan_bidang import PemecahanBidang
from .tools.cadastral.hitung_luas import HitungLuas
from .tools.cadastral.validasi_highlight import ValidasiHighlight
from .tools.cadastral.export_excel import ExportExcel
from .tools.topology.topology_checker import TopologyChecker


def get_icon(name):
    path = os.path.join(os.path.dirname(__file__), 'icons', name)
    return QIcon(path) if os.path.exists(path) else QIcon()


class CadTools:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.toolbar = None
        self.menu = None

    def initGui(self):
        # Toolbar
        self.toolbar = QToolBar('Editor Bidang dan Atribut')
        self.toolbar.setObjectName('EditorBidangToolbar')
        self.iface.mainWindow().addToolBar(self.toolbar)

        # Main menu under Plugins
        self.menu = QMenu('Editor Bidang dan Atribut', self.iface.mainWindow())
        self.iface.pluginMenu().addMenu(self.menu)

        # Submenus
        menu_geom = self.menu.addMenu('Geometri')
        menu_attr = self.menu.addMenu('Atribut')
        menu_cad = self.menu.addMenu('Kadastral')
        menu_topo = self.menu.addMenu('Topologi')

        # ── GEOMETRI ──────────────────────────────────────────────────────
        self._add_tool(
            tool_class=ExplodeParts,
            label='Pecah Multipart (Explode)',
            icon='explode.png',
            tooltip='Memecah fitur multipart menjadi singlepart',
            menu=menu_geom,
            toolbar=True
        )
        self._add_tool(
            tool_class=AutoClosePolygon,
            label='Tutup Poligon Otomatis',
            icon='close_polygon.png',
            tooltip='Menutup poligon yang belum tertutup rapat',
            menu=menu_geom,
            toolbar=True
        )
        self._add_tool(
            tool_class=PemecahanBidang,
            label='Pemecahan Bidang',
            icon='pemecahan.svg',
            tooltip='Membagi/memecah bidang tanah dengan rasio dan arah tertentu',
            menu=menu_geom,
            toolbar=True)

        # ── ATRIBUT ────────────────────────────────────────────────────
        self._add_tool(
            tool_class=SwapAttributes,
            label='Tukar Atribut (Swap)',
            icon='swap.svg',
            tooltip='Menukar atribut antara tepat 2 bidang yang dipilih',
            menu=menu_attr,
            toolbar=True
        )
        self._add_tool(
            tool_class=CopyAttributes,
            label='Salin Atribut ke Pilihan',
            icon='copy_attr.png',
            tooltip='Menyalin atribut dari 1 bidang sumber ke semua bidang yang dipilih',
            menu=menu_attr,
            toolbar=True)
        self._add_tool(
            tool_class=QuickFieldFill,
            label='Isi Kolom Cepat',
            icon='quick_fill.svg',
            tooltip='Mengisi banyak kolom sekaligus untuk fitur yang dipilih',
            menu=menu_attr,
            toolbar=True
        )
        self._add_tool(
            tool_class=BatchRename,
            label='Ubah Nama Nilai Massal',
            icon='batch_rename.png',
            tooltip='Mencari dan mengganti nilai dalam kolom di seluruh layer',
            menu=menu_attr,
            toolbar=False
        )
        self._add_tool(
            tool_class=AutoSuffixNomor,
            label='Penomoran Akhiran Otomatis',
            icon='suffix.svg',
            tooltip='Memberikan huruf akhiran otomatis ke nomor bidang hasil pecahan (001 → 001A, 001B)',
            menu=menu_attr,
            toolbar=True)
        self._add_tool(
            tool_class=CopyCoordinates,
            label='Salin Koordinat Geometri',
            icon='copy_coords.png',
            tooltip='Menyalin titik tengah koordinat bidang ke clipboard',
            menu=menu_attr,
            toolbar=False
        )

        # ── KADASTRAL ─────────────────────────────────────────────────────
        self._add_tool(
            tool_class=HitungLuas,
            label='Hitung Luas Otomatis',
            icon='hitung_luas.svg',
            tooltip='Memperbarui kolom luas secara otomatis',
            menu=menu_cad,
            toolbar=True
        )
        self._add_tool(
            tool_class=ValidasiHighlight,
            label='Validasi & Sorot Kolom Kosong',
            icon='validasi.svg',
            tooltip='Memeriksa kolom wajib dan menyorot bidang yang kosong (NULL)',
            menu=menu_cad,
            toolbar=True)
        self._add_tool(
            tool_class=ExportExcel,
            label='Ekspor Pilihan ke Excel',
            icon='export_excel.png',
            tooltip='Mengekspor atribut dari bidang yang dipilih ke file Excel (.xlsx)',
            menu=menu_cad,
            toolbar=False)

        # ── TOPOLOGI ──────────────────────────────────────────────────────
        self._add_tool(
            tool_class=TopologyChecker,
            label='Cek Topologi + Perbaikan Otomatis',
            icon='topology.svg',
            tooltip='Memeriksa dan memperbaiki kesalahan topologi (tumpang tindih, celah, potong silang)',
            menu=menu_topo,
            toolbar=True)

    def _add_tool(self, tool_class, label, icon, tooltip, menu, toolbar=False):
        tool_instance = tool_class(self.iface)
        action = QAction(get_icon(icon), label, self.iface.mainWindow())
        action.setToolTip(tooltip)
        action.triggered.connect(tool_instance.run)
        menu.addAction(action)
        if toolbar:
            self.toolbar.addAction(action)
        self.actions.append((action, tool_instance))

    def unload(self):
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        if self.toolbar:
            self.toolbar.deleteLater()
        self.actions.clear()
