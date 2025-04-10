
from flask import Flask, request, jsonify
from src.processor.guardrailsAi.guardrails_ai_functions import GuardrailsAi
from src.processor.llamaguard.llamaguard_guardrails import LG3Cat
from src.processor.llamaguard.llamaguard_guardrails import evaluate_safety
import logging
import ray
import asyncio
from ray import serve
import time
from src.processor.nemo_guardrails.nemo_guard import check_response
import yaml
import os
from langchain_openai.chat_models import ChatOpenAI
from src.processor.utils import load_llamaguard_model, load_llamaguard_tokenizer
from nemoguardrails import RailsConfig, LLMRails
import torch
guardrails_ai_obj = GuardrailsAi()
global llamaguard_model, llamaguard_tokenizer

# os.environ['DISABLE_NEST_ASYNCIO'] = "true"
import ray
ray.init(ignore_reinit_error=True)
with open("/home/aisearch/projects/GaurdRaaS/src/config/gaurdrail_config.yaml") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Initialize Ray
# asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())



class Guardrail(object) :

    def __init__(self, uri, client, rails_input_model, rails_output_model, llamaguard_tokenizer=None, llamaguard_model=None):
        
        self.uri = uri
        self.client= client
        self.kritaka_admin_db = self.client['kritaka_admin']
        self.kritaka_ragaas_db = self.client['kritaka_ragaas']
        self.kritaka_guardaas_db = self.client['kritaka_guardaas']
        self.llamaguard_tokenizer = llamaguard_tokenizer
        self.llamaguard_model = llamaguard_model
        self.rails_input_model = rails_input_model
        self.rails_output_model = rails_output_model


    def get_guardrails_metadata(self, guardrail_policy_id, guardrail_type):
        # Retrieve guardrail policies for the given customer from MongoDB
        try:
            collection = self.kritaka_guardaas_db['guardrails_metadata']
            ret_iterator = collection.find({"guardrail_policy_id": guardrail_policy_id, "policy_category": guardrail_type})
            guardrails_policies = list(ret_iterator)
            if guardrails_policies:
                logging.info(f"guardrails_policies: {guardrails_policies}")
                return guardrails_policies
            else:
                return []
        except Exception as e:
            return []

        
    def get_guardrail_policies(self,customer_id):
        try:
            collection = self.kritaka_admin_db['customer_policies']
            policies = collection.find_one({'customer_id': customer_id})
            if policies:
                return policies 
            else:
                return []
        except Exception as e:
            logging.error("Exception while fetching guardrail policies: {e}")

    @ray.remote
    def apply_guardrailsai_policies_parallely(policy_names, handle, text):
        logging.info("Applying guardrails.ai policies..")
        par_result = {}
        policy_functions = {
            "detect_pii": handle.detect_pii,
            "detect_prompt_injection": handle.detect_prompt_injection,
            "restrict_to_topic": handle.restrict_to_topic,
            "secrets_present": handle.secrets_present,
            "detect_toxic_language": handle.detect_toxic_language,
            "profanity_free": handle.profanity_free,
            "correct_language": handle.correct_language,
            "competitor_check": handle.competitor_check, 
            "saliency_check": handle.saliency_check,
            "gibberish_text": handle.gibberish_text,
            "nsfw_text": handle.nsfw_text,
            "EndpointIsReachable": handle.endpoint_is_reachable,
            "ends_with": handle.ends_with,
            "financial_tone": handle.financial_tone,
            "has_url": handle.has_url,
            "mentions_drugs": handle.mentions_drugs,
            "politeness_check": handle.politeness_check,
            "sensitive_topics": handle.sensitive_topics,
            "wiki_provenance": handle.wiki_provenance
        }

        policy_names = [policy for policy in policy_names if policy in policy_functions ]
        logging.info(f"Parallel Policies - Guardrails AI: {policy_names}")
        result_obj = [policy_functions[policy].remote(text) for policy in policy_names]
        for policy_name, result in zip(policy_names, result_obj):
            par_result[policy_name] = result.result()
        
        logging.info(f"GuardrailsAI Result: {par_result}")
        return par_result
    

    @ray.remote
    def apply_llamaguard_policies(policy_names, text):
        logging.info("Applying llamaguard policies..")

        policy_functions = {
            "violent_crimes" : LG3Cat.VIOLENT_CRIMES,
            "non_violent_crimes" : LG3Cat.NON_VIOLENT_CRIMES,
            "sex_crimes" : LG3Cat.SEX_CRIMES,
            "child_exploitation" : LG3Cat.CHILD_EXPLOITATION,
            "defamation" : LG3Cat.DEFAMATION,
            "specialized_advice" : LG3Cat.SPECIALIZED_ADVICE,
            "privacy" : LG3Cat.PRIVACY,
            "intellectual_property" : LG3Cat.INTELLECTUAL_PROPERTY,
            "indiscriminate_wepons" : LG3Cat.INDISCRIMINATE_WEAPONS,
            "hate" : LG3Cat.HATE,
            "self_harm" : LG3Cat.SELF_HARM,
            "sexual_content" : LG3Cat.SEXUAL_CONTENT,
            "elections" : LG3Cat.ELECTIONS,
            "code_interpreter_abuse" : LG3Cat.CODE_INTERPRETER_ABUSE
        }

        policy_names = [policy_functions[policy_name] for policy_name in policy_names]
        logging.info(f"Parallel Policies - LlamaGuard: {policy_names}")
        result = evaluate_safety(
            model = ray.get(llamaguard_model), 
            tokenizer = ray.get(llamaguard_tokenizer), 
            prompt = text,
            category_list=policy_names
            )
        logging.info(f"LlamaGuard Result: {result}")
        return result
    
    
    def apply_nemoguard_policies(self, text, guardrail_type):

        os.environ['OPENAI_API_KEY'] = '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'
        llm = ChatOpenAI()
        if guardrail_type == "PreLLM":
            nemo_input_config = RailsConfig.from_path(config["nemo_input_prompt"])
            rails_model = LLMRails(config=nemo_input_config, llm=llm)
        elif guardrail_type == "PostLLM":
            nemo_output_config = RailsConfig.from_path(config['nemo_output_prompt'])
            rails_model = LLMRails(config=nemo_output_config, llm = llm)


        query = [{
                "role": "user",
                "content": text
            }]
        logging.info("Applying nemo-guardrails on input")
        response = check_response(query=query, rails_model=rails_model)
        logging.info(f"Nemoguard - Response: {response}")
        return response
    
    @ray.remote
    def apply_sequential_policies(policy_names, handle, text):
        policy_functions = {
            "detect_pii": guardrails_ai_obj.detect_pii,
            "detect_prompt_injection": guardrails_ai_obj.detect_prompt_injection,
            "restrict_to_topic": guardrails_ai_obj.restrict_to_topic,
            "secrets_present": guardrails_ai_obj.secrets_present,
            "detect_toxic_language": guardrails_ai_obj.detect_toxic_language,
            "profanity_free": guardrails_ai_obj.profanity_free,
            "correct_language": guardrails_ai_obj.correct_language,
            "competitor_check": guardrails_ai_obj.competitor_check,
            "saliency_check": guardrails_ai_obj.saliency_check,
            "gibberish_text": guardrails_ai_obj.gibberish_text,
            "nsfw_text": guardrails_ai_obj.nsfw_text,
            "EndpointIsReachable": guardrails_ai_obj.endpoint_is_reachable,
            "ends_with": guardrails_ai_obj.ends_with,
            "financial_tone": guardrails_ai_obj.financial_tone,
            "has_url": guardrails_ai_obj.has_url,
            "mentions_drugs": guardrails_ai_obj.mentions_drugs,
            "politeness_check": guardrails_ai_obj.politeness_check,
            "sensitive_topics": guardrails_ai_obj.sensitive_topics,
            "wiki_provenance": guardrails_ai_obj.wiki_provenance
        }
        start_time = time.time()
        seq_text = text
        seq_result = []

        for policy_name in policy_names:
            if policy_name in policy_functions:
                try:
                    result = {}
                    logging.info(f"Sequential: Applying {policy_name}")
                    output = policy_functions[policy_name](seq_text)
                    result[policy_name] = output
                    logging.info(f"Sequential - Output: {result}")
                    seq_result.append(result)
                    if output['validated_output'] is not None:
                        seq_text = output['validated_output']
                except Exception as e:
                    logging.error("Error while applying Guardrails.ai policy: %s", e)

        logging.info("--- Sequential: Total time take - %s seconds ---" % (time.time() - start_time))
        return seq_result

    def apply_policies(self,text, policies, guardrail_type, handle):
        # Apply guardrail policies to the given text

        policy_functions = {
            "detect_pii": guardrails_ai_obj.detect_pii,
            "detect_prompt_injection": guardrails_ai_obj.detect_prompt_injection,
            "restrict_to_topic": guardrails_ai_obj.restrict_to_topic,
            "secrets_present": guardrails_ai_obj.secrets_present,
            "detect_toxic_language": guardrails_ai_obj.detect_toxic_language,
            "profanity_free": guardrails_ai_obj.profanity_free,
            "correct_language": guardrails_ai_obj.correct_language,
            "competitor_check": guardrails_ai_obj.competitor_check,
            "saliency_check": guardrails_ai_obj.saliency_check,
            "gibberish_text": guardrails_ai_obj.gibberish_text,
            "nsfw_text": guardrails_ai_obj.nsfw_text,
            "EndpointIsReachable": guardrails_ai_obj.endpoint_is_reachable,
            "ends_with": guardrails_ai_obj.ends_with,
            "financial_tone": guardrails_ai_obj.financial_tone,
            "has_url": guardrails_ai_obj.has_url,
            "mentions_drugs": guardrails_ai_obj.mentions_drugs,
            "politeness_check": guardrails_ai_obj.politeness_check,
            "sensitive_topics": guardrails_ai_obj.sensitive_topics,
            "wiki_provenance": guardrails_ai_obj.wiki_provenance
        }
        
        # guardrail_policy_ids = policies.get("guardrail_policy", [])
        seq_guard_policy = policies.get("guardrail_policy", {}).get("sequential", [])
        parallel_guard_policy = policies.get("guardrail_policy", {}).get("parallel", [])

        logging.info(f"Parallel policies: {parallel_guard_policy}")
        logging.info(f"Sequential policies: {seq_guard_policy}")

        policies_per_engine = {
            "guardrails.ai" : [],
            "llamaguard" : [],
            "nemoguard" : [],
            "sequential": []
        }
        policies_per_engine_results = {
            "parallel": None,
            "sequential": None
        }

        if seq_guard_policy:
            for guardrail_policy_id in seq_guard_policy:
                guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
                if guardrail_policy:
                    # engine = guardrail_policy[0].get("policy_engine")
                    policy_name = guardrail_policy[0].get("policy_name")
                    policies_per_engine['sequential'].append(policy_name)
            logging.info(f"List of sequential policies to be applied: {policies_per_engine['sequential']}")
            
        if parallel_guard_policy:
            for guardrail_policy_id in parallel_guard_policy:
                guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
                logging.info("Guardrail policy: {guardrail_policy}")

                if guardrail_policy:
                    engine = guardrail_policy[0].get("policy_engine")
                    if engine == "guardrails.ai":
                        policy_name = guardrail_policy[0].get("policy_name")
                        policies_per_engine['guardrails.ai'].append(policy_name)
                    elif engine == "llamaguard":
                        policy_name = guardrail_policy[0].get("policy_name")
                        policies_per_engine['llamaguard'].append(policy_name)
                    elif engine == "nemoguard":
                        policy_name = guardrail_policy[0].get("policy_name")
                        policies_per_engine['nemoguard'].append(policy_name)

            logging.info(f"Policy per Engine: {policies_per_engine}")
            
            # if guardrail_type == "PreLLM":
            #     rails_model = self.rails_input_model
            # elif guardrail_type == "PostLLM":
            #     rails_model = self.rails_output_model


            if policies_per_engine:
                response = {}
                for engine, policies in policies_per_engine.items():
                    if engine == "guardrails.ai" and policies:
                        print("Applying guardrails.ai using remote")
                        response['guardrails.ai'] = self.apply_guardrailsai_policies_parallely.remote(policies, handle, text)
                        # logging.info(f"GuardrailsAI response: {response['guardrails.ai']}")
                    elif engine == "llamaguard" and policies:
                        print("Applying llamaguard using remote")
                        response['llamaguard'] = self.apply_llamaguard_policies.remote(policies, text)

                    elif engine == "sequential" and policies:
                        print("Applying Sequential policies using remote")
                        response['sequential'] = self.apply_sequential_policies.remote(policies, handle, text)

                        # logging.info(f"Llamaguard response: {response['llamaguard']}")
                    elif engine == "nemoguard" and policies:
                        print("Applying nemoguard using remote")
                        response['nemoguard'] = self.apply_nemoguard_policies(text, guardrail_type)
                    #     # logging.info(f"Nemoguard response: {response['nemoguard']}")
                logging.info(f"Ray result object: {response}")
                # policies_per_engine_results['sequential'] = response
                # ray.shutdown()
                ray_result = [{engine: ray.get(res) if engine != 'nemoguard' else res} for engine, res in response.items()]

                print("Ray result: ", ray_result)

                policies_per_engine_results['parallel'] = ray_result
                # ray.shutdown()
            # if policies_per_engine:
            #     response = {}
            #     if policies_per_engine['guardrails.ai']:
                    
            #         logging.info(f"Engine is: Guardrails.ai")
            #         logging.info(f"Policies to be applied parallely: {policies_per_engine['guardrails.ai']}")
            #         start_time = time.time()
            #         response['guardrails.ai'] = self.apply_guardrailsai_policies_parallely(
            #                                                                     policies_per_engine['guardrails.ai'], 
            #                                                                     handle, 
            #                                                                     text
            #                                                                     )
            #         logging.info("--- Total time for Parallel processing: %s seconds ---" % (time.time() - start_time))
            #         logging.info(f"Guardrails AI Results: {response['guardrails.ai']}")
            #     else:
            #         logging.info("No guardrails.ai policy for parallel processing.")

            #     if policies_per_engine['nemoguard']:
            #         logging.info(f"Engine is: nemoguard")
            #         logging.info(f"Policies to be applied parallely: {policies_per_engine['nemoguard']}")
            #         start_time = time.time()
            #         response['nemoguard'] = self.apply_nemoguard_policies(text, guardrail_type)
            #         logging.info("--- Total time for Parallel processing of nemoguard: %s seconds ---" % (time.time() - start_time))
            #         logging.info(f"NemoGuard Results: {response['nemoguard']}")
            
            #     else:
            #         logging.info("No nemoguard policy for parallel processing.")
            #     policies_per_engine_results['parallel'] = response

                
            #     if policies_per_engine['llamaguard']:
            #         logging.info(f"Engine is: llamaguard")
            #         logging.info(f"Policies to be applied parallely: {policies_per_engine['llamaguard']}")
            #         start_time = time.time()
            #         response['llamaguard'] = self.apply_llamaguard_policies(policies_per_engine['llamaguard'], text)
            #         logging.info("--- Total time for Parallel processing: %s seconds ---" % (time.time() - start_time))
            #         logging.info(f"LlamaGuard Results: {response['llamaguard']}")
            
            #     else:
            #         logging.info("No llamaguard policy for parallel processing.")

            # else:
            #     logging.info("Failed to fetch parallel policy")
                



        # # Apply sequential policies
        # logging.info(f"Sequential Policies: {seq_guard_policy}")
        # start_time = time.time()

        # if not isinstance(seq_guard_policy, list):
        #     seq_guard_policy = [seq_guard_policy]

        # start_time = time.time()
        # seq_text = text
        # seq_result = []
        # for guardrail_policy_id in seq_guard_policy:
        #     guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
        #     if guardrail_policy:
        #         engine = guardrail_policy[0].get("policy_engine")
        #         policy_name = guardrail_policy[0].get("policy_name")
        #         logging.info(f"Checking {policy_name}")
        #         if engine == "guardrails.ai" and policy_name in policy_functions:
        #             try:
        #                 result = {}
        #                 logging.info(f"Sequential: Applying {policy_name}")
        #                 output = policy_functions[policy_name](seq_text)
        #                 result[policy_name] = output
        #                 logging.info(f"Sequential - Output: {result}")
        #                 seq_result.append(result)
        #                 seq_text = output['validated_output']
        #             except Exception as e:
        #                 logging.error("Error while applying Guardrails.ai policy: %s", e)
        #     else:
        #         logging.warning(f"No metadata found for guardrail_policy_id: {guardrail_policy_id}")
        
        # logging.info("--- Sequential: Total time take - %s seconds ---" % (time.time() - start_time))
        # policies_per_engine_results['sequential'] = seq_result

        return ray_result 
    