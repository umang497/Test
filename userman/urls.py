from django.conf.urls import url

from userman.views import register_user, get_user_details


urlpatterns = [
    url(r'register/$', register_user, name='register_user'),
    url(r'$', get_user_details, name='get_user_details'),
]
