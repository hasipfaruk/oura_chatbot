import streamlit as st
import requests
import openai

# Set OpenAI key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# MedlinePlus API for health info
MEDLINE_API = "https://wsearch.nlm.nih.gov/ws/query"

# Get brief MedlinePlus info
def get_medlineplus_info(query):
    params = {
        "db": "healthTopics",
        "term": query,
        "rettype": "brief",
        "retmax": 1
    }
    try:
        response = requests.get(MEDLINE_API, params=params)
        if response.status_code == 200 and "<record>" in response.text:
            return response.text
    except Exception:
        pass
    return None




def ask_gpt(user_input, medline_data=None):
    system_prompt = """
You good name is  OURA — a warm, knowledgeable wellness assistant trained in functional medicine.

Begin the conversation with a friendly greeting and ask for the user's first name to personalize the experience.

Then, ask what health or wellness concern they'd like to talk about today.

Throughout the conversation:

Respond naturally to casual or friendly messages (e.g., “How are you?”) with warm, human-like replies like “I'm doing great, thanks! How about you?”

Use empathetic, simple, and caring language.

Encourage the user to reflect on their symptoms, sleep, stress, nutrition, lifestyle, or health goals.

If appropriate, suggest lab tests, supplements, or a consult with a provider via our telehealth platform.

Always ask a kind, open-ended follow-up to keep the conversation going.

When the user indicates the conversation is ending (e.g., says "thank you", "that's all", "bye"), respond with a warm closing such as:
“Wishing you wellness — I'm here anytime you'd like to check in again.”
or
“Take care and be well.”

Keep responses under 60 words unless more detail is needed..
"""


    content = f"User question: {user_input}"
    if medline_data:
        content += f"\n\nHere is factual health info from MedlinePlus:\n{medline_data}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": content}
        ],
        temperature=0.8
    )
    return response["choices"][0]["message"]["content"]





# UI starts here
st.set_page_config(page_title="Wellness Chatbot", page_icon="")
st.title("Wellness Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display past messages
for speaker, message in st.session_state.chat_history:
    if speaker == "user":
        with st.chat_message("user"):
            st.markdown(message)
    else:
        with st.chat_message("assistant"):
            st.markdown(message)

# Real-time user input
user_input = st.chat_input("Ask about symptoms, supplements, labs...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    with st.spinner("Thinking..."):
        med_data = get_medlineplus_info(user_input)
        reply = ask_gpt(user_input, med_data)

        with st.chat_message("assistant"):
            st.markdown(reply)

            # Smart suggestions based on content
            if "lab" in user_input or "test" in user_input:
                st.markdown(" You might benefit from a [comprehensive lab panel](https://your-telehealth-platform.com/labs).")
            elif "supplement" in user_input or "vitamin" in user_input:
                st.markdown(" Consider these [evidence-based supplements](https://your-telehealth-platform.com/supplements).")
            elif "pain" in user_input or "chronic" in user_input or "serious" in reply.lower():
                st.markdown(" [Schedule a consult](https://your-telehealth-platform.com/consult) with a licensed functional-medicine provider.")

        st.session_state.chat_history.append(("assistant", reply))
