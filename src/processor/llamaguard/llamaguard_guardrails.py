
from enum import Enum
from src.processor.llamaguard.llamaguard_utils import  LLAMA_GUARD_3_CATEGORY, SafetyCategory, AgentType, build_custom_prompt, create_conversation, LLAMA_GUARD_2_CATEGORY_SHORT_NAME_PREFIX, PROMPT_TEMPLATE_2
from typing import List
class LG3Cat(Enum):
    '''
    assigns number to each category.
    Will be used as an index to pull out specific safety category from the defined list of categories.
    Based on the policy applied for the customer.
    '''
    VIOLENT_CRIMES =  0
    NON_VIOLENT_CRIMES = 1
    SEX_CRIMES = 2
    CHILD_EXPLOITATION = 3
    DEFAMATION = 4
    SPECIALIZED_ADVICE = 5
    PRIVACY = 6
    INTELLECTUAL_PROPERTY = 7
    INDISCRIMINATE_WEAPONS = 8
    HATE = 9
    SELF_HARM = 10
    SEXUAL_CONTENT = 11
    ELECTIONS = 12
    CODE_INTERPRETER_ABUSE = 13

def get_lg3_categories(category_list: List[LG3Cat] = [], all: bool = False, custom_categories: List[SafetyCategory] = [] ):
    categories = list()
    if all:
        categories = list(LLAMA_GUARD_3_CATEGORY)
        categories.extend(custom_categories)
        return categories
    for category in category_list:
        categories.append(LLAMA_GUARD_3_CATEGORY[LG3Cat(category).value])
    categories.extend(custom_categories)
    return categories

# Examples

print("Specific categories example:")
for category in get_lg3_categories([LG3Cat.VIOLENT_CRIMES, LG3Cat.SEX_CRIMES]):
    print(category.name)

print("\n\n\nAll standard categories example:")
for category in get_lg3_categories([],True):
    print(category)


# from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
# from typing import List, Tuple
# from enum import Enum
# import torch

# model_id = "meta-llama/LlamaGuard-7b"
# device = "cuda"
# dtype = torch.bfloat16

# tokenizer = AutoTokenizer.from_pretrained(model_id)
# model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype, device_map="auto") #

def evaluate_safety(model, tokenizer, prompt = "", category_list = [], categories = []):
    # prompt = [([prompt], AgentType.USER)]
    prompt = [([prompt])]
    if categories == []:
        if category_list == []:
            categories = get_lg3_categories(all = True)
        else:
            categories = get_lg3_categories(category_list)

    formatted_prompt = build_custom_prompt(
            agent_type = AgentType.USER,
            conversations = create_conversation(prompt[0]),
            categories=categories,
            category_short_name_prefix = LLAMA_GUARD_2_CATEGORY_SHORT_NAME_PREFIX,
            prompt_template = PROMPT_TEMPLATE_2,
            with_policy = True)
    print("**********************************************************************************")
    print("Prompt: ", prompt)
    print("Formated Prompt: ", formatted_prompt)
    input = tokenizer([formatted_prompt], return_tensors="pt")
    prompt_len = input["input_ids"].shape[-1]
    output = model.generate(**input, max_new_tokens=10, pad_token_id=0,
                            eos_token_id=128009
                            )
    results = tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True)

    print("===================================")
    print("Results:")
    print(f"> {results}")
    return results
    print("\n==================================\n")