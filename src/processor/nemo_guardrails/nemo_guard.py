import os
import nest_asyncio
nest_asyncio.apply()

from nemoguardrails import RailsConfig, LLMRails
from typing import Optional, Union, List
from langchain.llms.base import BaseLLM
from nemoguardrails.patch_asyncio import check_sync_call_from_async_loop
from nemoguardrails.utils import get_or_create_event_loop
from nemoguardrails.rails.llm.options import GenerationOptions


class NemoRails(LLMRails):
    config: RailsConfig
    llm: Optional[BaseLLM]


    def generate(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[dict]] = None,
        return_context: bool = False,
        options: Optional[Union[dict, GenerationOptions]] = None,
        state: Optional[dict] = None,
    ):
        """Synchronous version of generate_async."""

        if check_sync_call_from_async_loop():
            raise RuntimeError(
                "You are using the sync `generate` inside async code. "
                "You should replace with `await generate_async(...)` or use `nest_asyncio.apply()`."
            )

        loop = get_or_create_event_loop()

        return loop.run_until_complete(
            self.generate_async(
                prompt=prompt,
                messages=messages,
                options=options,
                state=state,
                return_context=return_context,
            )
        )

# Function to print and check response compliance
def check_response(query, rails_model):
    response = rails_model.generate(messages=query)
    content = response["content"]
    print("Response: ", response)
    return response
