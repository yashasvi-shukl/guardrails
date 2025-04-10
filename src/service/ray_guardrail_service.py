from flask import Flask, request, jsonify
from pymongo import MongoClient
from src.processor.ray_guardrail import Guardrail
from src.processor.guardrailsAi.ray_guardrails_ai_functions import GuardrailsAi
import ray
import os
from ray import serve
import logging
from src.processor.audit.audit import log_audit
import uuid
from src.common.kritaka_log_config import LogConfiguration
from langchain_openai.chat_models import ChatOpenAI
import logging
import datetime
import time
import yaml
import asyncio
from huggingface_hub import login
import torch
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_flash_sdp(False)
from src.processor.utils import load_llamaguard_model, load_llamaguard_tokenizer
from nemoguardrails import RailsConfig, LLMRails
from src.processor.nemo_guardrails.nemo_guard import NemoRails
os.environ["RAY_memory_usage_threshold"] = "0.9" 
os.environ["RAY_memory_monitor_refresh_ms"] = "0"
os.environ['TOKENIZERS_PARALLELISM'] = "true"
# os.environ['DISABLE_NEST_ASYNCIO'] = "true"
# asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
from asgiref.wsgi import WsgiToAsgi
import uvicorn

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

ray.init(
    address="auto", 
    ignore_reinit_error=True,
    num_cpus=12,)
entrypoint = GuardrailsAi.bind()
handle = serve.run(entrypoint)


with open("/home/aisearch/projects/GaurdRaaS/src/config/gaurdrail_config.yaml") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

try:
    os.environ['OPENAI_API_KEY'] = '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'
    llm = ChatOpenAI()
    nemo_input_config = RailsConfig.from_path(config["nemo_input_prompt"])
    nemo_output_config = RailsConfig.from_path(config['nemo_output_prompt'])
    rails_input_model = LLMRails(config=nemo_input_config, llm=llm)
    rails_output_model = LLMRails(config=nemo_output_config, llm = llm)
    logging.info("Loaded rails config")

except Exception as e:
    logging.error(f"Error while initializing namo-rails: {e}")


uri= config['mongodb_uri'] 
client = MongoClient(uri)
device = "auto"
dtype = torch.bfloat16

try:
    print("Loading tokenizer...")
    llamaguard_tokenizer = ray.put(load_llamaguard_tokenizer(config['llamaguard_tokenizer']))
    print("Loading Model...")
    llamaguard_model = ray.put(load_llamaguard_model(config['llamaguard_model'], dtype = dtype))
    print("Done. ")
except Exception as e:
    logging.error("Failed to load model or tokenizer.")



guardrail = Guardrail(
                        uri = uri,
                        client = client,
                        llamaguard_tokenizer = ray.get(llamaguard_tokenizer),
                        llamaguard_model = ray.get(llamaguard_model), 
                        rails_input_model = rails_input_model,
                        rails_output_model = rails_output_model
                        )

audit_data = {
    "uid": str(uuid.uuid4()),
    "start_timestamp": None,
    "customer_id": None,
    "input": None,
    "output": None,
    "end_timestamp": None,
    }

@app.route('/get_guardrails_metadata', methods=['POST'])
def get_guardrails():
    data = request.get_json()
    results = guardrail.get_guardrails_metadata()
    return jsonify({'results': results})


@app.route('/process_input_guardrail', methods=['POST'])
def process_input_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')

    audit_data = {
    "uid": str(uuid.uuid4()),
    "start_timestamp": str(datetime.datetime.fromtimestamp(time.time())),
    "customer_id": customer_id,
    "input": text,
    "output": None,
    "end_timestamp": None,
    }

    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    guardrail_type = "PreLLM"
    policies = guardrail.get_guardrail_policies(customer_id)
    logging.info(f"Policies: {policies}") 
    if policies:
        result = guardrail.apply_policies(text, policies, guardrail_type, handle)
        print("Final response: ", result)
        
        audit_data['output'] = str(result)
        audit_data['end_timestamp'] = str(datetime.datetime.fromtimestamp(time.time()))

        logging.info(f"Audit data: {audit_data}")
        log_audit(client=client, audit_data=audit_data)
        return result
    else:
        logging.info("No policy found")
        return "No policy found"


@app.route('/process_output_guardrail', methods=['POST'])
def process_output_guardrail():
    data = request.get_json()
    customer_id = data.get('customer_id')
    text = data.get('text')

    audit_data = {
    "uid": str(uuid.uuid4()),
    "start_timestamp": str(datetime.datetime.fromtimestamp(time.time())),
    "customer_id": customer_id,
    "input": text,
    "output": None,
    "end_timestamp": None,
    }

    if not customer_id or not text:
        return jsonify({'error': 'customer_id and text are required'}), 400
    
    guardrail_type = "PostLLM"
    policies = guardrail.get_guardrail_policies(customer_id)
    logging.info(f"Policies: {policies}") 
    if policies:
        result = guardrail.apply_policies(text, policies, guardrail_type, handle)
        print("Final response: ", result)
        
        audit_data['output'] = str(result)
        audit_data['end_timestamp'] = str(datetime.datetime.fromtimestamp(time.time()))

        logging.error("Audit data: {audit_data}")
        log_audit(client=client, audit_data=audit_data)
        return result
    else:
        logging.info("No policy found")
        return "No policy found"
    

if __name__ == '__main__':
    # asgi_app = WsgiToAsgi(app)
    # uvicorn.run(asgi_app, host="0.0.0.0", port=8001, loop='uvloop')
    app.run(host='0.0.0.0',port=5001,debug=False)