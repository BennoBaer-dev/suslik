# suslik — das CPU-Image: der universelle Rueckfall, laeuft ueberall, braucht keinen
# Treiber und kein durchgereichtes Geraet. Modelle sind INS Image gebacken.
#
# ────────────────────────────────────────────────────────────────────────────────
# 0.1.0.541 (17.09.2026, E4) — ZWEI ENTSCHEIDE, beide gemessen begruendet
# ────────────────────────────────────────────────────────────────────────────────
# (1) DIESES IMAGE ANALYSIERT WIEDER. Der Worker-Neubau (E3, .527) hatte fuer
#     `backend: cpu` keine Engine; der Worker starb beim Start mit einem SystemExit.
#     `engine_cpu.py` schliesst das — sie ist kein Neubau, sondern der bewiesene
#     CPU-Rechenweg von `engine_migraphx` mit eigenem Session-Bauer (Begruendung im
#     Kopf von engine_cpu.py).
#
# (2) INFERENZ-STACK GEWECHSELT: `onnxruntime==1.27.0` -> `onnxruntime-openvino==1.24.1`
#     (+ standalone `openvino==2025.4.1`), also derselbe Stack wie im gpu-Image.
#     DER BELEG, und er ist fremd gemessen: Feldtester-Vergleich vom 10.09.2026
#     (Discussion #29, dieselbe Maschine, dieselben Modelldateien, alle Modelle des
#     Urteilspfads) — der OpenVINO-CPU-EP rechnet durchgehend 3-7x schneller als das
#     nackte onnxruntime, **adaface 48,7 ms je Inferenz statt 192,2 ms**.
#     Die Pin-Regel in docker/requirements.txt verlangt fuer so einen Wechsel
#     ausdruecklich „bewusste Entscheidung + neue Abnahme"; die Abnahme ist die
#     Vorher/Nachher-Messung am Grundwahrheits-Korpus (.526-cpu gegen 0.1.0.541-cpu,
#     je Event Wanduhr UND Urteil — s. CHANGELOG 0.1.0.541).
#     WAS NICHT MITKOMMT: KEINE Intel-GPU-/NPU-Treiberpakete (kein compute-runtime,
#     kein IGC, kein libze, kein NPU-Tarball). Der OpenVINO-CPU-Plugin braucht keinen
#     Treiber. Dieses Image bleibt treiberfrei und ueberall lauffaehig.
FROM python:3.13-slim

# --- System-Deps ---
#   ffmpeg           : Video-Decode/Transcode (Browser-Kopien der Clips) und der
#                      Sample-Frame-Decode der Analyse. BEWUSST OHNE VAAPI-Treiber:
#                      dieses Image dekodiert in Software, und `engine_cpu` versucht
#                      deshalb gar nicht erst Hardware-Decode (sonst stuende in jedem
#                      Ereignis eine „hwdec_fallback"-Zeile, die auf den anderen
#                      Varianten ein echter Befund ist).
#   libgl1/libglib   : von opencv gebraucht
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python-Deps zuerst (eigener Layer -> Build-Cache, aendert sich selten) ---
#     onnxruntime-openvino MUSS ueber plain onnxruntime gewinnen: insightface zieht
#     plain `onnxruntime` als Abhaengigkeit herein und VERDECKT damit die
#     openvino-Variante (dann gibt es keinen OV-EP und der 3-7x-Hebel ist still weg).
#     Deshalb danach hart erzwingen — wortgleich zu Dockerfile.gpu.
COPY docker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip uninstall -y onnxruntime onnxruntime-openvino \
    && pip install --no-cache-dir --no-deps onnxruntime-openvino==1.24.1

# --- standalone OpenVINO, EXAKT die Version, die onnxruntime-openvino 1.24.1 ohnehin
#     gebuendelt mitbringt (2025.4.1) — das E3.5-Muster des gpu-Images, gleiche Zahl.
#     WARUM ER HIER STEHT, obwohl `engine_cpu` ihn nicht importiert: die
#     Hardware-Probe des Starts (`verifyd.hardware_probe`) fragt autoritativ
#     `openvino.Core().available_devices`. Ohne das Paket faellt sie auf „EP ist da,
#     Nutzung hier unbestaetigt" zurueck und probiert ersatzweise GPU-/NPU-Bindungen,
#     die auf einem treiberfreien Image nie gelingen koennen — der Startlog saehe
#     dann nach einem Treiber-Mismatch aus, wo schlicht kein Treiber im Image ist.
#     WARUM GEPINNT UND WARUM DIESE ZAHL: requirements.txt verbietet ein UNGEPINNTES
#     `openvino` (pip zieht eine neuere Runtime als die gebuendelte). Heben = bewusste
#     Entscheidung + neue Abnahme (A15-Regel), nie nebenbei.
RUN pip install --no-cache-dir openvino==2025.4.1

