import streamlit as st
import requests
import openai
import xml.etree.ElementTree as ET

# Set OpenAI key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# MedlinePlus API for health info
MEDLINE_API = "https://wsearch.nlm.nih.gov/ws/query"

# Get brief MedlinePlus info with XML parsing
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
            root = ET.fromstring(response.text)
            summary = root.find(".//summary")
            return summary.text if summary is not None else "No summary available."
    except Exception:
        pass
    return None

# Ask GPT with conversation history
def ask_gpt(user_input, medline_data=None):
    system_prompt = """
Your good name is OURA — a warm, knowledgeable wellness assistant trained in functional medicine.

If this is the first message in the conversation, begin with a friendly greeting and ask for the user's first name to personalize the experience, then ask what health or wellness concern they'd like to talk about today.

For ongoing conversations, respond directly to the user's input, maintaining context from the conversation history provided. Do not repeat the initial greeting or name request unless the user explicitly resets the conversation.

Throughout the conversation:
- Respond naturally to casual or friendly messages (e.g., “How are you?”) with warm, human-like replies like “I'm doing great, thanks! How about you?”
- Use empathetic, simple, and caring language.
- Encourage the user to reflect on their symptoms, sleep, stress, nutrition, lifestyle, or health goals.
- If appropriate, suggest lab tests, supplements, or a consult with a provider via our telehealth platform.
- Always ask a kind, open-ended follow-up to keep the conversation going, unless the user indicates they are done.
- When the user indicates the conversation is ending (e.g., says "thank you", "that's all", "bye"), respond with a warm closing such as:
  “Wishing you wellness — I'm here anytime you'd like to check in again.”
  or
  “Take care and be well.”

Keep responses under 60 words unless more detail is needed.
"""

    # Build message history
    messages = [{"role": "system", "content": system_prompt.strip()}]

    # Limit history to last 10 exchanges to avoid token limit
    max_history = 10
    history = st.session_state.chat_history[-max_history:] if len(st.session_state.chat_history) > max_history else st.session_state.chat_history
    for speaker, message in history:
        role = "user" if speaker == "user" else "assistant"
        messages.append({"role": role, "content": message})

    # Add current user input
    content = f"User question: {user_input}"
    if medline_data:
        content += f"\n\nHere is factual health info from MedlinePlus:\n{medline_data}"
    messages.append({"role": "user", "content": content})

    # Call GPT with error handling
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.8
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Sorry, I encountered an issue: {str(e)}. Please try again."

# UI starts here
st.set_page_config(page_title="OURA Health Care Chatbot", page_icon="")
st.title("OURA Health Care Chatbot")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Reset conversation button
# if st.button("Reset Conversation"):
#     st.session_state.chat_history = []
#     st.experimental_rerun()

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
            if "lab" in user_input.lower() or "test" in user_input.lower():
                st.markdown("You might benefit from a [comprehensive lab panel](https://your-telehealth-platform.com/labs).")
            elif "supplement" in user_input.lower() or "vitamin" in user_input.lower():
                st.markdown("Consider these [evidence-based supplements](https://your-telehealth-platform.com/supplements).")
            elif "pain" in user_input.lower() or "chronic" in user_input.lower() or "serious" in reply.lower():
                st.markdown("[Schedule a consult](https://your-telehealth-platform.com/consult) with a licensed functional-medicine provider.")

        st.session_state.chat_history.append(("assistant", reply))
