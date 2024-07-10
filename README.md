# Red-black-tree task Stefan Neskovic - Documentation

My task was to create a pipeline for the ETL of two datasets using Apache Airflow and the python programming language.

Create a data pipeline using Apache Airflow to perform an ETL (Extract, Transform, Load)
process for zoo animal data. The pipeline should:
1. Extract animal data from multiple CSV files.
2. Transform the data with various operations.
3. Aggregate and validate the data.
4. Load the final transformed and validated data into a new CSV file.


# Setup Apache Airflow

1. Create a Python virtual environment: ```sh python3 -m venv airflow_venv source airflow_venv/bin/activate ``` 
2. Install Apache Airflow: ```sh pip install apache-airflow==2.7.0 ```
3. Initialize the Airflow database: ```sh airflow db init ```
4. Create a DAG file (e.g., `rbt_dag.py`) in the `dags` folder
5. Write simple DAG and import required libraries

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
from airflow.utils.dates import days_ago
import os

    dag = DAG(
    'rbt_task',
    default_args={'start_date':days_ago(1)},
    schedule_interval='0 23 * * *',
    catchup=False
)
```


# Extract Tasks


## Create tasks to read data from two CSV files named zoo_animals.csv and zoo_health_records.csv.

```python
def  read_csvs(**kwargs):
	zoo_animals_path = os.path.join(BASE_DIR, "../data/zoo_animals.csv")
	zoo_health_records_path = os.path.join(BASE_DIR, "../data/zoo_health_records.csv")
	df1 = pd.read_csv(zoo_animals_path)
	df2 = pd.read_csv(zoo_health_records_path)
	df1_json = df1.to_json()
	df2_json = df2.to_json()
	kwargs['ti'].xcom_push(key='zoo_animals', value=df1_json)
	kwargs['ti'].xcom_push(key='zoo_health_records', value=df2_json)
```

- In this function, we use the Pandas library to read CSV files containing zoo animals and their health records. The files are read from the specified paths and converted into JSON format. The JSON data is then pushed to XCom, which is a storage mechanism in Apache Airflow for sharing data between tasks in a DAG (Directed Acyclic Graph). Specifically, the `xcom_push` method is used to store the JSON data with keys 'zoo_animals' and 'zoo_health_records', making the data available for downstream tasks within the same DAG.

	> https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html.

# Transform Tasks

 1. Merge the data from zoo_animals.csv and zoo_health_records.csv based on animal_id.
 2. Filter out animals where the age is less than 2 years.
 3. Convert the animal_name column to the title case.
 4. Ensure the health_status column contains only "Healthy" or "Needs Attention".

```python
def  transform_df(**kwargs):
	df1_json = kwargs['ti'].xcom_pull(key='zoo_animals', task_ids='extract_task')
	df2_json = kwargs['ti'].xcom_pull(key='zoo_health_records', task_ids='extract_task')
	df1 = pd.read_json(df1_json)
	df2 = pd.read_json(df2_json)
	df = pd.merge(df1,df2,on='animal_id')
	df = df[df['age'] >=2]
	df['animal_name'] = df['animal_name'].str.title()
	df = df[df['health_status'].isin(['Healthy', 'Needs Attention'])]
	df_json = df.to_json()
	kwargs['ti'].xcom_push(key = 'transformed_df', value = df_json)
