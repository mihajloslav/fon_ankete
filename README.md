# FON Anketa

Playwright automatizacija za popunjavanje anketa na **Studentskim servisima Fakulteta organizacionih nauka (FON)**.

Skripta otvara studentski servis, prijavljuje korisnika, ulazi u sekciju **Анкета**, prolazi kroz dostupne ankete i automatski popunjava njihove listiće.

> **Važno:** Projekat je napravljen za konkretnu strukturu FON studentskog servisa. Ako FON promeni HTML/JSF strukturu stranice, selektore ili način slanja formi, skripta može zahtevati izmene.

---

## Funkcionalnosti

Skripta automatski:

- otvara FON studentski servis;
- prijavljuje se korisničkim imenom i lozinkom;
- otvara sekciju **Анкета**;
- pronalazi dostupne ankete preko dugmeta **Попуни**;
- prolazi kroz sve listiće jedne ankete;
- na listićima koji imaju izbor nastavnika/saradnika bira nastavnike **redom**;
- preskače početnu praznu opciju `-- --`;
- pamti već izabrane nastavnike kako se isti nastavnik ne bi izabrao ponovo;
- popunjava odgovore na radio pitanjima;
- klikće **Следећи листић** ili **Даље**, u zavisnosti od stranice;
- prepoznaje završnu stranicu bez pitanja;
- na završnoj stranici klikće **Сачувај**;
- prelazi na sledeću dostupnu anketu;
- radi u vidljivom browser režimu, tako da se može pratiti šta skripta radi.

---

## Odgovori

Podrazumevani odgovori su podešeni na sledeći način:

| Pitanje | Odgovor |
|---|---|
| 1. Status po načinu finansiranja | `буџетски` |
| 2. Prosečna ocena | `8,51-9,50` |
| 3. Prisustvo na kursu | `између 30% и 70%` |
| Ostala pitanja | `6-Не могу да проценим` |

Ovi odgovori se mogu promeniti u `fon_ankete.py`.

---

## Zahtevi

Potrebno je imati:

- Python 3
- Playwright
- browser koji Playwright može da pokrene

Projekat je prvenstveno namenjen Linux okruženju.

---

## Instalacija

### 1. Kloniranje repozitorijuma

```bash
git clone <URL_REPOZITORIJUMA>
cd fon_ankete
```

### 2. Kreiranje virtualnog okruženja

```bash
python -m venv .venv
```

### 3. Aktiviranje virtualnog okruženja

```bash
source .venv/bin/activate
```

Na Windows-u:

```powershell
.venv\Scripts\activate
```

### 4. Instalacija Playwright-a

```bash
pip install playwright
```

### 5. Instalacija browsera

Ako koristiš Playwright-ov Chromium:

```bash
playwright install chromium
```

Ako Playwright prijavi da na Linux sistemu nedostaju biblioteke, instaliraj odgovarajuće sistemske zavisnosti za svoju distribuciju.

> Na Arch Linuxu Playwright može prikazati poruku da OS nije zvanično podržan i preuzeti Ubuntu fallback build. To samo po sebi ne znači da instalacija nije uspela.

---

## Konfiguracija

Pre pokretanja otvori:

```text
fon_ankete.py
```

i podesi:

```python
USERNAME = "tvoje_korisnicko_ime"
PASSWORD = "tvoja_lozinka"
```

Odgovore možeš promeniti ovde:

```python
Q1_ANSWER = "буџетски"
Q2_ANSWER = "8,51-9,50"
Q3_ANSWER = "између 30% и 70%"
DEFAULT_ANSWER = "6-Не могу да проценим"
```

Browser je podešen preko Playwright-a:

```python
browser = p.chromium.launch(
    headless=HEADLESS,
    slow_mo=SLOW_MO_MS,
)
```

Trenutno je:

```python
HEADLESS = False
```

što znači da se browser prozor vidi tokom izvršavanja.

---

## Pokretanje

Nakon aktiviranja virtualnog okruženja:

```bash
source .venv/bin/activate
```

pokreni:

```bash
python fon_ankete.py
```

Primer izlaza:

