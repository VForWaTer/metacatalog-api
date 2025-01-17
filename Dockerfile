FROM python:3.12.4


RUN mkdir /app
COPY metacatalog_api /app/metacatalog_api
COPY requirements.txt /app/requirements.txt
COPY README.md /app/README.md
COPY LICENSE /app/LICENSE
COPY setup.py /app/setup.py
COPY MANIFEST.in /app/MANIFEST.in

RUN pip install --upgrade pip && \
    #pip install poetry && \
    # poetry config virtualenvs.create false && \
    #cd /app && poetry install
    cd /app && pip install -e . && \
    pip install fire

WORKDIR /app

CMD ["python", "metacatalog_api/default_server.py", "--reload=True"]