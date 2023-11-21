import streamlit as st
import os
import pinecone
from langchain.llms import OpenAI
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from dotenv import load_dotenv
load_dotenv()



# ================================seting up pinecone================================
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment='gcp-starter'# this thing can be found at your acc at https://app.pinecone.io/
)

index_name = "itl-knl-base"
embeddings = OpenAIEmbeddings()
docsearch = Pinecone.from_existing_index(index_name, embeddings) # this is the vectorstore
query="Thời giờ làm việc của nhân viên ITL"
# top_k=docsearch.similarity_search_with_score(query)
# for i in range(len(top_k)):
#     print(top_k[i][0].metadata)
# [top_k[i][0].metadata for i in range(len(top_k))]
# top_k[0][0].metadata
# top_k[0][1]
# làm for loop, tinh similarity score trung binh

# ================================seting up OpenAI================================
prompt_template = """You are an expert about policies of ITL Corporation, I will ask you a question, and then provide you some chunks of text contain relevant information. 
Try to extract information from the provided text & answer in Vietnamese. You should answer straight to the point, prefer bullet-points. If the text does not contain relevant information, you should tell me that you don't have the answer.
Questions:
{user_question}  

Relevant Information:
{relevant_info}
"""

llm = OpenAI(temperature=0, max_tokens=2048)
llm_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template(prompt_template)
)



# ================================defining neccessary functions================================
def qa(user_question):
    """_summary_
    Query data from Pinecone database and then feed it to GPT using the prompt template
    """
    
    # query data
    top_k=docsearch.similarity_search_with_score(query=user_question, k=3)
    page_content=[i[0].page_content for i in top_k]
    metadata=[top_k[i][0].metadata for i in range(len(top_k))]

    # feed to GPT
    response = llm_chain(
        {
            'user_question': user_question,
            'relevant_info': page_content
        }
    )
    return response['text'], metadata

res, metadata = qa("thời gian làm việc của nhân viên ITL") 

meta_list=[]
for index in range(len(metadata)):
    a = [i for i in metadata[index].values()]
    a = "/".join(a)
    meta_list.append(a)


# ================================STREAMLIT APP================================
import streamlit as st
import random
import time


st.title("ITL Internal AI Assistant 🤖")

# Writing the disclaimer
style = """
    <style>
        .disclaimer {
            background-color: #2F2724;
            padding: 10px;
            color: #A9A9A9;
            font-style: italic;
            border-radius: 5px;
        }
    </style>
"""

st.write(style, unsafe_allow_html=True)

st.markdown("""
<details class="disclaimer">
    <summary><strong><em>⚠️ Note:</em></strong></summary>
     <p style="padding-left: 16px">Câu trả lời của AI chỉ mang tính chất tương đối. Đối với thông tin quan trọng, người dùng cần kiểm tra các tài liệu được dẫn nguồn</p>
</details>
""", unsafe_allow_html=True)

# AI Assistant can make mistakes. Consider checking the provided source documents for important information.


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages: 
    with st.chat_message(message["role"]):
        st.markdown(message['content'])

# Check if greeting has been shown before
if "greeting_shown" not in st.session_state:
    st.session_state.greeting_shown = False

# Random greeting messages
if not st.session_state.greeting_shown:
    st.session_state.greeting_shown = True
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = random.choice(
            [
                "Hello there! I am ITL BOT, an Artificial Intelligent developed by ITL Corporation. How can I assist you today?",
                "Hi, ITL-ers! Is there anything ITL BOT can help you with?",
                "Hello! Do you have any question you want me to find answer for?",
            ]
        )
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages = [{"role": "assistant", "content": full_response}]


# React to user input
if prompt := st.chat_input("Ask questions about ITL's policies"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response 
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response, metadata = qa(user_question=prompt)
        
        # metadata
        meta_list=[]
        for index in range(len(metadata)):
            a = [i for i in metadata[index].values()]
            a = "/".join(a)
            meta_list.append(a)
        
        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split(" "):
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(f"""
{full_response}

**Thông tin chi tiết, tham khảo:**

{meta_list[0]}\n
{meta_list[1]}\n
{meta_list[2]}\n
""")
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
