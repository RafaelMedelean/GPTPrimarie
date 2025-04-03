import csv
import threading
from openai import AzureOpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

client = AzureOpenAI(
    api_key="",
    api_version="",
    azure_endpoint=""
)

id = 3
csv_file_path = f'total_hcls/hcl_part{id}.csv'
output_csv_file_path = f'sumarizate_hcls/hcl_sumarizate_{id}.csv'
checkpoint_path = f'sumarizate_hcls/checkpoint_hcl_sumarizate_{id}.csv'

MAX_WORKERS = 25
CHECKPOINT_INTERVAL = 100
checkpoint_lock = threading.Lock()

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = list(csv.DictReader(csvfile))
    fieldnames = list(reader[0].keys()) + ['Hcl_sumarizat']

def summarize_hcl(row):
    numar_hcl = row['HCL']
    content_hcl = row['ContentComplet']
    context_sumarizare = f"HCL {numar_hcl}\n{content_hcl}"

    prompt = (f"""
!Realizează o sumarizare compactă, detaliată și structurată a Hotărârilor Consiliului Local (HCL-uri) ale Municipiului Timișoara, respectând strict formatul și cerințele explicite enumerate mai jos. Evită integral observațiile personale, comentariile suplimentare sau informațiile irelevante (precum comunicarea către instituții sau voturile acordate).
!Structura obligatorie și explicită a sumarizării:
**Număr și an HCL:**
HCL[an]/[număr]
-Exemplu: HCL 155/2009
-Acest HCL trebuie sa apara pe primul rand al sumarizarii.
**Site:**
https://www.primariatm.ro/hcl/[an]/[număr]
**Categorie**
-Analizand continutul acestui HCL, mapeaza-l la una dintre categoriile de mai jos, atunci cand mapezi un HCL incearca sa intelegi explicatia pentru fiecare categorie care este data dupa "-". Alege o singura categorie din cele 14 de mai jos marcate intre "...":
-1."Identitate, familie" - Evenimente de viață (nașteri, căsătorii, decese), acte de identitate, indemnizații.
-2."Autorizare spații comerciale" - Autorizații pentru funcționarea spațiilor comerciale.
-3."Taxe și impozite" - Taxe, impozite locale, amenzi și atestare fiscală.
-4."Construcții, urbanism, terenuri" - Certificate de urbanism, autorizații de construcție.
-5."Educație și sănătate" - Informații despre creșe, grădinițe, școli și licee.
-6."Transport, străzi" - Transport public, infrastructură rutieră, servicii de taxi și avize ale comisiei de circulație.
-7."Mediu, curățenie, deșeuri" - Servicii de salubritate în oraș și reciclarea deșeurilor.
-8."Evenimente, cultură, turism" - Agenda culturală și atracții turistice locale.
-9."Comerț, afaceri" - Servicii dedicate mediului de afaceri.
-10."Parcuri, agrement, sport" - Administrarea parcurilor, locurilor de joacă și bazelor sportive.
-11."Asistență socială" - Servicii sociale dedicate categoriilor defavorizate.
-12."Comunitate" - Asociații de proprietari.
-13."Utilități publice" - Furnizarea curentului electric, gazului, apei și serviciile de canalizare.
-14."Altele" - Daca un HCL nu poate fi mapat in cele 13 de mai sus alege aceasta categorie
**Idee principală:**
-Rezumat detaliat, clar și explicit al obiectului hotărârii, menționând obligatoriu dacă hotărârea modifică, abrogă sau înlocuiește explicit acte legislative sau regulamente anterioare. Precizează titlul exact al proiectului sau investiției și date tehnice esențiale (locație exactă, beneficiari, regim înălțime, indicatori urbanistici, etc.) dacă este cazul.
-Motivație și Modificări legislative relevante:
-Menționează explicit și complet denumirea exactă, numărul/anul și articolele precise ale tuturor actelor legislative și regulamentelor relevante (exemplu: O.G. nr.99/2000, H.G. nr.1739/2006, Legea nr.61/1991, Legea nr.215/2001 art.36 alin.(4) lit.e, alin.(6) lit.a pct.7 și 11, H.C.L. nr.102/2009, H.C.L. nr.290/2022, O.U.G. nr.57/2019).
-Precizează explicit proiectele și contractele specific menționate în secțiunea de motivație din hotărâre, inclusiv numerele acestora, datele și persoanele sau entitățile implicate explicit.
-Nu menționa niciodată avizele comisiilor interne, referatele primarului sau nume ale persoanelor din primărie implicate în aprobarea actelor.
**Articole esențiale din hotărâre:**
-Selectează explicit și strict numai articolele care aprobă, abrogă sau modifică direct conținutul legislativ, indicatorii tehnico-economici sau regulamentele existente.
-Nu include articolele care menționează atribuirea responsabilităților administrative interne sau comunicarea către instituții și organizații.
!Instrucțiuni finale obligatorii:
-Menține sumarizarea compactă și precisă.
-Nu utiliza diacritice, caractere speciale sau spații excesive.
-Nu include niciun alt element în afara rubricilor marcate explicit cu "** **".
-Nu adăuga observații, comentarii personale sau precizări suplimentare care nu sunt solicitate explicit în acest prompt.
-Respecta toate observatiile care sunt marcate cu "!" sau "-", dar nu le include in textul final al sumarizarii.
-Sumarizarea finală nu trebuie să fie un rezumat general al hotărârii, ci trebuie să respecte strict structura obligatorie și să includă exclusiv informațiile esențiale și relevante indicate mai sus.
-Uite un exemplu de sumarizare corecta a unui HCL care urmeaza structura dorita,foloseste l ca exemplu si nu il introduce in sumarizarea finala:
"
HCL 155/2009
Site: https://www.primariatm.ro/hcl/2009/155  
HCL 155/2009 confera Titlul de Cetatean de Onoare al Municipiului Timisoara domnului Dan Bedros, recunoscandu-i contribuțiile la promovarea imaginii orașului. Hotararea nu inlocuieste sau modifica acte anterioare, ci se adopta in conformitate cu legislatia in vigoare.  
Motivatie si Modificari legislative relevante:  
- Facand referire la art.36 alin.(8) si art.45 din Legea nr.215/2001 privind administratia publica locala, republicata si modificata, hotararea respecta cadrul legal stabilit pentru acordarea titlurilor onorifice la nivel local.  
Articole esentiale din hotarare:  
- ARTICOL UNIC: Se confera Titlul de Cetatean de Onoare al Municipiului Timisoara domnului Dan Bedros.
"
!Urmează strict aceste instrucțiuni marcate cu "-" sau "!" si exemplul dat mai sus aflat intre "..." pentru sumarizarea următorului HCL fara sa incluzi indicatiile sau exemplul dat mai sus.
!Acesta este HCL care trebuie sa fie sumarizat:{context_sumarizare}""")
    
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            chat_completion = client.chat.completions.create(
                model="gpt-4-32k",#"gpt-35-turbo-16k", #"gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ești un asistent specializat în sumarizare compacta, dar detaliata de informații precise privind legislația din texte."},
                    {"role": "user", "content": prompt}
                ]
            )
            sumarizare_hcl = chat_completion.choices[0].message.content
            row['Hcl_sumarizat'] = sumarizare_hcl
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

with open(output_csv_file_path, 'w', newline='', encoding='utf-8') as output_csvfile:
    writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summarized_rows)

print(f"Datele procesate au fost salvate în {output_csv_file_path}")
