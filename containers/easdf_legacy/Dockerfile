FROM python:3.8.5

COPY src/aeacus /app/aeacus
COPY containers/easdf_legacy/requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "-m", "aeacus.dns_legacy"]
