from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from .serializers import UserProfileSerializer,PostSerializer,PostLikeSerializer,CommentSerializer,CommentLikeSerializer,FollowSerializer,PublicUserProfileSerializer,FollowersSerializer,FollowingListSerializer,NotificationsSerializer,ChatMessageSerializer,UserDiscussionSerializer
from .models import UserProfile,CustomUser,Follow,Post,PostMedia,PostLike,Comment,CommentLike
from django.shortcuts import get_object_or_404
from django.db.models import Q
from notifications.utils import send_notification
from rest_framework import serializers
from .paginations import UserPostsPagination,UserFollowersPagination,UserFollowingPagination,UserNotificationsPagination,MessagesPagination,UserDiscussionPagination
from notifications.models import Notification
from chat.models import ChatMessage

# Create your views here.



#Login view
class CustomTokenObtainPairView(TokenObtainPairView):
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')

        if refresh_token:
            # Set the refresh token as a secure, HTTP-only cookie only for the '/api/auth/jwt/' path
            expires_at = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
            response.set_cookie(
                'refresh_token', 
                refresh_token, 
                httponly=True,   
                secure=False,        # Set True in production for HTTPS
                samesite='Lax',
                expires=expires_at,
                path='/api/auth/jwt/',  # Only available for '/api/auth/jwt/' path
            )
            # Remove refresh token from the response body
            del response.data['refresh']

        return response



