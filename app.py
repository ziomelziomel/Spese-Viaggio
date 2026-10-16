import streamlit as st
import pandas as pd
import json
import urllib.parse
import hashlib
from datetime import datetime

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
                st.warning("Questa coppia existe già.")
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

# Intestazione con Data e Ora correnti
ora_attuale = datetime.now().strftime("%d/%m/%Y %H:%M")
intestazione_wa = f"BACKUP_CASSA_VIAGGIO ({ora_attuale}):\n"

# Link WhatsApp dedicato con data e ora
url_wa_backup = "https://wa.me/?text=" + urllib.parse.quote(intestazione_wa + codice_backup)
st.sidebar.markdown(f'[![Invia Backup su WhatsApp](https://img.shields.io/badge/Invia_Backup_su-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)]({url_wa_backup})')

st.sidebar.write("Oppure incolla qui sotto il codice salvato per ripristinare:")
codice_da_ripristinare = st.sidebar.text_area("Incolla qui per ripristinare:", value="", height=80, key="txt_ripristino")

if st.sidebar.button("🔄 Ripristina"):
    testo_grezzo = codice_da_ripristinare.strip()
    
    # Rimuove qualsiasi intestazione che inizia con BACKUP_CASSA_VIAGGIO
    if "BACKUP_CASSA_VIAGGIO" in testo_grezzo and "{" in testo_grezzo:
        pos_json = testo_grezzo.find("{")
        testo_grezzo = testo_grezzo[pos_json:].strip()
        
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
    
    modalita_pagamento = st.radio("Chi ha pagato?", ["Cassa Comune", "Anticipato da una coppia"])
    
    pagato_da = "Cassa Comune"
    if modalita_pagamento == "Anticipato da una coppia":
        pagato_da = st.selectbox("Quale coppia ha anticipato i soldi?", st.session_state["partecipanti"])
    
    st.write("Seleziona quali coppie partecipano a questa spesa:")
    coppie_coinvolte = {}
    cols = st.columns(min(len(st.session_state["partecipanti"]), 2))
    for i, p in enumerate(st.session_state["partecipanti"]):
        with cols[i % len(cols)]:
            coppie_coinvolte[p] = st.checkbox(p, value=True, key=f"cb_{p}")
            
    submitted = st.form_submit_button("Registra Spesa")
    
    if submitted:
        try:
            importo_spesa = round(float(importo_spesa_str.replace(',', '.')), 2)
        except ValueError:
            importo_spesa = 0.0

        coinvolti_list = [p for p, attivo in coppie_coinvolte.items() if attivo]
        if not descrizione:
            st.warning("Inserisci una descrizione per la spesa.")
        elif importo_spesa <= 0:
            st.warning("L'importo deve essere maggiore di zero.")
        elif not coinvolti_list:
            st.warning("Seleziona almeno una coppia per questa spesa.")
        else:
            st.session_state["spese"].append({
                "Descrizione": descrizione,
                "Importo": importo_spesa,
                "Pagato da": pagato_da,
                "Coppie Coinvolte": ", ".join(coinvolti_list),
                "Nr Coppie": len(coinvolti_list)
            })
            st.success(f"Spesa '{descrizione}' registrata con successo!")
            st.rerun()

# --- SEZIONE: STORICO SPESE E BILANCI ---
st.divider()
st.subheader("📊 Riepilogo Movimenti e Saldi per Coppia")

quote_spese = {p: 0.0 for p in st.session_state["partecipanti"]}
crediti_anticipi = {p: 0.0 for p in st.session_state["partecipanti"]}

