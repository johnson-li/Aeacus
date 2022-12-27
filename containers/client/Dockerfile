FROM python:3.8.5

COPY src/aeacus /app/aeacus
COPY containers/client/requirements.txt /app/requirements.txt
COPY submodules/aioquic /app/aioquic

WORKDIR /app/aioquic
RUN python setup.py install

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "-m", "aeacus.dummy_client", "https://aeacus.xuebing.me:4433"]
