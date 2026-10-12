import streamlit as st
import pandas as pd
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials

# Configurazione della pagina
st.set_page_config(page_title="Spese di Viaggio con Cassa Comune", page_icon="✈️", layout="centered")

# Nome del file di salvataggio automatico su Google Drive
DRIVE_FILENAME = "spese_viaggio_auto_backup.xlsx"

# --- FUNZIONI DI SINCRONIZZAZIONE AUTOMATICA CON GOOGLE DRIVE ---
def get_drive_service():
    """Ottiene il servizio Google Drive usando le credenziali attive della sessione Streamlit"""
    try:
        # Streamlit gestisce le credenziali OAuth dell'utente connesso
        if "google_credentials" in st.session_state:
            creds = Credentials(**st.session_state["google_credentials"])
            return build('drive', 'v3', credentials=creds)
    except Exception:
        pass
    return None

def carica_dati_da_drive():
    """Scarica i dati in automatico da Google Drive se il file esiste"""
    try:
        service = get_drive_service()
        if not service:
            return False
        
        # Cerca il file su Drive
        results = service.files().list(
            q=f"name='{DRIVE_FILENAME}' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        files = results.get('files', [])
        
        if files:
            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)
            xl = pd.ExcelFile(fh)
            
            # Legge Spese
            if 'Spese' in xl.sheet_names:
                df_spese = xl.parse('Spese').fillna("")
                st.session_state["spese"] = df_spese.to_dict(orient='records') if not df_spese.empty else []
            
            # Legge Versamenti
            versamenti_dict = {}
            if 'Versamenti' in xl.sheet_names:
                df_vers = xl.parse('Versamenti').fillna("")
                for _, row in df_vers.iterrows():
                    cols = list(row.index)
                    if len(cols) >= 2:
                        p = str(row.iloc[0]).strip()
                        if p and p.lower() != 'nan':
                            try:
                                v = float(str(row.iloc[1]).replace(',', '.'))
                            except:
                                v = 0.0
                            versamenti_dict[p] = round(v, 2)
            
            if versamenti_dict:
                st.session_state["versamenti"] = versamenti_dict
                st.session_state["partecipanti"] = list(versamenti_dict.keys())
                return True
    except Exception:
        pass
    return False

