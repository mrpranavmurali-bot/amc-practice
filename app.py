import os
import streamlit as st # type: ignore[reportMissingImports]
import anthropic as ar # pyright: ignore[reportMissingImports]
import json
import random
import plotly.graph_objects as go # type: ignore[reportMissingImports]
import base64

# Top image

# Session state variables start here

AUTHOR_NAME = "Pranav Murali"

# Stub for testing without API calls
STUB_MODE = False

# Log API calls and responses for debugging
LOG_MODE = True

# Get the API key from Streamlit secrets
api_key = st.secrets["ANTHROPIC_API_KEY"]

# Encouraging quotes for users
with open("encouragement.json", "r") as f:
    encouragement_data = json.load(f)

# Set difficulty
def set_difficulty(difficulty):
    diff_label = "Hard"
    if 1 <= difficulty <= 3:
        diff_label = "Easy"
    elif 4 <= difficulty < 7:
        diff_label = "Medium"
    return diff_label


if "screen" not in st.session_state:
    st.session_state.screen = "home"

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "score" not in st.session_state:
    st.session_state.score = 0

if "topic_results" not in st.session_state:
    st.session_state.topic_results = {}

if "difficulty" not in st.session_state:
    st.session_state.difficulty = 0

diff_label = set_difficulty(st.session_state.difficulty)

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "exam_complete" not in st.session_state:
    st.session_state.exam_complete = False

if "correct_count" not in st.session_state:
    st.session_state.correct_count = 0

if "wrong_count" not in st.session_state:
    st.session_state.wrong_count = 0

if "blank_count" not in st.session_state:
    st.session_state.blank_count = 0

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = None

if "question_submitted" not in st.session_state:
    st.session_state.question_submitted = False

# Initializing points system
Correct_pts = 6
Wrong_pts = 0
Blank_pts = 1.5

def generate_questions(num_questions, topic=None, difficulty=None):
    client = ar.Anthropic(api_key=api_key)
    if difficulty ==  None:
        difficulty = st.session_state.get('difficulty', 6)
    
    diff_label = set_difficulty(difficulty)
    
    topic_text = f"Focus all questions on {topic}." if topic else "Cover a variety of AMC 10 topics."
    prompt = f"Generate {num_questions} unique AMC 10 style questions with difficulty level {diff_label}. Format the output as a JSON array of objects, where each object has the following structure: {{'question': 'Question text here', 'options': ['A: answer text', 'B: answer text', 'C: answer text', 'D: answer text', 'E: answer text'], 'answer': 'Correct option letter here', 'topic': 'topic name here', 'solution': 'Step by step solution here'}}. Ensure that the questions are challenging and cover a variety of topics commonly found in AMC 10 exams. {topic_text}. No two sessions should have the same questions. The JSON should be properly formatted and parsable. Verify that each question has exactly one correct answer and that the answer is mathematically correct. Word problems are allowed and encouraged. Write all solutions in an impersonal, step-by-step mathematical style. ABSOLUTELY DO NOT use personal pronouns like 'we', 'our', 'I', 'me' or 'you'. Use passive voice or direct mathematical statements instead. For example: 'The equation is solved by...' or 'Substituting gives...' 'Please keep a organized format with headers and use Latex formatting for mathematical expressions where appropriate and organize the steps.And, do not make the user have to scroll through a wall of text for the solution. Break it up into at max 2-3 clear, concise steps with appropriate spacing and formatting. Please also don't make the user have to choose the closest answer. Make sure the correct answer is exactly one of the options and that the options are clearly labeled A through E. If an irrational decimal, it should be rounded to the nearest hundredth and the correct answer should reflect that rounding. Do not include any extraneous text or commentary in the output. Only output the JSON array of questions as specified, with no additional explanations or comments. I'd also appreciate it if you could ensure that the questions are original and not directly copied from existing AMC 10 exams or other sources, while still adhering to the style and difficulty level of AMC 10 questions. Thank you! The correct answer should be exactly one of the options and that option should be clearly labeled A to E.'"
    
    if STUB_MODE:
        print("STUB MODE: Returning pre-generated questions from JSON files instead of calling API.")
        # Return a stub response for testing
        if(num_questions == 15):
            #mini exam stub
            return json.load(open("mini_test.json"))
        elif(num_questions == 25):
            return json.load(open("full_test.json"))
        else:
            return json.load(open("general_practice.json"))
    # Simplified API call to avoid complex schema/tool parameters causing syntax issues
    print(f"Calling API with {num_questions} questions, difficulty={diff_label}")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10000,
    )
    try:
        text = response.content[0].text
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
        questions_data = json.loads(text)
        if LOG_MODE:
            print(f"Prompt: {prompt}")
            print(f"JSON response: {json.dumps(questions_data, indent=4)}")
        return questions_data
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        st.error(f"Failed to generate questions: {e}")
        return []


