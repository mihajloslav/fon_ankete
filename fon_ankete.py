#!/usr/bin/env python3
"""
Automatsko popunjavanje anketa na student.fon.bg.ac.rs.

VAŽNO:
- Ne stavljaj stvarnu lozinku u fajl koji ćeš slati drugima.
- Promeni samo vrednosti u CONFIG delu.
- Skripta koristi Playwright i otvara Chromium u vidljivom režimu (HEADLESS=False).
"""

import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================
# CONFIG — OVDE MENJAŠ VREDNOSTI
# ============================================================

USERNAME = "OVDE_UNESI_KORISNICKO_IME"
PASSWORD = "OVDE_UNESI_LOZINKU"


# Prva tri pitanja
Q1_ANSWER = "буџетски"
Q2_ANSWER = "8,51-9,50"
Q3_ANSWER = "између 30% и 70%"

# Sva ostala pitanja
DEFAULT_ANSWER = "6-Не могу да проценим"

BASE_URL = "https://student.fon.bg.ac.rs/"
HEADLESS = False
SLOW_MO_MS = 10



# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================

def click_radio_by_label(question, answer_text: str) -> bool:
    """
    U okviru jednog pitanja klikne radio dugme čiji label sadrži
    zadati tekst.
    """
    label = question.locator("label").filter(
        has_text=re.compile(re.escape(answer_text), re.IGNORECASE)
    ).first

    if label.count() == 0:
        return False

    label.click()
    return True


def select_teacher(page, selected_teachers: set[str]) -> None:
    """
    Izaberi nastavnika/saradnika na trenutnom listiću.

    Bira PRVU STVARNU opciju koja još
    nije izabrana na prethodnim listićima ove ankete. Placeholder
    "-- --" se uvek preskače.

    Ovo je bitno zato što FON na sledećem listiću uklanja nastavnika
    koji je već izabran, pa se lista postepeno skraćuje:

        listić 1 -> prvi nastavnik
        listić 2 -> sledeći preostali nastavnik
        listić 3 -> sledeći preostali nastavnik
        ...
    """
    teacher_select = page.locator("select[name='main:ddlNastavnik']")

    if teacher_select.count() == 0 or not teacher_select.first.is_visible():
        return

    select = teacher_select.first
    options = select.locator("option")
    option_count = options.count()

    if option_count < 2:
        raise RuntimeError(
            "Pronađen je dropdown za nastavnika/saradnika, "
            "ali nema nijedne stvarne opcije za izbor."
        )

    # Idi redom kroz preostale nastavnike.
    # Prva opcija je placeholder "-- --" i namerno je NE biramo.
    selected_index = None
    selected_name = None
    selected_value = None

    for i in range(option_count):
        option = options.nth(i)
        value = option.get_attribute("value") or ""
        name = option.inner_text().strip()

        # Preskoči placeholder i sve što je već izabrano.
        if not value or not name or name == "-- --":
            continue
        if name in selected_teachers:
            continue

        selected_index = i
        selected_name = name
        selected_value = value
        break

    if selected_index is None:
        raise RuntimeError(
            "Na dropdown-u nema više neizabranih nastavnika/saradnika. "
            "Placeholder '-- --' je preskočen."
        )

    # Biramo po value atributu, a ne po indexu, jer se lista na
    # svakom sledećem listiću menja.
    select.select_option(value=selected_value)
    selected_teachers.add(selected_name)

    # Kratko čekanje da browser obradi change event pre nastavka.
    page.wait_for_timeout(150)
    print(f"      nastavnik/saradnik: {selected_name}")


def fill_current_sheet(page) -> None:
    """
    Popunjava trenutno otvoreni anketni listić:
      pitanje 1 -> Q1_ANSWER
      pitanje 2 -> Q2_ANSWER
      pitanje 3 -> Q3_ANSWER
      ostala -> DEFAULT_ANSWER
    """
    questions = page.locator("td.bottomBorder")
    count = questions.count()

    if count == 0:
        raise RuntimeError("Nisam pronašao pitanja na trenutnom listiću.")

    print(f"      pronađeno pitanja: {count}")

    for i in range(count):
        question = questions.nth(i)

        if i == 0:
            answer = Q1_ANSWER
        elif i == 1:
            answer = Q2_ANSWER
        elif i == 2:
            answer = Q3_ANSWER
        else:
            answer = DEFAULT_ANSWER

        # Samo radio pitanja koja imaju zadati odgovor.
        if question.locator("input[type='radio']").count() == 0:
            print(f"      pitanje {i + 1}: nema radio dugmad -> preskačem")
            continue

        if click_radio_by_label(question, answer):
            print(f"      pitanje {i + 1}: {answer}")
        else:
            # Ne nastavljamo tiho ako struktura ankete nije ono što očekujemo.
            question_text = question.inner_text().strip().replace("\n", " ")
            print(
                f"      UPOZORENJE: odgovor nije pronađen za pitanje "
                f"{i + 1}: {question_text[:150]}"
            )


