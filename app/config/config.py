import os

import torch

XF_APPID = 'ff9d26aa'
XF_APISecret = 'YTlhZDY0M2ZhYzk4ZjcwMGMyMDhhYThj'
XF_APIKey = 'd78a8f15d26324aacc0614a4e16a8b50'

ALIBABA_CLOUD_ACCESS_KEY_ID = 'LTAI5tQWNMa7bd7fvhCyy6wW'
ALIBABA_CLOUD_ACCESS_KEY_SECRET = 'iC3NLgz053kDhIdusmiGH1rBy4sxai'
# XF_APIKey = 'b6b16e755c03b0ab2bd1063a0c6cf4c3'
# # 实验室eta服务器的配置
PROJECT_DIR = r"/dev_data_2/zkyao/code/Weld-GPT_demo"
MYSQL_USER = "zkyao"  # TODO: mysql账号
MYSQL_PASSWORD = "aa12345678"  # TODO: mysql密码
device = torch.device('cuda:3' if torch.cuda.is_available() else 'cpu')

# 三乔服务器的配置（原Windows）
# PROJECT_DIR = r"D:\\projects\\Weld-GPT_demo"

# 三乔服务器的配置（现Linux）
# PROJECT_DIR = r"/media/pc/299D817A2D97AD94/Weld-GPT_demo"

# 三乔硬盘炸了之后的配置
# PROJECT_DIR = r"/media/pc/225A6D42D4FA828F/Weld-GPT_demo"

#三乔内置硬盘的配置
# PROJECT_DIR = r"/home/pc/Desktop/projects/Weld-GPT_demo"
# MYSQL_USER = "root"  # TODO: mysql账号
# MYSQL_PASSWORD = "SQMYSQL"  # TODO: mysql密码
# device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


CHINESE_VERSION_DIR = os.path.join(PROJECT_DIR, "app")
SPEECH_DIR = os.path.join(CHINESE_VERSION_DIR, "data/speech")  # TODO【路径】:语音文件存放的路径
TEXT_PATH = os.path.join(CHINESE_VERSION_DIR, "sampled_text/sampled_text.json")   # TODO【路径】:语音转文字结果存放的路径
_DATAFILE_PATH = os.path.join(PROJECT_DIR, 'intent_and_slot/data')  # TODO【路径】:模型训练数据的路径
_MODEL_PATH = os.path.join(PROJECT_DIR, 'models')  # TODO【路径】:模型文件的路径
LOG_DIR = os.path.join(CHINESE_VERSION_DIR, 'logs') # TODO【路径】:日志的目录


class Args:
    DATAFILE_PATH = _DATAFILE_PATH
    MODEL_PATH = _MODEL_PATH

    train_path = os.path.join(DATAFILE_PATH, 'train_process.json')
    test_path = os.path.join(DATAFILE_PATH, 'test_process.json')

    seq_labels_path = os.path.join(DATAFILE_PATH, 'intents.txt')
    token_labels_path = os.path.join(DATAFILE_PATH, 'slots.txt')

    bert_dir = os.path.join(MODEL_PATH, 'bert-base-chinese')
    save_dir = os.path.join(MODEL_PATH, 'checkpoints')
    # load_dir = os.path.join(MODEL_PATH, 'checkpoint_zh_0521')
    load_dir = os.path.join('/dev_data_2/zkyao/code/Weld-GPT_demo/intent_and_slot/checkpoints0521/checkpoint-50000')

    do_train = False
    do_test = False
    do_predict = True

    device = None

    # 生成seq_label到id的映射，和id到seq_label的映射
    seq_label2id = {}
    id2seq_label = {}
    with open(seq_labels_path, 'r') as fp:
        seq_labels = fp.read().split('\n')
        for i, label in enumerate(seq_labels):
            seq_label2id[label] = i
            id2seq_label[i] = label

    # 生成token_label到id的映射，和id到token_label的映射
    token_label2id = {}
    id2token_label = {}
    with open(token_labels_path, 'r') as fp:
        token_labels = fp.read().split('\n')
        for i, label in enumerate(token_labels):
            token_label2id[label] = i
            id2token_label[i] = label

    # 生成ner_label到id的映射，和id到ner_label的映射
    tmp = ['O']
    for label in token_labels:
        B_label = 'B-' + label
        I_label = 'I-' + label
        tmp.append(B_label)
        tmp.append(I_label)
    ner_label2id = {}
    id2ner_label = {}
    for i, label in enumerate(tmp):
        ner_label2id[label] = i
        id2ner_label[i] = label

    hidden_size = 768
    seq_labels_num = len(seq_labels)
    token_labels_num = len(tmp)
    max_len = 128
    batchsize = 64
    lr = 2e-5
    epoch = 10
    hidden_dropout_prob = 0.1

if __name__ == '__main__':
    args = Args()
    print('This is config.py')