def salva_dati_su_drive():
    """Salva automaticamente i dati correnti su Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return
        
        # Crea il file Excel in memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_spese_exp = pd.DataFrame(st.session_state["spese"]) if st.session_state["spese"] else pd.DataFrame(columns=["Descrizione", "Importo", "Pagato da", "Coinvolti", "Num_Coinvolti"])
            df_spese_exp.to_excel(writer, sheet_name='Spese', index=False)
            
            df_vers_exp = pd.DataFrame(list(st.session_state["versamenti"].items()), columns=["Partecipante", "Versato"])
            df_vers_exp.to_excel(writer, sheet_name='Versamenti', index=False)
        
        excel_data = output.getvalue()
        media = MediaIoBaseUpload(io.BytesIO(excel_data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resumable=True)
        
        # Cerca se il file esiste già su Drive
        results = service.files().list(
            q=f"name='{DRIVE_FILENAME}' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        files = results.get('files', [])
        
        if files:
            # Aggiorna il file esistente
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Crea un nuovo file
            file_metadata = {'name': DRIVE_FILENAME}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    except Exception:
        pass

# --- GESTIONE AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Area Riservata - Spese Viaggio")
    password = st.text_input("Inserisci la password per accedere:", type="password", key="login_pass")
    
    if st.button("Accedi"):
        if password == "viaggio2026":
            st.session_state["authenticated"] = True
            # Prova a caricare i dati automatici da Drive subito dopo il login
            carica_dati_da_drive()
            st.rerun()
        else:
            st.error("Password errata. Riprova.")
    st.stop()

# --- APPLICAZIONE PRINCIPALE ---
st.title("✈️ Gestione Cassa e Spese di Viaggio")

# Inizializzazione delle strutture dati di base
if "partecipanti" not in st.session_state:
    st.session_state["partecipanti"] = []

if "versamenti" not in st.session_state:
    st.session_state["versamenti"] = {}

if "spese" not in st.session_state:
    st.session_state["spese"] = []

if "extra_versamenti" not in st.session_state:
    st.session_state["extra_versamenti"] = []

if "reset_vers_counter" not in st.session_state:
    st.session_state["reset_vers_counter"] = 0

# Al primo avvio autenticato, se i dati sono vuoti prova a recuperarli da Drive in automatico
if not st.session_state["partecipanti"] and "drive_checked" not in st.session_state:
    st.session_state["drive_checked"] = True
    if carica_dati_da_drive():
        st.rerun()

# --- MENU LATERALE (BARRA SINISTRA) ---
st.sidebar.header("⚙️ Configurazione & Cassa")

# 1. Gestione Partecipanti tramite Form
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
                salva_dati_su_drive()  # Salvataggio automatico
                st.success(f"Aggiunto {valore}!")
                st.rerun()
            else:
                st.warning("Il partecipante esiste già.")
        else:
            st.warning("Inserisci un nome valido.")

# Rimozione partecipante
lista_rimozione = [""] + st.session_state["partecipanti"]
partecipante_da_rimuovere = st.sidebar.selectbox("Rimuovi partecipante", lista_rimozione)
if st.sidebar.button("Rimuovi"):
    if partecipante_da_rimuovere and partecipante_da_rimuovere in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].remove(partecipante_da_rimuovere)
        if partecipante_da_rimuovere in st.session_state["versamenti"]:
            del st.session_state["versamenti"][partecipante_da_rimuovere]
        salva_dati_su_drive()  # Salvataggio automatico
        st.sidebar.success(f"Rimosso {partecipante_da_rimuovere}!")
        st.rerun()

st.sidebar.divider()

# 2. Gestione Versamenti in Cassa
st.sidebar.subheader("💰 Versamenti Cassa")
c = st.session_state["reset_vers_counter"]

partecipanti_validi = st.session_state["partecipanti"] if st.session_state["partecipanti"] else []

persona_versamento = st.sidebar.selectbox(
    "Partecipante", 
    [""] + partecipanti_validi, 
    key=f"sel_vers_{c}"
)
importo_versamento_str = st.sidebar.text_input(
    "Importo versato (€) (es. 50.00 o 12.50)", 
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

    if persona_versamento and persona_versamento != "" and importo_versamento > 0:
        if persona_versamento not in st.session_state["versamenti"]:
            st.session_state["versamenti"][persona_versamento] = 0.0
        st.session_state["versamenti"][persona_versamento] += importo_versamento
        st.session_state["extra_versamenti"].append({
            "Partecipante": persona_versamento,
            "Importo": round(importo_versamento, 2),
            "Tipo": tipo_versamento
        })
        salva_dati_su_drive()  # Salvataggio automatico
        st.sidebar.success(f"Registrati {importo_versamento:.2f}€ per {persona_versamento}!")
        st.session_state["reset_vers_counter"] += 1
        st.rerun()
    else:
        st.sidebar.warning("Seleziona un partecipante valido e inserisci un importo maggiore di zero.")

st.sidebar.divider()

# Sincronizzazione manuale di emergenza (opzionale)
if st.sidebar.button("🔄 Sincronizza con Google Drive"):
    if carica_dati_da_drive():
        st.sidebar.success("Dati sincronizzati!")
        st.rerun()
    else:
        st.sidebar.info("Nessun backup trovato su Drive o sincronizzazione non attiva.")

st.sidebar.divider()
if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- CONTROLLI PRELIMINARI E PULIZIA EMERGENZA ---
if not st.session_state["partecipanti"]:
    st.warning("⚠️ **Nessun partecipante trovato.** Aggiungi i partecipanti dalla barra laterale per iniziare.")
    if st.button("🔄 Cerca dati su Google Drive"):
        if carica_dati_da_drive():
            st.rerun()
    st.stop()

# --- CALCOLI FINANZIARI GENERALI ---
totale_versato = sum(st.session_state["versamenti"].values())
totale_speso = sum(float(s.get("Importo", 0.0)) for s in st.session_state["spese"])
cassa_rimanente = totale_versato - totale_speso

# Mostra metriche principali della cassa con 2 decimali fissi
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
    importo_spesa_str = st.text_input("Importo (€) (es. 25.00 o 12.50)", value="")
    
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
        try:
            importo_spesa = round(float(importo_spesa_str.replace(',', '.')), 2)
        except ValueError:
            importo_spesa = 0.0

        coinvolti_list = [p for p, attivo in partecipanti_coinvolti.items() if attivo]
        if not descrizione:
            st.warning("Inserisci una descrizione per la spesa.")
        elif importo_spesa <= 0:
            st.warning("L'importo deve essere maggiore di zero.")
        elif not coinvolti_list:
            st.warning("Seleziona almeno un partecipante per questa spesa.")
        else:
            st.session_state["spese"].append({
                "Descrizione": descrizione,
                "Importo": importo_spesa,
                "Pagato da": pagato_da,
                "Coinvolti": ", ".join(coinvolti_list),
                "Num_Coinvolti": len(coinvolti_list)
            })
            salva_dati_su_drive()  # Salvataggio automatico
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
    totale = float(spesa.get("Importo", 0.0))
    pagatore = spesa.get("Pagato da", "Cassa Comune")
    n_coinvolti = int(spesa.get("Num_Coinvolti", 1))
    
    if pagatore != "Cassa Comune" and pagatore in crediti_anticipi:
        crediti_anticipi[pagatore] += totale
        
    coinvolti_str = str(spesa.get("Coinvolti", ""))
    lista_coinvolti = [p.strip() for p in coinvolti_str.split(",") if p.strip()]
    
    if n_coinvolti == 0:
        n_coinvolti = max(len(lista_coinvolti), 1)
        
    quota_capite = totale / n_coinvolti
    for p in lista_coinvolti:
        if p in quote_spese:
            quote_spese[p] += quota_capite

st.write("### 💶 Situazione Contabile per Persona:")
col_res1, col_res2 = st.columns(2)
for i, p in enumerate(st.session_state["partecipanti"]):
    versato_p = round(st.session_state["versamenti"].get(p, 0.0), 2)
    speso_p = round(quote_spese.get(p, 0.0), 2)
    anticipato_p = round(crediti_anticipi.get(p, 0.0), 2)
    
    saldo_p = round((versato_p + anticipato_p) - speso_p, 2)
    
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
        salva_dati_su_drive()
        st.rerun()
with col_r2:
    if st.button("🗑️ Reset totale dati (Annulla tutto)"):
        st.session_state["partecipanti"] = []
        st.session_state["versamenti"] = {}
        st.session_state["spese"] = []
        st.session_state["extra_versamenti"] = []
        st.session_state["reset_vers_counter"] += 1
        salva_dati_su_drive()
        st.rerun()
