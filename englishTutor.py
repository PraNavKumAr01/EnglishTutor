import streamlit as st
import io
import base64
import os
import sys
from deepgram import DeepgramClient, SpeakOptions
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_groq import ChatGroq

# Set up environment variables and API keys
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
os.environ["DEEPGRAM_API_KEY"] = st.secrets["DEEPGRAM_API_KEY"]

llm = ChatGroq(temperature=0, model_name="llama3-8b-8192")

def text_to_speech(transcript):
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

def execute_python_code(code):
    try:
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        exec(code)
        output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def english_tutor():
    st.header("English Tutor")
    
    option = st.selectbox("Select an option:", ["Have a Conversation", "Improve Your Vocabulary", "Test Your Grammar"])

    if "prev_option" not in st.session_state:
        st.session_state.prev_option = option
    elif st.session_state.prev_option != option:
        st.session_state.conversation_history = []
        st.session_state.prev_option = option

    if option == "Have a Conversation":
        conversation_style = st.selectbox("Conversation Style:", ["Formal", "Casual"])
    if option == "Test Your Grammar":
        user_level = st.selectbox("What is your level in English", ["Expert", "Intermediate", "Beginner"])

    question = st.text_area("Start the chat")

    if st.button("Submit"):
        if len(st.session_state.conversation_history) > 10:
            st.session_state.conversation_history = st.session_state.conversation_history[-10:]

        if option == "Have a Conversation":
            if conversation_style == "Formal":
                prompt = "You are an English tutor in disguise having a formal conversation with a student. Respond to their questions or statements in a professional and academic manner. Always keep the conversation going, Instead of asking them what they want to talk about, suggest topics (make sure these topics are friendly to students) and start talking about them to motivate the user to get into a conversation and try to get them to talk to you by initializing the conversation, but below your response to the conversation put a review of what the user said and if they used good English or what could have been a better way to say it"
            else:
                prompt = "You are an English tutor in disguise having a casual conversation with a student. Respond to their questions or statements in a friendly and casual manner. Always keep the conversation going, Instead of asking them what they want to talk about, suggest topics (make sure these topics are friendly to students) and start talking about them to motivate the user to get into a conversation and try to get them to talk to you by initializing the conversation, but below your response to the conversation put a review of what the user said and if they used good English or what could have been a better way to say it"
        
            response, review = get_conversation_response(question, prompt)

            audio_bytes = text_to_speech(response)
            audio_file = io.BytesIO(audio_bytes)
            st.audio(audio_file, format='audio/wav')

            st.success(f"Tutor's response: {response}")
            if review:
                st.info(review)

        elif option == "Improve Your Vocabulary":
            prompt = "You are an English tutor in disguise helping a student improve their vocabulary. Provide detailed explanations and examples like antonyms and similar words to what the student asks"
            response = get_response(question, prompt)
            st.success(f"Tutor's response: {response}")

        else:
            prompt = f"You are an English tutor in disguise helping a student by testing their grammar. Give them exercises according to their level which is {user_level}, like fill in the blanks to complete this sentence, or change the tense of this sentence and then provide them with a review and help them get better"
            response = get_response(question, prompt)
            st.success(f"Tutor's response: {response}")

def python_tutor():
    st.header("Python Tutor")

    option = st.selectbox("Select an option:", ["Python Theory", "Code Exercises"])

    if "prev_option" not in st.session_state:
        st.session_state.prev_option = option
    elif st.session_state.prev_option != option:
        st.session_state.conversation_history = []
        st.session_state.current_response = ""
        st.session_state.exercise_answer = ""
        st.session_state.prev_option = option

    if option == "Python Theory":
        topic = st.selectbox("Select a topic:", ["Variables", "Data Types", "Control Structures", "Functions", "Object-Oriented Programming"])
        
        starter_questions = {
            "Variables": ["What is a variable?", "How to declare?", "Naming conventions?"],
            "Data Types": ["Basic data types?", "Type conversion?", "Mutable vs Immutable?"],
            "Control Structures": ["If-else statements?", "For loops?", "While vs For loops?"],
            "Functions": ["Defining functions?", "Parameters & arguments?", "Return vs Print?"],
            "Object-Oriented Programming": ["What is a class?", "Creating objects?", "What are methods?"]
        }

        st.write("Starter Questions:")
        cols = st.columns(3) 
        for i, question in enumerate(starter_questions[topic]):
            with cols[i % 3]:
                if st.button(question, key=f"{topic}_{i}"):
                    prompt = f"You are a Python tutor explaining the concept of {topic} to a beginner. The question is: {question}"
                    st.session_state.current_response = get_response(question, prompt)

        custom_question = st.text_area("Or ask your own question about the selected topic:")
        if st.button("Submit Custom Question"):
            prompt = f"You are a Python tutor explaining the concept of {topic} to a beginner. Provide a clear and concise explanation with examples."
            st.session_state.current_response = get_response(custom_question, prompt)

        if st.session_state.current_response:
            st.markdown("### Tutor's Response:")
            st.success(st.session_state.current_response)

    elif option == "Code Exercises":
        difficulty = st.selectbox("Select difficulty:", ["Beginner", "Intermediate", "Advanced"])
        exercise_type = st.selectbox("Select exercise type:", ["Complete the Code", "Debug the Code", "Implement a Function"])

        if st.button("Generate Exercise"):
            prompt = f"You are a Python tutor creating a {difficulty} level {exercise_type} exercise. Provide a problem statement and initial code if necessary. After that, provide the complete solution to the exercise."
            response = get_response("Generate a Python exercise with solution", prompt)
            
            parts = response.split("Solution:", 1)
            exercise = parts[0].strip()
            st.session_state.exercise_answer = parts[1].strip() if len(parts) > 1 else "No solution provided."

            st.markdown("### Exercise:")
            st.markdown(exercise)

        st.markdown("### Your Solution:")
        user_solution = st.text_area("Enter your solution here:", height=200)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Run Code"):
                output = execute_python_code(user_solution)
                st.markdown("### Output:")
                st.code(output, language="python")
        with col2:
            if st.button("Submit for Review"):
                prompt = f"You are a Python tutor reviewing a {difficulty} level {exercise_type} solution. Analyze the following code, provide feedback, and suggest improvements if necessary:"
                response = get_response(user_solution, prompt)
                st.markdown("### Tutor's Feedback:")
                st.info(response)
        with col3:
            if st.button("Show Answer", key="show_answer_button"):
                st.markdown("### Exercise Answer:")
                st.markdown(st.session_state.exercise_answer)

def main():
    st.title("AI Tutor")

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "current_response" not in st.session_state:
        st.session_state.current_response = ""
    if "exercise_answer" not in st.session_state:
        st.session_state.exercise_answer = ""

    tutor_type = st.sidebar.selectbox("Choose a tutor:", ["English", "Python"])

    if tutor_type == "English":
        english_tutor()
    else:
        python_tutor()

    if st.button("Clear History"):
        st.session_state.conversation_history.clear()
        st.session_state.current_response = ""
        st.session_state.exercise_answer = ""

if __name__ == "__main__":
    main()
