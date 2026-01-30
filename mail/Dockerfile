FROM python:3.11-slim

WORKDIR /app

# Désactiver le buffering Python pour voir les logs en temps réel
ENV PYTHONUNBUFFERED=1

# Timezone
ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Script
COPY email_report.py .

CMD ["python", "email_report.py"]
