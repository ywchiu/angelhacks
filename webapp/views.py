from collections import Counter
from django.shortcuts import render
from django.shortcuts import render_to_response, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
import datetime
import rethinkdb as r
import json
import requests
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('django')

def get_user_data(userid):
    key = 'EAAQlXupoFlsBAFqAr5FVNfsBGDTEyDDU1kS1erZCxcLP4noSlaLdD7TaIdXWxtkfHKtwJP1wGaG4YRe5B7na7ZCUDZC8ihY0wLXIsQMv0dNfDPxbnpk1ZCEuYSOi4DwZCXyxWBruL1S5nzjyYawncOYySGHBzyTrVz7vmbhfKaAZDZD'
    res = requests.get('https://graph.facebook.com/v2.6/{}?access_token={}&debug=all&format=json&method=get&pretty=0&suppress_http_code=1'.format(userid, key))
    logger.debug(res.json())
    result = res.json()
    result.pop('__debug__')
    return result

def store_message(type='text', user_info='', content='', timestamp=''):
    data = Counter({})
    user_info = Counter(user_info)
    data = data + user_info
    data['type'] = type
    #data['user_info'] = user_info
    data['content'] = content
    data['timestamp'] = datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    conn = r.connect( "localhost", 28015).repl()
    feed = r.db('angelhacksdb').table("userfeed").insert(data).run(conn)
    conn.close()
    

def index(request):
    context = {'latest_question_list': 'latest_question_list'}
    return render(request, 'index.html', context)


def getMessage(request):
    conn = r.connect( "localhost", 28015).repl()
    feed = r.db('angelhacksdb').table("userfeed").run(conn)
    conn.close()
    context = [] 
    for change in feed:
        context.append(change)
    return HttpResponse(json.dumps(context), content_type="application/json")
    #context = {'latest_question_list': 'latest_question_list'}

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        data = {}
        msg = json.loads(request.body.decode('utf-8'))
        logger.debug(msg) 
        if msg['object'] == 'page':
            for pageEntry in msg['entry']:
                data['timestamp'] = pageEntry['time']
                for event in pageEntry['messaging']:
                    if 'delivery' in event:
                        logger.debug("DELIVERY A MESSAGE {}".format(event['delivery']))
                    elif 'message' in event:
                        userid = event['sender']['id']
                        user_info = get_user_data(userid)
                        if 'text' in event['message']:
                            logger.debug("RECEIVED A MESSAGE {}".format(event['message']['text'].encode('utf-8')))
                            store_message(type='text', user_info=user_info, content=event['message']['text'], timestamp=event['timestamp'])
                        elif 'attachments' in event['message']:
                            logger.debug("RECEIVED A ATTACHMENT".format(event['message']))
                            store_message(type='image', user_info=user_info, content=event['message']['attachments'][0]['payload']['url'], timestamp=event['timestamp'])
                    elif 'postback' in event:
                        logger.debug("RECEIVED A POSTBACK {}".format(event['postback']))
                    else:
                        logger.debug("RECEIVED AN EVENT {}".format(event))

    context = {'hello': 'ok'}
    return HttpResponse(json.dumps(context), content_type="application/json")

