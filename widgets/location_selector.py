"""
地区级联选择器 - 省→市→区三级联动
数据来源: data/qweather_china.json (和风天气 Location ID)
"""

import json
from pathlib import Path

from PyQt5.QtWidgets import QComboBox, QListView, QWidget, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPalette, QColor

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "qweather_china.json"
_data_cache = None


def _load_location_data():
    global _data_cache
    if _data_cache is not None:
        return _data_cache
    with open(_DATA_FILE, encoding="utf-8") as f:
        _data_cache = json.load(f)
    return _data_cache


def lookup_city_id_by_name(city_name, region=""):
    """根据城市名和省份名查找对应的 QWeather Location ID

    Args:
        city_name: 城市名（如"武汉"、"上海市"）
        region: 省份名（如"湖北省"），用于精确匹配

    Returns:
        str: QWeather Location ID（如 "101020100"）
        找不到返回 None
    """
    if not city_name:
        return None

    data = _load_location_data()
    city_clean = city_name.replace("市", "").replace("省", "").replace("区", "")

    for prov in data:
        prov_name = prov.get("name", "").replace("市", "").replace("省", "")
        if region and prov_name != region.replace("省", ""):
            continue

        for city in prov.get("cities", []):
            city_n = city.get("name", "").replace("市", "")
            if city_n == city_clean or city_clean in city_n:
                districts = city.get("districts", [])
                if districts:
                    return str(districts[0].get("id"))

        if not region:
            for city in prov.get("cities", []):
                city_n = city.get("name", "").replace("市", "")
                if city_n == city_clean or city_clean in city_n:
                    districts = city.get("districts", [])
                    if districts:
                        return str(districts[0].get("id"))

    return None


class LocationSelector(QWidget):
    location_changed = pyqtSignal(str)

    def __init__(self, current_id="101010100", parent=None):
        super().__init__(parent)
        self._data = _load_location_data()
        self._updating = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.province_combo = QComboBox()
        self.city_combo = QComboBox()
        self.district_combo = QComboBox()

        for combo in (self.province_combo, self.city_combo, self.district_combo):
            view = QListView()
            view.setStyleSheet("color: #333333; background-color: #ffffff;")
            combo.setView(view)
            combo.setMinimumWidth(80)
            combo.setMaximumWidth(100)
            pal = combo.palette()
            pal.setColor(QPalette.Text, QColor("#1f2937"))
            pal.setColor(QPalette.ButtonText, QColor("#1f2937"))
            pal.setColor(QPalette.WindowText, QColor("#1f2937"))
            combo.setPalette(pal)
            layout.addWidget(combo, 3)

        layout.addStretch(2)

        self.province_combo.currentIndexChanged.connect(self._on_province_changed)
        self.city_combo.currentIndexChanged.connect(self._on_city_changed)
        self.district_combo.currentIndexChanged.connect(self._on_district_changed)

        self._populate_provinces()
        if current_id:
            self._select_by_id(current_id)

    def _populate_provinces(self):
        self.province_combo.blockSignals(True)
        self.province_combo.clear()
        for prov in self._data:
            self.province_combo.addItem(prov["name"])
        self.province_combo.blockSignals(False)
        if self._data:
            self._on_province_changed(0)

    def _on_province_changed(self, index):
        if index < 0 or self._updating:
            return
        if index >= len(self._data):
            return
        prov = self._data[index]
        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        for city in prov["cities"]:
            self.city_combo.addItem(city["name"])
        self.city_combo.blockSignals(False)
        if prov["cities"]:
            self._on_city_changed(0)

    def _on_city_changed(self, index):
        if index < 0 or self._updating:
            return
        prov_idx = self.province_combo.currentIndex()
        if prov_idx < 0 or prov_idx >= len(self._data):
            return
        prov = self._data[prov_idx]
        if index >= len(prov["cities"]):
            return
        city = prov["cities"][index]
        self.district_combo.blockSignals(True)
        self.district_combo.clear()
        for dist in city["districts"]:
            self.district_combo.addItem(dist["name"], dist["id"])
        self.district_combo.blockSignals(False)
        if city["districts"]:
            self._on_district_changed(0)

    def _on_district_changed(self, index):
        if index < 0:
            return
        loc_id = self.district_combo.itemData(index)
        if loc_id:
            self.location_changed.emit(str(loc_id))

    def _select_by_id(self, target_id):
        self._updating = True
        target = str(target_id)
        for pi, prov in enumerate(self._data):
            for ci, city in enumerate(prov["cities"]):
                for di, dist in enumerate(city["districts"]):
                    if dist["id"] == target:
                        self.province_combo.blockSignals(True)
                        self.province_combo.setCurrentIndex(pi)
                        self.province_combo.blockSignals(False)

                        self.city_combo.blockSignals(True)
                        self.city_combo.clear()
                        for c in prov["cities"]:
                            self.city_combo.addItem(c["name"])
                        self.city_combo.setCurrentIndex(ci)
                        self.city_combo.blockSignals(False)

                        self.district_combo.blockSignals(True)
                        self.district_combo.clear()
                        for d in city["districts"]:
                            self.district_combo.addItem(d["name"], d["id"])
                        self.district_combo.setCurrentIndex(di)
                        self.district_combo.blockSignals(False)

                        self._updating = False
                        return
        self._updating = False

    def set_location_by_id(self, location_id):
        self._select_by_id(location_id)

    def current_location_id(self):
        idx = self.district_combo.currentIndex()
        if idx >= 0:
            data = self.district_combo.itemData(idx)
            if data:
                return str(data)
        return "101010100"
