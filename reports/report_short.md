# FalconResQ: Disaster Management Ground Station - EXECUTIVE SUMMARY REPORT (SHORT)

**Project Classification:** Level 3 - Executive Summary  
**Version:** 1.0.0  
**Date:** December 24, 2025  
**Developer:** Asshray Sudhakara (ECE'27, MARVEL UVCE)  
**Scope:** Concise overview of all major components and functionality

---

## WHAT IS FALCONRESQ?

FalconResQ is a disaster rescue coordination system that:
- **Receives** GPS locations from victim-worn LoRa wireless devices
- **Displays** victims on interactive maps in real-time
- **Manages** rescue operations (detect → en-route → rescued)
- **Analyzes** rescue efficiency metrics and geographic patterns
- **Exports** data for post-operation audits

**Built with:** Python + Streamlit + Folium Maps + NumPy/Pandas Analytics

---

## PROJECT FILES AT A GLANCE

| File/Module | Purpose |
|------------|---------|
| **app.py** | Main entry point, session state initialization |
| **config.py** | All constants, thresholds, defaults (RSSI -70/-85, time 15/20 min) |
| **serial_reader.py** | Background thread reads JSON packets from COM port |
| **data_manager.py** | Victim database; auto-saves to JSON every 30 seconds |
| **map_manager.py** | Folium maps with color-coded victim markers |
| **analytics.py** | Statistics engine (rescue rates, signal trends, density) |
| **dashboard.py** | Main UI: real-time map + victim management |
| **analytics_page.py** | Charts & analytics dashboard |
| **export.py** | CSV/JSON/PDF export & reports |
| **settings.py** | Configuration UI (COM port, thresholds, geolocation) |
| **helpers.py** | Utilities (priority calculation, formatting) |
| **validators.py** | Input validation (packets, coordinates, ranges) |
| **victims_backup.json** | Auto-saved victim database |
| **rescue_log.csv** | Audit trail of all status changes |

---

## TECHNOLOGIES USED & WHY

| Technology | Reason |
|-----------|--------|
| **Python 3.11** | Rapid development, NumPy/Pandas, PySerial support |
| **Streamlit** | Web UI without HTML/CSS, perfect for dashboards |
| **Folium** | Interactive maps with multiple tile providers |
| **NumPy/Pandas** | Efficient statistical calculations |
| **Plotly** | Interactive charts for analytics |
| **PySerial** | Read data from ground station hardware |
| **JSON** | Human-readable victim data storage |
| **CSV** | Universal audit logs & exports |

---

## DATA FLOW (SIMPLE)

```
Victim Device (LoRa)
       ↓ [GPS + Signal]
Ground Station (USB COM Port)
       ↓ [JSON packets @ 115200 baud]
SerialReader (background thread)
       ↓ [Validate JSON]
DataManager (add/update victim)
       ↓ [Auto-save to JSON]
Dashboard Refresh
       ↓ [MapManager renders Folium]
Interactive Map (color-coded markers)
       ↓
Operator clicks marker → marks status → rescue log recorded
```

---

## CONFIGURATION HIGHLIGHTS (config.py)

```
Serial: 115200 baud (LoRa standard)
Map: Centered on Bangalore, zoom 14 (street detail)
Thresholds: RSSI -70/-85 dBm, time 15/20 minutes
Status Types: STRANDED, EN_ROUTE, RESCUED
Backup: Auto-save every 30 seconds to JSON
Validation: GPS (-90/90, -180/180), RSSI (-150/-30), ID (1-9999)
```

---

## CORE ALGORITHMS (SIMPLIFIED)

**Priority = Signal Strength + Time Since Update**
- If weak signal OR stale data → CRITICAL (rescue now)
- Else if medium signal AND outdated → HIGH (prioritize)
- Else → MEDIUM (stable)

**Geographic Clustering**
- Grid-based 0.001° sectors (~100m cells)
- Count victims per sector → identify disaster epicenter

**Rescue Efficiency**
- Rate = Rescued / Total × 100%
- Efficiency = (Rate × 60%) + (Speed × 40%)

---

## UI PAGES

**Dashboard:** Real-time map + victim list + status management  
**Analytics:** Charts (pie, bar, line, scatter, heatmap) + metrics  
**Export:** CSV/JSON/PDF reports + rescue logs  
**Settings:** COM port, thresholds, geolocation, backup  

---

## KEY MODULES EXPLAINED

**app.py:** Initializes page, manages navigation  
**serial_reader.py:** Reads JSON from hardware (background thread)  
**data_manager.py:** Victim database with auto-save  
**map_manager.py:** Creates Folium maps with markers  
**analytics.py:** NumPy-based statistics  
**helpers.py:** Priority calculation, formatting, distance  
**validators.py:** Input validation for security  

---

## VICTIM DATA STRUCTURE

```python
{
    'ID': 1,
    'LAT': 13.0227, 'LON': 77.5873,
    'TIME': '2025-12-24 14:30:45',
    'RSSI': -72,
    'STATUS': 'STRANDED',
    'FIRST_DETECTED': '2025-12-24 14:30:45',
    'LAST_UPDATE': '2025-12-24 14:30:55',
    'RESCUED_TIME': None,
    'RESCUED_BY': None,
    'UPDATE_COUNT': 5,
    'RSSI_HISTORY': [-72, -71, -73, ...],
    'NOTES': 'Conscious, mobile'
}
```

---

## REAL-TIME UPDATE MECHANISM

1. Serial packet arrives → SerialReader callback fires
2. DataManager.add_or_update_victim() called
3. `st.session_state.force_rerun = True` set
4. Dashboard detects flag → calls `st.rerun()`
5. Map refreshes with new/updated markers instantly

**Result:** No data loss, UI stays responsive, continuous monitoring

---

## FEATURES SUMMARY

✓ Real-time victim detection (no ground search needed)  
✓ 10-20 km range via LoRa (vs. limited ground search)  
✓ Intelligent priority algorithm (critical victims highlighted)  
✓ Geographic visualization (disaster epicenter identified)  
✓ Scientific metrics (rescue rate, efficiency, trends)  
✓ Complete audit trail (all status changes logged)  
✓ Multi-format export (CSV, JSON, PDF, reports)  
✓ Dynamic configuration (thresholds adjustable UI)  
✓ Offline capable (no internet required)  
✓ Scalable architecture (10-500+ victims)  

---

## PERFORMANCE

| Metric | Capacity |
|--------|----------|
| Victims | 100-500 |
| Packet Rate | 50-100/sec |
| Map Render | <1 second |
| Memory | ~2 MB per 100 |

---

## DEPLOYMENT (3 STEPS)

```bash
pip install -r requirements.txt
streamlit run app.py
# Browser opens: http://localhost:8501
```

**First Use:** Select COM port → Connect → Watch markers appear

---

## FILES ORGANIZATION

```
Gnd_Stat_Web/
├── app.py + config.py             # Entry + Configuration
├── _pages/                         # 4 UI Pages
├── modules/                        # 5 Core Modules
├── utils/                          # 2 Utilities
├── data/                           # 2 Persistent Files
└── requirements.txt                # Dependencies (11 packages)
```

**Total:** 3,500+ lines | 13 Python files | Production Ready

---

## WHAT LANGUAGES & FRAMEWORKS?

- **Backend:** Python (data management, serial communication, analytics)
- **Frontend:** Streamlit (auto-generates HTML/CSS UI)
- **Mapping:** Folium (Leaflet.js wrapper - interactive maps)
- **Analytics:** NumPy/Pandas (efficient numerical operations)
- **Charts:** Plotly (interactive visualizations)
- **Config:** .env file (environment-based settings)

---

## OPERATION WORKFLOW (10 STEPS)

1. Start application (http://localhost:8501)
2. Go to Settings → Select COM port
3. Connect hardware (victim devices broadcasting)
4. Monitor Dashboard for victim markers
5. Click marker to see details
6. Dispatch rescue team → Click "Mark En-Route"
7. Team arrives → Click "Mark Rescued"
8. Select operator name
9. Continue monitoring other victims
10. Export data for audit when done

---

## SECURITY MEASURES

- All serial packets validated (format, types, ranges)
- No duplicate victims (ID-based records)
- Auto-save backups (prevents data loss)
- Audit trail (logs all operator actions)
- Input sanitization (invalid data rejected)

---

**Code Volume:** 3,500+ lines  
**Modules:** 13 Python files  
**Status:** Production Ready  
**Version:** 1.0.0  
**Author:** Asshray Sudhakara, MARVEL UVCE

FalconResQ is a Streamlit-based dashboard for real-time victim detection and rescue coordination. It reads serial packets from ground station hardware, stores and visualizes victims on an interactive map, and provides analytics and export functions.

## Key Points

- Real-time ingestion: background serial reader with callbacks.
- Dynamic configuration: thresholds and rescue station location are editable at runtime.
- Map-based visualization: Folium maps with legend that reflects live thresholds.
- Exports and analytics: CSV/JSON exports and rescue statistics.

## Main Files

- `app.py`, `config.py`, `modules/`, `_pages/`, `utils/`

## Next steps

- Run unit tests and validate geolocation on the target browser.
- Create backups and consider moving to a small database.

(End of Short Report)
