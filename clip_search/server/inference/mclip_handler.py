import os
import argparse
import json

import torch
import torch.nn.functional as F
from ts.torch_handler.base_handler import BaseHandler
import transformers

class CLIPHandler(BaseHandler):
    def __init__(self):
        super(CLIPHandler, self).__init__()
        self.initialized = False

    def initialize(self, ctx):
        self.manifest = ctx.manifest
        properties = ctx.system_properties
        model_dir = properties.get("model_dir")

        gpu_id = properties.get("gpu_id")
        torch.cuda.set_device(f"cuda:{gpu_id}")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model_pt_path = self.manifest["model"]["serializedFile"]
        self.model = torch.jit.load(model_pt_path, map_location=self.device)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained("M-CLIP/M-BERT-Base-69")

        self.model.eval()
        self.initialized = True

    def preprocess(self, requests):
        input_texts = []
        for idx, data in enumerate(requests):
            request = data.get('body', {})
            input_text = request.get('input_text', "")
            input_texts.append(input_text)

        txt_tok = self.tokenizer(input_texts, padding=True, return_tensors="pt")
        txt_tok['input_ids'] = txt_tok['input_ids'].to(self.device)
        txt_tok['token_type_ids'] = txt_tok['token_type_ids'].to(self.device)
        txt_tok['attention_mask'] = txt_tok['attention_mask'].to(self.device)
        return txt_tok

    def inference(self, txt_tok):
        text_features = self.model(txt_tok['input_ids'], txt_tok['token_type_ids'], txt_tok['attention_mask'])
        text_features = F.normalize(text_features, p=2, dim=1).to("cpu", non_blocking=True)
        return text_features

    def postprocess(self, text_features):
        return [{'feature': text_feature.tolist()} for text_feature in text_features]
