import streamlit as st
import pandas as pd

# Titolo della pagina
st.set_page_config(page_title="Spese di Viaggio", page_icon="✈️", layout="centered")

# --- GESTIONE PASSWORD ---
# Puoi cambiare la password qui sotto (es. "tua_password")
PASSWORD_CORRETTA = "viaggio2026"

def check_password():
    """Restituisce True se l'utente ha inserito la password corretta."""
    if "password_corretta" not in st.session_state:
        st.session_state["password_corretta"] = False

    if st.session_state["password_corretta"]:
        return True

    st.subheader("🔒 Area Protetta")
    inserita = st.text_input("Inserisci la password per accedere:", type="password")
    
    if st.button("Accedi"):
        if inserita == PASSWORD_CORRETTA:
            st.session_state["password_corretta"] = True
            st.rerun()
        else:
            st.error("Password errata. Riprova.")
    return False

if not check_password():
    st.stop()

# --- APPLICAZIONE PRINCIPALE (Sbloccata) ---
st.title("✈️ Cassa Viaggio")
st.write("Gestione spese condivise semplice e veloce.")

# Inizializzazione della memoria delle spese
if "spese" not in st.session_state:
    st.session_state["spese"] = []

# Sezione inserimento nuova spesa
with st.form("form_spesa", clear_on_submit=True):
    st.subheader("Aggiungi una spesa")
    descrizione = st.text_input("Descrizione (es. Cena, Benzina, Hotel)")
    importo = st.number_input("Importo (€)", min_value=0.0, step=1.0)
    pagato_da = st.selectbox("Chi ha pagato?", ["Stefano", "Moglie", "Amici / Altri"])
    
    st.write("Chi partecipa alla spesa?")
    p_stefano = st.checkbox("Stefano", value=True)
    p_moglie = st.checkbox("Moglie", value=True)
    p_altri = st.checkbox("Amici / Altri", value=False)
    
    invia = st.form_submit_button("Registra Spesa")
    
    if invia:
        if descrizione and importo > 0:
            partecipanti = []
            if p_stefano: partecipanti.append("Stefano")
            if p_moglie: partecipanti.append("Moglie")
            if p_altri: partecipanti.append("Amici / Altri")
            
            if partecipanti:
                st.session_state["spese"].append({
                    "Descrizione": descrizione,
                    "Importo": importo,
                    "Pagato Da": pagato_da,
                    "Partecipanti": ", ".join(partecipanti),
                    "Num_Partecipanti": len(partecipanti)
                })
                st.success("Spesa aggiunta con successo!")
            else:
                st.warning("Seleziona almeno un partecipante.")
        else:
            st.warning("Inserisci una descrizione e un importo valido.")

# Mostra lo storico delle spese
if st.session_state["spese"]:
    st.divider()
    st.subheader("📋 Storico Spese")
    df_spese = pd.DataFrame(st.session_state["spese"])
    st.dataframe(df_spese[["Descrizione", "Importo", "Pagato Da", "Partecipanti"]], use_container_width=True)
    
    # Pulsante per resettare i dati di prova
    if st.button("Svuota tutte le spese"):
        st.session_state["spese"] = []
        st.rerun()