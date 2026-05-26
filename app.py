import streamlit as st
import pymssql
from io import BytesIO
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

st.set_page_config(page_title="Busca Visual 100% Azure", layout="centered")
st.title(" Busca Visual de Produtos - 100% Azure Cloud")

AZURE_IA_KEY = "Senha****tOJQQJ99CEACZoyfiXJ3w3AAAFACOGuEAw"
AZURE_IA_ENDPOINT = "https://endpoint/"

AZURE_DB_SERVER = "servidor"
AZURE_DB_USER = "user"
AZURE_DB_PASSWORD = "senha"
AZURE_DB_NAME = "db_"
@st.cache_resource
def inicializar_ia_azure():
    credentials = CognitiveServicesCredentials(AZURE_IA_KEY)
    return ComputerVisionClient(AZURE_IA_ENDPOINT, credentials)

client_ia = inicializar_ia_azure()


arquivo_imagem = st.file_uploader("Escolha uma foto...", type=["jpg", "jpeg", "png"])

if arquivo_imagem is not None:
  
    st.image(arquivo_imagem, caption="Imagem enviada")
    st.write(" Enviando imagem para a Inteligência Artificial da Azure...")
    
    try:
        dados_imagem = BytesIO(arquivo_imagem.getvalue())
        
        analise = client_ia.tag_image_in_stream(dados_imagem)
        
        if analise.tags:
            tags_filtradas = [tag.name.lower() for tag in analise.tags if tag.name.lower() not in ['indoor', 'isolated', 'background', 'studio shot', 'product']]
            
            if tags_filtradas:
                objeto_detectado = tags_filtradas[0] # Pega a tag mais forte (ex: 'mouse' ou 'laptop')
                st.success(f"Azure AI identificou o objeto: **{objeto_detectado.capitalize()}**")
                
                st.write("🔍 Consultando estoque no Azure SQL...")
                conn = pymssql.connect(server=AZURE_DB_SERVER, user=AZURE_DB_USER, password=AZURE_DB_PASSWORD, database=AZURE_DB_NAME)
                cursor = conn.cursor()
                
                query = "SELECT NomeProduto, Preco, Estoque FROM Produtos WHERE NomeProduto LIKE %s"
                cursor.execute(query, (f"%{objeto_detectado}%",))
                produtos = cursor.fetchall()
                
                if produtos:
                    st.subheader("Products found in your Azure Database:")
                    for prod in produtos:
                        st.metric(label=f" {prod[0]}", value=f"$ {prod[1]}", delta=f"{prod[2]} units in stock")
                else:
                    st.warning(f"No products with the term '{objeto_detectado}' were found in the database.")
                
                conn.close()
            else:
                st.warning("A IA detectou apenas o fundo da imagem. Tente outra foto com o objeto em evidência!")
        else:
            st.warning("Nenhuma tag encontrada para esta imagem.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro na comunicação com a Azure: {e}")