st.markdown(f"""
    <div style="color: #00bcd4; padding: 10px; border-radius: 8px; border: 1px solid #c9a84c; text-align: center;">
        <p style="color: #00bcd4; font-size: 14px; margin: 0;">An <strong><u>Actually Hard</u></strong> AMC 10 Practice Module created by <strong>{AUTHOR_NAME}</strong></p>
    </div>
""", unsafe_allow_html=True)
st.markdown("""
    <h1 style="color: #00ff00;">AIME LAB: An Actually Hard AMC 10 Practice Module</h1>
""", unsafe_allow_html=True)
st.markdown("""
    <h1 style="color: #00ff00;">Choose your practice mode</h1>
""", unsafe_allow_html=True)
st.markdown("""    <p style="color: #00bcd4; font-size: 16px;"> Note: Full solutions are offered for all practice modes, but only after you submit an answer (or choose to leave blank) for each question. This is to encourage active problem-solving and prevent users from simply reading through solutions without attempting the problems themselves. </p>""",
             unsafe_allow_html=True)

if st.session_state.screen == "home":
    if st.button("Full Practice Exam", key="full_exam"):
        st.session_state.difficulty = random.randint(6, 10)
        st.session_state.answers = []
        st.session_state.current_question = 0
        st.session_state.exam_complete = False
        st.session_state.correct_count = 0
        st.session_state.wrong_count = 0
        st.session_state.blank_count = 0
        with st.spinner("Generating..."):
            st.session_state.questions = generate_questions(25, difficulty=st.session_state.difficulty)
        st.session_state.screen = "full_exam"
        st.rerun()
    if st.button("Mini Practice Exam",  key="mini_exam"):
        st.session_state.difficulty = random.randint(6, 10)
        st.session_state.answers = []
        st.session_state.current_question = 0
        st.session_state.exam_complete = False
        st.session_state.correct_count = 0
        st.session_state.wrong_count = 0
        st.session_state.blank_count = 0
        with st.spinner("Generating... "):
            st.session_state.questions = generate_questions(15, difficulty=st.session_state.difficulty)
        st.session_state.screen = "mini_exam"
        st.rerun()
    if st.button("General Practice", key="general_practice"):
        st.session_state.screen = "practice_menu"
   
 
if st.session_state.screen == "practice_menu":
        st.subheader("Select a Topic to Practice")
        topics = ["Algebra", "Geometry", "Number Theory", "Probability-Statistics", "All Topics"]
        qchoice = st.number_input("How many questions?", min_value=1, max_value=25, value=5)
        for topic in topics:
            if st.button(topic, key=f"practice_{topic}"):
                st.session_state.selected_topic = topic
                st.session_state.answers = []
                st.session_state.current_question = 0
                st.session_state.exam_complete = False
                st.session_state.correct_count = 0
                st.session_state.wrong_count = 0
                st.session_state.blank_count = 0
                with st.spinner("Generating..."):
                    st.session_state.questions = generate_questions(qchoice, topic=topic, difficulty=st.session_state.difficulty)
                st.session_state.screen = "topic_practice"
                st.rerun()
                
