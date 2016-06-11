from django.shortcuts import render
from django.shortcuts import render_to_response, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
import rethinkdb as r
import json
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('django')

def store_message(event):
    data = {}
    data['userid'] = event['sender']['id']
    data['content'] = event['message']['text']
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
        if msg['object'] == 'page':
            for pageEntry in msg['entry']:
                data['timestamp'] = pageEntry['time']
                for event in pageEntry['messaging']:
                    if 'delivery' in event:
                        logger.debug("DELIVERY A MESSAGE {}".format(event['delivery']))
                    elif 'message' in event:
                        logger.debug("RECEIVED A MESSAGE {}".format(event['message']['text'].encode('utf-8')))
                        store_message(event)
                    elif 'postback' in event:
                        logger.debug("RECEIVED A POSTBACK {}".format(event['postback']))
                    else:
                        logger.debug("RECEIVED AN EVENT {}".format(event))

    context = {'hello': 'ok'}
    return HttpResponse(json.dumps(context), content_type="application/json")

