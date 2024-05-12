import streamlit as st
import io
import base64
import os
from deepgram import DeepgramClient, SpeakOptions
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_groq import ChatGroq

llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", api_key=st.secrets["GROQ_API_KEY"])

def text_to_speech(transcript):
    os.environ["DEEPGRAM_API_KEY"] = st.secrets["DEEPGRAM_API_KEY"]

    try:
        deepgram = DeepgramClient()
        speak_options = {"text": transcript}

        options = SpeakOptions(
            model="aura-stella-en",
            encoding="linear16",
            container="wav"
        )

        response = deepgram.speak.v("1").stream(speak_options, options)

        return response.stream.getvalue()

    except Exception as e:
        print(f"Exception: {e}")

def get_response(question, prompt):

    prompt_template = PromptTemplate(
        input_variables=["question", "history"],
        template=prompt + "{history}\nHuman: {question}",
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.invoke({"question": question, "history": "\n".join(st.session_state.conversation_history)})

    response = result["text"]

    st.session_state.conversation_history.append(f"Human: {question}")
    st.session_state.conversation_history.append(f"Assistant: {response}")

    return response

def get_conversation_response(question, prompt):

    prompt_template = PromptTemplate(
        input_variables=["question", "history"],
        template=prompt + "{history}\nHuman: {question}",
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.invoke({"question": question, "history": "\n".join(st.session_state.conversation_history)})
    response_content = result["text"]
    
    if "Review:" in response_content:
        response_parts = response_content.split('Review:')
        conversation_response = response_parts[0].strip()
        review = 'Review:'.join(response_parts[1:]).strip()
    else:
        conversation_response = response_content.strip()
        review = None

    st.session_state.conversation_history.append(f"Human: {question}")
    st.session_state.conversation_history.append(f"Assistant: {response_content}")

    return conversation_response, review

def main():
    st.title("English Tutor")

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    option = st.selectbox("Select an option:", ["Have a Conversation", "Improve Your Vocabulary", "Test Your Grammer"])

    if "prev_option" not in st.session_state:
        st.session_state.prev_option = option
    elif st.session_state.prev_option != option:
        st.session_state.conversation_history = []
        st.session_state.prev_option = option

    if option == "Have a Conversation":
        conversation_style = st.selectbox("Conversation Style:", ["Formal", "Casual"])
    if option == "Test Your Grammer":
        user_level = st.selectbox("What is your level in english", ["Expert", "Intermediate", "Beginner"])

    question = st.text_area("Start the chat")

    if st.button("Submit"):

        if len(st.session_state.conversation_history) > 10:
            st.session_state.conversation_history[-10:]

        if option == "Have a Conversation":

            if conversation_style == "Formal":
                prompt = "You are an English tutor in disguise having a formal conversation with an indian student who is around the age of 50. Respond to their questions or statements in a professional and academic manner. Always keep the conversation going, Instead of asking them what they want to talk about, suggest topics (make sure these topics are friendly to indians and also someone who is around 50 years old) and start talking about them to motivate the user to get into a conversation and try to get them to talk to you by initialiting the conversation, but below your response to the conversatoin put a review of what the user said and if they used good english or what could have been a better way to say it"
            else:
                prompt = "You are an English tutor in disguise having a casual conversation with an indian student who is around the age of 50. Respond to their questions or statements in a friendly and casual manner. Always keep the conversation going, Instead of asking them what they want to talk about, suggest topics (make sure these topics are friendly to indians and also someone who is around 50 years old) and start talking about them to motivate the user to get into a conversation and try to get them to talk to you by initialiting the conversation, but below your response to the conversatoin put a review of what the user said and if they used good english or what could have been a better way to say it"
        
            response, review = get_conversation_response(question, prompt)

            audio_bytes = text_to_speech(response)
            audio_file = io.BytesIO(audio_bytes)
            st.audio(audio_file, format='audio/wav')

            st.success(f"Tutors response: {response}")
            if review:
                st.info(review)


        elif option == "Improve Your Vocabulary":

            prompt = "You are an English tutor in disguise helping an indian student who is around the age of 50 improve their vocabulary. Provide detailed explanations and examples like anonyms and similar words to what the student asks"
            response = get_response(question, prompt)
            st.success(f"Tutors response: {response}")

        else:

            prompt = f"You are an English tutor in disguise helping an indian student who is around the age of 50 by testing their grammer. Give them exercises according to their level which is {user_level}, like fill in the blanks to complete this sentences, or change the tense of this sentence and then provide them with a review and help them get better"
            response = get_response(question, prompt)
            st.success(f"Tutors response: {response}")

if __name__ == "__main__":
    main()
