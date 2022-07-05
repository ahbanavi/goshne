FROM python:3.10-alpine3.16 AS builder

## Virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

## Install dependencies:
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

FROM python:3.10-alpine3.16

## Set timezone
ENV TZ Asia/Tehran

## Activate virtualenv
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

## set working directory and add app
WORKDIR /usr/src/app

COPY . .

CMD [ "python", "./main.py" ]