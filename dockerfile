FROM apache/airflow:2.7.0



WORKDIR /opt/airflow

ENV PIP_USER=false
RUN python3 -m venv /opt/airflow/venv1


COPY requirements.txt .

RUN /opt/airflow/venv1/bin/pip install -r requirements.txt
RUN /opt/airflow/venv1/bin/pip install --upgrade pip
RUN /opt/airflow/venv1/bin/pip list
ENV PIP_USER=true


EXPOSE 8080

ENTRYPOINT ["airflow"]
CMD ["webserver"]