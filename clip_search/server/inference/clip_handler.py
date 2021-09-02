import os
import argparse
import json

import torch
import torch.nn.functional as F
from ts.torch_handler.base_handler import BaseHandler

import clip

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
        self.tokenize = lambda text : clip.tokenize(text).to(self.device)

        self.model.eval()
        self.initialized = True

    def preprocess(self, requests):
        input_texts = []
        for idx, data in enumerate(requests):
            request = data.get('body', {})
            input_text = request.get('input_text', "")

            input_texts.append(input_text)
        tokenized = self.tokenize(input_texts)
        return tokenized

    def inference(self, tokenized):
        tokenized = tokenized.to(self.device, non_blocking=True)
        text_features = self.model.encode_text(tokenized)
        text_features = F.normalize(text_features, p=2, dim=1).to("cpu", non_blocking=True)
        return text_features

    def postprocess(self, text_features):
        return [{'feature': text_feature.tolist()} for text_feature in text_features]
