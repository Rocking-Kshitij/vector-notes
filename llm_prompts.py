from langchain_core.prompts import PromptTemplate
from config import llm


def remove_thoughts(input):
    data = input[input.rfind('</think>')+10:]
    return data



get_question_prompt = PromptTemplate(
    # subject, topic, subtopic
    input_variable={"content": "content"},
    template="""Generate a appropriate prompt for below information / code snippet in concise language. Provided information / code snippet should be appropriate answer to the prompt you create.
    Note that:
        1) Only provide the prompt. Nothing else.
        2) Keep prompt very concise and technical.
        3) Dont be descriptive but use technical keywords.
    Here is the information / code snippet:
    {content}
    """
)


get_question_chain = get_question_prompt | llm | remove_thoughts

get_description_prompt = PromptTemplate(
    input_variable={"problem": "problem", "solution": "solution"},
    template = """
        Explain in clear, simple, concise and logical way :
        Problem : {problem}
        Solution : {solution}
    """
)

get_description_chain = get_description_prompt | llm | remove_thoughts