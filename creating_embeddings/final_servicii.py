import csv
import ast
import re
from tqdm import tqdm

csv_file_path = 'embedded_hcls/servicii_csv_formated_sections_with_small_prompt_coloana_hcls.csv'
csv_hcl_match_path = 'sumarizate_hcls/all_hcl_sumarizate_cleaned.csv'
output_csv_file_path = 'final_csvs/final_servicii_csv_with_HCL_sumarizate_appended.csv'

hcl_dict = {}
with open(csv_hcl_match_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        hcl_key = row['HCL'].strip()
        hcl_content = row['ContentComplet'].strip()
        hcl_dict[hcl_key] = hcl_content

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = list(csv.DictReader(csvfile))
    fieldnames = list(reader[0].keys()) + ['QuerryHCL', 'final_prompt_2']

rows = []

regex_hcl = re.compile(r'(?:HCLMT|HCL)\s*(?:nr\.)?\s*(\d+)[/\d\.]*[/\.](\d{4})')

for row in tqdm(reader, desc="Processing rows"):
    mentiuni = ast.literal_eval(row['Lista_mentiuni'])

    formatted_hcls = set()
    for ment in mentiuni:
        if 'HCL' in ment:
            match = regex_hcl.search(ment)
            if match:
                numar = match.group(1).strip()
                an = match.group(2)[-2:]
                formatted_hcls.add(f"{numar}/{an}")

    row['QuerryHCL'] = sorted(list(formatted_hcls))

    final_prompt_with_hcl = row['final_prompt'] if row['final_prompt'] else ""

    for hcl in row['QuerryHCL']:
        if hcl in hcl_dict:
            final_prompt_with_hcl += f"\n\nHCL {hcl}\n\n{hcl_dict[hcl]}"

    row['final_prompt_2'] = final_prompt_with_hcl if final_prompt_with_hcl.strip() else row['final_prompt']
    rows.append(row)

with open(output_csv_file_path, 'w', newline='', encoding='utf-8') as output_csvfile:
    writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Processed data has been saved to {output_csv_file_path}")
