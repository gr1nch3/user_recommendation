from django.urls import path, re_path, include
from django.conf.urls.static import static


from .views import recommend_users


urlpatterns = [
    path("q2", recommend_users, name="recommend_users"),
]