if len(st.session_state["spese"]) > 0:
    st.write("### Cronologia Spese")
    
    spese_formattate = []
    for s in st.session_state["spese"]:
        imp = float(s.get("Importo", 0.0))
        c_coinvolte = s.get("Coppie Coinvolte", s.get("Coinvolti", ""))
        nr_c = s.get("Nr Coppie", s.get("Num_Coinvolti", len(str(c_coinvolte).split(",")) if c_coinvolte else 1))
        
        stringa_coinvolti_formattata = f"[{nr_c}] {c_coinvolte}"
        
        spese_formattate.append({
            "Descrizione": s.get("Descrizione", ""),
            "Importo (€)": f"{imp:.2f} €",
            "Pagato da": s.get("Pagato da", "Cassa Comune"),
            "N. Coppie / Coinvolti": stringa_coinvolti_formattata
        })
    
    df_spese = pd.DataFrame(spese_formattate)
    st.dataframe(df_spese, use_container_width=True, hide_index=True)

    # --- MODIFICA O ELIMINA SPESA ESISTENTE ---
    with st.expander("✏️ Modifica o Elimina una Spesa Registrata"):
        opzioni_spese = [f"{i}. {s['Descrizione']} - {float(s['Importo']):.2f} € (Pagato da: {s['Pagato da']})" 
                           for i, s in enumerate(st.session_state["spese"])]
        
        spesa_scelta = st.selectbox("Seleziona la spesa da modificare o eliminare:", [""] + opzioni_spese, key="sel_mod_spesa")
        
        if spesa_scelta:
            idx_mod = int(spesa_scelta.split(".")[0])
            spesa_corrente = st.session_state["spese"][idx_mod]
            
            with st.form("form_modifica_spesa"):
                st.write(f"**Modifica spesa #{idx_mod}:**")
                nuova_desc = st.text_input("Nuova Descrizione", value=spesa_corrente.get("Descrizione", ""))
                nuovo_imp_str = st.text_input("Nuovo Importo (€)", value=str(spesa_corrente.get("Importo", 0.0)))
                
                opzioni_paganti = ["Cassa Comune"] + st.session_state["partecipanti"]
                pagatore_corrente = spesa_corrente.get("Pagato da", "Cassa Comune")
                idx_pagatore = opzioni_paganti.index(pagatore_corrente) if pagatore_corrente in opzioni_paganti else 0
                
                nuovo_pagato_da = st.selectbox("Chi ha pagato?", opzioni_paganti, index=idx_pagatore)
                
                st.write("Coppie partecipanti:")
                stringa_coinvolti = spesa_corrente.get("Coppie Coinvolte", spesa_corrente.get("Coinvolti", ""))
                coinvolti_attuali = [p.strip() for p in stringa_coinvolti.split(",") if p.strip()]
                
                nuovi_coinvolti_dict = {}
                cols_m = st.columns(2)
                for i, p in enumerate(st.session_state["partecipanti"]):
                    is_checked = p in coinvolti_attuali
                    with cols_m[i % 2]:
                        nuovi_coinvolti_dict[p] = st.checkbox(p, value=is_checked, key=f"mod_cb_{idx_mod}_{p}")
                
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    btn_salva_mod = st.form_submit_button("💾 Salva Modifiche")
                with col_sub2:
                    btn_elimina_mod = st.form_submit_button("🗑️ Elimina Questa Spesa")
                
                if btn_salva_mod:
                    try:
                        imp_val = round(float(nuovo_imp_str.replace(',', '.')), 2)
                    except ValueError:
                        imp_val = 0.0
                    
                    lista_c_nuova = [p for p, attivo in nuovi_coinvolti_dict.items() if attivo]
                    
                    if not nuova_desc:
                        st.warning("Inserisci una descrizione.")
                    elif imp_val <= 0:
                        st.warning("L'importo deve essere maggiore di zero.")
                    elif not lista_c_nuova:
                        st.warning("Seleziona almeno una coppia.")
                    else:
                        st.session_state["spese"][idx_mod] = {
                            "Descrizione": nuova_desc,
                            "Importo": imp_val,
                            "Pagato da": nuovo_pagato_da,
                            "Coppie Coinvolte": ", ".join(lista_c_nuova),
                            "Nr Coppie": len(lista_c_nuova)
                        }
                        st.success("Spesa modificata con successo!")
                        st.rerun()
                
                if btn_elimina_mod:
                    spesa_rimossa = st.session_state["spese"].pop(idx_mod)
                    st.success(f"Spesa '{spesa_rimossa.get('Descrizione', '')}' eliminata!")
                    st.rerun()

# Calcolo dei saldi
for spesa in st.session_state["spese"]:
    totale = float(spesa.get("Importo", 0.0))
    pagatore = spesa.get("Pagato da", "Cassa Comune")
    
    c_str = spesa.get("Coppie Coinvolte", spesa.get("Coinvolti", ""))
    lista_coinvolti = [p.strip() for p in str(c_str).split(",") if p.strip()]
    n_coinvolti = int(spesa.get("Nr Coppie", spesa.get("Num_Coinvolti", len(lista_coinvolti))))
    if n_coinvolti == 0:
        n_coinvolti = max(len(lista_coinvolti), 1)
    
    if pagatore != "Cassa Comune" and pagatore in crediti_anticipi:
        crediti_anticipi[pagatore] += totale
        
    quota_capite = totale / n_coinvolti
    for p in lista_coinvolti:
        if p in quote_spese:
            quote_spese[p] += quota_capite

