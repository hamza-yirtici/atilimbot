from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

client = Client()

csv_file = 'combined.csv'
input_keys = ['question']
output_keys = ['answer']

dataset = client.upload_csv(
    csv_file=csv_file,
    input_keys=input_keys,
    output_keys=output_keys,
    name="Course dates",
    description="Dataset containing course dates",
    data_type="kv"
)