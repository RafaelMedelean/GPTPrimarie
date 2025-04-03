import csv
import threading
from openai import AzureOpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

#east
client = AzureOpenAI(
    api_key="",
    api_version="",
    azure_endpoint=""
)

id = 2
csv_file_path = f'sumarizate_hcls/checkpoint_hcl_sumarizate_{id}_summarized_hcls_cleaned.csv'
output_csv_file_path = f'sumarizate_hcls/checkpoint_hcl_sumarizate_{id}_with_embeddings.csv'
checkpoint_path = f'sumarizate_hcls/CHECKPOINT_hcl_sumarizate_{id}_embeddings.csv'

MAX_WORKERS = 25
CHECKPOINT_INTERVAL = 750
checkpoint_lock = threading.Lock()

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = list(csv.DictReader(csvfile))
    fieldnames = list(reader[0].keys()) + ['embedding']

def summarize_hcl(row):
    hcl_sumarizat_formatat = row['Hcl_sumarizat']
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            response = client.embeddings.create(
                input=hcl_sumarizat_formatat,
                model="text-embedding-3-large"
            )
            # Extract just the embedding array from the response.
            response_dict = response.model_dump()  # Convert to dict if needed.
            embedding_array = response_dict["data"][0]["embedding"]
            row['embedding'] = embedding_array
            return row
        except Exception as e:
            if '429' in str(e):
                print("Rate limit hit, retrying in 60 seconds...")
                time.sleep(60)
                return summarize_hcl(row)
            else:
                raise e

summarized_rows = []
checkpoint_lock = threading.Lock()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(summarize_hcl, row): row for row in reader}

    for idx, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Procesare HCL-uri")):
        result_row = future.result()
        summarized_rows.append(result := result if (result := future.result()) else None)

        if (idx := len(summarized_rows)) % CHECKPOINT_INTERVAL == 0:
            with checkpoint_lock:
                with open(checkpoint_path, 'w', newline='', encoding='utf-8') as checkpoint_file:
                    writer = csv.DictWriter(checkpoint_file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(summarized_rows)
                print(f"Checkpoint salvat după {idx} rânduri la {checkpoint_path}")
            break

# Salvare CSV final
with open(output_csv_file_path, 'w', newline='', encoding='utf-8') as output_csvfile:
    writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summarized_rows)

print(f"Datele procesate au fost salvate în {output_csv_file_path}")
