from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response




class UserPostsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10



class UserFollowersPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 50




class UserFollowingPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 50




class UserNotificationsPagination(PageNumberPagination):
    page_size=15
    page_size_query_param = 'page_size'
    max_page_size = 20
    def get_paginated_response(self, data):
        return Response({
            'notifications_count':self.request.notifications_count,
            'results':data,
            'count':self.page.paginator.count,
            'next':self.get_next_link(),
            'previous':self.get_previous_link()
        })



class UsersPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 50





class MessagesPagination(PageNumberPagination):
    page_size = 11
    page_size_query_param = 'page_size'
    max_page_size = 11


    def get_paginated_response(self, data):
        return Response({
            'messages_count':self.request.messages_count,
            'results':reversed(data),
            'count':self.page.paginator.count,
            'next':self.get_next_link(),
            'previous':self.get_previous_link()
        })




class UserDiscussionPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 15