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

# --- MENU LATERALE: GESTIONE PARTECIPANTI E VERSAMENTI ---
st.sidebar.header("⚙️ Configurazione & Cassa")

# Gestione partecipanti (Aggiunta e Rimozione)
st.sidebar.subheader("👥 Partecipanti")
nuovo_partecipante = st.sidebar.text_input("Aggiungi partecipante")
if st.sidebar.button("Aggiungi"):
    if nuovo_partecipante and nuovo_partecipante not in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].append(nuovo_partecipante)
        st.session_state["versamenti"][nuovo_partecipante] = 0.0
        st.sidebar.success(f"Aggiunto {nuovo_partecipante}!")
        st.rerun()

# Selezione partecipante da rimuovere
partecipante_da_rimuovere = st.sidebar.selectbox("Rimuovi partecipante", [""] + st.session_state["partecipanti"])
if st.sidebar.button("Rimuovi"):
    if partecipante_da_rimuovere in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].remove(partecipante_da_rimuovere)
        if partecipante_da_rimuovere in st.session_state["versamenti"]:
            del st.session_state["versamenti"][partecipante_da_rimuovere]
        st.sidebar.success(f"Rimosso {partecipante_da_rimuovere}!")
        st.rerun()

st.sidebar.divider()
st.sidebar.write("### 💰 Gestione Versamenti / Cassa")
persona_versamento = st.sidebar.selectbox("Partecipante", st.session_state["partecipanti"] if st.session_state["partecipanti"] else [""], key="sel_vers")
importo_versamento = st.sidebar.number_input("Importo versato (€)", min_value=0.0, format="%.2f", key="imp_vers")
tipo_versamento = st.sidebar.radio("Tipo versamento", ["Iniziale", "Incremento (Cassa in rosso)"])

if st.sidebar.button("Registra Versamento"):
    if persona_versamento and importo_versamento > 0:
        st.session_state["versamenti"][persona_versamento] += importo_versamento
        st.session_state["extra_versamenti"].append({
            "Partecipante": persona_versamento,
            "Importo": importo_versamento,
            "Tipo": tipo_versamento
        })
        st.sidebar.success(f"Registrati {importo_versamento}€ per {persona_versamento}!")
        st.rerun()
    else:
        st.sidebar.warning("Seleziona un partecipante e un importo valido.")

if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- CONTROLLI PRELIMINARI ---
if not st.session_state["partecipanti"]:
    st.warning("⚠️ Non ci sono partecipanti configurati. Aggiungi almeno un partecipante dalla barra laterale.")
    st.stop()

# --- CALCOLI FINANZIARI GENERALI ---
totale_versato = sum(st.session_state["versamenti"].values())
totale_speso = sum(s["Importo"] for s in st.session_state["spese"])
cassa_rimanente = totale_versato - totale_speso

# Mostra metriche principali della cassa
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Cassa Totale Versata", f"{totale_versato:.2f} €")
col_m2.metric("Spese Totali", f"{totale_speso:.2f} €")
col_m3.metric("Disponibilità Cassa", f"{cassa_rimanente:.2f} €", delta=f"{cassa_rimanente:.2f} €")

if cassa_rimanente < 0:
    st.error("⚠️ **ATTENZIONE: La cassa comune è in rosso!** È necessario effettuare un incremento di cassa dalla barra laterale.")

st.divider()

# --- SEZIONE 1: REGISTRA SPESA ---
st.subheader("📝 Registra Spesa")

with st.form("form_spesa", clear_on_submit=True):
    descrizione = st.text_input("Descrizione spesa (es. Cena, Benzina, Biglietti museo...)")
    importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
    
    # Scelta chi paga: Cassa comune oppure anticipo di un singolo partecipante
    modalita_pagamento = st.radio("Chi ha pagato?", ["Cassa Comune", "Anticipato da un partecipante"])
    
    pagato_da = "Cassa Comune"
    if modalita_pagamento == "Anticipato da un partecipante":
        pagato_da = st.selectbox("Chi ha anticipato i soldi?", st.session_state["partecipanti"])
    
    st.write("Seleziona chi partecipa a questa spesa:")
    partecipanti_coinvolti = {}
    cols = st.columns(min(len(st.session_state["partecipanti"]), 4))
    for i, p in enumerate(st.session_state["partecipanti"]):
        with cols[i % len(cols)]:
            partecipanti_coinvolti[p] = st.checkbox(p, value=True, key=f"p_{p}")
            
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

# --- SEZIONE 2: STORICO SPESE E BILANCI ---
st.divider()
st.subheader("📊 Riepilogo Movimenti e Saldi Individuali")

if len(st.session_state["spese"]) > 0:
    st.write("### Cronologia Spese")
    df_spese = pd.DataFrame(st.session_state["spese"])
    st.dataframe(df_spese, use_container_width=True)

# Calcolo dei saldi individuali
# Se la spesa è pagata dalla cassa: pesa solo come quota a carico del partecipante.
# Se la spesa è anticipata da un partecipante: chi ha anticipato riceve un credito pari all'importo, e ciascuno paga la sua quota.
quote_spese = {p: 0.0 for p in st.session_state["partecipanti"]}
crediti_anticipi = {p: 0.0 for p in st.session_state["partecipanti"]}

for spesa in st.session_state["spese"]:
    totale = spesa["Importo"]
    pagatore = spesa["Pagato da"]
    n_coinvolti = spesa["Num_Coinvolti"]
    quota_capite = totale / n_coinvolti
    
    if pagatore != "Cassa Comune" and pagatore in crediti_anticipi:
        crediti_anticipi[pagatore] += totale
        
    lista_coinvolti = spesa["Coinvolti"].split(", ")
    for p in lista_coinvolti:
        if p in quote_spese:
            quote_spese[p] += quota_capite

st.write("### 💶 Situazione Contabile per Persona:")
st.info("• **Versato in cassa:** Soldi immessi nel fondo comune.\n• **Spesa a carico:** Totale delle quote dei vari acquisti.\n• **Anticipi extra:** Soldi spesi di tasca propria (se applicabile).\n• **Saldo:** Positivo (+) = credito/rimanenza | Negativo (-) = deve integrare o versare.")

col_res1, col_res2 = st.columns(2)
for i, p in enumerate(st.session_state["partecipanti"]):
    versato_p = st.session_state["versamenti"].get(p, 0.0)
    speso_p = quote_spese.get(p, 0.0)
    anticipato_p = crediti_anticipi.get(p, 0.0)
    
    # Saldo = Versato in cassa + Anticipi fatti di tasca propria - Spese a suo carico
    saldo_p = (versato_p + anticipato_p) - speso_p
    
    col = col_res1 if i % 2 == 0 else col_res2
    with col:
        st.markdown(f"**👤 {p}**")
        st.text(f"Versato in cassa: {versato_p:.2f} €\nSpesa a carico:  {speso_p:.2f} €\nAnticipi tasca:  {anticipato_p:.2f} €")
        st.metric(label=f"Saldo di {p}", value=f"{saldo_p:.2f} €")
        st.markdown("---")

if st.button("🗑️ Reset totale dati (Azzera tutto)"):
    st.session_state["spese"] = []
    st.session_state["versamenti"] = {p: 100.0 for p in st.session_state["partecipanti"]}
    st.session_state["extra_versamenti"] = []
    st.rerun()