```text
Otvaram studentski servis...
Prijavljujem se...
Uspešno prijavljen.
Otvaram 'Анкета'...

[1] Otvaram anketu...
    Listić 1:
      nastavnik/saradnik: ...
      pronađeno pitanja: ...
      pitanje 1: буџетски
      pitanje 2: 8,51-9,50
      pitanje 3: између 30% и 70%
      ...

    Listić 2:
      nastavnik/saradnik: ...
      ...

    Završna stranica ankete -> klik na Сачувај
    Anketa 1 sačuvana.
```

---

## Izbor nastavnika/saradnika

Neke ankete imaju obavezni dropdown:

```text
Изаберите наставника/сарадника
```

Prva opcija je:

```text
-- --
```

i ona se preskače.

Skripta zatim bira dostupne nastavnike/saradnike redom. Pošto se nakon izbora nastavnika njegova opcija uklanja sa narednih listića, skripta vodi evidenciju već izabranih nastavnika i bira sledećeg dostupnog.

Primer:

```text
Listić 1 → Nastavnik A
Listić 2 → Nastavnik B
Listić 3 → Nastavnik C
...
```

Ne postoji konfiguracija za ručni izbor jednog konkretnog nastavnika — izbor se obavlja automatski redom.

---

## Tok jedne ankete

Skripta očekuje sledeći tok:

```text
Анкета
   │
   ▼
Попуни
   │
   ▼
Listić 1
   │
   ├── izbor nastavnika/saradnika
   ├── pitanja
   │
   ▼
Следећи листић / Даље
   │
   ▼
Listić 2
   │
   ├── izbor nastavnika/saradnika
   ├── pitanja
   │
   ▼
...
   │
   ▼
Završna stranica
   │
   ├── Сачувај
   └── Одустани
   │
   ▼
Sledeća anketa
```

Posebno je obrađena završna stranica: ona nema pitanja, već samo dugmad **Сачувај** i **Одустани**. Zato skripta prvo proverava da li postoji `Сачувај`, pre nego što pokuša da pronađe pitanja.

---

## Greške i debugging

Skripta koristi:

```python
HEADLESS = False
```

zato se browser vidi i lakše je pratiti gde je došlo do problema.

Ako dođe do greške, skripta pokušava da sačuva screenshot:

```text
anketa_error.png
```

To može pomoći pri utvrđivanju da li se struktura stranice promenila.

Ako FON promeni HTML stranice, posebno proveriti selektore za:

- `Попуни`
- `Следећи листић`
- `Даље`
- `Сачувај`
- `select[name='main:ddlNastavnik']`
- pitanja sa `td.bottomBorder`

---

## Bezbednost

**Nikada nemoj commitovati stvarnu lozinku u Git repozitorijum.**

Preporučuje se da se lokalni fajl sa kredencijalima ne šalje na GitHub.

Dodaj najmanje:

```gitignore
.venv/
__pycache__/
*.pyc
anketa_error.png
```

Ako želiš da projekat bude javno dostupan, još bolje je da kredencijale držiš u environment varijablama umesto direktno u Python fajlu.

Na primer:

```python
import os

USERNAME = os.environ["FON_USERNAME"]
PASSWORD = os.environ["FON_PASSWORD"]
```

Zatim u terminalu:

```bash
export FON_USERNAME="tvoje_korisnicko_ime"
export FON_PASSWORD="tvoja_lozinka"
```

---

## GitHub

Pre prvog commit-a proveri da u kodu nema stvarne lozinke:

```bash
git diff
```

i:

```bash
git status
```

Primer `.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
anketa_error.png
.env
```

Ako je lozinka ikada već commitovana na GitHub, samo brisanje iz novog commit-a nije dovoljno — lozinku treba promeniti.

---

## Napomena

Ovaj projekat je automatizacija korisničkog browser procesa. Koristi ga samo sa svojim nalogom i u skladu sa pravilima i uslovima korišćenja studentskog servisa.

Struktura FON studentskog servisa može se menjati bez najave, pa skripta nije garantovano kompatibilna sa budućim verzijama sajta.

---

## License

Ako želiš da projekat bude javno objavljen, izaberi odgovarajuću licencu za repozitorijum, npr. MIT, GPL-3.0 ili drugu licencu koja odgovara tvojoj nameni.
