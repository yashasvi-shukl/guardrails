import ray
from ray import serve
from guardrails import Guard
#from guardrails.hub import * #DetectPromptInjection, ToxicLanguage
from guardrails.hub import NSFWText, GibberishText, DetectPromptInjection, ToxicLanguage, CompetitorCheck, ProfanityFree, WikiProvenance, SensitiveTopic, MentionsDrugs,HasUrl, SecretsPresent,RestrictToTopic ,CorrectLanguage ,SaliencyCheck ,FinancialTone, EndsWith,EndpointIsReachable , PolitenessCheck
import openai
import guardrails as gd
from guardrails.validators import PIIFilter
import os
import logging

# Set the environment variable for OpenAI API key
os.environ['OPENAI_API_KEY'] = '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'


# Initialize Ray and Ray Serve
ray.init(ignore_reinit_error=True)
serve.start()

@serve.deployment(
    # specify the number of GPU's available; zero if it is run on cpu
    ray_actor_options={"num_cpus": 10},
    # the number of instances of the  deployment in the cluster
    autoscaling_config={"min_replicas": 1, "max_replicas": 2},
    # the concurrency of the deployment
    max_concurrent_queries=50,
)
class GuardrailsAi:
    # def __init__(self):
    #     self.guard = Guard()
    
    def detect_prompt_injection(self, prompt):
        # create a pinecone index called "detect-prompt-injection" before running this
        guard = Guard().with_prompt_validation(validators=[DetectPromptInjection(
            pinecone_index="detect-prompt-injection",
            on_fail="exception"
            )])
        # guard = Guard.from_string(validators=[]).with_prompt_validation(validators=[DetectPromptInjection(
        #     pinecone_index="detect-prompt-injection",
        #     on_fail="exception"
        #     )])
        
        # guard = Guard().with_prompt_validation(validators=[DetectPromptInjection(
        #         pinecone_index="detect-prompt-injection",
        #         on_fail="exception"
        #         )])
        
        try:
            response = guard(
                llm_api=openai.chat.completions.create,
                prompt=prompt,
            )
            logging.info(response)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        

    def detect_toxic_language(self, text):
        guard = gd.Guard.from_string(
        validators=[ToxicLanguage( threshold=0.5, validation_method="sentence", on_fail="exception")],
        description="testmeout",
        )
        try:
            output = guard.parse(
            llm_output=text,
            metadata={}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return  outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return  outcome_dict

    
    def detect_pii(self, text):

        pii_list = ["US_SSN", "US_DRIVER_LICENSE","EMAIL_ADDRESS", "PHONE_NUMBER"]
        # Setup Guard
        #guard = Guard().use(DetectPII, pii_list, "exception")
        # guard.validate("Good morning!")  # Validator passes
        guard = gd.Guard.from_string(
        validators=[PIIFilter(pii_entities="pii", on_fail="fix")],
        description="testmeout",
        )
    
        
        try:
            output = guard.parse(
            llm_output=text,
            metadata={"pii_entities": pii_list },
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
    
    def competitor_check(self, text):
        competitor_list = ["Apple", "Samsung"]
        #guard = Guard().use(CompetitorCheck, competitor_list, "exception")
        guard = gd.Guard.from_string(
        validators=[CompetitorCheck(competitors=competitor_list, on_fail="fix")],
        description="testmeout",
        )

        try:
            #guard.validate(text)
            output = guard.parse(
            llm_output=text,
            metadata={},
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
            return outcome_dict
        except Exception as e:
            return {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
        
    def gibberish_text(self, text):
        # Use the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[GibberishText(threshold=0.5, validation_method="sentence", on_fail="exception")],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        

    def nsfw_text(self, text):
        # Use the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[NSFWText(threshold=0.8, validation_method="sentence", on_fail="exception")],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict 
        
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def profanity_free(self, text):
        # Use the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[ProfanityFree(on_fail="exception")],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def correct_language(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[CorrectLanguage(expected_language_iso="en", threshold=0.75,on_fail= 'exception')],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def restrict_to_topic(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[RestrictToTopic(
        valid_topics=["sports"],
        invalid_topics=["music"],
        disable_classifier=True,
        disable_llm=False,
        on_fail="exception"
        )],
        description="testmeout",
        )

        # guard.validate("""
        # In Super Bowl LVII in 2023, the Chiefs clashed with the Philadelphia Eagles in a fiercely contested battle, ultimately emerging victorious with a score of 38-35.
        # """)  # Validator passes

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def secrets_present(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[SecretsPresent(on_fail="exception")],
        description="testmeout",
        )
        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict 
        
    def endpoint_is_reachable(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[EndpointIsReachable(on_fail="exception")],
        description="testmeout",
        )

        # response = guard.validate("https://www.guardrailsai.com/")  # Validator passes

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def ends_with(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[EndsWith(end="a",on_fail="exception")],
        description="testmeout",
        )
        # response = guard.validate("Llama")  # Validator passes

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict


    def financial_tone(self, text):
        # Use the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[FinancialTone(on_fail="exception")],
        description="testmeout",
        )
        # Test passing response
        # guard.validate(
        #     "Growth is strong and we have plenty of liquidity.",
        #     metadata={"financial_tone": "positive"}
        # )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={"financial_tone": "positive"}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def has_url(self, text):
            # Setup Guard
            guard = gd.Guard.from_string(
            validators=[HasUrl(on_fail='exception')],
            description="testmeout",
            )

            # guard.validate("guardrailsai.com")  # Validator passes
            try:
                output = guard.parse(
                llm_output=text,
                metadata={}, 
                )
                outcome_dict = {
                "raw_llm_input": output.raw_llm_output,
                "validated_output": None,
                "validation_passed": output.validation_passed
                }
                return outcome_dict #"Test Passed"
            except Exception as e:
                outcome_dict = {
                "raw_llm_input": text,
                "validated_output": None,
                "validation_passed": False
                }
                return outcome_dict
                
    def mentions_drugs(self, text):
        # Setup the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[MentionsDrugs(on_fail="exception")],
        description="testmeout",
        )

        # Test passing response
        # guard.validate("You should take this medicine every day after breakfast.")

        
        try:
            output = guard.parse(
            llm_output=text,
            metadata={}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
                
    def politeness_check(self, text):
        # Setup Guard
        guard = gd.Guard.from_string(
        validators=[PolitenessCheck(
        llm_callable="gpt-3.5-turbo",
        on_fail="exception")],
        description="testmeout",
        )
        try:
            output = guard.parse(
            llm_output=text,
            metadata={}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return  outcome_dict

    def sensitive_topics(self, text):
        guard = gd.Guard.from_string(
        validators=[SensitiveTopic(
        sensitive_topics=["politics"],
        disable_classifier=False,
        disable_llm=False,
        on_fail="exception")],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    def wiki_provenance(self, text):
        # Use the Guard with the validator
        guard = gd.Guard.from_string(
        validators=[WikiProvenance(
        topic_name="Apple company",
        validation_method="sentence",
        llm_callable="gpt-3.5-turbo",
        on_fail="exception")],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={"pass_on_invalid": True}, 
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict

    def saliency_check(self, text):
        # Initialize The Guard with this validator
        guard = gd.Guard.from_string(
        validators=[SaliencyCheck(
        "assets/", # name of your directry where source file store 
        llm_callable="gpt-3.5-turbo",
        threshold=0.1,
        on_fail="exception",)],
        description="testmeout",
        )

        try:
            output = guard.parse(
            llm_output=text,
            metadata={ }, # no additional metadata are needed for this
            )
            outcome_dict = {
            "raw_llm_input": output.raw_llm_output,
            "validated_output": None,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            outcome_dict = {
            "raw_llm_input": text,
            "validated_output": None,
            "validation_passed": False
            }
            return outcome_dict
        
    # def contains_string(self, text):
    #     guard = gd.Guard.from_string(
    #     validators=[ContainsString(substring="s", on_fail="exception")],
    #     description="testmeout",
    #     )

    #     try:
    #         output = guard.parse(
    #         llm_output=text,
    #         metadata={}, 
    #         )
    #         outcome_dict = {
    #         "raw_llm_input": output.raw_llm_output,
    #         "validated_output": None,
    #         "validation_passed": output.validation_passed
    #         }
    #         return  outcome_dict #"Test Passed"
    #     except Exception as e:
    #         outcome_dict = {
    #         "raw_llm_input": text,
    #         "validated_output": None,
    #         "validation_passed": False
    #         }
    #         return  outcome_dict
