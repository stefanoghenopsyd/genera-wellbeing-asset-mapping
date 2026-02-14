import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="PWB Asset Mapping", layout="centered")

# --- CSS PERSONALIZZATO (Logo, Titolo, Footer) ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
    }
    .privacy-text {
        font-size: 0.8em;
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        text-align: justify;
        color: #555;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: grey;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #eee;
        z-index: 100;
    }
    .stApp {
        margin-bottom: 60px; /* Spazio per il footer */
    }
    </style>
    """, unsafe_allow_html=True)

# --- DEFINIZIONE DOMANDE E DIMENSIONI (Modello Ryff) ---
# Struttura: (Domanda, Dimensione, è_positivo?)
# Se è_positivo = False, il punteggio verrà invertito (7 - x)
QUESTIONS = [
    ("Tutto sommato, sono soddisfatto della persona che sono e accetto anche i miei lati meno perfetti.", "Autoaccettazione", True),
    ("Spesso mi sento deluso dal mio passato e vorrei poter cambiare molte parti della mia personalità.", "Autoaccettazione", False),
    
    ("Ho persone care con cui posso condividere i miei sentimenti profondi e so di poter contare su di loro.", "Relazioni positive", True),
    ("Trovo difficile aprirmi con gli altri e spesso sento che le mie relazioni sono superficiali o poco gratificanti.", "Relazioni positive", False),
    
    ("Prendo le mie decisioni in base ai miei valori personali, anche se questo significa andare contro l'opinione comune.", "Autonomia", True),
    ("Tendo a preoccuparmi troppo di ciò che gli altri pensano di me e spesso cambio idea per compiacere chi mi circonda.", "Autonomia", False),
    
    ("Mi sento capace di gestire le responsabilità della vita quotidiana e di creare situazioni adatte alle mie esigenze.", "Padronanza ambientale", True),
    ("Spesso mi sento sopraffatto dagli impegni quotidiani e ho l'impressione di non avere il controllo sugli eventi della mia vita.", "Padronanza ambientale", False),
    
    ("Ho un chiaro senso di direzione e sento che le attività che svolgo quotidianamente hanno un significato profondo.", "Scopo nella vita", True),
    ("A volte ho la sensazione di girare a vuoto e mi chiedo se ciò che faccio nella vita serva davvero a qualcosa.", "Scopo nella vita", False),
    
    ("Vedo me stesso come una persona in continua evoluzione e cerco costantemente nuove esperienze che mi permettano di imparare.", "Crescita personale", True),
    ("Ho la sensazione di essere bloccato da tempo e non provo più interesse nel cercare di migliorare me stesso o le mie abilità.", "Crescita personale", False)
]

DEFINIZIONI_DIMENSIONI = {
    "Autoaccettazione": "Atteggiamento positivo verso sé stessi e il proprio passato.",
    "Crescita personale": "Apertura a nuove esperienze e sviluppo continuo.",
    "Scopo nella vita": "Sensazione che la propria esistenza abbia una direzione e un senso.",
    "Relazioni positive": "Capacità di stabilire legami profondi e di fiducia.",
    "Autonomia": "Autodeterminazione e indipendenza dai condizionamenti sociali.",
    "Padronanza ambientale": "Capacità di gestire e scegliere contesti adatti ai propri bisogni."
}

# --- FUNZIONI DI UTILITÀ ---

def salva_su_google_sheet(dati):
    """Salva i dati su Google Sheet usando i secrets di Streamlit."""
    try:
        # Recupera le credenziali dai secrets
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Apre il foglio (sostituisci con il nome esatto del tuo foglio se diverso)
        sheet = client.open("PWB_Data").sheet1 
        sheet.append_row(dati)
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio dei dati (Cloud): {e}")
        return False

def crea_radar_chart(punteggi, categorie):
    """Genera il grafico radar."""
    N = len(categorie)
    
    # Angoli per il radar
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1] # Chiudere il cerchio
    
    # Valori (chiudere il cerchio)
    values = list(punteggi.values())
    values += values[:1]
    
    # Colori personalizzabili (MATCH CON LOGO GENERA)
    colore_riempimento = "#4CAF50" # Verde esempio - CAMBIARE CON CODICE HEX LOGO
    colore_linea = "#2E7D32"       # Verde scuro esempio - CAMBIARE CON CODICE HEX LOGO
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Disegna assi e etichette
    plt.xticks(angles[:-1], categorie, color='grey', size=10)
    
    # Disegna ylabels
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5, 6], ["1", "2", "3", "4", "5", "6"], color="grey", size=7)
    plt.ylim(0, 6.5)
    
    # Plot dati
    ax.plot(angles, values, linewidth=2, linestyle='solid', color=colore_linea)
    ax.fill(angles, values, color=colore_riempimento, alpha=0.4)
    
    # Rimuovi bordo esterno brutto
    ax.spines['polar'].set_visible(False)
    
    return fig

# --- MAIN APP ---

def main():
    # 1. HEADER E LOGO
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("GENERA Logo Colore.png", use_container_width=True)
        except:
            st.warning("Immagine 'GENERA Logo Colore.png' non trovata. Caricala nella repository.")
    
    st.markdown('<h1 class="main-title">Psychological Wellbeing Asset Mapping:<br>quali sono le tue risorse di benessere?</h1>', unsafe_allow_html=True)

    # Inizializzazione session state per gestire il flusso
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        # --- SEZIONE 1: INTRODUZIONE ---
        with st.expander("Introduzione e Modello Teorico", expanded=True):
            st.markdown("""
            Carol Ryff definisce lo **Psychological Well-being (PWB)** secondo una prospettiva eudaimonica, spostando l'attenzione dal semplice piacere (edonismo) alla realizzazione del potenziale umano e alla ricerca di significato. 
            
            Secondo l’autrice il benessere non è uno stato statico, ma un processo dinamico articolato in sei dimensioni fondamentali:
            * **Autoaccettazione:** atteggiamento positivo verso sé stessi e il proprio passato.
            * **Crescita personale:** apertura a nuove esperienze e sviluppo continuo.
            * **Scopo nella vita:** sensazione che la propria esistenza abbia una direzione e un senso.
            * **Relazioni positive:** capacità di stabilire legami profondi e di fiducia.
            * **Autonomia:** autodeterminazione e indipendenza dai condizionamenti sociali.
            * **Padronanza ambientale:** capacità di gestire e scegliere contesti adatti ai propri bisogni.
            
            In questa ottica, stare bene significa "funzionare bene", integrando le proprie sfide personali in un percorso di crescita consapevole.
            
            ### Obiettivo del test
            Diventare più consapevoli delle nostre risorse di benessere psicologico.
            """)
            
            st.markdown('<div class="privacy-text"><b>Proseguendo nella compilazione acconsento a che i dati raccolti potranno essere utilizzati in forma aggregata esclusivamente per finalità statistiche.</b></div>', unsafe_allow_html=True)
            st.divider()

        with st.form("questionario_form"):
            # --- SEZIONE 2: INFORMAZIONI SOCIO ANAGRAFICHE ---
            st.subheader("Informazioni socio anagrafiche")
            
            # Riga 1: Nome
            nome = st.text_input("Nome o Nickname")
            
            # Riga 2: Genere e Età
            c_gen, c_eta = st.columns(2)
            with c_gen:
                genere = st.selectbox("Genere", ["Maschile", "Femminile", "Non binario", "Non risponde"])
            with c_eta:
                eta = st.selectbox("Fascia d'età", ["fino a 20 anni", "21-30 anni", "31-40 anni", "41-50 anni", "51-60 anni", "61-70 anni", "più di 70 anni"])
            
            # Riga 3: Titolo di studio e Job
            c_edu, c_job = st.columns(2)
            with c_edu:
                titolo_studio = st.selectbox("Titolo di studio", ["Licenza media", "Qualifica professionale", "Diploma di maturità", "Laurea triennale", "Laurea magistrale (o ciclo unico)", "Titolo post lauream"])
            with c_job:
                job = st.selectbox("Job", ["Imprenditore", "Top manager", "Middle manager", "Impiegato", "Operaio", "Tirocinante", "Libero professionista"])

            st.divider()

            # --- SEZIONE 3: TEST ---
            st.subheader("Test di Autovalutazione")
            st.info("""
            **Istruzioni:** Ecco una serie di 12 item sviluppati sulla base delle 6 dimensioni del modello di Carol Ryff. 
            Per ogni dimensione, troverai un'affermazione che indica un alto benessere e una che indica una criticità o una sfida. 
            Valuta il tuo accordo con ciascuna di esse su una scala a 6 punti (1 = Per nulla d'accordo, 6 = Completamente d'accordo).
            """)

            risposte_raw = {}
            punteggi_dimensioni = {dim: [] for dim in DEFINIZIONI_DIMENSIONI.keys()}
            
            # Ciclo sulle domande
            for idx, (domanda, dimensione, is_positive) in enumerate(QUESTIONS):
                st.markdown(f"**{idx + 1}. {dimensione}**")
                score = st.slider(domanda, 1, 6, 3, key=f"q_{idx}")
                
                # Salvataggio raw per DB
                risposte_raw[f"Item_{idx+1}"] = score
                
                # Calcolo Punteggio (Reverse Scoring se negativo)
                if not is_positive:
                    final_score = 7 - score
                else:
                    final_score = score
                
                punteggi_dimensioni[dimensione].append(final_score)
                st.write("") # Spaziatura

            submitted = st.form_submit_button("Ottieni il tuo Profilo di Benessere")

            if submitted:
                if not nome:
                    st.error("Per favore inserisci un Nome o Nickname.")
                else:
                    # --- CALCOLO RISULTATI ---
                    risultati_medi = {dim: np.mean(vals) for dim, vals in punteggi_dimensioni.items()}
                    media_totale = np.mean(list(risultati_medi.values()))
                    
                    # Preparazione dati per DB
                    user_id = str(uuid.uuid4())
                    record = [user_id, nome, genere, eta, titolo_studio, job] + list(risposte_raw.values())
                    
                    # Tentativo salvataggio
                    salvato = salva_su_google_sheet(record)
                    
                    # Salvataggio stato
                    st.session_state.risultati = risultati_medi
                    st.session_state.media_totale = media_totale
                    st.session_state.submitted = True
                    st.rerun()

    else:
        # --- SEZIONE 4: FEEDBACK ---
        risultati = st.session_state.risultati
        media_totale = st.session_state.media_totale
        
        st.success("Analisi completata!")
        
        # 1. Feedback Grafico (Radar)
        st.subheader("La tua Mappa del Benessere")
        fig = crea_radar_chart(risultati, list(risultati.keys()))
        st.pyplot(fig)
        
        # 2. Feedback Narrativo
        st.subheader("Analisi Descrittiva")
        st.markdown(f"**Punteggio Complessivo:** {media_totale:.2f} / 6.0")
        
        # Logica Eudaimonica (> 3.5 è una media teorica positiva su scala 1-6)
        if media_totale > 3.5:
            st.info("Il tuo punteggio indica un orientamento eudaimonico positivo: stai integrando efficacemente sfide e risorse nel tuo percorso di vita.")
            
        # Identificazione Punti di Forza e Aree di Miglioramento
        sorted_res = sorted(risultati.items(), key=lambda item: item[1], reverse=True)
        top_2 = sorted_res[:2]
        bottom_2 = sorted_res[-2:]
        
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown("### 🌟 Le tue Risorse principali")
            for dim, val in top_2:
                st.markdown(f"**{dim}** (Score: {val:.1f})")
                st.caption(DEFINIZIONI_DIMENSIONI[dim])
                st.write("---")

        with col_res2:
            st.markdown("### 🪴 Aree da coltivare")
            for dim, val in bottom_2:
                st.markdown(f"**{dim}** (Score: {val:.1f})")
                st.caption(DEFINIZIONI_DIMENSIONI[dim])
                st.write("---")
        
        if st.button("Ricomincia il test"):
            st.session_state.submitted = False
            st.rerun()

    # Footer
    st.markdown('<div class="footer">Powered by GÉNERA</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
