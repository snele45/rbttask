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


def transform_df(**kwargs):
    df1_json = kwargs['ti'].xcom_pull(key='zoo_animals', task_ids='extract_task')
    df2_json = kwargs['ti'].xcom_pull(key='zoo_health_records', task_ids='extract_task')

    df1 = pd.read_json(df1_json)
    df2 = pd.read_json(df2_json)

    df = pd.merge(df1,df2,on='animal_id')
    df = df[df['age'] >=2]
    
    df['animal_name'] = df['animal_name'].str.title()

    df = df[df['health_status'].isin(['Healthy', 'Needs Attention'])]
    


dag = DAG(
    'rbt_task',
    default_args={'start_date':days_ago(1)},
    schedule_interval='0 23 * * *',
    catchup=False
)


extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=read_csvs,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id = 'transform_task',
    python_callable=transform_df,
    provide_context = True,
    dag = dag,
)



extract_task >> transform_task
