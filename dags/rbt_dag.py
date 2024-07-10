from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
from airflow.utils.dates import days_ago

def read_csvs(**kwargs):
    df1 = pd.read_csv("/home/snele/rbttask/data/zoo_animals.csv")
    df2 = pd.read_csv("/home/snele/rbttask/data/zoo_health_records.csv")
    
    df1_json = df1.to_json()
    df2_json = df2.to_json()
    

    kwargs['ti'].xcom_push(key='zoo_animals', value=df1_json)
    kwargs['ti'].xcom_push(key='zoo_health_records', value=df2_json)





dag = DAG(
    'rbt_task',
    default_args={'start_date':days_ago(1)},
    schedule_interval='0 23 * * *',
    catchup=False
)


extract_task = PythonOperator(
    task_id='read_csvs',
    python_callable=read_csvs,
    provide_context=True,
    dag=dag,
)



extract_task
