
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView
from django.views.decorators.csrf import csrf_exempt
# from django_private_chat2 import urls as django_private_chat2_urls


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
#     path('s3direct/', include('s3direct.urls')),
# ]
# from graphql_extensions.views import GraphQLView

from graphene_django.views import GraphQLView as BaseGraphQLView
from app.views import activate_account, resend_email, webhook


class GraphQLView(FileUploadGraphQLView):

    @staticmethod
    def format_error(error):
        formatted_error = super(GraphQLView, GraphQLView).format_error(error)

        try:
            formatted_error['status'] = error.original_error.context
        except AttributeError:
            pass

        return formatted_error


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('activate/<token>', activate_account, name='activate'),
    path('resend/<token>', resend_email, name='resend'),
    path("webhook/", webhook, name="webhook"),
    path('accounts/', include('allauth.urls')),
    # path('chat/', include(django_private_chat2_urls))
]   