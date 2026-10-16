import streamlit as st
import pandas as pd
import json
import urllib.parse
import hashlib

# Configurazione della pagina
st.set_page_config(page_title="Spese di Viaggio con Cassa Comune", page_icon="✈️", layout="centered")

# --- GESTIONE AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Area Riservata - Spese Viaggio")
    password = st.text_input("Inserisci la password per accedere:", type="password", key="login_pass")
    
    if st.button("Accedi"):
        if password == "viaggio2026":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Password errata. Riprova.")
    st.stop()

# --- APPLICAZIONE PRINCIPALE ---
st.title("✈️ Gestione Cassa e Spese di Viaggio (per Coppie)")

# Inizializzazione con le 4 coppie fisse
COPPIE_FISSE = ["ANDREA e CINZIA", "MELO e LAURA", "SANDRO e FULVIA", "MACIO e SIMONA"]

if "partecipanti" not in st.session_state or not st.session_state["partecipanti"]:
    st.session_state["partecipanti"] = list(COPPIE_FISSE)

if "spese" not in st.session_state:
    st.session_state["spese"] = []

if "extra_versamenti" not in st.session_state:
    st.session_state["extra_versamenti"] = [
        {"Partecipante": p, "Importo": 200.0, "Tipo": "Iniziale (Default)"} for p in COPPIE_FISSE
    ]

if "reset_vers_counter" not in st.session_state:
    st.session_state["reset_vers_counter"] = 0

if "backup_refresh_id" not in st.session_state:
    st.session_state["backup_refresh_id"] = 0

# --- FUNZIONE PER CALCOLARE I VERSAMENTI TOTALI PER COPPIA ---
def calcola_versamenti():
    versamenti = {p: 0.0 for p in st.session_state["partecipanti"]}
    for v in st.session_state["extra_versamenti"]:
        p = v["Partecipante"]
        if p in versamenti:
            versamenti[p] += float(v["Importo"])
    return versamenti

st_versamenti = calcola_versamenti()

# --- MENU LATERALE (BARRA SINISTRA) ---
st.sidebar.header("⚙️ Configurazione & Cassa")

# 1. Gestione Coppie
st.sidebar.subheader("👥 Coppie Partecipanti")

with st.sidebar.form("form_aggiungi_coppia", clear_on_submit=True):
    nuova_coppia = st.text_input("Nome nuova coppia (es. Mario e Anna)")
    btn_aggiungi = st.form_submit_button("Aggiungi Coppia")
    
    if btn_aggiungi:
        valore = nuova_coppia.strip()
        if valore:
            if valore not in st.session_state["partecipanti"]:
                st.session_state["partecipanti"].append(valore)
                st.session_state["extra_versamenti"].append({
                    "Partecipante": valore,
                    "Importo": 400.0,
                    "Tipo": "Iniziale (Default)"
                })
                st.success(f"Aggiunta coppia {valore}!")
                st.rerun()
            else:
                st.warning("Questa coppia esiste già.")
        else:
            st.warning("Inserisci un nome valido.")

# Rimozione coppia
lista_rimozione = [""] + st.session_state["partecipanti"]
coppia_da_rimuovere = st.sidebar.selectbox("Rimuovi coppia", lista_rimozione)
if st.sidebar.button("Rimuovi Coppia"):
    if coppia_da_rimuovere and coppia_da_rimuovere in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].remove(coppia_da_rimuovere)
        st.session_state["extra_versamenti"] = [v for v in st.session_state["extra_versamenti"] if v["Partecipante"] != coppia_da_rimuovere]
        st.sidebar.success(f"Rimossa coppia {coppia_da_rimuovere}!")
        st.rerun()

st.sidebar.divider()

# 2. Gestione Versamenti in Cassa
st.sidebar.subheader("💰 Versamenti Cassa")
c = st.session_state["reset_vers_counter"]

coppie_valide = st.session_state["partecipanti"] if st.session_state["partecipanti"] else []

persona_versamento = st.sidebar.selectbox(
    "Coppia", 
    [""] + coppie_valide, 
    key=f"sel_vers_{c}"
)
importo_versamento_str = st.sidebar.text_input(
    "Importo versato (€) (es. 50.00 o 100.00)", 
    value="", 
    key=f"imp_vers_{c}"
)
tipo_versamento = st.sidebar.radio(
    "Tipo versamento", 
    ["Iniziale", "Incremento (Cassa in rosso)"], 
    key=f"tipo_vers_{c}"
)

