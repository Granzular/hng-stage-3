from django.urls import path
from main import views
from rest_framework.routers import DefaultRouter

app_name = 'main'

router = DefaultRouter(trailing_slash=False)
router.register(r'profiles',views.ProfileViewSet,basename='create-list-profile')
urlpatterns = router.urls
