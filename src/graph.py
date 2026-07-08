import time
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from google import genai
from google.genai.errors import ServerError

from src.config import GEMINI_API_KEY
from src.generate import generate_answer

client = genai.Client(api_key=GEMINI_API_KEY)


class GraphState(TypedDict):
    """The shared 'clipboard' that travels through every node in the graph."""
    question: str
    needs_retrieval: Optional[bool]
    answer: Optional[str]
    sources: Optional[list]
    history: list  # list of {"question": ..., "answer": ...} from previous turns


def call_gemini_with_retry(model, contents, max_retries=3, delay_seconds=10):
    """
    Calls Gemini, retrying a few times if the server is temporarily
    overloaded (503), instead of crashing immediately.
    """
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except ServerError as e:
            if attempt < max_retries - 1:
                print(f"  [Retry] Server busy, waiting {delay_seconds}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay_seconds)
            else:
                raise e


def format_history(history, limit=3):
    """
    Turn the last few conversation turns into readable text for a prompt.
    Capped at `limit` turns so the prompt doesn't grow unbounded as a
    conversation gets longer (a simple 'sliding window' memory).
    """
    if not history:
        return ""

    recent_turns = history[-limit:]
    formatted = "\n".join(
        f"Q: {turn['question']}\nA: {turn['answer']}" for turn in recent_turns
    )
    return f"Previous conversation:\n{formatted}\n\n"


def router_node(state: GraphState) -> GraphState:
    """
    Decide whether this question needs document retrieval, or can be
    answered directly without touching the vector database at all.
    """
    question = state["question"]
    history_text = format_history(state.get("history", []))

    routing_prompt = f"""{history_text}Determine if this question is about Docker, Kubernetes, or FastAPI 
— even generally, even if you already know the answer, and even if it's a follow-up referring 
to the previous conversation. If the topic is Docker, Kubernetes, or FastAPI in any way, always 
answer YES, since we want to ground answers in our official documentation rather than general 
knowledge. Only answer NO if the question is completely unrelated to these three topics 
(e.g. greetings, small talk, general knowledge, math, or the user sharing personal info like their name).

Question: {question}

Respond with exactly one word: YES or NO."""

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=routing_prompt,
    )

    decision = response.text.strip().upper()
    needs_retrieval = "YES" in decision

    print(f"[Router] Decision: {'retrieve documents' if needs_retrieval else 'answer directly'}")

    return {**state, "needs_retrieval": needs_retrieval}


def rag_node(state: GraphState) -> GraphState:
    """Run the existing retrieve + generate pipeline, passing conversation history through."""
    result = generate_answer(state["question"], history=state.get("history", []))
    return {**state, "answer": result["answer"], "sources": result["sources"]}


def direct_answer_node(state: GraphState) -> GraphState:
    """Answer directly, without any document retrieval, but still aware of prior turns."""
    history_text = format_history(state.get("history", []))

    prompt = f"""You are a helpful assistant having an ongoing conversation. 
Use the conversation history below to remember facts the user has already told you 
(like their name), and answer naturally as a continuation of the conversation.

{history_text}Current question: {state['question']}

Answer:"""

    print(f"\n[DEBUG] Full prompt sent to model:\n{prompt}\n")

    response = call_gemini_with_retry(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )
    return {**state, "answer": response.text, "sources": []}


def route_decision(state: GraphState) -> str:
    """Tells the graph which node to go to next, based on the router's decision."""
    return "rag_node" if state["needs_retrieval"] else "direct_answer_node"


def build_graph():
    """Assemble the graph: nodes, edges, and the conditional routing logic."""
    workflow = StateGraph(GraphState)

    workflow.add_node("router_node", router_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("direct_answer_node", direct_answer_node)

    workflow.add_edge(START, "router_node")

    workflow.add_conditional_edges(
        "router_node",
        route_decision,
        {
            "rag_node": "rag_node",
            "direct_answer_node": "direct_answer_node",
        },
    )

    workflow.add_edge("rag_node", END)
    workflow.add_edge("direct_answer_node", END)

    return workflow.compile()


if __name__ == "__main__":
    graph = build_graph()
    history = []

    test_questions = [
        "How do I stop my container from losing data on restart?",
        "What about for Kubernetes instead?",
        "My name is Hiruni",
        "Do you know my name?",
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        result = graph.invoke({
            "question": question,
            "needs_retrieval": None,
            "answer": None,
            "sources": None,
            "history": history,
        })
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")

        history.append({"question": question, "answer": result["answer"]})