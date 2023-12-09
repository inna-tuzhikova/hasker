from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import QuestionViewSet


schema_view = get_schema_view(
   openapi.Info(
      title='Hasker API',
      default_version='v1',
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


router = DefaultRouter()
router.register('questions', QuestionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'swagger<format>/',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    )
]
