import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import requests
import json
from datetime import datetime

FEEDLY_API_ENDPOINT = 'https://cloud.feedly.com/v3/'
MERCURY_API_ENDPOINT = 'https://mercury.postlight.com/parser?url='

f = open('feedly_token.txt', 'r')
FEEDLY_TOKEN = f.read()
f.close()

f = open('mercury_token.txt', 'r')
MERCURY_TOKEN = f.read()
f.close()

def xstr(s):
    return '' if s is None else s.encode('utf-8').strip()

def mercuryParser(urlToParse):
    url = MERCURY_API_ENDPOINT + urlToParse
    headers = {'x-api-key': MERCURY_TOKEN}
    r = requests.get(url, headers=headers)
    # cannot find the error code, does it handle error?
    if r.status_code == requests.codes.ok:
        articleInfo = json.loads(r.text)
        return articleInfo
    else:
        return {}

def getAPI(endpoint):
    url = FEEDLY_API_ENDPOINT + endpoint
    headers = {'Authorization': 'OAuth ' + FEEDLY_TOKEN}
    r = requests.get(url, headers=headers)
    return r

def postAPI(endpoint, jsondata):
    url = FEEDLY_API_ENDPOINT + endpoint
    headers = {'Authorization': 'OAuth ' + FEEDLY_TOKEN}
    r = requests.post(url, headers=headers, data=json.dumps(jsondata))
    return r

def getCategoryID(label):
    r = getAPI('categories')

    categoryList = json.loads(r.text)
    catID = ''

    for cat in categoryList:
        if cat['label'] == label:
            catID = cat['id']
    return catID

def getStreamItems(streamID):
    r = getAPI("streams/contents?count=10000&unreadOnly=true&streamId=" + streamID)
    streamContent = json.loads(r.text)
    streamURLs = []
    for stream in streamContent['items']:
        item = {}
        item['url'] = ''
        item['author'] = stream['author']
        item['pubdate'] = datetime.fromtimestamp(int(stream['published']/1000)).strftime('%Y-%m-%d %H:%M:%S')
        item['title'] = stream['title']
        item['fingerprint'] = stream['fingerprint']
        item['summary'] = stream['summary']['content']

        if 'canonicalUrl' in stream and stream['canonicalUrl'].startswith('http'):
            item['url'] = stream['canonicalUrl']
        elif 'originId' in stream and stream['originId'].startswith('http'):
            item['url'] = stream['originId']

        if item['url']:
            streamURLs.append(item)
    return streamURLs

def markCategoryAsRead(categoryID):
    item = {}
    item['type'] = 'categories'
    item['action'] = 'markAsRead'
    item['asOf'] = datetime.now().strftime('%s%f')[:-3]
    item['categoryIds'] = [categoryID]

    r = postAPI('markers', item)
    if r.status_code == requests.codes.ok:
        return True
    return r.text

secID = getCategoryID('Security')
articleInfoList = getStreamItems(secID)

# print json.dumps(articleInfoList)

html = '<html><body>'

for articleInfo in articleInfoList:
    html += '<h3><a href="#' + articleInfo['fingerprint'] + '">' + articleInfo['title'] + '</a></h3>'
    html += articleInfo['summary'] + '<br><br>'

for articleInfo in articleInfoList:
    article = mercuryParser(articleInfo['url'])
    articleContent = xstr(article['content'])

    html += '<a name="' + articleInfo['fingerprint'] + '" style="page-break-before:always" />'
    html += '<h3>' + articleInfo['title'] + '</h3>'
    html += articleInfo['author'] + '&ensp;&ensp;|&ensp;&ensp;' + articleInfo['pubdate'] + '<br>'
    html += '<a href="' + articleInfo['url'] + '">' + articleInfo['url'] + '</a><br>'
    html += articleContent

html += '</body></html>'

f = open('SecurityNews_' + datetime.now().strftime('%Y-%m-%d') + '.html', 'w') 
f.write(html)
f.close()

# # markCategoryAsRead(secID)