from flask import Flask, request, jsonify
from pymongo import MongoClient
from ray_guardrail import Guardrail
from ray_guardrails_ai_functions import GuardrailsAi
import ray
from ray import serve

app = Flask(__name__)

ray.init(address="auto", ignore_reinit_error=True)
entrypoint = GuardrailsAi.bind()
handle = serve.run(entrypoint)
# MongoDB client setup

#uri ="mongodb://localhost:27017/"
uri= "mongodb+srv://kritaka_user:q3DCrlV5gg2xZZYr@cluster0.jkkz8m5.mongodb.net/admin?appName=Cluster0"

client = MongoClient(uri)

guardrail = Guardrail(uri, client)



@app.route('/get_guardrails_metadata', methods=['POST'])
def get_guardrails():

    data = request.get_json()
    print(data)
    results = guardrail.get_guardrails_metadata()
    print(results)
    return jsonify({'results': results})


@app.route('/process_input_guardrail', methods=['POST'])
def process_input_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')
    
    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    guardrail_type = "PreLLM"
    # policies = guardrail.get_guardrails(customer_id, guardrail_type)
    policies = guardrail.get_guardrail_policies(customer_id)
    # print(type(policies))
    print("Policies: ",policies) #{'_id': ObjectId('667b39c9fdd9d80c58aed6ec'), 'customer_id': 12345, 'rag_policy': {'semantic_search': {}, 'prompt': {}}, 'guardrail_policy': [12345, 30000, 12346]}
    results = guardrail.apply_policies(text, policies, guardrail_type, handle)
    
    return jsonify({'results': results})

@app.route('/process_output_guardrail', methods=['POST'])
def process_output_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')
    
    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    guardrail_type = "PostLLM"
    policies = guardrail.get_guardrail_policies(customer_id,guardrail_type)
    results = guardrail.apply_policies(text, policies, guardrail_type, handle)
    
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=False)


'''
import warnings
warnings.filterwarnings("ignore")
from flask import Flask, request, jsonify
from pymongo import MongoClient
import logging
# logging.basicConfig(filename='/home/aisearch/projects/GaurdRaaS/src/service/log/guardraas_log', level=logging.INFO)

from src.common.kritaka_log_config import LogConfiguration
import logging


log_config = LogConfiguration(
    application_name='kritaka-guardraas',
    with_console_logging=True,
    with_file_logging=True,
    log_file_path='./var/log/kritaka/guardraas/evaluate_guardrails.log'
)
log_config.set_level(logging.INFO)
logging.basicConfig(
    filename=log_config.log_file_path,
    level=logging.INFO,
    format=log_config.log_format,
    force=True
)
logger = logging.getLogger('kritaka-guardraas')


app = Flask(__name__)

# MongoDB client setup

#uri ="mongodb://localhost:27017/"
uri= "mongodb+srv://kritaka_user:q3DCrlV5gg2xZZYr@cluster0.jkkz8m5.mongodb.net/admin?appName=Cluster0"

client = MongoClient(uri)

guardrail = Guardrail(uri, client)


@app.route('/get_guardrails_metadata', methods=['POST'])
def get_guardrails():

    data = request.get_json()
    # print(data)
    results = guardrail.get_guardrails_metadata()
    # print(results)
    return jsonify({'results': results})


@app.route('/process_input_guardrail', methods=['POST'])
def process_input_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')
    
    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    if isinstance(customer_id, int):
        guardrail_type = "PreLLM"
        logging.info("Applying input guardrails...")
        policies = guardrail.get_guardrail_policies(customer_id)
        # print(policies)
        logging.info(f"Policies for the customer {customer_id}: {policies}") #{'_id': ObjectId('667b39c9fdd9d80c58aed6ec'), 'customer_id': 12345, 'rag_policy': {'semantic_search': {}, 'prompt': {}}, 'guardrail_policy': [12345, 30000, 12346]}
        if len(policies)>0:
            results = guardrail.apply_policies(text, policies, guardrail_type)
            # serve.run(app, route_prefix="/")
            return jsonify({'results': results})
    else:
        logging.error("Expeted customer id in integer format.")

@app.route('/process_output_guardrail', methods=['POST'])
def process_output_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')
    
    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    if isinstance(customer_id, int):
        guardrail_type = "PostLLM"
        logging.info("Applying output guardrails...")
        policies = guardrail.get_guardrail_policies(customer_id)
        logging.info(f"Policies for the customer {customer_id}: {policies}")
        if len(policies)>0:
            results = guardrail.apply_policies(text, policies, guardrail_type)
            return jsonify({'results': results})
        else:
            return []
    else:
        logging.error("Expeted customer id in integer format.")

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)

'''