FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git make ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock requirements.txt setup.py ./
COPY zk_offline_dqn ./zk_offline_dqn
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY paper ./paper
COPY artifacts/reports/final_ndss ./artifacts/reports/final_ndss
COPY artifacts/reports/provenance/sp1 ./artifacts/reports/provenance/sp1
COPY Makefile README.md ./

RUN python -m pip install --upgrade pip \
    && (python -m pip install -r requirements.lock || python -m pip install -r requirements.txt) \
    && python -m pip install -e .

CMD ["make", "help"]
