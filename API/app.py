from flask import Flask
from flask_cors import CORS
from transformers import BertTokenizer, BertModel

app = Flask(__name__)
CORS(app , supports_credentials=True , origins="*")
app.config['SECRET_KEY'] = "SECRET KEY"

tokenizer = BertTokenizer.from_pretrained('./model/')
model = BertModel.from_pretrained('./model/')
