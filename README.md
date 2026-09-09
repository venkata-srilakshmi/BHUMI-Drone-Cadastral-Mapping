# BHOOMI-AI: Drone-Based AI Parcel Mapping & Automated Cadastral Feature Extraction

<div align="center">

![BHOOMI-AI Banner](https://img.shields.io/badge/BHOOMI--AI-Government%20of%20India-0259a0?style=for-the-badge&logo=gov.in)
![SIH26012](https://img.shields.io/badge/Smart%20India%20Hackathon-SIH26012-amber?style=for-the-badge)
![Ministry of Rural Development](https://img.shields.io/badge/Ministry%20of-Rural%20Development-emerald?style=for-the-badge)

**"From Drone Imagery to Verified Digital Land Maps."**

*A High-Precision AI & GIS Decision-Support Platform for Drone Orthomosaic Parcel Mapping, Automated Cadastral Object Extraction, Boundary Discrepancy Screening, and Human-in-the-Loop Surveyor Verification.*

</div>

---

## 📋 Executive Overview & Problem Statement

Under statutory national initiatives such as the **SVAMITVA Scheme** and the **Digital India Land Records Modernization Programme (DILRMP)**, rural and peri-urban land mapping is undergoing massive transformation through drone photogrammetry. However, survey directorates face major operational bottlenecks:
1. Manual on-screen parcel digitization from orthomosaics is labor-intensive, slow, and prone to human error.
2. Detecting boundary encroachments and spatial discrepancies between legacy revenue maps (created decades ago) and centimeter-level drone captures is difficult and manually tracked.
3. Automated AI models cannot legally dictate land ownership without transparent, verifiable human-in-the-loop audit trails for authorized survey officials.

### The BHOOMI-AI Solution
**BHOOMI-AI** automates the transition from raw aerial drone orthomosaics into verified digital land maps. It combines deep learning parcel boundary segmentation, YOLO-compatible cadastral object detection (buildings, roads, water bodies, agricultural fields), automated polygonization with georeferencing, Hausdorff metric discrepancy screening against legacy maps, and an interactive GIS workspace allowing Survey Officers to adjust vertices, record statutory justifications, and generate official Government of India survey dossiers.

---

## 🌟 Key Platform Features

| Capability | Technical Description |
| :--- | :--- |
| **Drone Imagery Ingestion** | Ingests OpenDroneMap / photogrammetry orthomosaics (GeoTIFF, PNG, JPG) with georeferencing metadata. |
| **Modular AI Segmentation** | U-Net & DeepLabV3+ architecture with sliding-window tiling for gigapixel aerial imagery, paired with a robust Computer Vision edge/contour extraction engine. |
| **Cadastral Feature Extraction** | YOLO-compatible detection of buildings, road networks, surface water reservoirs, agricultural parcels, tree clusters, and boundary walls. |
| **GIS Polygonization & Georeferencing** | Converts raster masks into topologically valid EPSG:4326 GIS polygons (`make_valid`, Douglas-Peucker simplification, metric area/perimeter calculation). |
| **Discrepancy Screening Engine** | Quantifies spatial variations between legacy revenue maps and drone captures: Hausdorff boundary displacement in meters, area delta %, and overlap ratio (IoU). |
| **Human-in-the-Loop Vertex Editor** | Authorized Survey Officers can drag polygon corner pins to align with ground truth, saving modifications to an immutable audit trail without overwriting original AI baselines. |
| **AI Geospatial Assistant** | Natural-language query interface (*"Show buildings inside agricultural parcels"*, *"Show parcels with boundary discrepancies"*) executing safe spatial operations. |
| **Multi-Temporal Change Detection** | Compares Survey $T_1$ vs Survey $T_2$ to isolate new constructions, demolished structures, and altered parcel boundaries. |
| **Statutory PDF Report Generation** | Generates official Government of India survey dossiers using ReportLab with executive KPIs, discrepancy tables, and signature endorsements. |
| **Open Geospatial Exports** | One-click export to OGC GeoJSON, Land Revenue CSV registers, and Google Earth / GNSS KML files. |

---

## 🛠️ Technology Stack

- **Frontend:** React 18, Vite, Tailwind CSS, Leaflet, React-Leaflet, Lucide React, Recharts, Axios, React Router.
- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 ORM.
- **AI & Computer Vision:** PyTorch, OpenCV (`opencv-python`), NumPy, SciPy, Pillow.
- **GIS Engine:** Shapely 2.0+, Geodesic & UTM Metric Projections, Douglas-Peucker Polygon Approximation.
- **Reporting & Storage:** ReportLab PDF Engine, OGC GeoJSON/KML Exporters, S3-ready storage abstraction.
- **Database:** PostgreSQL + PostGIS (Production) / Zero-configuration SQLite Spatial fallback (Development).
- **Authentication:** JWT (JSON Web Tokens), Bcrypt password hashing, Role-Based Access Control (`admin`, `survey_officer`, `viewer`).
- **Containerization:** Multi-stage Dockerfiles, Docker Compose.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed

### 1. Clone & Configure Environment
```bash
git clone <repository-url>
cd bhoomi-ai

# Copy environment file
cp .env.example .env
```

### 2. Run Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server (runs on http://localhost:8000)
uvicorn main:app --reload --port 8000
```
*On initial startup, the backend automatically initializes database tables, seeds demo user accounts, and generates the SIH Ramnagar Village prototype dataset.*

- **FastAPI Interactive OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Status Endpoint:** [http://localhost:8000/](http://localhost:8000/)

### 3. Run Frontend
```bash
cd ../frontend

# Install npm packages
npm install

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🐳 Docker Deployment

To launch the complete multi-tier system (PostgreSQL/PostGIS database, FastAPI backend, and React Nginx frontend) with one command:

```bash
docker-compose up --build
```
- **Web Portal:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **PostGIS Database:** `localhost:5432` (User: `postgres`, DB: `bhoomi_db`)

---

## 🔑 Demo Credentials

BHOOMI-AI comes pre-seeded with 3 role-based administrative accounts. You can type them manually or click the **1-Click Quick Demo Buttons** on the Login screen:

| Role | Email | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Survey Officer** *(Recommended)* | `officer@bhoomi.gov.in` | `Officer@2026` | Full GIS map access, vertex boundary editing, parcel verification/rejection, upload, and report export. |
| **Administrator** | `admin@bhoomi.gov.in` | `Admin@2026` | Full administrative control, survey creation, user management, and system-wide analytics. |
| **Public Viewer** | `viewer@bhoomi.gov.in` | `Viewer@2026` | Read-only inspection of verified digital land records, search, and public downloads. |

---

## 🎬 End-to-End SIH Hackathon Demo Workflow

Follow this complete presentation walkthrough to demonstrate the full end-to-end workflow to judges:

1. **Login:**
   - Navigate to `http://localhost:5173/login`.
   - Click the **"Survey Officer"** quick button (populates `officer@bhoomi.gov.in` / `Officer@2026`) and click **Sign In**.
2. **Executive Dashboard:**
   - Review executive KPIs: Total Surveys, AI Parcels Mapped, Verified Parcels, Flagged Discrepancies, and Cadastral Objects.
   - Inspect Recharts visualizations: Land use breakdown, verification status funnel, and cadastral feature distribution.
3. **Survey Intake (or One-Click Demo Provisioning):**
   - Click **"New Survey"** in the top navigation.
   - Enter survey parameters, or simply click the glowing **"Load Pre-Configured Demo"** button.
   - Watch the 10-stage processing timeline: File Validation → AI Segmentation → Feature Detection → Boundary Extraction → Polygon Generation → GIS Validation → Completed.
4. **Interactive GIS Map Workspace:**
   - Click **"Open Interactive GIS Map"** (`/surveys/1/map`).
   - Switch base layers between **Satellite Imagery** (Esri World Imagery) and **Street Map**.
   - Toggle vector layers: AI Parcels, Legacy Cadastral Boundaries (dashed blue), Buildings (orange), Roads (slate), Water Bodies (cyan).
5. **Inspect Boundary Discrepancy:**
   - In the parcel list or directly on the map, click parcel **`P-103`**.
   - Observe the discrepancy screening card: **2.4 meters displacement** on the eastern field bund with an area variation of **5.2%**.
   - Notice the statutory disclaimer explicitly highlighting: *"Screening Result: AI drone candidate boundary. Final legal title determination rests with authorized survey officer."*
6. **Human-in-the-Loop Boundary Adjustment:**
   - Click **"Edit Boundary Vertices"**.
   - Notice the interactive blue vertex pins appear on the map, alongside the dotted gray original AI baseline.
   - Drag a corner vertex to align the boundary with the physical field bund.
   - Click **"Commit Adjustment"**.
   - In the modal, review the original area vs adjusted area, provide the statutory justification (*"Adjusted boundary to align with physical stone bund verified on-site with DGPS rover"*), and click **"Commit & Update Geometry"**.
7. **Statutory Verification Approval:**
   - Click **"Approve"** on parcel `P-103`.
   - Status transitions to **`VERIFIED`** (green badge), and an immutable audit log entry is added with timestamp and officer name.
8. **AI Natural-Language Spatial Assistant:**
   - Click the **"AI Assistant"** button on the top right of the map.
   - Click the suggested prompt: *"Show buildings inside agricultural parcels"*.
   - The AI identifies buildings located on agricultural land and highlights the matching parcel (`P-101`) directly on the map!
9. **Multi-Temporal Change Detection:**
   - Click **"Change Detection"** in the sidebar.
   - Compare Survey 2025 vs Survey 2026 to visualize newly constructed agricultural sheds (+3), removed structures (-1), and boundary shifts.
10. **Official PDF Dossier & Geospatial Export:**
    - Click **"Reports & Dossiers"** in the sidebar.
    - Click **"Download Official PDF Dossier"** to stream a clean, Government of India / Ministry of Rural Development survey report with tables, discrepancy matrices, and endorsement signature blocks.
    - Download **GeoJSON**, **CSV Revenue Register**, and **Google Earth KML** files.

---

## 🧠 AI Architecture & Custom Model Integration

BHOOMI-AI is architected with a decoupled, modular AI service layer located in `backend/app/ai/`:

### 1. Parcel Boundary Segmentation (`ai/parcel_segmentation/`)
- Architecture: `CadastralUNet` (or DeepLabV3+ compatible).
- Preprocessor: Tiled sliding-window inference with 15% margin overlap to eliminate edge artifacts on large drone orthomosaics.
- Prototype Inference Engine: High-precision computer vision pipeline utilizing CLAHE contrast adjustment, bilateral ridge filtering, Canny edge detection, and morphological contour closure.
- **How to plug in a custom trained model:**
  1. Train your PyTorch model on a cadastral dataset (e.g. UAVid, DroneDeploy, or AIRS).
  2. Save your checkpoint as `models/cadastral_unet.pt`.
  3. Instantiate `ParcelSegmenter(weights_path="models/cadastral_unet.pt")`.

### 2. Cadastral Object Detection (`ai/feature_detection/`)
- Architecture: YOLO-compatible interface (`CadastralFeatureDetector`).
- Detects: `building`, `road`, `water_body`, `agricultural_field`, `tree_cluster`, `boundary_wall`, `survey_marker`.
- Outputs GeoJSON features with bounding boxes, polygons, and confidence scores.
- **How to plug in a custom YOLO model:**
  1. Export your trained YOLOv8/YOLOv11 weights (e.g. `best.pt`).
  2. Load model via `ultralytics.YOLO("best.pt")` inside `detect_features()` method in `app/ai/feature_detection/detector.py`.

---

## 🌐 AWS Cloud Architecture (Production Scale)

For enterprise state or national deployment under DILRMP:
- **Storage:** Amazon S3 with CloudFront CDN for serving high-resolution tiled orthomosaics and generated PDF dossiers.
- **Compute:** AWS ECS (Fargate) or EC2 instances with GPU acceleration (G4dn/G5) running the FastAPI backend and AI inference workers.
- **Database:** Amazon RDS PostgreSQL 15+ with PostGIS extension for spatial indexing (`GIST` indexes on parcel geometries).
- **Task Queue:** Amazon SQS + Celery/Redis for managing long-running photogrammetry tile extraction and deep-learning pipelines.

---

## 🧪 Automated Test Suite

Run the comprehensive unit and API integration tests:

```bash
cd backend

# Run GIS geometry, discrepancy, auth, and export tests
python tests/test_backend.py

# Run end-to-end API integration tests
python tests/test_api_integration.py
```

---

## ⚖️ Statutory Disclaimer

> **IMPORTANT ADMINISTRATIVE NOTICE:**  
> BHOOMI-AI is an AI-assisted decision-support system designed to assist revenue and survey officials under the Ministry of Rural Development. AI-extracted boundaries, cadastral feature classifications, and discrepancy calculations are screening candidates and do **not** constitute final legal title or legally binding boundary determinations until validated and endorsed by an authorized Survey Officer in accordance with state land revenue regulations.

---

<div align="center">

**Developed for Smart India Hackathon (SIH26012)**  
*Ministry of Rural Development • Government of India*

</div>
