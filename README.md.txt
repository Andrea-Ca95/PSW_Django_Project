# Appunto

**Appunto** è una web app sviluppata con Django per la gestione di servizi e appuntamenti presso uno studio professionale generico non medico.

Il progetto è stato realizzato per l’esame di **Progettazione e Sviluppo Web** e utilizza Django, Python, HTML, CSS, JavaScript e SQLite in ambiente locale.

---

## Descrizione generale

Appunto permette a utenti con ruoli differenti di consultare servizi, visualizzare appuntamenti e accedere ad aree riservate in base ai propri permessi.

La piattaforma è pensata per uno studio professionale generico, ad esempio uno studio di consulenza, uno studio amministrativo, uno studio tecnico o un centro servizi professionali.

---

## Tecnologie utilizzate

- Python
- Django
- HTML
- CSS custom
- JavaScript
- SQLite
- Django Authentication System
- Django Admin
- Git e GitHub

---

## Ruoli utente

L'applicazione prevede tre ruoli principali:

### Admin

L'admin può:

- accedere al pannello amministrativo Django;
- gestire categorie di servizi;
- gestire servizi;
- gestire profili cliente;
- gestire profili professionista;
- gestire appuntamenti;
- usare filtri, ricerca e azioni personalizzate nell'admin.

### Professionista

Il professionista può:

- accedere alla propria area riservata;
- visualizzare gli appuntamenti assegnati;
- vedere il cliente associato a ogni appuntamento;
- consultare lo stato delle prenotazioni.

### Cliente

Il cliente può:

- registrarsi;
- accedere alla propria area riservata;
- consultare i servizi disponibili;
- visualizzare le proprie prenotazioni.

---

## Funzionalità implementate

- Home pubblica con descrizione del progetto.
- Contatore visite tramite sessione.
- Lista pubblica dei servizi.
- Ricerca server-side sui servizi.
- Filtro per categoria.
- Paginazione della lista servizi.
- Pagina dettaglio servizio.
- Visualizzazione dei professionisti associati a un servizio.
- Sistema di login e logout Django.
- Registrazione cliente tramite form personalizzato.
- Gestione ruoli tramite gruppi e permessi Django.
- Area riservata cliente.
- Area riservata professionista.
- Pagina 403 personalizzata per accessi non autorizzati.
- Django Admin personalizzata con:
  - liste personalizzate;
  - filtri;
  - campi di ricerca;
  - fieldsets;
  - azioni sugli appuntamenti.
- Comando custom per creare dati demo iniziali.

---

## Modelli principali

### ServiceCategory

Rappresenta una categoria di servizi.

Esempi:

- Consulenza
- Documenti
- Supporto tecnico

### Service

Rappresenta un servizio prenotabile dello studio.

Contiene:

- nome;
- descrizione;
- categoria;
- durata;
- prezzo;
- stato attivo/non attivo.

### ProfessionalProfile

Rappresenta il profilo di un professionista.

Ogni professionista è collegato a un utente Django e può essere associato a più servizi.

### CustomerProfile

Rappresenta il profilo di un cliente.

Ogni cliente è collegato a un utente Django.

### Appointment

Rappresenta un appuntamento.

Contiene:

- cliente;
- professionista;
- servizio;
- data;
- orario;
- stato;
- note.

Gli stati previsti sono:

- In attesa
- Confermato
- Annullato
- Completato

---

## Validazioni e vincoli logici

Il progetto include alcune regole di validazione:

- non è possibile prenotare appuntamenti nel passato;
- un servizio disattivato non può essere prenotato;
- un professionista può essere assegnato solo a servizi che offre;
- un professionista non può avere due appuntamenti attivi nello stesso giorno e orario.

---

## Dati demo

Il progetto include un comando Django personalizzato per creare gruppi, utenti demo, servizi e appuntamenti iniziali.

Comando:

```bash
python manage.py seed_appunto