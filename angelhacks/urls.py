from django.conf.urls import patterns, include, url
from django.contrib import admin
from webapp import views
urlpatterns = patterns('',
    # Examples:
     url(r'^$', 'webapp.views.index', name='index'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
