import streamlit as st
import pandas as pd

# Configurazione della pagina
st.set_page_config(page_title="Spese di Viaggio con Cassa Comune", page_icon="✈️", layout="centered")

# --- GESTIONE AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Area Riservata - Spese Viaggio")
    password = st.text_input("Inserisci la password per accedere:", type="password")
    
    if st.button("Accedi"):
        if password == "viaggio2026":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Password errata. Riprova.")
    st.stop()

# --- APPLICAZIONE PRINCIPALE ---
st.title("✈️ Gestione Cassa e Spese di Viaggio")

# Inizializzazione delle strutture dati nella sessione
if "partecipanti" not in st.session_state:
    st.session_state["partecipanti"] = ["Mario", "Anna", "Luca", "Sara"]

if "versamenti" not in st.session_state:
    st.session_state["versamenti"] = {p: 100.0 for p in st.session_state["partecipanti"]}

if "spese" not in st.session_state:
    st.session_state["spese"] = []

if "extra_versamenti" not in st.session_state:
    st.session_state["extra_versamenti"] = []

if "reset_vers_counter" not in st.session_state:
    st.session_state["reset_vers_counter"] = 0

# --- MENU LATERALE (BARRA SINISTRA) ---
st.sidebar.header("⚙️ Configurazione & Cassa")

# 1. Gestione Partecipanti tramite Form (evita la sparizione dei campi e gli errori di ricaricamento)
st.sidebar.subheader("👥 Partecipanti")

with st.sidebar.form("form_aggiungi_partecipante", clear_on_submit=True):
    nuovo_partecipante = st.text_input("Nome nuovo partecipante")
    btn_aggiungi = st.form_submit_button("Aggiungi")
    
    if btn_aggiungi:
        valore = nuovo_partecipante.strip()
        if valore:
            if valore not in st.session_state["partecipanti"]:
                st.session_state["partecipanti"].append(valore)
                if valore not in st.session_state["versamenti"]:
                    st.session_state["versamenti"][valore] = 0.0
                st.success(f"Aggiunto {valore}!")
                st.rerun()
            else:
                st.warning("Il partecipante esiste già.")
        else:
            st.warning("Inserisci un nome valido.")

# Rimozione partecipante (gestita in sicurezza)
lista_rimozione = [""] + st.session_state["partecipanti"]
partecipante_da_rimuovere = st.sidebar.selectbox("Rimuovi partecipante", lista_rimozione)
if st.sidebar.button("Rimuovi"):
    if partecipante_da_rimuovere and partecipante_da_rimuovere in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].remove(partecipante_da_rimuovere)
        if partecipante_da_rimuovere in st.session_state["versamenti"]:
            del st.session_state["versamenti"][partecipante_da_rimuovere]
        st.sidebar.success(f"Rimosso {partecipante_da_rimuovere}!")
        st.rerun()

st.sidebar.divider()

# 2. Gestione Versamenti in Cassa (Con chiavi dinamiche legate al contatore di reset)
st.sidebar.subheader("💰 Versamenti Cassa")
c = st.session_state["reset_vers_counter"]

partecipanti_validi = st.session_state["partecipanti"] if st.session_state["partecipanti"] else []

persona_versamento = st.sidebar.selectbox(
    "Partecipante", 
    [""] + partecipanti_validi, 
    key=f"sel_vers_{c}"
)
importo_versamento = st.sidebar.number_input(
    "Importo versato (€)", 
    min_value=0.0, 
    format="%.2f", 
    key=f"imp_vers_{c}"
)
tipo_versamento = st.sidebar.radio(
    "Tipo versamento", 
    ["Iniziale", "Incremento (Cassa in rosso)"], 
    key=f"tipo_vers_{c}"
)

if st.sidebar.button("Registra Versamento"):
    if persona_versamento and persona_versamento != "" and importo_versamento > 0:
        if persona_versamento not in st.session_state["versamenti"]:
            st.session_state["versamenti"][persona_versamento] = 0.0
        st.session_state["versamenti"][persona_versamento] += importo_versamento
        st.session_state["extra_versamenti"].append({
            "Partecipante": persona_versamento,
            "Importo": importo_versamento,
            "Tipo": tipo_versamento
        })
        st.sidebar.success(f"Registrati {importo_versamento}€ per {persona_versamento}!")
        st.session_state["reset_vers_counter"] += 1
        st.rerun()
    else:
        st.sidebar.warning("Seleziona un partecipante valido e un importo maggiore di zero.")

st.sidebar.divider()
if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- CONTROLLI PRELIMINARI ---
if not st.session_state["partecipanti"]:
    st.warning("⚠️ Non ci sono partecipanti configurati. Aggiungi almeno un partecipante dalla barra laterale per procedere.")
    st.stop()

# --- CALCOLI FINANZIARI GENERALI ---
totale_versato = sum(st.session_state["versamenti"].values())
totale_speso = sum(s.get("Importo", 0.0) for s in st.session_state["spese"])
cassa_rimanente = totale_versato - totale_speso

