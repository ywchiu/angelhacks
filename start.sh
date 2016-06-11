ps -ef | grep runserver | awk '{print $2}' |xargs kill -9
nohup python manage.py runserver 127.0.0.1:8888 &
