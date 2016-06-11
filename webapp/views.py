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

def send_text_message(recipient_id, message_text):
    message_data = {}
    message_data['recipient'] = {'id': recipient_id}
    message_data['message'] = {'text': message_text}
    call_send_api(message_data)

def call_send_api(msg):
    key = 'EAAQlXupoFlsBAFqAr5FVNfsBGDTEyDDU1kS1erZCxcLP4noSlaLdD7TaIdXWxtkfHKtwJP1wGaG4YRe5B7na7ZCUDZC8ihY0wLXIsQMv0dNfDPxbnpk1ZCEuYSOi4DwZCXyxWBruL1S5nzjyYawncOYySGHBzyTrVz7vmbhfKaAZDZD'
    logger.debug(msg)
    res = requests.post('https://graph.facebook.com/v2.6/me/messages',
                  data=json.dumps(msg),
                  params={'access_token': key},
                  headers = {'content-type':  'application/json'}
                 )
    logger.debug(res.text)

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
    feed = r.db('angelhacksdb').table("userfeed").order_by(r.desc('timestamp')).run(conn)
    conn.close()
    context = []
    dic = {}
    with open('/webapps/angelhacks/webapp/mood.tab', 'r') as f:
         for l in f.readlines():
             ele = l.strip().split('\t', 1)
             dic[ele[0]] = ele[1]
    for change in feed:
        res = ''
        for key in dic:
            if key.lower() in change['content'].lower():
                res = dic[key]
                break
        change['autoreply'] = res
        context.append(change)
    return HttpResponse(json.dumps(context), content_type="application/json")
    #context = {'latest_question_list': 'latest_question_list'}

@csrf_exempt
def sendmsg(request):
    message_id = request.POST['message_id']
    message_text = request.POST['message_text']
    logger.debug(message_id)
    conn = r.connect( "localhost", 28015).repl()
    msg = r.db('angelhacksdb').table("userfeed").get(message_id).run(conn)
    r.db('angelhacksdb').table("userfeed").get(message_id).update({'response': message_text}).run(conn)
    conn.close()
    send_text_message(msg['userid'], message_text)
    context = {}
    return HttpResponse(json.dumps(context), content_type="application/json")

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
                        user_info['userid'] = userid
                        if 'text' in event['message']:
                            msg_text = event['message']['text']
                            logger.debug("RECEIVED A MESSAGE {}".format(event['message']['text'].encode('utf-8')))
                            store_message(type='text', user_info=user_info, content=msg_text, timestamp=event['timestamp'])
                            #send_text_message(userid, "I received {}".format(msg_text.encode('utf-8')))
                        elif 'attachments' in event['message']:
                            logger.debug("RECEIVED A ATTACHMENT".format(event['message']))
                            store_message(type='image', user_info=user_info, content=event['message']['attachments'][0]['payload']['url'], timestamp=event['timestamp'])
                    elif 'postback' in event:
                        logger.debug("RECEIVED A POSTBACK {}".format(event['postback']))
                    else:
                        logger.debug("RECEIVED AN EVENT {}".format(event))

    context = {'hello': 'ok'}
    return HttpResponse(json.dumps(context), content_type="application/json")

