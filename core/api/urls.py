from django.urls import include, path

from .views import *


urlpatterns = [
    #authentication
    path('auth/jwt/create/', CustomTokenObtainPairView.as_view() ),
    path('auth/jwt/refresh/', CustomTokenRefreshView.as_view() ),
    path('auth/jwt/logout/', LogoutView.as_view() ),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    #User profile
    path('get/profile/', GetUserProfileView.as_view() ),
    path('update/profile/pic/', UpdateProfilePicView.as_view() ),
    path('update/profile/', UpdateUserProfileView.as_view() ),

    #Public user Profile(visiting someone else's profile)
    path('get/public_profile/<int:user_id>/', GetPublicUserProfile.as_view() ),
    
    #Following/Unfollowing
    path('follow/', CreateFollowView.as_view() ),
    path('unfollow/', DeleteFollowView.as_view() ),

    #Posts (Create,Update,Delete)
    path('posts/create/', CreatePostView.as_view() ),
    path('posts/update/', UpdatePostView.as_view() ),
    path('posts/delete/', DeletePostView.as_view() ),

    #get specific user's Posts
    path('posts/get/<int:user_id>/',UserPostsView.as_view() ),

    #Feed
    path('feed/', FeedView.as_view() ),

    #delete media
    path('media/delete/',DeletePostMediaView.as_view() ),

    #Post like/unlike
    path('post/like/',PostLikeView.as_view()),
    path('post/unlike/',PostUnlikeView.as_view()),

    #Comments/Replies
    path('comments/create/',CreateCommentView.as_view()),
    path('comments/update/',UpdateCommentView.as_view()),
    path('comments/delete/',DeleteCommentView.as_view()),
    path('reply/update/',UpdateCommentReplyView.as_view()),
    path('reply/delete/',DeleteCommentReplyView.as_view()),


    #Comments/Replies Like/Unlike
    path('comment/like/',CommentLikeView.as_view()),
    path('comment/unlike/',CommentUnlikeView.as_view()),
    
    #Followrs list
    path('followers/<int:user_id>/',UserFollowersView.as_view()),
    path('following/<int:user_id>/',UserFollowingView.as_view()),

    #User notifications
    path('notifications/get/<int:user_id>/',GetUserNotificationsView.as_view()),

    #setting notifications as SEEN for authenticated user
    path('notifications/seen/',NotificationsReadView.as_view()),

    #retrieve Discussion
    path('discussions/<int:user_id>/',RetrieveDiscussionView.as_view() ),
    path('discussions/list/',RetrieveDiscussionUsers.as_view() ),
    #setting discussion as SEEN
    path('discussions/seen/<int:user_id>/',UserDiscussionSeenView.as_view() ),


] 