def click_next_sheet(page) -> bool:
    """
    Klikne 'Следећи листић' ili 'Даље'.
    Vraća True ako je kliknut neki od tih dugmića.
    """
    for button_text in ("Следећи листић", "Даље"):
        button = page.get_by_role(
            "button",
            name=re.compile(re.escape(button_text), re.IGNORECASE)
        )

        if button.count() > 0 and button.first.is_visible():
            button.first.click()
            page.wait_for_load_state("domcontentloaded")
            return True

        # Neke stare JSF stranice mogu input[type=submit] da izlože
        # drugačije od get_by_role("button").
        submit = page.locator(
            f"input[type='submit'][value*='{button_text}']"
        )

        if submit.count() > 0 and submit.first.is_visible():
            submit.first.click()
            page.wait_for_load_state("domcontentloaded")
            return True

    return False


def fill_one_survey(page, survey_number: int) -> None:
    """
    Popunjava jedan red ankete, prolazi kroz sve njene listiće,
    a zatim klikće 'Сачувај'.
    """
    print(f"\n[{survey_number}] Otvaram anketu...")

    # Klik na prvo trenutno dostupno dugme "Попуни".
    fill_buttons = page.locator(
        "input[type='submit'][value*='Попуни']"
    )

    if fill_buttons.count() == 0:
        raise RuntimeError("Nema više dostupnih anketa sa dugmetom 'Попуни'.")

    fill_buttons.first.click()
    page.wait_for_load_state("domcontentloaded")

    sheet_number = 1
    selected_teachers: set[str] = set()

    while True:
        print(f"    Listić {sheet_number}:")

        # VAŽNO:
        # Nakon klika na "Даље" sa poslednjeg pravog listića,
        # FON otvara završnu stranicu koja VIŠE NEMA PITANJA.
        # Na toj stranici postoje samo dugmad "Сачувај" i "Одустани".
        # Zato "Сачувај" moramo proveriti PRE pokušaja da pronađemo pitanja.
        save_button = page.locator(
            "input[type='submit'][value='Сачувај']"
        )

        if save_button.count() > 0 and save_button.first.is_visible():
            print("    Završna stranica ankete -> klik na Сачувај")
            save_button.first.click()
            page.wait_for_load_state("domcontentloaded")
            break

        # Ako nema završne stranice, trenutno smo na stranici
        # koja sadrži pitanja. Neke ankete imaju obavezan dropdown
        # za nastavnika/saradnika na SVAKOM listiću, pa ga prvo popuni.
        select_teacher(page, selected_teachers)
        fill_current_sheet(page)

        # Nakon popunjavanja pokušaj da pređeš na sledeći listić.
        if not click_next_sheet(page):
            raise RuntimeError(
                "Nisam pronašao ni 'Следећи листић' ni 'Даље', "
                "a nije pronađena ni završna stranica sa 'Сачувај'. "
                "Struktura stranice se verovatno promenila."
            )

        sheet_number += 1

    print(f"    Anketa {survey_number} sačuvana.")


# ============================================================
# MAIN
# ============================================================

def main():
    if USERNAME.startswith("OVDE_") or PASSWORD.startswith("OVDE_"):
        raise SystemExit(
            "Prvo upiši USERNAME i PASSWORD u CONFIG delu skripte."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO_MS,
        )

        context = browser.new_context()
        page = context.new_page()

        try:
            # ------------------------------------------------
            # 1. LOGIN
            # ------------------------------------------------
            print("Otvaram studentski servis...")
            page.goto(BASE_URL, wait_until="domcontentloaded")

            print("Prijavljujem se...")
            page.locator("#j_username").fill(USERNAME)
            page.locator("#j_password").fill(PASSWORD)
            page.locator("#login").click()

            page.wait_for_load_state("domcontentloaded")

            # Provera da li smo stvarno ulogovani.
            page.get_by_text("Анкета", exact=True).first.wait_for(
                state="visible",
                timeout=15000
            )

            print("Uspešno prijavljen.")

            # ------------------------------------------------
            # 2. OTVORI ANKETU
            # ------------------------------------------------
            print("Otvaram 'Анкета'...")
            page.get_by_text("Анкета", exact=True).first.click()
            page.wait_for_load_state("domcontentloaded")

            # ------------------------------------------------
            # 3. POPUNJAVAJ SVE DOSTUPNE ANKETE
            # ------------------------------------------------
            survey_number = 1

            while True:
                available = page.locator(
                    "input[type='submit'][value*='Попуни']"
                )

                if available.count() == 0:
                    break

                fill_one_survey(page, survey_number)
                survey_number += 1

                # Nakon čuvanja treba da smo nazad na tabeli.
                page.wait_for_timeout(300)

            print("\n========================================")
            print("ZAVRŠENO")
            print(f"Popunjeno anketa: {survey_number - 1}")
            print("========================================")

            # Ostavi browser otvoren kratko da se vidi rezultat.
            page.wait_for_timeout(2000)

        except PlaywrightTimeoutError as e:
            print("\nGREŠKA: stranica nije odgovorila očekivano.")
            print(e)
            page.screenshot(path="anketa_error.png", full_page=True)
            print("Sačuvan screenshot: anketa_error.png")
            raise

        except Exception as e:
            print("\nGREŠKA:")
            print(e)
            page.screenshot(path="anketa_error.png", full_page=True)
            print("Sačuvan screenshot: anketa_error.png")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    main()
