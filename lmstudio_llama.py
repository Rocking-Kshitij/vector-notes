from typing import Any, Dict, Iterator, List, Mapping, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from ollama import Client
import time, requests
# this class connects to lmstudio and implements it in langchain

class CustomLLamaLLM(LLM):
    llama_model: str

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

        history = [{"role": "user", "content": prompt}]
        output = client.chat.completions.create(
            model=self.llama_model,
            messages = history,
            temperature=0.8,
        ).choices[0].message.content
        if kwargs.get('prompt_show') == True:
            return output, prompt
        else:
            return output

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters."""
        return {
            # The model name allows users to specify custom token counting
            # rules in LLM monitoring applications (e.g., in LangSmith users
            # can provide per token pricing for their model and monitor
            # costs for the given LLM.)
            "model_name": "llama_lmstudio",
        }

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model. Used for logging purposes only."""
        return "custom"


class CustomEmbedding(Embeddings):
    embedding_model : str
    """ParrotLink embedding model integration.

    # TODO: Populate with relevant params.
    Key init args — completion params:
        model: str
            Name of ParrotLink model to use.

    See full list of supported init args and their descriptions in the params section.

    # TODO: Replace with relevant init params.
    Instantiate:
        .. code-block:: python

            from langchain_parrot_link import ParrotLinkEmbeddings

            embed = ParrotLinkEmbeddings(
                model="...",
                # api_key="...",
                # other params...
            )

    Embed single text:
        .. code-block:: python

            input_text = "The meaning of life is 42"
            embed.embed_query(input_text)

        .. code-block:: python

            # TODO: Example output.

    # TODO: Delete if token-level streaming isn't supported.
    Embed multiple text:
        .. code-block:: python

             input_texts = ["Document 1...", "Document 2..."]
            embed.embed_documents(input_texts)

        .. code-block:: python

            # TODO: Example output.

    # TODO: Delete if native async isn't supported.
    Async:
        .. code-block:: python

            await embed.aembed_query(input_text)

            # multiple:
            # await embed.aembed_documents(input_texts)

        .. code-block:: python

            # TODO: Example output.

    """

    def __init__(self, embedding_model: str):
        self.embedding_model = embedding_model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embedding_client = OpenAI(
        api_key = "lm-studio",
        base_url = "http://127.0.0.1:1234/v1")
        data = texts
        # embedding_model = "text-embedding-nomic-embed-text-v1.5@q8_0"
        def get_embedding(embedding_client, model_name, text_input):
            output = embedding_client.embeddings.create(input = text_input, model=model_name)
            embedding = []
            for embedding_object in output.data:
                embedding.append(embedding_object.embedding)
            return embedding
        data_embeddings = [get_embedding(embedding_client = embedding_client, model_name = self.embedding_model, text_input= text)[0] for text in data]
        return data_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.embed_documents([text])[0]

    # optional: add custom async implementations here
    # you can also delete these, and the base class will
    # use the default implementation, which calls the sync
    # version in an async executor:

    # async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
    #     """Asynchronous Embed search docs."""
    #     ...

    # async def aembed_query(self, text: str) -> List[float]:
    #     """Asynchronous Embed query text."""
    #     ...



class OllamaCustomLLamaLLM(LLM):
    model: str
    url:str

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        client = Client(host = self.url)

        history = [{"role": "user", "content": prompt}]
        output = client.chat(model=self.model, messages=[
              {
                'role': 'user',
                'content': prompt,
              },
            ])['message']['content']
        if kwargs.get('prompt_show') == True:
            return output, prompt
        else:
            return output

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters."""
        return {
            # The model name allows users to specify custom token counting
            # rules in LLM monitoring applications (e.g., in LangSmith users
            # can provide per token pricing for their model and monitor
            # costs for the given LLM.)
            "model_name": "ollama_remote",
        }

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model. Used for logging purposes only."""
        return "custom"




class OllamaCustomFastAPILLM(LLM):
    model: str
    url:str
    sleep_time:int

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        params = {"question": prompt, "model": self.model}
        i = 0
        for i in range(20): # check for message 20 times
            response = requests.get(self.url, params=params).json()
            if response["status"] == "processing":
                i+=1
            else:
                output = response["message"]
                break
            time.sleep(self.sleep_time) # check every 20 s for result
        i = 0
        if kwargs.get('prompt_show') == True:
            return output, prompt
        else:
            return output

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters."""
        return {
            # The model name allows users to specify custom token counting
            # rules in LLM monitoring applications (e.g., in LangSmith users
            # can provide per token pricing for their model and monitor
            # costs for the given LLM.)
            "model_name": "ollama_fastapi",
        }

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model. Used for logging purposes only."""
        return "custom"
