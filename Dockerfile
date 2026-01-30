FROM python:3.11-slim

WORKDIR /app

# Désactiver le buffering Python pour voir les logs en temps réel
ENV PYTHONUNBUFFERED=1

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY app/ .

# Créer le dossier data
RUN mkdir -p /app/data

CMD ["python", "analyzer.py"]
