FROM python:3.6
RUN mkdir -p /app
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
#ENTRYPOINT python sioRepository.py
ENTRYPOINT python sioManager.py
