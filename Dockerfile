FROM python:3.8-buster


RUN apt-get update && apt-get install -y 

RUN pip install --upgrade pip

RUN pip install python-dotenv

RUN pip install Flask

RUN pip install aiomysql

RUN pip install databases

RUN pip install pymodbus

RUN pip install async-modbus

RUN pip install flask[async]



WORKDIR /app



COPY . .

EXPOSE 5000

CMD [ "python", "app.py" ]

