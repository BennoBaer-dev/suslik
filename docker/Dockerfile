# suslik — Stufe-1-Smoke-Test-Image (CPU).
# Ziel: bootet es, serviert die UI, erreicht es Frigate, laeuft der Setup-Wizard,
# analysiert es ein Event auf CPU? Modelle sind INS Image gebacken (deine Entscheidung).
FROM python:3.13-slim

# --- System-Deps ---
#   ffmpeg           : Video-Decode/Transcode (Browser-Kopien der Clips)
#   libgl1/libglib   : von opencv gebraucht
#   sshpass          : nur fuer frigate_sync (im Test AUS) — der Vollstaendigkeit halber
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libgl1 libglib2.0-0 sshpass \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python-Deps zuerst (eigener Layer -> Build-Cache, aendert sich selten) ---
COPY docker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# --- Modelle BACKEN (kein Runtime-Download) ---
#   AdaFace liegt im Repo unter models/ ; buffalo_l an insightfaces Suchort ~/.insightface
COPY NOTICE LICENSE /app/
COPY models/ /app/models/
COPY docker/buffalo_l/ /root/.insightface/models/buffalo_l/

# --- Code + Container-Config ---
COPY verifyd.py analyze.py anlernen.py face_audit.py abnahme.py auftritte.py szenarien.py decode.py worker.py no_person.py sync_refs.py /app/
COPY webui/ /app/webui/
COPY core/ /app/core/
COPY routes/ /app/routes/
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
