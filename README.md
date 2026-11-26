# KinoBilietas

Kino teatro bilietų pardavimo internetu sistema (VILNIUS TECH, ISPK kompleksinis projektas, PRIfs-23).

## Technologijos

| Dalis | Technologija |
|---|---|
| Serveris | Python 3.12, Django 5, Django REST Framework, simplejwt |
| Duomenų bazė | PostgreSQL 16 (vietiniam kūrimui SQLite) |
| Klientas | React 18, Vite, React Router |
| Diegimas | Docker Compose: Nginx, Gunicorn, PostgreSQL |
| Testai | pytest-django |

## Paleidimas su Docker (NFR-08)

```bash
cp .env.example .env      # pakeiskite slaptažodžius
docker compose up --build
```

Atidaryti: http://localhost:8080. Migracijos ir demonstraciniai duomenys sukuriami automatiškai.

## Paleidimas be Docker (kūrimui)

```bash
# 1 terminalas: serveris
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt   # Linux/macOS: .venv/bin/pip
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# 2 terminalas: klientas
cd frontend
npm install
npm run dev
```

Atidaryti: http://localhost:5173. Be `POSTGRES_HOST` kintamojo naudojama SQLite.

## Demonstraciniai duomenys

`python manage.py seed_demo` sukuria 3 sales, 6 filmus ir seansus 14 dienų nuo šiandien.
Iš naujo: `python manage.py seed_demo --is-naujo`.

| Rolė | El. paštas | Slaptažodis |
|---|---|---|
| Administratorius | admin@kinobilietas.lt | `DEMO_ADMIN_PASSWORD` (numatytasis Admin2026) |
| Klientas | ona@pavyzdys.lt | Kinas2026 |

## Struktūra (Koudo-Jodano architektūra)

| Komponentas | Vieta |
|---|---|
| K1 Žiūrovų sąsaja, K2 Administravimo sąsaja | `frontend/src` |
| K3 REST API | `backend/*/views.py`, `backend/*/urls.py` (`/api/v1/`) |
| K4 Autentifikacijos komponentas | `backend/naudotojai` |
| K5 Repertuaro komponentas | `backend/repertuaras` |
| K6 Salių komponentas | `backend/sales` |
| K7 Duomenų valdymo komponentas | Django ORM, migracijos |

API dokumentacija (OpenAPI): `/api/v1/docs/`.

## 1 sprinto įgyvendinimas

| Istorija | Kas veikia |
|---|---|
| NI-01 | Repertuaras pagal datą (šiandien +13 d.), tik būsimi suplanuoti seansai |
| NI-02 | Filtrai pagal žanrą ir salę, artimiausios datos pasiūlymas |
| NI-03 | Filmo puslapis su aprašymu, trukme, cenzu ir 14 d. seansais |
| NI-04 | Interaktyvi salės schema, iki 10 vietų, preliminari kaina |
| NI-05 | Filmų kūrimas, redagavimas ir šalinimas (administratorius) |
| NI-06 | Seansų kūrimas su kainomis, pabaigos skaičiavimas, persidengimo tikrinimas, atšaukimas |
| NI-07 | Salių schemų redaktorius su vietų tipais ir talpa |
| NI-08 | Registracija, prisijungimas (užrakinimas po 5 bandymų), atsijungimas, rolės |

## Testai

```bash
cd backend
python -m pytest -q
```

Automatiniai testai (pytest-django) tikrina TC-01–TC-05 ir TC-08–TC-19.

## Šakos

- `main`: stabili versija.
- `dev`: kūrimo šaka, į ją suliejamos `feature/NI-xx` šakos.
- `feature/NI-xx-...`: viena naudotojo istorija.