if st.session_state.screen == "full_exam" and not st.session_state.exam_complete:
    st.write(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
    if st.session_state.current_question < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_question]
        st.write(q["question"])
        options = q["options"]
        selected_option = st.radio("Select your answer:", options)
        if st.button("Submit Answer", key=f"submit_{st.session_state.current_question}"):
            st.session_state.answers.append(selected_option)
            topic = q["topic"]
            if topic not in st.session_state.topic_results:
                st.session_state.topic_results[topic] = {"correct": 0, "wrong": 0, "blank": 0}
            if selected_option.startswith(q["answer"]):
                st.session_state.correct_count += 1
                st.session_state.topic_results[topic]["correct"] += 1
            else:
                st.session_state.wrong_count += 1
                st.session_state.topic_results[topic]["wrong"] += 1
            st.session_state.current_question += 1
            st.rerun()
        if st.button("Leave Blank", key=f"blank_practice_{st.session_state.current_question}"):
            st.session_state.answers.append(None)
            st.session_state.blank_count += 1
            topic = q["topic"]
            if topic not in st.session_state.topic_results:
                st.session_state.topic_results[topic] = {"correct": 0, "wrong": 0, "blank": 0}
            st.session_state.topic_results[topic]["blank"] += 1
            st.session_state.current_question += 1
            st.rerun()
        if st.session_state.current_question > 0 and st.button("Previous Question", key=f"prev_{st.session_state.current_question}"):
            st.session_state.current_question -= 1
            st.rerun()
        if st.session_state.current_question == len(st.session_state.questions) - 1:
            st.write("This is the last question. After submitting, you will see your results. Do you want to review your answers before submitting?")
            screen = st.radio("Choose an option:", ["Review Answers", "Submit Exam"])
            if screen == "Review Answers":
                for i, q in enumerate(st.session_state.questions):
                    st.write(f"**Question {i + 1}:** {q['question']}")
                    st.write(f"**Your Answer:** {st.session_state.answers[i] if i < len(st.session_state.answers) else 'No answer submitted'}")
                    # I want to use this screen for them to go back and change any answers if they want before submitting, so I won't show the correct answer or solution here. That way they can review their answers and make any last minute changes before seeing the solutions and correct answers in the final review screen after submission. I want to put all 25 questions in square buttons to go back to a question
                    if st.button(f"Go to Question {i + 1}", key=f"goto_{i}"):
                        st.session_state.current_question = i
                        st.rerun()
                    st.write("---")
                if st.button("Submit Exam", key="submit_final_practice"):
                    st.session_state.exam_complete = True
                    st.rerun()
    else:
        st.session_state.exam_complete = True
        st.rerun()

