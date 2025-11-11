import streamlit as st
import requests

API_URL = "http://localhost:8002/api"  

st.set_page_config(page_title="🛒 Shopyverse - Reco Tester", layout="centered")
st.title("🛒 Shopyverse - Test du système de recommandation")

st.write("Sélectionnez un produit et consultez les recommandations associées.")

# --- STEP 1: Load list of products from API ---
@st.cache_data
def load_products():
    resp = requests.get(f"{API_URL}/products/list")
    if resp.status_code == 200:
        return resp.json()
    else:
        return []

products = load_products()

if not products:
    st.warning("Aucun produit disponible. Ajoutez-en d'abord via /api/products.")
else:
    # Create a dropdown list
    product_names = {p["name"]: p["id"] for p in products}
    selected_name = st.selectbox("Choisissez un produit :", list(product_names.keys()))
    selected_id = product_names[selected_name]

    if st.button("Afficher les recommandations"):
        with st.spinner("Recherche en cours..."):
            reco = requests.get(f"{API_URL}/recommendations", params={"product_id": selected_id})

        if reco.status_code == 200:
            recommended_products = reco.json()

            st.subheader("🔎 Recommandations :")
            for p in recommended_products:
                st.markdown(f"""
                **{p['name']}**  
                *Catégorie:* {p.get('category', 'N/A')}  
                *Prix:* {p.get('price', 'N/A')} €  
                ___
                """)
        else:
            st.error("Aucune recommandation trouvée.")
