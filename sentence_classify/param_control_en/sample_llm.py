from datasets import load_dataset
import json
from vllm import LLM, SamplingParams
import os
import re

os.environ["VLLM_USE_V1"] = "0"
os.environ["VLLM_USE_MODELSCOPE"] = "True"
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"

model_path="/dev_data/zkyao/pretrain_model/Qwen2.5-32B-Instruct"
llm = LLM(model=model_path, tokenizer=model_path, trust_remote_code=False, max_model_len=8192, tensor_parallel_size=2)
tokenizer = llm.get_tokenizer()
sampling_params = SamplingParams(temperature=0.0, max_tokens=1024, repetition_penalty=1.00)


prompt_template_up = """Generate diverse English sentences expressing "increase voltage by {number} volts" or "increase current by {number} amps" with the following requirements:

1. Use varied verbs meaning "increase" (e.g., raise, boost, bump up, push up, etc.) - be creative with uncommon expressions
2. Include both technical and casual/colloquial phrasings
3. The amount should be an increase (not "increase to") - crucial distinction!
4. Units (V/A) can be included or omitted
5. Vary sentence structures and expressions

Bad examples (what NOT to generate):
1. "Increase the voltage to {number} volts" (WRONG - this means "to" a specific value)
2. "Adjust the current to {number} amps" (WRONG - doesn't imply increase)
3. "Set voltage at {number}" (WRONG - no increase implied)

Good examples:
1. "Bump up the voltage by {number} volts"
2. "We need to add {number} more volts to the system"
3. "Give it an extra {number}V kick"
4. "The current should go up by {number} amps"
5. "Crank the voltage {number} volts higher"
6. "Let's push {number} more volts through"
7. "Up the current by {number}A"
8. "Need a {number} volt boost"
9. "Throw in another {number} volts"
10. "Current needs to come up {number} amps"

Generate 5 diverse variations for voltage increase by {number} volts and 5 for current increase by {number} amps. Prioritize creative, non-repetitive phrasings that still maintain technical accuracy about the increase amount."""

prompt_template_down = """Generate diverse English sentences expressing "decrease voltage by {number} volts" or "decrease current by {number} amps" with the following requirements:

1. Use varied verbs meaning "decrease" (e.g., reduce, lower, cut, drop, etc.) - include creative and unconventional expressions
2. Mix technical terminology with casual/colloquial phrasings
3. The amount must be a reduction (not "decrease to") - absolutely avoid phrases implying final value
4. Units (V/A) are optional
5. Vary sentence structures and expressions

Bad examples (what NOT to generate):
1. "Reduce the voltage to {number} volts" (WRONG - this means setting to a specific value)
2. "Set the current at {number} amps" (WRONG - no reduction implied)
3. "Adjust voltage down to {number}" (WRONG - implies target value)

Good examples:
1. "Cut the voltage by {number} volts"
2. "We need to drop {number} volts from the system"
3. "Take the current down another {number} amps"
4. "Shave off {number}V from the supply"
5. "The voltage should come down by {number} volts"
6. "Knock the current back {number}A"
7. "Trim {number} volts off the output"
8. "Need a {number} volt reduction"
9. "Deduct {number} more volts"
10. "Current needs to fall by {number} amps"

Generate 5 diverse variations for voltage decrease by {number} volts and 5 for current decrease by {number} amps. Prioritize creative, non-repetitive phrasings that clearly communicate the reduction amount (not final value). Include some unexpected verb choices while maintaining technical accuracy."""

prompt_template_control = """Generate diverse English sentences expressing "set voltage to {number} volts" or "set current to {number} XX amps" with these requirements:

1. Use varied control/setting verbs (e.g., set, adjust, fix, regulate, etc.) - include both technical and colloquial terms
2. Must imply achieving a specific target value (not a change by some amount)
3. Units (V/A) can be included or omitted
4. Include indicator words like "to", "at", or "of" that specify target values

Bad examples (what NOT to generate):
1. "Increase voltage by {number} volts" (WRONG - implies change, not target)
2. "Reduce current {number} amps" (WRONG - missing target preposition)
3. "Make it {number} volts higher" (WRONG - suggests relative change)

Good examples:
1. "Set voltage to {number} volts"
2. "Regulate current at {number} amps"
3. "Output should stabilize at {number}V"
4. "Fix the potential difference at {number}"
5. "Dial it in to exactly {number} volts"
6. "Target current: {number}A"
7. "Hold voltage steady at {number}"
8. "Tune to {number} microvolts"
9. "Lock in {number} volts"
10. "Maintain {number} amp flow"

Generate 5 variations for voltage control to {number} volts and 5 for current control to {number} amps. Ensure every example clearly indicates achieving a specific value (not a relative change), using appropriate prepositions like "to", "at", or "of"."""

import random

datasets = []
for label in ['up', 'down', 'control']:
    for _ in range(200):
        number = random.randint(1, 400)
        prompt_template = prompt_template_up if label == 'up' else prompt_template_down if label == 'down' else prompt_template_control
        prompt = prompt_template.format(number=number)
        datasets.append({"prompt": prompt, "label": label, "slot": number})

prompts = [data['prompt'] for data in datasets]
outputs = llm.generate(prompts, sampling_params=sampling_params)
outputs = [output.outputs[0].text for output in outputs]


pattern = r'\d+\.\s+"([^"]+)"\n'
fw = open('sample_output.json', 'w+', encoding='utf-8')
for output, data in zip(outputs, datasets):
    matches = re.findall(pattern, output)
    for match in matches:
        new_dict = {
            "input": match,
            "label": data['label'],
            "slot": data['slot']
        }
        fw.write(json.dumps(new_dict, ensure_ascii=False) + '\n')
fw.close()


