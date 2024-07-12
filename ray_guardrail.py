
from flask import Flask, request, jsonify
from pymongo import MongoClient
from guardrails_ai_functions import GuardrailsAi
import logging
import ray
from ray import serve

guardrails_ai_obj = GuardrailsAi()

class Guardrail(object) :

    def __init__(self,uri,client):
        self.uri = uri
        self.client= client
        self.kritaka_admin_db = self.client['kritaka_admin']
        self.kritaka_ragaas_db = self.client['kritaka_ragaas']
        self.kritaka_guardaas_db = self.client['kritaka_guardaas']

    def get_guardrails_metadata(self, guardrail_policy_id, guardrail_type):
        # Retrieve guardrail policies for the given customer from MongoDB
        try:
            collection = self.kritaka_guardaas_db['guardrails_metadata']
            # print(type(guardrail_policy_id))
            ret_iterator = collection.find({"guardrail_policy_id": guardrail_policy_id, "policy_category": guardrail_type})
            guardrails_policies = list(ret_iterator)
            if guardrails_policies:
                # print("guardrails_policies: ", guardrails_policies)
                logging.info(f"guardrails_policies: {guardrails_policies}")
                return guardrails_policies
            else:
                return []
        except Exception as e:
            return []

        
    def get_guardrail_policies(self,customer_id):
        try:
            # Retrieve guardrail policies for the given customer from MongoDB
            collection = self.kritaka_admin_db['customer_policies']
            policies = collection.find_one({'customer_id': customer_id})
            if policies:
                return policies #{'_id': ObjectId('667b39c9fdd9d80c58aed6ec'), 'customer_id': 12345, 'rag_policy': {'semantic_search': {}, 'prompt': {}}, 'guardrail_policy': [12345, 30000, 12346]}
            else:
                return []
        except Exception as e:
            logging.error("Exception while fetching guardrail policies: {e}")


    def apply_policy_parallely(self, engine, policy_names, handle, text):
        policy_functions = {
            "detect_prompt_injection": handle.detect_prompt_injection,
            "detect_toxic_language": handle.detect_toxic_language,
            "competitor_check": handle.competitor_check,
            "detect_pii": handle.detect_pii,
            "gibberish_text": handle.gibberish_text,
            "profanity_free": handle.profanity_free,
            "wiki_provenance": handle.wiki_provenance,
            "correct_language": handle.correct_language,
            "nsfw_text": handle.nsfw_text,
            "RestrictToTopic": handle.restricttotopic,
            "saliency_check": handle.saliency_check,
            "secrets_present": handle.secrets_present,
            "EndpointIsReachable": handle.endpoint_is_reachable,
            "ends_with": handle.ends_with,
            "financial_tone": handle.financial_tone,
            "has_url": handle.has_url,
            "mentions_drugs": handle.mentions_drugs,
            "politeness_check": handle.politeness_check,
        }
        
        result_obj = [policy_functions[policy].remote(text) for policy in policy_names]

        return [result.result() for result in result_obj]
    

    def apply_policies(self,text, policies, guardrail_type, handle):
        # Apply guardrail policies to the given text

        policy_functions = {
            "detect_prompt_injection": guardrails_ai_obj.detect_prompt_injection,
            "detect_toxic_language": guardrails_ai_obj.detect_toxic_language,
            "competitor_check": guardrails_ai_obj.competitor_check,
            "detect_pii": guardrails_ai_obj.detect_pii,
            "gibberish_text": guardrails_ai_obj.gibberish_text,
            "profanity_free": guardrails_ai_obj.profanity_free,
            "wiki_provenance": guardrails_ai_obj.wiki_provenance,
            "correct_language": guardrails_ai_obj.correct_language,
            "nsfw_text": guardrails_ai_obj.nsfw_text,
            "RestrictToTopic": guardrails_ai_obj.restricttotopic,
            "saliency_check": guardrails_ai_obj.saliency_check,
            "secrets_present": guardrails_ai_obj.secrets_present,
            "EndpointIsReachable": guardrails_ai_obj.endpoint_is_reachable,
            "ends_with": guardrails_ai_obj.ends_with,
            "financial_tone": guardrails_ai_obj.financial_tone,
            "has_url": guardrails_ai_obj.has_url,
            "mentions_drugs": guardrails_ai_obj.mentions_drugs,
            "politeness_check": guardrails_ai_obj.politeness_check,
        }
        
        results = {}
        guardrail_policy_ids = policies.get("guardrail_policy", [])


        
        seq_guard_policy = policies.get("guardrail_policy", {}).get("sequential", [])
        parallel_guard_policy = policies.get("guardrail_policy", {}).get("parallel", [])
        #seq_guard_policy = guardrail_policy_ids #guardrail_policy_ids.get("sequential", [])
        #parallel_guard_policy = guardrail_policy_ids #guardrail_policy_ids.get("parallel", [])

        policy_name_list = []
        for guardrail_policy_id in parallel_guard_policy:
            guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
            if guardrail_policy:
                engine = guardrail_policy[0].get("policy_engine")
                policy_name = guardrail_policy[0].get("policy_name")
                policy_name_list.append(policy_name)
                print("Engine is: ", engine)
                print("List of policy name is: ", policy_name_list)
                par_result = self.apply_policy_parallely(engine, policy_name_list, handle, text)
        #return par_result



        

        
        # Apply sequential policies
        sequential_results = {}
        current_text = text
        for guardrail_policy_id in seq_guard_policy:
            guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
            if guardrail_policy:
                engine = guardrail_policy[0].get("policy_engine")
                policy_name = guardrail_policy[0].get("policy_name")
                if policy_name in policy_functions:
                    # Execute policy function synchronously
                    try:
                        '''
                        result_obj = [policy_functions[policy].remote(text) for policy in policy_names]

                        return [result.result() for result in result_obj]
                        '''

                        current_text = policy_functions[policy_name].remote(current_text).result()
                        sequential_results[policy_name] = current_text
                    except Exception as e:
                        sequential_results[policy_name] = str(e)
                        break



        # if not isinstance(guardrail_policy_ids, list):
        #     guardrail_policy_ids = [guardrail_policy_ids]

        # start_time = time.time()
        # for guardrail_policy_id in guardrail_policy_ids:
        #     guardrail_policy = self.get_guardrails_metadata(guardrail_policy_id, guardrail_type)
        #     if guardrail_policy:
        #         engine = guardrail_policy[0].get("policy_engine")
        #         policy_name = guardrail_policy[0].get("policy_name")
                
        #         if engine == "guardrails.ai" and policy_name in policy_functions:
        #             try:
        #                 logging.info(f"Applying {policy_name} policy using GuardrailsAI Engine..")
        #                 result = policy_functions[policy_name](text)
        #                 logging.info(f"{policy_name}: {result}")
        #                 results[policy_name] = result
        #             except Exception as e:
        #                 logging.error("Error while applying Guardrails.ai policy: %s", e)
        #                 results.append({"policy": policy_name, "error": str(e)})
        #     else:
        #         logging.warning(f"No metadata found for guardrail_policy_id: {guardrail_policy_id}")
        
        # logging.info("--- %s seconds ---" % (time.time() - start_time))
        

        return results