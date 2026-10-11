import streamlit as st
import pandas as pd

# Configurazione della pagina
st.set_page_config(page_title="Spese di Viaggio", page_icon="✈️", layout="centered")

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
    st.stop()  # Interrompe l'esecuzione finché non si effettua il login

# --- APPLICAZIONE PRINCIPALE ---
st.title("✈️ Gestione Spese di Viaggio")

# Inizializzazione della memoria delle spese e dei partecipanti nella sessione Streamlit
if "spese" not in st.session_state:
    st.session_state["spese"] = []

if "partecipanti" not in st.session_state:
    # Puoi personalizzare i nomi dei partecipanti del viaggio qui
    st.session_state["partecipanti"] = ["Mario", "Anna", "Luca", "Sara"]

# Menu laterale per configurare i partecipanti
st.sidebar.header("⚙️ Impostazioni")
nuovo_partecipante = st.sidebar.text_input("Aggiungi partecipante")
if st.sidebar.button("Aggiungi"):
    if nuovo_partecipante and nuovo_partecipante not in st.session_state["partecipanti"]:
        st.session_state["partecipanti"].append(nuovo_partecipante)
        st.sidebar.success(f"Aggiunto {nuovo_partecipante}!")
        st.rerun()

st.sidebar.write("**Partecipanti attivi:**")
st.sidebar.write(", ".join(st.session_state["partecipanti"]))

if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- SEZIONE 1: AGGIUNGI SPESA ---
st.subheader("📝 Inserisci una nuova spesa")

with st.form("form_spesa", clear_on_submit=True):
    descrizione = st.text_input("Descrizione spesa (es. Cena al ristorante, Taxi...)")
    importo = st.number_input("Importo Totale (€)", min_value=0.0, format="%.2f")
    pagato_da = st.selectbox("Chi ha anticipato i soldi?", st.session_state["partecipanti"])
    
    st.write("Seleziona chi partecipa a questa spesa:")
    # Di default tutti sono selezionati
    partecipanti_coinvolti = {}
    cols = st.columns(len(st.session_state["partecipanti"]))
    for i, p in enumerate(st.session_state["partecipanti"]):
        with cols[i % len(cols)]:
            partecipanti_coinvolti[p] = st.checkbox(p, value=True)
            
    submitted = st.form_submit_button("Aggiungi Spesa")
    
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
            st.success(f"Spesa '{descrizione}' aggiunta con successo!")

# --- SEZIONE 2: RIEPILOGO E BILANCI ---
st.divider()
st.subheader("📊 Riepilogo e Situazione Conti")

if len(st.session_state["spese"]) > 0:
    df_spese = pd.DataFrame(st.session_state["spese"])
    st.dataframe(df_spese, use_container_width=True)
    
    # Calcolo dei bilanci individuali
    bilanci = {p: 0.0 for p in st.session_state["partecipanti"]}
    
    for spesa in st.session_state["spese"]:
        pagatore = spesa["Pagato da"]
        totale = spesa["Importo"]
        coinvolti_N = spesa["Num_Coinvolti"]
        quota_capite = totale / coinvolti_N
        
        # Chi paga guadagna credito (+ importo totale anticipato)
        bilanci[pagatore] += totale
        
        # Chi partecipa accumula il debito (- quota individuale)
        # Scompongo la stringa dei coinvolti per riattribuire le quote
        lista_coinvolti_corrente = spesa["Coinvolti"].split(", ")
        for p in lista_coinvolti_corrente:
            if p in bilanci:
                bilanci[p] -= quota_capite

    st.write("### 💶 Saldo finale per persona:")
    st.info("Valori positivi (+) = devono avere soldi | Valori negativi (-) = devono dare soldi")
    
    col1, col2 = st.columns(2)
    for i, (persona, saldo) in enumerate(bilanci.items()):
        col = col1 if i % 2 == 0 else col2
        col.metric(label=persona, value=f"{saldo:.2f} €")
        
    if st.button("🗑️ Cancella tutte le spese"):
        st.session_state["spese"] = []
        st.rerun()
else:
    st.info("Nessuna spesa inserita finora. Aggiungi la prima spesa qui sopra!")