if st.session_state.screen == "mini_exam" and not st.session_state.exam_complete:
    st.write(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
    if st.session_state.current_question < len(st.session_state.questions):
        q = st.session_state.questions[st.session_state.current_question]
        st.write(q["question"])
        options = q["options"]
        selected_option = st.radio("Select your answer:", options)
        if st.button("Submit Answer", key=f"submit_{st.session_state.current_question}"):
            st.session_state.answers.append(selected_option)
            topic = q["topic"]
            if topic not in st.session_state.topic_results:
                st.session_state.topic_results[topic] = {"correct": 0, "wrong": 0, "blank": 0}
            if selected_option.startswith(q["answer"]):
                st.session_state.correct_count += 1
                st.session_state.topic_results[topic]["correct"] += 1
            else:
                st.session_state.wrong_count += 1
                st.session_state.topic_results[topic]["wrong"] += 1
            st.session_state.current_question += 1
            st.rerun()
        if st.button("Leave Blank", key=f"blank_practice_{st.session_state.current_question}"):
            st.session_state.answers.append(None)
            st.session_state.blank_count += 1
            topic = q["topic"]
            if topic not in st.session_state.topic_results:
                st.session_state.topic_results[topic] = {"correct": 0, "wrong": 0, "blank": 0}
            st.session_state.topic_results[topic]["blank"] += 1
            st.session_state.current_question += 1
            st.rerun()
        if st.session_state.current_question > 0 and st.button("Previous Question", key=f"prev_{st.session_state.current_question}"):
            st.session_state.current_question -= 1
            st.rerun()
        if st.session_state.current_question == len(st.session_state.questions) - 1:
            st.write("This is the last question. After submitting, you will see your results. Do you want to review your answers before submitting?")
            screen = st.radio("Choose an option:", ["Review Answers", "Submit Exam"])
            if screen == "Review Answers":
                for i, q in enumerate(st.session_state.questions):
                    st.write(f"**Question {i + 1}:** {q['question']}")
                    st.write(f"**Your Answer:** {st.session_state.answers[i] if i < len(st.session_state.answers) else 'No answer submitted'}")
                    if st.button(f"Go to Question {i + 1}", key=f"goto_mini_{i}"):
                        st.session_state.current_question = i
                        st.rerun()
                    st.write("---")
                if st.button("Submit Exam", key="submit_final_practice"):
                    st.session_state.exam_complete = True
                    st.rerun()
    else:
        st.session_state.exam_complete = True
        st.rerun()

if st.session_state.screen == "topic_practice":
    if st.session_state.current_question < len(st.session_state.questions):
        st.write(f"Practicing {st.session_state.selected_topic} - Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        q = st.session_state.questions[st.session_state.current_question]
        st.write(q["question"])
        options = q["options"]
        selected_option = st.radio("Select your answer:", options)
        if st.button("Submit Answer", key=f"submit_practice_{st.session_state.current_question}"):
            st.session_state.answers.append(selected_option)
            if selected_option.startswith(q["answer"]):
                st.write(f"✅ Correct! {random.choice(encouragement_data['correct'])}")
                solution_expander = st.expander("View Solution")
                with solution_expander:
                    st.write(q["solution"])
                st.write("Press any button to continue to the next question.")
                st.session_state.correct_count += 1
            else:
                st.write(f"❌ Wrong! {random.choice(encouragement_data['wrong'])}")
                solution_expander = st.expander("View Solution")
                with solution_expander:
                    st.write(q["solution"])
                st.write("Press any button to continue to the next question.")
                st.session_state.wrong_count += 1
            st.session_state.current_question += 1
        if st.button("Leave Blank", key=f"blank_practice_{st.session_state.current_question}"):
            st.session_state.answers.append(None)
            st.write(f"❌ Skipped! {random.choice(encouragement_data['wrong'])}")
            solution_expander = st.expander("View Solution")
            with solution_expander:
                st.write(q["solution"])
            st.write("Press any button to continue to the next question.")
            st.session_state.blank_count += 1
            topic = q["topic"]
            if topic not in st.session_state.topic_results:
                st.session_state.topic_results[topic] = {"correct": 0, "wrong": 0, "blank": 0}
            st.session_state.topic_results[topic]["blank"] += 1
            st.session_state.current_question += 1
        if st.session_state.current_question > 0 and st.button("Previous Question", key=f"prev_practice_{st.session_state.current_question}"):
            st.session_state.current_question -= 1
            st.rerun()
        if st.session_state.current_question == len(st.session_state.questions) - 1:
            st.write("This is the last question. After submitting, you will see your results. Do you want to review your answers before submitting?")
            screen = st.radio("Choose an option:", ["Review Answers", "Submit Exam"])
            if screen == "Review Answers":
                for i, q in enumerate(st.session_state.questions):
                    st.write(f"**Question {i + 1}:** {q['question']}")
                    st.write(f"**Your Answer:** {st.session_state.answers[i] if i < len(st.session_state.answers) else 'No answer submitted'}")
                    if st.button(f"Go to Question {i + 1}", key=f"goto_practice_{i}"):
                        st.session_state.current_question = i
                        st.rerun()
                    st.write("---")
                if st.button("Submit Exam", key="submit_final_practice"):
                    st.session_state.exam_complete = True
                    st.rerun()
    else:
        st.write("Practice Complete!")
        st.write(f"Correct: {st.session_state.correct_count}")
        st.write(f"Wrong: {st.session_state.wrong_count}")
        st.write(f"Blank: {st.session_state.blank_count}")
        if st.button("Back to Home", key="back_home_practice"):
            st.session_state.screen = "home"

if st.session_state.screen == "full_exam" and st.session_state.exam_complete:
    st.subheader("Exam Complete!")
    st.write(f"Correct: {st.session_state.correct_count}")
    st.write(f"Wrong: {st.session_state.wrong_count}")
    st.write(f"Blank: {st.session_state.blank_count}")
    score = (st.session_state.correct_count * Correct_pts) + (st.session_state.wrong_count * Wrong_pts) + (st.session_state.blank_count * Blank_pts)
    st.write(f"Your Score: {score} out of 150" )
    topic_breakdown = st.session_state.topic_results
    st.subheader("Topic Breakdown:")
    if st.session_state.topic_results:
        col1, col2, col3 = st.columns(3)
        topics = list(st.session_state.topic_results.keys())
        correct_vals = [r["correct"] for r in st.session_state.topic_results.values()]
        wrong_vals = [r["wrong"] for r in st.session_state.topic_results.values()]
        blank_vals = [r["blank"] for r in st.session_state.topic_results.values()]
        for col, title, values, color in [
            (col1, "Correct", correct_vals, ["#00ff00", "#00cc00", "#009900", "#006600", "#003300", "#00ff66"]),
            (col2, "Wrong", wrong_vals, ["#ff4444", "#cc0000", "#990000", "#ff0000", "#ff6666", "#cc3333"]),
            (col3, "Blank", blank_vals, ["#888888", "#666666", "#aaaaaa", "#444444", "#999999", "#bbbbbb"])
            ]:
            with col:
                fig = go.Figure(data=[go.Pie(
                    labels=topics,
                    values=values,
                    hole=0.6,
                    marker_colors=color
                      )])
                fig.update_layout(
                    title=title,
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                      height=300,
                      margin=dict(t=40, b=0, l=0, r=0)
                        )
                st.plotly_chart(fig, width=300, height=300)
        if st.button("Back to Home", key="back_home_full"):
            st.session_state.screen = "home"
            st.session_state.exam_complete = False
            st.session_state.topic_results = {}
        solutions_expander = st.expander("View Solutions")
        with solutions_expander:
            for i, q in enumerate(st.session_state.questions):
                st.write(f"**Question {i + 1}:** {q['question']}")
                if i < len(st.session_state.answers):
                    st.write(f"**Your Answer:** {st.session_state.answers[i]}")
                else:
                    st.write(f"**Your Answer:** No answer submitted")
                st.write(f"**Correct Answer:** {q['answer']}")
                st.write(f"**Solution:** {q['solution']}")
                st.write("---")


if st.session_state.screen == "mini_exam" and st.session_state.exam_complete:
    st.subheader("Exam Complete!")
    st.write(f"Correct: {st.session_state.correct_count}")
    st.write(f"Wrong: {st.session_state.wrong_count}")
    st.write(f"Blank: {st.session_state.blank_count}")
    score = (st.session_state.correct_count * Correct_pts) + (st.session_state.wrong_count * Wrong_pts) + (st.session_state.blank_count * Blank_pts)
    st.write(f"Your Score: {score} out of 90")
    topic_breakdown = st.session_state.topic_results
    st.subheader("Topic Breakdown:")
    if st.session_state.topic_results:
        col1, col2, col3 = st.columns(3)
        topics = list(st.session_state.topic_results.keys())
        correct_vals = [r["correct"] for r in st.session_state.topic_results.values()]
        wrong_vals = [r["wrong"] for r in st.session_state.topic_results.values()]
        blank_vals = [r["blank"] for r in st.session_state.topic_results.values()]
        for col, title, values, color in [
            (col1, "Correct", correct_vals, ["#00ff00", "#00cc00", "#009900", "#006600", "#003300", "#00ff66"]),
            (col2, "Wrong", wrong_vals, ["#ff4444", "#cc0000", "#990000", "#ff0000", "#ff6666", "#cc3333"]),
            (col3, "Blank", blank_vals, ["#888888", "#666666", "#aaaaaa", "#444444", "#999999", "#bbbbbb"])
            ]:
            with col:
                fig = go.Figure(data=[go.Pie(
                    labels=topics,
                    values=values,
                    hole=0.6,
                    marker_colors=color
                      )])
                fig.update_layout(
                    title=title,
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                      height=300,
                      margin=dict(t=40, b=0, l=0, r=0)
                      )
                st.plotly_chart(fig, width=300, height=300)
        if st.button("Back to Home", key="back_home_mini"):
            st.session_state.screen = "home"
            st.session_state.exam_complete = False
            st.session_state.topic_results = {}
        solutions_expander = st.expander("View Solutions")
        with solutions_expander:
            for i, q in enumerate(st.session_state.questions):
                st.write(f"**Question {i + 1}:** {q['question']}")
                if i < len(st.session_state.answers):
                    st.write(f"**Your Answer:** {st.session_state.answers[i]}")
                else:
                    st.write(f"**Your Answer:** No answer submitted")
                st.write(f"**Correct Answer:** {q['answer']}")
                st.write(f"**Solution:** {q['solution']}")
                st.write("---")