st.write("### 💶 Situazione Contabile per Coppia:")
col_res1, col_res2 = st.columns(2)

# --- COSTRUZIONE MESSAGGIO COMPLETO PER WHATSAPP ---
testo_whatsapp = "✈️ *RIEPILOGO CASSA VIAGGIO*\n\n"
testo_whatsapp += f"💰 *Cassa Totale Versata:* {totale_versato:.2f} €\n"
testo_whatsapp += f"💸 *Spese Totali:* {totale_speso:.2f} €\n"
testo_whatsapp += f"🏦 *Disponibilità Residua:* {cassa_rimanente:.2f} €\n\n"

# 1. Dettaglio Voci di Spesa
if len(st.session_state["spese"]) > 0:
    testo_whatsapp += "📝 *ELENCO SPESE REGISTRATE:*\n"
    for idx, s in enumerate(st.session_state["spese"], 1):
        imp = float(s.get("Importo", 0.0))
        desc = s.get("Descrizione", "")
        pagatore = s.get("Pagato da", "Cassa Comune")
        coinvolti = s.get("Coppie Coinvolte", s.get("Coinvolti", ""))
        nr_c = s.get("Nr Coppie", len(str(coinvolti).split(",")) if coinvolti else 1)
        
        testo_whatsapp += f"{idx}. *{desc}* - {imp:.2f} €\n"
        testo_whatsapp += f"   • Pagato da: {pagatore}\n"
        testo_whatsapp += f"   • Per: [{nr_c} coppie] {coinvolti}\n"
    testo_whatsapp += "\n"

# 2. Saldi Generali per Coppia
testo_whatsapp += "📊 *SALDI FINALI PER COPPIA:*\n"
for i, p in enumerate(st.session_state["partecipanti"]):
    versato_p = round(st_versamenti.get(p, 0.0), 2)
    speso_p = round(quote_spese.get(p, 0.0), 2)
    anticipato_p = round(crediti_anticipi.get(p, 0.0), 2)
    saldo_p = round((versato_p + anticipato_p) - speso_p, 2)
    
    testo_whatsapp += f"\n👫 *{p}*\n"
    testo_whatsapp += f"• Versato: {versato_p:.2f} €\n"
    testo_whatsapp += f"• Speso: {speso_p:.2f} €\n"
    if anticipato_p > 0:
        testo_whatsapp += f"• Anticipato di tasca: {anticipato_p:.2f} €\n"
    testo_whatsapp += f"• Saldo attuale: {saldo_p:.2f} €\n"
    
    col = col_res1 if i % 2 == 0 else col_res2
    with col:
        st.markdown(f"**Coppia 👫 {p}**")
        st.text(f"Versato in cassa: {versato_p:.2f} €\nSpesa a carico:  {speso_p:.2f} €\nAnticipi tasca:  {anticipato_p:.2f} €")
        st.metric(label=f"Saldo di {p}", value=f"{saldo_p:.2f} €")
        st.markdown("---")

# --- SEZIONE INVIO WHATSAPP ---
st.subheader("📲 Condividi su WhatsApp")
url_wa = "https://wa.me/?text=" + urllib.parse.quote(testo_whatsapp)
st.markdown(f'[![Invia su WhatsApp](https://img.shields.io/badge/Invia_Riepilogo_su-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)]({url_wa})')

st.divider()
col_r1, col_r2 = st.columns(2)
with col_r1:
    if st.button("🔄 Pulisci memoria spese"):
        st.session_state["spese"] = []
        st.rerun()
with col_r2:
    if st.button("🗑️ Reset totale dati (Annulla tutto)"):
        st.session_state["partecipanti"] = list(COPPIE_FISSE)
        st.session_state["extra_versamenti"] = [
            {"Partecipante": p, "Importo": 400.0, "Tipo": "Iniziale (Default)"} for p in COPPIE_FISSE
        ]
        st.session_state["spese"] = []
        st.session_state["reset_vers_counter"] += 1
        st.rerun()
