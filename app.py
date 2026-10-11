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
    # Dizionario per memorizzare quanto versato inizialmente/extra da ciascuno
    st.session_state["versamenti"] = {p: 100.0 for p in st.session_state["partecipanti"]}

if "spese" not in st.session_state:
    st.session_state["spese"] = []

if "extra_versamenti" not in st.session_state:
    st.session_state["extra_versamenti"] = []

# --- MENU LATERALE: GESTIONE PARTECIPANTI E VERSAMENTI ---
st.sidebar.header("⚙️ Configurazione & Cassa")

# Aggiunta partecipante
nuovo_partecipante = st.sidebar.text_input("Nuovo partecipante")
if st.sidebar.button("Aggiungi partecipante"):
    if nuovo_partecipante and nuovo_partecipante not in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].append(nuovo_partecipante)
        st.session_state["versamenti"][nuovo_partecipante] = 0.0
        st.sidebar.success(f"Aggiunto {nuovo_partecipante}!")
        st.rerun()

st.sidebar.divider()
st.sidebar.write("### 💰 Gestione Versamenti / Cassa")
persona_versamento = st.sidebar.selectbox("Partecipante", st.session_state["partecipanti"], key="sel_vers")
importo_versamento = st.sidebar.number_input("Importo versato (€)", min_value=0.0, format="%.2f", key="imp_vers")
tipo_versamento = st.sidebar.radio("Tipo versamento", ["Iniziale", "Incremento (Cassa in rosso)"])

if st.sidebar.button("Registra Versamento"):
    if importo_versamento > 0:
        st.session_state["versamenti"][persona_versamento] += importo_versamento
        st.session_state["extra_versamenti"].append({
            "Partecipante": persona_versamento,
            "Importo": importo_versamento,
            "Tipo": tipo_versamento
        })
        st.sidebar.success(f"Registrati {importo_versamento}€ per {persona_versamento}!")
        st.rerun()
    else:
        st.sidebar.warning("Inserisci un importo valido.")

if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

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

# --- SEZIONE 1: REGISTRA SPESA DALLA CASSA ---
st.subheader("📝 Registra Spesa / Prelievo dalla Cassa")

with st.form("form_spesa", clear_on_submit=True):
    descrizione = st.text_input("Descrizione spesa (es. Cena, Benzina, Biglietti museo...)")
    importo = st.number_input("Importo prelevato dalla cassa (€)", min_value=0.0, format="%.2f")
    pagato_da_cassa = st.selectbox("Chi ha gestito il pagamento materiale?", st.session_state["partecipanti"])
    
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
                "Gestito da": pagato_da_cassa,
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
# Saldo = (Quanto ha versato in cassa) - (La somma delle quote delle spese a cui ha partecipato)
quote_spese = {p: 0.0 for p in st.session_state["partecipanti"]}

for spesa in st.session_state["spese"]:
    totale = spesa["Importo"]
    n_coinvolti = spesa["Num_Coinvolti"]
    quota_capite = totale / n_coinvolti
    
    lista_coinvolti = spesa["Coinvolti"].split(", ")
    for p in lista_coinvolti:
        if p in quote_spese:
            quote_spese[p] += quota_capite

st.write("### 💶 Situazione Contabile per Persona:")
st.info("• **Versato:** Totale immesso nella cassa comune.\n• **Speso a carico:** La somma delle quote dei vari acquisti.\n• **Saldo:** Positivo (+) = credito/rimanenza | Negativo (-) = deve versare ancora nella cassa.")

col_res1, col_res2 = st.columns(2)
for i, p in enumerate(st.session_state["partecipanti"]):
    versato_p = st.session_state["versamenti"][p]
    speso_p = quote_spese[p]
    saldo_p = versato_p - speso_p
    
    col = col_res1 if i % 2 == 0 else col_res2
    with col:
        st.markdown(f"**👤 {p}**")
        st.text(f"Versato in cassa: {versato_p:.2f} €\nSpesa a carico:  {speso_p:.2f} €")
        st.metric(label=f"Saldo di {p}", value=f"{saldo_p:.2f} €")
        st.markdown("---")

if st.button("🗑️ Reset totale dati (Azzera tutto)"):
    st.session_state["spese"] = []
    st.session_state["versamenti"] = {p: 100.0 for p in st.session_state["partecipanti"]}
    st.session_state["extra_versamenti"] = []
    st.rerun()
