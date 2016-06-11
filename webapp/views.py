from django.shortcuts import render
from django.shortcuts import render_to_response, HttpResponse, redirect
import rethinkdb as r
import json

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
