import os
# os.environ["CUDA_VISIBLE_DEVICES"] = '0'

import torch
from transformers import BertTokenizer
from config import Args
from model import BertForIntentAndSlot
from main import Trainer

import uvicorn
from fastapi import FastAPI, Request, Form
from starlette_session import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret", cookie_name="cookie0")


@app.post('/')
async def index(request: Request, text=Form(None)):
    args = Args()
    device = args.device

    tokenizer = BertTokenizer.from_pretrained(args.bert_dir)
    model = BertForIntentAndSlot(args)
    model.load_state_dict(torch.load(args.load_dir))
    model.to(device)
    trainer = Trainer(model, args)

    res = trainer.predict(text, tokenizer)

    for item in res['槽位']:
        request.session.update({item[0]: item[1]})

    return {**request.session}

if __name__ == '__main__':
    uvicorn.run(app, port=8030)