if st.sidebar.button("Registra Versamento"):
    try:
        importo_versamento = float(importo_versamento_str.replace(',', '.'))
    except ValueError:
        importo_versamento = 0.0

    if persona_versamento and persona_versamento != "" and importo_versamento != 0:
        st.session_state["extra_versamenti"].append({
            "Partecipante": persona_versamento,
            "Importo": round(importo_versamento, 2),
            "Tipo": tipo_versamento
        })
        st.sidebar.success(f"Registrati {importo_versamento:.2f}€ per {persona_versamento}!")
        st.session_state["reset_vers_counter"] += 1
        st.rerun()
    else:
        st.sidebar.warning("Seleziona una coppia valida e inserisci un importo diverso da zero.")

# --- SEZIONE: MODIFICA O ELIMINA QUALSIASI VERSAMENTO ---
if len(st.session_state["extra_versamenti"]) > 0:
    with st.sidebar.expander("✏️ Modifica o Elimina Versamento"):
        opzioni_vers = [f"{i}. {v['Partecipante']} - {v['Importo']} € ({v['Tipo']})" 
                        for i, v in enumerate(st.session_state["extra_versamenti"])]
        
        vers_scelto = st.selectbox("Seleziona quota/versamento:", [""] + opzioni_vers, key="sel_mod_vers")
        
        if vers_scelto:
            idx_v = int(vers_scelto.split(".")[0])
            v_corr = st.session_state["extra_versamenti"][idx_v]
            
            nuovo_imp_v_str = st.text_input("Importo (€) (Metti 0 se non partecipa)", value=str(v_corr["Importo"]), key=f"mod_v_imp_{idx_v}")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button("💾 Aggiorna", key=f"btn_upd_v_{idx_v}"):
                    try:
                        nuovo_imp_v = round(float(nuovo_imp_v_str.replace(',', '.')), 2)
                    except ValueError:
                        nuovo_imp_v = 0.0
                    
                    st.session_state["extra_versamenti"][idx_v]["Importo"] = nuovo_imp_v
                    st.sidebar.success("Quota aggiornata!")
                    st.rerun()
            with col_v2:
                if st.button("🗑️ Elimina", key=f"btn_del_v_{idx_v}"):
                    st.session_state["extra_versamenti"].pop(idx_v)
                    st.sidebar.success("Voce eliminata!")
                    st.rerun()

st.sidebar.divider()

# 3. Backup & Ripristino Testuale con Invio Diretto su WhatsApp
st.sidebar.subheader("📋 Backup via WhatsApp")

if st.sidebar.button("🔄 Aggiorna Dati Backup"):
    st.session_state["backup_refresh_id"] += 1
    st.rerun()

dati_correnti = {
    "partecipanti": st.session_state["partecipanti"],
    "spese": st.session_state["spese"],
    "extra_versamenti": st.session_state["extra_versamenti"]
}
codice_backup = json.dumps(dati_correnti, ensure_ascii=False)

# Link WhatsApp dedicato
url_wa_backup = "https://wa.me/?text=" + urllib.parse.quote("BACKUP_CASSA_VIAGGIO:\n" + codice_backup)
st.sidebar.markdown(f'[![Invia Backup su WhatsApp](https://img.shields.io/badge/Invia_Backup_su-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)]({url_wa_backup})')

st.sidebar.write("Oppure incolla qui sotto il codice salvato per ripristinare:")
codice_da_ripristinare = st.sidebar.text_area("Incolla qui per ripristinare:", value="", height=80, key="txt_ripristino")

if st.sidebar.button("🔄 Ripristina"):
    testo_grezzo = codice_da_ripristinare.strip()
    
    # Rimuove l'intestazione "BACKUP_CASSA_VIAGGIO:" se presente nel testo incollato
    if "BACKUP_CASSA_VIAGGIO:" in testo_grezzo:
        testo_grezzo = testo_grezzo.split("BACKUP_CASSA_VIAGGIO:")[-1].strip()
        
    if testo_grezzo:
        try:
            dati_caricati = json.loads(testo_grezzo)
            st.session_state["partecipanti"] = dati_caricati.get("partecipanti", list(COPPIE_FISSE))
            st.session_state["spese"] = dati_caricati.get("spese", [])
            st.session_state["extra_versamenti"] = dati_caricati.get("extra_versamenti", [])
            st.sidebar.success("Ripristinato con successo!")
            st.rerun()
        except Exception:
            st.sidebar.error("Codice di ripristino errato o incompleto.")
    else:
        st.sidebar.warning("Incolla prima un codice di backup valido.")

st.sidebar.divider()
if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

st_versamenti = calcola_versamenti()

# --- CALCOLI FINANZIARI GENERALI ---
totale_versato = sum(st_versamenti.values())
totale_speso = sum(float(s.get("Importo", 0.0)) for s in st.session_state["spese"])
cassa_rimanente = totale_versato - totale_speso

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Cassa Totale Versata", f"{
