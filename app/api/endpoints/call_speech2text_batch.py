import os
import glob
from speech import speech2text

def process_pcm_files(directory):
    city = directory[-2:]
    print(f"正在处理城市{city}")
    with open(os.path.join(directory, f'{city}_text.txt'), 'w', encoding='utf-8') as f:
        pcm_files = glob.glob(os.path.join(directory, '*.pcm'))
        for pcm_file in pcm_files:
            result = speech2text(pcm_file)
            f.write(result+'\n')

if __name__ == "__main__":
    directories = [
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/东北',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/山东',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/河南',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/随州',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/麻城'
    ]
    for directory in directories:
        process_pcm_files(directory)