# Mostra metriche principali della cassa
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Cassa Totale Versata", f"{totale_versato:.2f} €")
col_m2.metric("Spese Totali", f"{totale_speso:.2f} €")
col_m3.metric("Disponibilità Cassa", f"{cassa_rimanente:.2f} €", delta=f"{cassa_rimanente:.2f} €")

if cassa_rimanente < 0:
    st.error("⚠️ **ATTENZIONE: La cassa comune è in rosso!** Effettua un incremento di cassa dalla barra laterale.")

st.divider()

# --- SEZIONE CENTRALE: REGISTRA SPESA ---
st.subheader("📝 Registra Spesa")

with st.form("form_spesa", clear_on_submit=True):
    descrizione = st.text_input("Descrizione spesa (es. Cena, Benzina, Biglietti museo...)")
    importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
    
    modalita_pagamento = st.radio("Chi ha pagato?", ["Cassa Comune", "Anticipato da un partecipante"])
    
    pagato_da = "Cassa Comune"
    if modalita_pagamento == "Anticipato da un partecipante":
        pagato_da = st.selectbox("Chi ha anticipato i soldi?", st.session_state["partecipanti"])
    
    st.write("Seleziona chi partecipa a questa spesa:")
    partecipanti_coinvolti = {}
    cols = st.columns(min(len(st.session_state["partecipanti"]), 4))
    for i, p in enumerate(st.session_state["partecipanti"]):
        with cols[i % len(cols)]:
            partecipanti_coinvolti[p] = st.checkbox(p, value=True, key=f"cb_{p}")
            
    submitted = st.form_submit_button("Registra Spesa")
    
    if submitted:
        coinvolti_list = [p for p, attivo in partecipanti_coinvolti.items() if attivo]
        if not descrizione:
            st.warning("Inserisci una descrizione per la spesa.")
        elif importo <= 0:
            st.warning("L'importo deve essere maggiore di zero.")
        elif not coinvolti_list:
            st.warning("Seleziona almeno un partecipante per questa spesa.")
        else:
            st.session_state["spese"].append({
                "Descrizione": descrizione,
                "Importo": importo,
                "Pagato da": pagato_da,
                "Coinvolti": ", ".join(coinvolti_list),
                "Num_Coinvolti": len(coinvolti_list)
            })
            st.success(f"Spesa '{descrizione}' registrata con successo!")
            st.rerun()

# --- SEZIONE: STORICO SPESE E BILANCI ---
st.divider()
st.subheader("📊 Riepilogo Movimenti e Saldi Individuali")

if len(st.session_state["spese"]) > 0:
    st.write("### Cronologia Spese")
    df_spese = pd.DataFrame(st.session_state["spese"])
    st.dataframe(df_spese, use_container_width=True)

# Calcolo dei saldi individuali in modo sicuro
quote_spese = {p: 0.0 for p in st.session_state["partecipanti"]}
crediti_anticipi = {p: 0.0 for p in st.session_state["partecipanti"]}

for spesa in st.session_state["spese"]:
    totale = spesa.get("Importo", 0.0)
    pagatore = spesa.get("Pagato da", spesa.get("Gestito da", "Cassa Comune"))
    n_coinvolti = spesa.get("Num_Coinvolti", 1)
    
    if pagatore != "Cassa Comune" and pagatore in crediti_anticipi:
        crediti_anticipi[pagatore] += totale
        
    coinvolti_str = spesa.get("Coinvolti", "")
    lista_coinvolti = [p.strip() for p in coinvolti_str.split(",") if p.strip()] if coinvolti_str else []
    
    if n_coinvolti == 0:
        n_coinvolti = max(len(lista_coinvolti), 1)
        
    quota_capite = totale / n_coinvolti
    for p in lista_coinvolti:
        if p in quote_spese:
            quote_spese[p] += quota_capite

st.write("### 💶 Situazione Contabile per Persona:")
col_res1, col_res2 = st.columns(2)
for i, p in enumerate(st.session_state["partecipanti"]):
    versato_p = st.session_state["versamenti"].get(p, 0.0)
    speso_p = quote_spese.get(p, 0.0)
    anticipato_p = crediti_anticipi.get(p, 0.0)
    
    saldo_p = (versato_p + anticipato_p) - speso_p
    
    col = col_res1 if i % 2 == 0 else col_res2
    with col:
        st.markdown(f"**👤 {p}**")
        st.text(f"Versato in cassa: {versato_p:.2f} €\nSpesa a carico:  {speso_p:.2f} €\nAnticipi tasca:  {anticipato_p:.2f} €")
        st.metric(label=f"Saldo di {p}", value=f"{saldo_p:.2f} €")
        st.markdown("---")

col_r1, col_r2 = st.columns(2)
with col_r1:
    if st.button("🔄 Pulisci memoria spese"):
        st.session_state["spese"] = []
        st.rerun()
with col_r2:
    if st.button("🗑️ Reset totale dati (Annulla tutto)"):
        st.session_state["partecipanti"] = ["Mario", "Anna", "Luca", "Sara"]
        st.session_state["versamenti"] = {p: 100.0 for p in st.session_state["partecipanti"]}
        st.session_state["spese"] = []
        st.session_state["extra_versamenti"] = []
        st.session_state["reset_vers_counter"] += 1
        st.rerun()
