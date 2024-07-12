import ray
from ray import serve
from guardrails import Guard
#from guardrails.hub import * #DetectPromptInjection, ToxicLanguage
from guardrails.hub import DetectPromptInjection , ToxicLanguage, GibberishText , CompetitorCheck, PIIFilter
import openai
import guardrails as gd

import os

# Set the environment variable for OpenAI API key
os.environ['OPENAI_API_KEY'] = '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'


# Initialize Ray and Ray Serve
ray.init(ignore_reinit_error=True)
serve.start()

@serve.deployment(
    # specify the number of GPU's available; zero if it is run on cpu
    ray_actor_options={"num_cpus": 5},
    # the number of instances of the  deployment in the cluster
    autoscaling_config={"min_replicas": 1, "max_replicas": 10},
    # the concurrency of the deployment
    max_concurrent_queries=50,
)
class GuardrailsAi:
    # async def __init__(self):
    #     self.guard = Guard()
    
    async def detect_prompt_injection(self, prompt):
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
            guard(
                llm_api=openai.chat.completions.create,
                prompt=prompt,
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    async def detect_toxic_language(self, text):
        guard = Guard().use(
                        ToxicLanguage, threshold=0.5, validation_method="sentence", on_fail="exception"
                    )
        try:
            # Test failing response
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    async def gibberish_text(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            GibberishText, threshold=0.5, validation_method="sentence", on_fail="exception"
        )

        # Test passing response
        # guard.validate(
        #     "Azure is a cloud computing service created by Microsoft. It's a significant competitor to AWS."
        # )
        try:
            guard.validate(
                text
                )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    async def detect_pii(self, text):

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
            "raw_llm_output": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
            return outcome_dict #"Test Passed"
        except Exception as e:
            return "Test Failed"
    
    async def competitor_check(self, text):
        competitor_list = ["Apple", "Samsung"]
        #guard = Guard().use(CompetitorCheck, competitor_list, "exception")
        guard = gd.Guard.from_string(
        validators=[CompetitorCheck(competitors=competitor_list, on_fail="fix")],
        description="testmeout",
        )

        # response = guard.validate(
        # "The apple doesn't fall far from the tree."
        # )  # Validator passes

        try:
            #guard.validate(text)
            output = guard.parse(
            llm_output=text,
            metadata={},
            )
            outcome_dict = {
            "raw_llm_output": output.raw_llm_output,
            "validated_output": output.validated_output,
            "validation_passed": output.validation_passed
            }
            return outcome_dict
        except Exception as e:
            return "Test Failed"
        
        
    '''
    async def competitor_check(self, text):
        competitor_list = ["Apple", "Samsung"]
        guard = Guard().use(CompetitorCheck, competitor_list, "exception")

        # response = guard.validate(
        # "The apple doesn't fall far from the tree."
        # )  # Validator passes

        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

            
    async def detect_pii(self, text):

        pii_list = ["EMAIL_ADDRESS", "PHONE_NUMBER"]
        # Setup Guard
        guard = Guard().use(DetectPII, pii_list, "exception")
        # guard.validate("Good morning!")  # Validator passes
        
        try:
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    
       
    async def profanity_free(self, text):
        # Use the Guard with the validator
        guard = Guard().use(ProfanityFree, on_fail="exception")

        # # Test passing response
        # guard.validate(
        #     """
        #     Director Denis Villeneuve's Dune is a visually stunning and epic adaptation of the classic science fiction novel.
        #     It is reminiscent of the original Star Wars trilogy, with its grand scale and epic storytelling.
        #     """
        # )

        try:
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
    
    async def wiki_provenance(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            WikiProvenance,
            topic_name="Apple company",
            validation_method="sentence",
            llm_callable="gpt-3.5-turbo",
            on_fail="exception"
        )

        # Test passing response
        # guard.validate("Apple was founded by Steve Jobs in April 1976.", metadata={"pass_on_invalid": True})  # Pass

        # Test failing response
        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

    
    async def correct_language(self, text):
        # Setup Guard
        guard = Guard().use(
            CorrectLanguage(expected_language_iso="en", threshold=0.75)
        )

        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    async def nsfw_text(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            NSFWText, threshold=0.8, validation_method="sentence", on_fail="exception"
        )

        # Test passing response
        # guard.validate(
        #     "Christopher Nolan's Tenet is a mind-bending action thriller that will keep you on the edge of your seat. The film is a must-watch for all Nolan fans."
        # )

        try:
            
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

       
    async def restricttotopic(self, text):
        # Setup Guard
        guard = Guard().use(
            RestrictToTopic(
                valid_topics=["sports"],
                invalid_topics=["music"],
                disable_classifier=True,
                disable_llm=False,
                on_fail="exception"
            )
        )

        # guard.validate("""
        # In Super Bowl LVII in 2023, the Chiefs clashed with the Philadelphia Eagles in a fiercely contested battle, ultimately emerging victorious with a score of 38-35.
        # """)  # Validator passes

        try:
            guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

        
    async def saliency_check(self, text):
        # Initialize The Guard with this validator
        guard = Guard().use(
            SaliencyCheck,
            "assets/",
            llm_callable="gpt-3.5-turbo",
            threshold=0.1,
            on_fail="exception",
        )

        # Test passing response
        # guard.validate(
        #     """
        #     San Francisco is a major Californian city, known for its finance, culture, and density. 
        #     Originally inhabited by the Yelamu tribe, the city grew rapidly during the Gold Rush and became a major West Coast port. 
        #     Despite a devastating earthquake and fire in 1906, San Francisco rebuilt and played significant roles in World War II and international relations. 
        #     The city is also known for its liberal activism and social movements.
        #     """
        # )  # Pass

        try:
            
            guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

    
    async def secrets_present(self, text):
        # Setup Guard
        guard = Guard().use(SecretsPresent, on_fail="exception")

        # response = guard.validate(
        #     """
        #     async def hello():
        #         name = "James"
        #         age = 25
        #         return {"name": name, "age": age}
        #     """
        # )  # Validator passes

        try:
            response = guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    async def endpoint_is_reachable(self, text):
        # Setup Guard
        guard = Guard().use(EndpointIsReachable, on_fail="exception")

        # response = guard.validate("https://www.guardrailsai.com/")  # Validator passes

        try:
            response = guard.validate(text)  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
    
    
    async def ends_with(self, text):
        # Setup Guard
        guard = Guard().use(EndsWith, end="a", on_fail="exception")

        # response = guard.validate("Llama")  # Validator passes

        try:
            response = guard.validate(text)  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    async def financial_tone(self, text):
        # Use the Guard with the validator
        guard = Guard().use(FinancialTone, on_fail="exception")

        # Test passing response
        # guard.validate(
        #     "Growth is strong and we have plenty of liquidity.",
        #     metadata={"financial_tone": "positive"}
        # )

        try:
            
            guard.validate(
                text,
                metadata={"financial_tone": "positive"}
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
      
    async def has_url(self, text):
        # Setup Guard
        guard = Guard().use(
            HasUrl
        )

        # guard.validate("guardrailsai.com")  # Validator passes
        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
       
    async def mentions_drugs(self, text):
        # Setup the Guard with the validator
        guard = Guard().use(MentionsDrugs, on_fail="exception")

        # Test passing response
        # guard.validate("You should take this medicine every day after breakfast.")

        
        try:
            response = guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        

       
    async def politeness_check(self, text):
        # Setup Guard
        guard = Guard().use(
            PolitenessCheck,
            llm_callable="gpt-3.5-turbo",
            on_fail="exception",
        )

        # res = guard.validate(
        #     "Hello, I'm Claude 3, and am here to help you with anything!",
        #     metadata={"pass_on_invalid": True},
        # )  # Validation passes
        
        try:
            res = guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed" 


    '''

# Deploy the service
serve.run(GuardrailsAi.bind())







'''
import ray
from ray import serve
from guardrails import Guard
from guardrails.hub import * #DetectPromptInjection, ToxicLanguage
import openai

# Initialize Ray and Ray Serve
ray.init(ignore_reinit_error=True)
serve.start()

@serve.deployment
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
            guard(
                llm_api=openai.chat.completions.create,
                prompt=prompt,
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def detect_toxic_language(self, text):
        guard = Guard().use(
                        ToxicLanguage, threshold=0.5, validation_method="sentence", on_fail="exception"
                    )
        try:
            # Test failing response
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def competitor_check(self, text):
        competitor_list = ["Apple", "Samsung"]
        guard = Guard().use(CompetitorCheck, competitor_list, "exception")

        # response = guard.validate(
        # "The apple doesn't fall far from the tree."
        # )  # Validator passes

        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

            
    def detect_pii(self, text):

        pii_list = ["EMAIL_ADDRESS", "PHONE_NUMBER"]
        # Setup Guard
        guard = Guard().use(DetectPII, pii_list, "exception")
        # guard.validate("Good morning!")  # Validator passes
        
        try:
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def gibberish_text(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            GibberishText, threshold=0.5, validation_method="sentence", on_fail="exception"
        )

        # Test passing response
        # guard.validate(
        #     "Azure is a cloud computing service created by Microsoft. It's a significant competitor to AWS."
        # )
        try:
            guard.validate(
                text
                )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
       
    def profanity_free(self, text):
        # Use the Guard with the validator
        guard = Guard().use(ProfanityFree, on_fail="exception")

        # # Test passing response
        # guard.validate(
        #     """
        #     Director Denis Villeneuve's Dune is a visually stunning and epic adaptation of the classic science fiction novel.
        #     It is reminiscent of the original Star Wars trilogy, with its grand scale and epic storytelling.
        #     """
        # )

        try:
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
    
    def wiki_provenance(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            WikiProvenance,
            topic_name="Apple company",
            validation_method="sentence",
            llm_callable="gpt-3.5-turbo",
            on_fail="exception"
        )

        # Test passing response
        # guard.validate("Apple was founded by Steve Jobs in April 1976.", metadata={"pass_on_invalid": True})  # Pass

        # Test failing response
        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

    
    def correct_language(self, text):
        # Setup Guard
        guard = Guard().use(
            CorrectLanguage(expected_language_iso="en", threshold=0.75)
        )

        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def nsfw_text(self, text):
        # Use the Guard with the validator
        guard = Guard().use(
            NSFWText, threshold=0.8, validation_method="sentence", on_fail="exception"
        )

        # Test passing response
        # guard.validate(
        #     "Christopher Nolan's Tenet is a mind-bending action thriller that will keep you on the edge of your seat. The film is a must-watch for all Nolan fans."
        # )

        try:
            
            guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

       
    def restricttotopic(self, text):
        # Setup Guard
        guard = Guard().use(
            RestrictToTopic(
                valid_topics=["sports"],
                invalid_topics=["music"],
                disable_classifier=True,
                disable_llm=False,
                on_fail="exception"
            )
        )

        # guard.validate("""
        # In Super Bowl LVII in 2023, the Chiefs clashed with the Philadelphia Eagles in a fiercely contested battle, ultimately emerging victorious with a score of 38-35.
        # """)  # Validator passes

        try:
            guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

        
    def saliency_check(self, text):
        # Initialize The Guard with this validator
        guard = Guard().use(
            SaliencyCheck,
            "assets/",
            llm_callable="gpt-3.5-turbo",
            threshold=0.1,
            on_fail="exception",
        )

        # Test passing response
        # guard.validate(
        #     """
        #     San Francisco is a major Californian city, known for its finance, culture, and density. 
        #     Originally inhabited by the Yelamu tribe, the city grew rapidly during the Gold Rush and became a major West Coast port. 
        #     Despite a devastating earthquake and fire in 1906, San Francisco rebuilt and played significant roles in World War II and international relations. 
        #     The city is also known for its liberal activism and social movements.
        #     """
        # )  # Pass

        try:
            
            guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"

    
    def secrets_present(self, text):
        # Setup Guard
        guard = Guard().use(SecretsPresent, on_fail="exception")

        # response = guard.validate(
        #     """
        #     def hello():
        #         name = "James"
        #         age = 25
        #         return {"name": name, "age": age}
        #     """
        # )  # Validator passes

        try:
            response = guard.validate(
                text
            )  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def endpoint_is_reachable(self, text):
        # Setup Guard
        guard = Guard().use(EndpointIsReachable, on_fail="exception")

        # response = guard.validate("https://www.guardrailsai.com/")  # Validator passes

        try:
            response = guard.validate(text)  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
    
    
    def ends_with(self, text):
        # Setup Guard
        guard = Guard().use(EndsWith, end="a", on_fail="exception")

        # response = guard.validate("Llama")  # Validator passes

        try:
            response = guard.validate(text)  
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
    
    def financial_tone(self, text):
        # Use the Guard with the validator
        guard = Guard().use(FinancialTone, on_fail="exception")

        # Test passing response
        # guard.validate(
        #     "Growth is strong and we have plenty of liquidity.",
        #     metadata={"financial_tone": "positive"}
        # )

        try:
            
            guard.validate(
                text,
                metadata={"financial_tone": "positive"}
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
      
    def has_url(self, text):
        # Setup Guard
        guard = Guard().use(
            HasUrl
        )

        # guard.validate("guardrailsai.com")  # Validator passes
        try:
            guard.validate(text)
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        
       
    def mentions_drugs(self, text):
        # Setup the Guard with the validator
        guard = Guard().use(MentionsDrugs, on_fail="exception")

        # Test passing response
        # guard.validate("You should take this medicine every day after breakfast.")

        
        try:
            response = guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed"
        

       
    def politeness_check(self, text):
        # Setup Guard
        guard = Guard().use(
            PolitenessCheck,
            llm_callable="gpt-3.5-turbo",
            on_fail="exception",
        )

        # res = guard.validate(
        #     "Hello, I'm Claude 3, and am here to help you with anything!",
        #     metadata={"pass_on_invalid": True},
        # )  # Validation passes
        
        try:
            res = guard.validate(
                text
            )
            return "Test Passed"
        except Exception as e:
            return "Test Failed" 

'''