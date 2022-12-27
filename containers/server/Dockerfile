FROM python:3.8.5

COPY src/aeacus /app/aeacus
COPY resources/aeacus_secrets/fullchain.pem /app/fullchain.pem
COPY resources/aeacus_secrets/privkey.pem /app/privkey.pem
COPY containers/server/requirements.txt /app/requirements.txt
COPY submodules/aioquic /app/aioquic

WORKDIR /app/aioquic
RUN python setup.py install

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "-m", "aeacus.dummy_server", "--certificate", "fullchain.pem", "--private-key", "privkey.pem"]
