FROM python:3.12.4

# Install Node.js for building the SvelteKit app
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

RUN mkdir /app
COPY metacatalog_api /app/metacatalog_api
COPY requirements.txt /app/requirements.txt
COPY README.md /app/README.md
COPY LICENSE /app/LICENSE
COPY setup.py /app/setup.py
COPY MANIFEST.in /app/MANIFEST.in


# Install Node.js dependencies and build the SvelteKit app
ARG METACATALOG_ENVIRONMENT
RUN cd /app/metacatalog_api/apps/manager && \
    npm install && \
    if [ "$METACATALOG_ENVIRONMENT" = "production" ]; then \
        VITE_BACKEND_URL="" npm run build; \
    else \
        npm run build; \
    fi

RUN pip install --upgrade pip && \
    #pip install poetry && \
    # poetry config virtualenvs.create false && \
    #cd /app && poetry install
    cd /app && pip install -e . && \
    pip install fire  && \
    pip install debugpy

WORKDIR /app

CMD ["python", "metacatalog_api/default_server.py", "--reload=True"]