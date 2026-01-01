# FalconResQ 

**FalconResQ** is a drone-assisted emergency rescue communication and monitoring system designed for disaster scenarios where conventional infrastructure fails. The system combines **LoRa-based distress beacons**, an **aerial relay mounted on a drone**, and a **web-based ground station** to detect, aggregate, prioritize, and visualize victim signals over long distances with minimal power consumption.

This repository contains the **Ground Station software and system integration logic** used to receive, process, and analyze rescue beacon data in real time.

---

##  Problem Context

In disasters such as floods, landslides, earthquakes, and remote-area accidents:
- Cellular networks are unreliable or unavailable
- Victims cannot actively communicate their location
- Rescue teams lack real-time situational awareness

FalconResQ addresses this gap by enabling **low-power, long-range distress signaling** and **aerial data collection**, allowing rescue operators to detect and prioritize victims rapidly.

---

##  System Overview

FalconResQ is a **three-layer architecture**:

###  Beacon Layer (Victim Devices)
- Heltec Wireless Tracker–based LoRa beacons
- GNSS-enabled (latitude, longitude, timestamp)
- Battery-powered with aggressive power optimization
- Randomized, collision-avoidant LoRa transmissions

###  Aerial Relay Layer (Drone)
- Drone-mounted **WiFi LoRa 32 V3** receiver
- Scans multiple uplink channels
- Acts as a mobile concentrator
- Relays decoded packets to the ground station

###  Ground Station Layer (This Repository)
- Streamlit-based web application
- Real-time monitoring dashboard
- Victim prioritization and clustering
- Map visualization, analytics, and data export

---

##  Ground Station Features

###  Real-Time Monitoring
- Live serial data ingestion from drone receiver
- RSSI, SNR, GNSS coordinates, timestamps
- Automatic victim ID de-duplication

###  Interactive Map Visualization
- Victim markers with signal quality indicators
- Heatmaps for density-based hotspot detection
- Sector overlays for area division
- Rescue center reference point

###  Priority Assignment
Victims are automatically ranked using:
- Signal strength (RSSI)
- Signal quality (SNR)
- Time since last detection
- Distance from rescue center

###  Analytics Dashboard
- Detection statistics
- Signal quality distributions
- Temporal trends
- Geographic clustering

###  Data Management
- Auto-save of live data
- Export logs as **JSON / CSV**
- Manual restore of previous sessions

---

##  Repository Structure

```
FalconResQ/
│
├── app.py                 # Main Streamlit application entry point
├── config.py              # Central configuration parameters
│
├── modules/               # Core application logic
│   ├── DataManager.py     # Victim state tracking & persistence
│   ├── MapManager.py      # Folium-based map rendering
│   ├── Analytics.py       # Statistical and clustering analysis
│   ├── SerialReader.py    # Serial data ingestion from LoRa receiver
│
├── utils/
│   ├── helpers.py         # Formatting, calculations, priority logic
│   ├── validators.py     # Data validation utilities
│
├── _pages/                # Streamlit multi-page UI
│   ├── dashboard.py
│   ├── analytics.py
│   ├── settings.py
│
├── data/                  # Auto-saved logs and exports
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

##  Hardware Used

### Ground & Drone Side
- **Heltec WiFi LoRa 32 V3** (Drone-mounted receiver)
- External sub-GHz antenna (SMA)
- ELRS 2.4 GHz (Drone control – independent of LoRa)

### Beacon Side
- Heltec Wireless Tracker
- GNSS: Multi-constellation (GPS, Galileo, GLONASS, BeiDou)

---

##  Communication Characteristics

- Frequency band: Sub-GHz ISM (IN865 region)
- Modulation: LoRa
- Bandwidth: 125 kHz
- Spreading Factor: SF7–SF12 (configurable)
- Range: **10–20 km line-of-sight (tested and theoretical)**
- Decoding possible even at **negative SNR values**

---

##  Installation & Setup

###  Clone Repository
```bash
git clone https://github.com/Asshray-Sudhakar/FalconResQ.git
cd FalconResQ
```

###  Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

###  Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run Ground Station
```bash
streamlit run app.py
```

---

##  Testing & Validation

The system has been validated for:
- GPS acquisition time (TTFF)
- RSSI and SNR vs distance
- Urban obstacle effects
- Multi-beacon collision avoidance
- Long-range aerial reception

Results are logged and visualized directly in the dashboard.

---

##  Future Enhancements

- Multi-drone coordination
- Autonomous search patterns
- Satellite backhaul integration
- Encrypted payloads
- AI-assisted victim prioritization

---

##  Academic & Research Context

This project was developed as a **Level 3 R&D project under MARVEL, UVCE**, and is aligned with:
- Disaster-response communication systems
- UAV-based sensing networks
- Low-power wide-area networks (LPWAN)

---

##  Acknowledgements

- **MARVEL R&D Lab, UVCE**
- **UVCE Graduate Association (UVCEGA)**
- Faculty mentors and technical reviewers
- Family support during prototyping and field testing

---

##  License

This project is intended for **academic, research, and non-commercial humanitarian use**. Licensing details can be added as required.

---

##  Contact

**Asshray Sudhakar**  
Electronics & Communication Engineering, UVCE  
Project: *FalconResQ*

---

If you are interested in contributing, testing, or extending FalconResQ, feel free to explore the codebase and reach out.

