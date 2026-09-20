from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from agents.tools import AGENT_TOOLS
from core.config import settings

AGENT_SYSTEM_PROMPT = (
    "You are CareerCopilot's career assistant agent. You help candidates understand "
    "how well their resume matches a job, what skills they are missing, and how to "
    "close those gaps. Always use the available tools to gather real data about the "
    "candidate's resume and the job description before answering. Never guess or "
    "invent information. When asked for a roadmap, first call calculate_match_score "
    "to find missing skills, then call create_learning_plan with those missing skills. "
    "For each significant missing skill, you may also call recommend_learning_resources "
    "(docs + video links), get_flashcards, get_quiz, or get_interview_questions if the "
    "candidate would benefit from them. Summarize everything clearly for the candidate "
    "at the end."
)


def build_career_agent():
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.2,
    )
    return create_react_agent(llm, AGENT_TOOLS, prompt=AGENT_SYSTEM_PROMPT)


async def run_career_agent(user_message: str) -> str:
    agent = build_career_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": user_message}]})
    messages = result.get("messages", [])
    if not messages:
        return "I couldn't generate a response."
    content = messages[-1].content
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
        text = "\n".join(text_parts).strip()
        if text:
            return text

    return "I couldn't generate a text roadmap. Please try again."