```
In this function, we continue using the Pandas library and XCom and inter-task communication within Apache Airflow. The function first pulls the JSON data for zoo animals and health records from XCom, which were previously stored by another task. Using Pandas, the data frames are merged based on the 'animal_id' column. We then filter out animals younger than 2 years old and convert the 'animal_name' column to title case. Additionally, we ensure the 'health_status' column contains only "Healthy" or "Needs Attention" using the `isin` function. The transformed data frame is then converted back to JSON format and pushed to XCom for use by subsequent tasks.


# Aggregation and Validation Tasks

 1. Aggregate the data to count the number of animals in each species and the
number of "Healthy" vs "Needs Attention" statuses.
 2. Validate the aggregated data to ensure the counts are correct and no data is
missing.

```python
def  aggregation(**kwargs):
df_json = kwargs['ti'].xcom_pull(key ='transformed_df', task_ids='transform_task')
df = pd.read_json(df_json)
species_count = df.groupby('species').size().reset_index(name='count')
health_status_count = df.pivot_table(index='species', columns='health_status', aggfunc='size', fill_value=0).reset_index()
total_animals_count = df.shape[0]
aggregated_count = health_status_count[['Healthy', 'Needs Attention']].sum().sum()
assert  total_animals_count == aggregated_count, "Some data is not valid!"
kwargs['ti'].xcom_push(key='validated_data', value=df.to_json())
kwargs['ti'].xcom_push(key='species_count', value=species_count.to_json())
kwargs['ti'].xcom_push(key='health_status_count', value=health_status_count.to_json())
```
 The function pulls the transformed JSON data from XCom and loads it into a DataFrame. It then uses `groupby` to count the number of animals by species, creating a summary of species counts.

To analyze health statuses by species, we use the `pivot_table` function, which reshapes the data by creating a table where rows represent species and columns represent health statuses ("Healthy" or "Needs Attention"). The `aggfunc='size'` parameter counts the number of occurrences for each combination of species and health status. The `fill_value=0` parameter is used to replace any missing values in the pivot table with 0, ensuring that all combinations are represented even if no animals fall into a particular category.

The `reset_index` function is applied to both the grouped data and the pivot table to convert the grouped indices back into columns, making the data easier to work with in subsequent tasks.

Finally, the total number of animals is verified using `shape`, and an assertion is performed to ensure data validity by comparing the total animal count with the aggregated health status counts using `sum().sum()`. The resulting data is then pushed back to XCom for further use.


# Load Task

```python
def  load(**kwargs):
	df_json = kwargs['ti'].xcom_pull(key='validated_data', task_ids='aggregate_task')
	df = pd.read_json(df_json)
	etl_path = os.path.join(BASE_DIR, "../data/etl_zoo.csv")
	df.to_csv(etl_path,index=False)
```
In this function, we use the Pandas library to save the DataFrame as a CSV file. The transformed JSON data is pulled from XCom and converted back into a DataFrame. We then use `to_csv` to write the DataFrame to a CSV file, specifying `index=False` to avoid adding an extra column named "Unnamed: 0", which would be a duplicate and is not desired.


# Airflow DAG

```python
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

aggregate_task = PythonOperator(
	task_id = 'aggregate_task',
	python_callable=aggregation,
	provide_context = True,
	dag = dag,
)

load_task = PythonOperator(
	task_id = 'load_task',
	python_callable=load,
	provide_context=True,
	dag=dag
)
extract_task  >>  transform_task  >>  aggregate_task  >>  load_task
```
I defined each task using the `PythonOperator`, specifying the task ID, the corresponding Python function, and the DAG. 
The tasks are `extract_task`, `transform_task`, `aggregate_task`, and `load_task`. Finally, I set up the task pipeline with the sequence `extract_task >> transform_task >> aggregate_task >> load_task`, ensuring they execute in the correct order.


# Visualization

I received an additional task to visualize the processed data from the pipeline, and I chose the following visuals: a bar chart showing the relationship between species and health status, a pie chart showing species distribution, and a pie chart showing health status distribution. For visualization I used matplotlib and seaborn libraries.

![Combined plots](https://i.ibb.co/PGgzyf6/combined-plots.png)

# Dockerize

I have written a Dockerfile that simulates everything mentioned in the documentation related to setting up a virtual environment and introducing additional constraints. The Dockerfile successfully created the image, and I also wrote a Docker Compose YAML file that successfully runs all the services except for the Airflow database initialization. Despite finding numerous suggestions from various resources to resolve this issue, I consistently encounter missing libraries in the Dockerfile.

![enter image description here](https://i.ibb.co/92JHwvv/Screenshot-from-2024-07-10-20-41-16.png)
```Dockerfile 
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
```
>https://github.com/apache/airflow/issues/14616
>https://www.reddit.com/r/learnpython/comments/xvzlwl/docker_airflow_error_can_not_perform_a_user/
>https://stackoverflow.com/questions/73955605/docker-airflow-error-can-not-perform-a-user-install-user-site-packages-a
