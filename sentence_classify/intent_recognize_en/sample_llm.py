from datasets import load_dataset
import json
from vllm import LLM, SamplingParams
import os
import re
import random

os.environ["VLLM_USE_V1"] = "0"
os.environ["VLLM_USE_MODELSCOPE"] = "True"
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

model_path="/dev_data/zkyao/pretrain_model/Qwen2.5-32B-Instruct"
llm = LLM(model=model_path, tokenizer=model_path, trust_remote_code=False, max_model_len=8192, tensor_parallel_size=2)
tokenizer = llm.get_tokenizer()
sampling_params = SamplingParams(
    temperature=0.8,
    top_p=0.9,
    presence_penalty=0.1,  # 额外增加新主题的可能性
    frequency_penalty=0.1,
    max_tokens=1024,
    repetition_penalty=1.05
)


prompt_template_rag = """## Generate 10 diverse questions with the following split:
- 5 welding/electrical engineering-related questions (technical, practical, or theoretical)
- 5 random or casual questions (can be general knowledge, opinion-based, humorous, or completely unrelated)

## Requirements for Welding Questions (5):
1. Cover different aspects: equipment, techniques, safety, materials, troubleshooting
2. Mix beginner and advanced-level questions
3. Include open-ended and specific technical questions

### Examples:
"What’s the best way to prevent porosity in MIG welding?"
"Why does TIG welding require a high-frequency start?"
"How do you choose the right electrode for stainless steel?"

## Requirements for Random/Casual Questions (5):
1. Should not be related to welding/engineering
Can be:
- Fun/lighthearted: "If animals could talk, which would be the rudest?"
- Philosophical: "Is free will an illusion?"
- Everyday life: "What’s the best way to keep motivated when working from home?"
- Hypothetical: "What would happen if gravity stopped for 1 second?"

## Encourage creativity and variety

## Output Format: Return a numbered list (1-10).

## Example Output:
1. What’s the difference between AC and DC welding, and when should you use each?
2. How do you troubleshoot excessive spatter in stick welding?
3. Why is argon commonly used as a shielding gas in TIG welding?
4. What safety precautions are critical when welding in confined spaces?
5. How does preheating affect weld quality in high-carbon steel?
6. If you could instantly master one skill, what would it be?
7. What’s the weirdest food combination you’ve ever tried?
8. What’s your favorite underrated movie?
9. Would you rather live without the internet or without air conditioning?
10. What’s the most useless invention that somehow still exists?

## Instructions for LLM:
- Ensure clear separation between technical and casual questions.
- Avoid repetitive phrasing—vary question structures (how/why/what/when).

## Now generate 10 diverse questions based on the above requirements.
"""

datasets = []
for _ in range(200):
    prompt = prompt_template_rag
    datasets.append({"prompt": prompt})

prompts = [data['prompt'] for data in datasets]
outputs = llm.generate(prompts, sampling_params=sampling_params)
outputs = [output.outputs[0].text for output in outputs]


# pattern = r'\d+\.\s+"([^"]+)"\n'
# fw = open('sample_output.json', 'w+', encoding='utf-8')
# for output, data in zip(outputs, datasets):
#     matches = re.findall(pattern, output)
#     for match in matches:
#         new_dict = {
#             "input": match,
#             "label": "RAG"
#         }
#         fw.write(json.dumps(new_dict, ensure_ascii=False) + '\n')
# fw.close()

fw = open('sample_output_text.json', 'w+', encoding='utf-8')
for output, data in zip(outputs, datasets):
    new_dict = {
        "input": output.strip(),
        "label": "RAG"
    }
    fw.write(json.dumps(new_dict, ensure_ascii=False) + '\n')
fw.close()


