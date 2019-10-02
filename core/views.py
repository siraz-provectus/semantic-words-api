from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from pymystem3 import Mystem

import wget
import sys
import gensim, logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import zipfile
import requests
import re

url = 'https://raw.githubusercontent.com/akutuzov/universal-pos-tags/4653e8a9154e93fe2f417c7fdb7a357b7d6ce333/ru-rnc.map'
# model_url = 'http://vectors.nlpl.eu/repository/11/183.zip'
# m = wget.download(model_url)
# model_file = model_url.split('/')[-1]
model_file = '183.zip'
with zipfile.ZipFile(model_file, 'r') as archive:
  stream = archive.open('model.bin')
  model = gensim.models.KeyedVectors.load_word2vec_format(stream, binary=True)

mapping = {}
r = requests.get(url, stream=True)
for pair in r.text.split('\n'):
    pair = re.sub('\s+', ' ', pair, flags=re.U).split(' ')
    if len(pair) > 1:
        mapping[pair[0]] = pair[1]

class FindSimilar(APIView):
  permission_classes = (IsAuthenticated,)

  def post(self, request):
    params = request.POST

    processed_mystem = tag_mystem(text=params['word'])
    similar = model.most_similar(positive=processed_mystem, topn=int(params['count']))

    data = {'similar': similar}

    return Response(data)


def tag_mystem(text='Текст нужно передать функции в виде строки!'):
    m = Mystem()
    processed = m.analyze(text)
    tagged = []
    for w in processed:
        try:
            lemma = w["analysis"][0]["lex"].lower().strip()
            pos = w["analysis"][0]["gr"].split(',')[0]
            pos = pos.split('=')[0].strip()
            if pos in mapping:
                tagged.append(lemma + '_' + mapping[pos]) # здесь мы конвертируем тэги
            else:
                tagged.append(lemma + '_X') # на случай, если попадется тэг, которого нет в маппинге
        except KeyError:
            continue # я здесь пропускаю знаки препинания, но вы можете поступить по-другому
    return tagged