#tokens refresh views
class CustomTokenRefreshView(APIView):
    def post(self, request):
        try:
            # Get the refresh token from cookies
            refresh_token = request.COOKIES.get('refresh_token')

            if refresh_token is None:
                return Response({"detail": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Create a new RefreshToken instance
                old_token = RefreshToken(refresh_token)

                user_id = old_token['user_id']
                user = CustomUser.objects.get(id=user_id)

                # Generate a new access and refresh token
                new_token = RefreshToken.for_user(user)
                access_token = str(new_token.access_token)
                new_refresh_token = str(new_token)
                # Optionally blacklist the old token if blacklisting is enabled
                old_token.blacklist()
                # Create a response with the new access token
                response = Response({
                    "access": access_token
                }, status=status.HTTP_200_OK)

                # Set the new refresh token in the cookie
                expires_at = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
                response.set_cookie(
                    key='refresh_token',
                    value=new_refresh_token,
                    httponly=True,
                    secure=False,  # Set to False if testing on local without HTTPS
                    samesite='Lax',
                    expires=expires_at,
                    path='/api/auth/jwt/'
                )

                return response

            except InvalidToken:
                return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)



#logout view
class LogoutView(APIView):

    def post(self, request):
        # If you want to blacklist the refresh token
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Clear the refresh token cookie
            response = Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
            response.delete_cookie('refresh_token', path='/api/auth/jwt/')
            return response
        
        except Exception as e:
            return Response({"detail": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)





class GetUserProfileView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self,request,*args,**kwargs):
        user = request.user

        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response('Profile does not exist',status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(user_profile)
        return Response(serializer.data,status=status.HTTP_200_OK)



class UpdateProfilePicView(APIView):
    permission_classes= [IsAuthenticated]
    
    def put(self,request):
        user = request.user

        try:
            user_profile = UserProfile.objects.get(user__id=user.id)

        except UserProfile.DoesNotExist:
            return Response('Profile does not exist!',status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'err':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        new_image = request.FILES.get('avatar')
        if not new_image:
            return Response('No image is provided!',status=status.HTTP_400_BAD_REQUEST)
        
        user_profile.avatar = new_image
        user_profile.save()
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data,status=status.HTTP_200_OK)




class UpdateUserProfileView(generics.UpdateAPIView):
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # Fetch the profile of the authenticated user
        return self.request.user.userprofile




class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response('You must provide a user id!',status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_to_follow = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response("User does not exist!",status=status.HTTP_400_BAD_REQUEST)

        follow_instance,created = Follow.objects.get_or_create(
            follower=request.user,
            following = user_to_follow
        )
        if not created:
            return Response({'Error':'You are already following this user!'},status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'success':f'You are now following {user_to_follow.username}'},status=status.HTTP_201_CREATED)



class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self,request):

        user_id = request.data.get('user_id')

        if not user_id:
            return Response('You must provide a user id!',status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_to_unfollow = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response('User does not exist!',status=status.HTTP_400_BAD_REQUEST)
        
        follow_instance = Follow.objects.filter(follower=request.user, following=user_to_unfollow).first()

        if follow_instance:
            follow_instance.delete()
            return Response({'success':f'you have unfollowed {user_to_unfollow.username}'})

        return Response({'error':'You are not following this user!'},status=status.HTTP_400_BAD_REQUEST)






class CreatePostView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        post = serializer.save(author = self.request.user)
        media_files = self.request.FILES.getlist('media')

        for media_file in media_files:
            media_type = 'image' if media_file.content_type.startswith('image') else 'video'
            PostMedia.objects.create(post=post,media_type=media_type,file=media_file)
        send_notification(action_user=self.request.user,request=self.request,post=post,message=f"{self.request.user.username} created a new post!")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context


class UpdatePostView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer


    def get_object(self):
        post_id = self.request.data.get('post_id')  # Get post_id from request body
        post = get_object_or_404(Post, pk=post_id, author=self.request.user)
        return post

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        post = serializer.save()

        # Handle new media files if provided (for partial updates)
        media_files = self.request.FILES.getlist('media')
        if media_files:
            for media_file in media_files:
                media_type = 'image' if media_file.content_type.startswith('image') else 'video'
                PostMedia.objects.create(post=post, media_type=media_type, file=media_file)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class DeletePostView(generics.DestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        post_id = self.request.data.get('post_id',None)
        post = get_object_or_404(Post,id=post_id,author=self.request.user)
        return post

    def perform_destroy(self, instance):
        return super().perform_destroy(instance)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        user = self.request.user
        followed_users = user.following.values_list('following',flat=True)
        posts = Post.objects.filter(Q(author__in=followed_users) | Q(author=user) | Q(is_public=True)).order_by('-created_at')

        serializer = PostSerializer(posts,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context





class FeedView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            user = self.request.user

            followed_users = user.following.values_list('following', flat=True)
            return Post.objects.filter(Q(author__in=followed_users) | Q(author=user) | Q(is_public=True)).order_by('-created_at')
        else:
            return Post.objects.filter(is_public=True).order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context




class DeletePostMediaView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get_object(self):
        post_id = self.request.data.get('post_id')
        post = get_object_or_404(Post,id=post_id,author=self.request.user)

        media_id = self.request.data.get('media_id')
        return get_object_or_404(PostMedia,id=media_id,post=post)


    def perform_destroy(self, instance):
        instance.file.delete()
        instance.delete()


    def delete(self,instance,request,*args,**kwargs):
        response = super().delete(request, *args, **kwargs)

        post_id = request.data.get('post_id')
        post = get_object_or_404(Post,id=post_id,author=request.user)
        serializer = PostSerializer(post,context={'user':request.user})

        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context




class PostLikeView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,*args,**kwargs):
        post_id = request.data.get('post_id')
        if not post_id:
            return Response('You must provide a post id',status=status.HTTP_400_BAD_REQUEST)

        post = get_object_or_404(Post,id=post_id)
        user = request.user

        if PostLike.objects.filter(user=user,post=post).exists():
            return Response({'error':'You have already liked this post'},status=status.HTTP_400_BAD_REQUEST)

        like = PostLike.objects.create(post=post,user=user)
        serializer = PostLikeSerializer(like)
        if user != post.author:
            send_notification(action_user=request.user,request=request,target_user=post.author,post=post,message=f"{request.user.username} liked your post")
        return Response(serializer.data,status=status.HTTP_201_CREATED)




class PostUnlikeView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostLikeSerializer

    def delete(self,request,*args,**kwargs):
        post_id = request.data.get('post_id')
        if not post_id:
            return Response('You must provide a post id!',status=status.HTTP_400_BAD_REQUEST)

        post = get_object_or_404(Post,id=post_id)
        user = request.user
        like = PostLike.objects.filter(post=post,user=user).first()
        if not like:
            return Response({'error':'Like does not exist on this post!'},status=status.HTTP_400_BAD_REQUEST)
        
        like.delete()
        return Response('Post unliked successfully!',status=status.HTTP_200_OK)




class CreateCommentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer


    def perform_create(self,serializer):
        post_id = self.request.data.get('post_id')
        parent_id = self.request.data.get('parent_id',None)
        parent_comment = None
        post = get_object_or_404(Post,id=post_id)

        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                return Response({'error':'Comment does not exist!'},status=status.HTTP_400_BAD_REQUEST)

        serializer.save(author=self.request.user,post=post,parent=parent_comment)
        if self.request.user != post.author:
            send_notification(action_user=self.request.user,request=self.request,target_user=post.author,post=post,message=f"{self.request.user.username} commented on your post")
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context


class DeleteCommentView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def get_object(self):
        comment_id = self.request.data.get('comment_id')
        post_id = self.request.data.get('post_id')
        post = get_object_or_404(Post,id=post_id)
        comment = Comment.objects.get(id=comment_id,author=self.request.user,post=post).first()
        return comment
    def destroy(self,request,*args,**kwargs):
        comment = self.get_object()
        post = comment.post
        comment.delete()
        remaining_comments = Comment.objects.filter(post=post,parent__isnull=True)
        serializer = CommentSerializer(remaining_comments,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class DeleteCommentReplyView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        post_id = self.request.data.get('post_id')
        reply_id = self.request.data.get('reply_id')
        parent_id =self.request.data.get('parent_id',None)
        if parent_id:
            post = get_object_or_404(Post,id=post_id)
            reply = Comment.objects.filter(author=self.request.user,post=post,parent=parent_id).first()
            return reply

    def destroy(self, request, *args, **kwargs):
        reply = self.get_object()
        post = reply.post
        parent_id = request.data.get('parent_id')
        reply.delete()
        remaining_replies = Comment.objects.filter(post=post,parent=parent_id)
        serializer = CommentSerializer(remaining_replies,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class CommentLikeView(generics.CreateAPIView):
    serializer_class = CommentLikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self,request,*args,**kwargs):
        comment_id = request.data.get('comment_id')
        if not comment_id:
            return Response('You must provide a comment id',status=status.HTTP_400_BAD_REQUEST)

        comment = get_object_or_404(Comment,id=comment_id)
        user = request.user

        if CommentLike.objects.filter(user=user,comment=comment).exists():
            return Response({'error':'You have already liked this comment'},status=status.HTTP_400_BAD_REQUEST)

        like = CommentLike.objects.create(comment=comment,user=user)
        serializer = CommentLikeSerializer(like)
        if user != comment.author:
            send_notification(action_user=user,request=request,target_user=comment.author,post=comment.post,message=f"{request.user.username} liked your comment!")
        return Response(serializer.data,status.HTTP_201_CREATED)






class CommentUnlikeView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentLikeSerializer

    def delete(self,request,*args,**kwargs):
        comment_id = request.data.get('comment_id')
        if not comment_id:
            return Response('You must provide a comment id!',status=status.HTTP_400_BAD_REQUEST)

        comment = get_object_or_404(Comment,id=comment_id)
        user = request.user
        like = CommentLike.objects.filter(comment=comment,user=user).first()
        if not like:
            return Response({'error':'You did not like this comment!'},status=status.HTTP_400_BAD_REQUEST)
        
        like.delete()
        return Response('Comment unliked successfully!',status=status.HTTP_200_OK)




class UpdateCommentView(generics.UpdateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        comment_id = self.request.data.get('comment_id')
        user = self.request.user
        comment = get_object_or_404(Comment,id=comment_id,author=user)
        return comment

    def perform_update(self, serializer):
        serializer.save()


    def update(self,request,*args,**kwargs):
        comment = self.get_object()
        comment_serializer = self.get_serializer(comment,data=request.data)
        if comment_serializer.is_valid(raise_exception=True):
            self.perform_update(comment_serializer)
        post_id = request.data.get('post_id')
        post = get_object_or_404(Post,id=post_id)
        comments = Comment.objects.filter(post=post,parent__isnull=True)
        serializer = CommentSerializer(comments,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class UpdateCommentReplyView(generics.UpdateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        reply_id = self.request.data.get('reply_id')
        parent_id = self.request.data.get('parent_id')
        user = self.request.user
        reply = get_object_or_404(Comment,id=reply_id,author=user,parent=parent_id)
        return reply

    def perform_update(self, serializer):
        serializer.save()


    def update(self,request,*args,**kwargs):
        comment = self.get_object()
        comment_serializer = self.get_serializer(comment,data=request.data)
        if comment_serializer.is_valid(raise_exception=True):
            self.perform_update(comment_serializer)
        post_id = request.data.get('post_id')
        post = get_object_or_404(Post,id=post_id)
        parent_id = request.data.get('parent_id')
        replies = Comment.objects.filter(post=post,parent=parent_id)
        serializer = CommentSerializer(replies,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class CreateFollowView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def perform_create(self, serializer):
        target_user_id = self.request.data.get('user_id')
        if not target_user_id:
            raise serializers.ValidationError('You must provide a user id')
        try:
            target_user = CustomUser.objects.get(id=target_user_id)

        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('User Does not exist!')
        
        serializer.save(follower=self.request.user,following=target_user)

    def create(self,request,*args,**kwargs):
        serializer = self.get_serializer(data=request.data)
        target_user = get_object_or_404(CustomUser,id=request.data.get('user_id'))
        if Follow.objects.filter(follower=request.user,following=target_user).exists():
            return Response('You are already following this user!',status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        target_user = get_object_or_404(CustomUser,id=request.data.get('user_id'))
        target_user_profile = get_object_or_404(UserProfile,user=target_user)
        profile_serializer = PublicUserProfileSerializer(target_user_profile)
        if request.user != target_user:
            send_notification(action_user=request.user,request=request,target_user=target_user,message=f"{request.user.username} is following you")
        return Response(profile_serializer.data,status=status.HTTP_201_CREATED)




        
class DeleteFollowView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def get_object(self):
        target_user_id = self.request.data.get('user_id')
        target_user = get_object_or_404(CustomUser,id=target_user_id)
        follow = get_object_or_404(Follow,follower=self.request.user,following=target_user)
        return follow


    def delete(self, request, *args, **kwargs):
        follow = self.get_object()
        follow.delete()
        target_user = get_object_or_404(CustomUser,id=request.data.get('user_id'))
        target_user_profile = UserProfile.objects.get(user=target_user)
        serializer = PublicUserProfileSerializer(target_user_profile)
        return Response(serializer.data,status=status.HTTP_200_OK)



class GetPublicUserProfile(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PublicUserProfileSerializer

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        if user_id:
            try:
                user_profile = UserProfile.objects.get(user__id=user_id)
            except UserProfile.DoesNotExist:
                return Response('Profile does not exist',status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error':str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            serializer = self.get_serializer(user_profile)
            return Response(serializer.data,status=status.HTTP_200_OK)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context




class UserPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PostSerializer
    pagination_class = UserPostsPagination

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(CustomUser,id=user_id)
        paginator = self.pagination_class()

        if request.user.is_authenticated:
            relationship = Follow.objects.get(following=user,follower=request.user)
            print('rel: ',relationship)
            if relationship:
                user_posts = Post.objects.filter(author=user).order_by('-created_at')
                paginated_queryset = paginator.paginate_queryset(user_posts,request)
                serializer = PostSerializer(paginated_queryset,many=True,context={'user':request.user})
                return paginator.get_paginated_response(serializer.data)
            else:
                print('rel else: ')
                user_posts = Post.objects.filter(author=user,is_public=True).order_by('-created_at')
                paginated_queryset = paginator.paginate_queryset(user_posts,request)
                serializer = PostSerializer(paginated_queryset,many=True,context={'user':request.user})
                return paginator.get_paginated_response(serializer.data)
        else:
            user_posts = Post.objects.filter(author=user,is_public=True).order_by('-created_at')
            paginated_queryset = paginator.paginate_queryset(user_posts,request)
            serializer = PostSerializer(paginated_queryset,many=True,context={'user':request.user})
            return paginator.get_paginated_response(serializer.data)


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context





class UserFollowersView(generics.ListAPIView):
    permission_classes =  [IsAuthenticatedOrReadOnly]
    serializer_class = FollowSerializer
    pagination_class = UserFollowersPagination

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(CustomUser,id=user_id)
        paginator = self.pagination_class()
        followers = Follow.objects.filter(following=user)
        paginated_queryset = paginator.paginate_queryset(followers,request)
        serializer = FollowersSerializer(paginated_queryset,many=True)
        return paginator.get_paginated_response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context



class UserFollowingView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = FollowingListSerializer
    pagination_class = UserFollowingPagination

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(CustomUser,id=user_id)
        paginator = self.pagination_class()
        following_list = Follow.objects.filter(follower=user)
        paginated_queryset = paginator.paginate_queryset(following_list,request)
        serializer = FollowingListSerializer(paginated_queryset,many=True)
        return paginator.get_paginated_response(serializer.data)


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context


class GetUserNotificationsView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationsSerializer
    pagination_class = UserNotificationsPagination

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        if not user_id:
            return Response('You must provide a user id!',status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(CustomUser,id=user_id)
        paginator = self.pagination_class()
        notifications = Notification.objects.filter(target_user=user).order_by('-timestamp')
        notifications_count = notifications.filter(is_read=False).count()
        request.notifications_count = notifications_count
        paginated_queryset = paginator.paginate_queryset(notifications,request)
        context = self.get_serializer_context()
        serializer = NotificationsSerializer(paginated_queryset,many=True,context=context)
        return paginator.get_paginated_response(serializer.data)


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context






class NotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,*args,**kwargs):
        Notification.objects.filter(target_user=request.user,is_read=False).update(is_read=True)
        return Response(status=status.HTTP_200_OK)





class RetrieveDiscussionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer
    pagination_class = MessagesPagination

    def get(self,request,*args,**kwargs):
        recipient_id = self.kwargs.get('user_id')
        user = request.user
        paginator = self.pagination_class()
        discussion = ChatMessage.objects.filter(
            ( Q(sender=user) & Q(receiver__id=recipient_id) ) | ( Q(sender__id=recipient_id) & Q(receiver=user) )
        )
        messages_count = discussion.filter(sender__id=recipient_id,is_read=False).count()
        request.messages_count = messages_count
        paginated_queryset = paginator.paginate_queryset(discussion.order_by('-created_at'),request)
        serializer = ChatMessageSerializer(paginated_queryset,many=True)
        return paginator.get_paginated_response(serializer.data)

    

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['user'] = self.request.user
        return context







class RetrieveDiscussionUsers(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDiscussionSerializer
    pagination_class = UserDiscussionPagination


    def get_queryset(self):
        user = self.request.user
        return CustomUser.objects.filter(
            Q(received_messages__sender=user) | 
            Q(sent_messages__receiver=user)
            ).exclude(id=user.id).distinct()


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request']= self.request
        context['user'] = self.request.user
        return context





class UserDiscussionSeenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,*args,**kwargs):
        user_id = self.kwargs.get('user_id')
        if not user_id:
            return Response('You must provide a user id !',status=status.HTTP_400_BAD_REQUEST)
        target_user = get_object_or_404(CustomUser,id=user_id)
        messages = ChatMessage.objects.filter(sender=target_user,receiver=request.user,is_read=False).update(is_read=True)
        return Response(status=status.HTTP_200_OK)