# --- OpenVINO-Kompilat-Cache ins VOLUME. Muster ist Dockerfile.gpu (NEO_CACHE_DIR) und
#     Dockerfile.rocm (ORT_MIGRAPHX_MODEL_CACHE_PATH): unter `clips/`, weil dieser
#     Ordner vom Backup ausgenommen ist (Kompilate sind regenerierbar) und weil der
#     Dienst dort bereits einen Deckel fuehrt (`ov_cache_max_gb`, verifyd.py:7569-7576,
#     er raeumt beide ov_cache-Ordner). Ohne cache_dir kompiliert der OV-CPU-EP bei
#     JEDEM Prozessstart jede Stufe neu — und dieser Worker startet oefter als einmal.
#     ACHTUNG, dieselbe Falle wie beim NEO-Cache: /data ist ein Volume-Mount, ein RUN
#     mkdir hier waere davon verdeckt. `engine_cpu.cache_vorbereiten` legt den Ordner
#     deshalb zur LAUFZEIT an und meldet laut, wenn er nicht schreibbar ist.
ENV SUSLIK_OV_CACHE_DIR=/data/clips/ov_cache_models

# --- Modelle BACKEN (kein Runtime-Download) ---
#   AdaFace liegt im Repo unter models/ ; buffalo_l an insightfaces Suchort ~/.insightface
COPY NOTICE LICENSE /app/
COPY models/ /app/models/
COPY docker/buffalo_l/ /root/.insightface/models/buffalo_l/

# --- Code + Container-Config ---
# R1-UMZUG (E3.5, 14.09.2026): die Neubau-Dateien des Workers liegen seit dem
#   E3-Schnitt in der Projektwurzel und MUESSEN mit ins Image — verifyd startet
#   worker_dienst.py aus /app (verifyd.worker_dienst_pfad, ohne Rueckfall).
#   Die Engines werden im Dienst LAZY importiert (worker_dienst.engine_bauen), die
#   jeweils fremde Engine stoert deshalb in keinem Image. In DIESEM Image rechnet
#   `engine_cpu` (E4, .541); sie importiert `engine_migraphx` (Bestands-Mechanik) und
#   ueber dieses `engine_cuda` (reine ONNX-Helfer) — beide muessen also wirklich hier
#   liegen und sind kein toter Ballast.
COPY verifyd.py analyze.py anlernen.py face_audit.py abnahme.py auftritte.py szenarien.py decode.py worker.py no_person.py sync_refs.py \
     worker_dienst.py worker_kern.py bild_kern.py engine_ov.py engine_cuda.py engine_migraphx.py engine_cpu.py /app/
COPY webui/ /app/webui/
COPY core/ /app/core/
COPY routes/ /app/routes/
# PE1 Person-Learn (stufe2.md B5): bereinigte Prototyp-Kette + Modelle;
# Pfad-Bruecken: verify_data->/data (Deckung), prototyp/daten->Werkstatt im Volume.
COPY docker/personlern_stage/ /app/prototyp/
COPY docker/personlern_stage_modelle/ /app/prototyp/modelle/rtmpose/
COPY modelle/dinov2_vits14_126x252.onnx /app/modelle/
# .203: Person-ReID-Backbone (Intel OMZ 0277, Apache-2.0 inkl. Modelldatei; Bezug/Checksumme: core/personmodell.py BACKBONES + wiki/erkennung.md)
COPY modelle/person-reidentification-retail-0265.onnx /app/modelle/
ENV SUSLIK_DATA_DIR=/data SUSLIK_WERKSTATT=/data/personlern/werkstatt VERIFY_DATA_DIR=/data
COPY VERSION /app/VERSION
COPY docker/verifyd.container.yaml /app/verifyd.yaml

# Feste Versionsnummer ins Image (tools/build.sh reicht sie aus der VERSION-Datei als --build-arg rein).
ARG VERSION=dev
ENV SUSLIK_VERSION=$VERSION SUSLIK_VARIANT=cpu
LABEL org.opencontainers.image.title="suslik" org.opencontainers.image.version="$VERSION" org.opencontainers.image.source="https://github.com/BennoBaer-dev/suslik"

# Datenverzeichnis kommt als Volume (leer = frisches System = Wizard). web_port bleibt 8199 im
# Container; nach aussen mappt compose auf 8299.
EXPOSE 8199
CMD ["python", "verifyd.py", "--config", "verifyd.yaml"]
