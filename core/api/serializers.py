
from rest_framework import serializers
from .models import UserProfile,CustomUser,PostMedia,Post,PostLike,Comment,CommentLike,Follow
from notifications.models import Notification
from chat.models import ChatMessage


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','username','first_name','last_name','email']




class UserProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    user = UserSerializer()
    class Meta:
        model = UserProfile
        fields = ['id','user','bio','avatar','is_following','followers_count','following_count']
        read_only_fields = ['followers_count','following_count','is_following']

    def get_followers_count(self, obj):
        return obj.user.followers.count()
    
    def get_following_count(self,obj):
        return obj.user.following.count()

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            # Update the related user instance
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        avatar = validated_data.get('avatar', None)

        # If avatar is None or not provided, skip updating it
        if avatar is not None:
            instance.avatar = avatar

        # Update the UserProfile instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def get_is_following(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return Follow.objects.filter(follower=user,following=obj.user).exists()
        return False


class AuthorProfileSrializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio','avatar',]

class AuthorSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    userprofile = AuthorProfileSrializer(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id','username','first_name','last_name','email','userprofile','followers_count','following_count']

    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self,obj):
        return obj.following.count()






class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id','media_type','file']



class PostSerializer(serializers.ModelSerializer):

    author = AuthorSerializer(read_only=True)
    media = PostMediaSerializer(many=True,read_only=True)
    likes = serializers.IntegerField(source='likes.count',read_only=True)
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id','author','content','likes','is_liked','comments','comments_count','is_following','media','is_public','created_at','updated_at']

    def get_is_liked(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

    def get_comments(self,obj):
        top_level_comments = Comment.objects.filter(post=obj,parent=None).order_by('-created_at')
        user =  self.context.get('user')
        return CommentSerializer(top_level_comments,many=True,context={'user':user}).data

    def get_comments_count(self,obj):
        return Comment.objects.filter(post=obj,parent=None).count()

    def get_is_following(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated and user.id != obj.author.id:
            return Follow.objects.filter(follower=user,following=obj.author).exists()
        return False





class PostLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostLike
        fields = ('id','user','post','created_at')




class CommentSerializer(serializers.ModelSerializer):

    replies = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    likes = serializers.IntegerField(source='likes.count',read_only=True)
    is_liked = serializers.SerializerMethodField()
    

    class Meta:
        model = Comment
        fields = ('id','author','post','replies','parent','likes','is_liked','content','created_at')
        read_only_fields = ('post','created_at')

    def get_is_liked(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False


    def get_replies(self,obj):
        if obj.is_top_level():
            return CommentSerializer(obj.replies.all(),many=True).data
        return []

    def get_author(self,obj):
        return UserProfileSerializer(obj.author.userprofile).data

    def validate_parent(self,value):
        if value and value.parent is not None:
            raise serializers.ValidationError('Replies cannot have replies nested inside them!')
        return value



class CommentLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentLike
        fields = ('id','user','comment','created_at')





class FollowSerializer(serializers.ModelSerializer):
    
    following = UserSerializer(read_only=True)
    follower = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id','following','follower','created_at')



class PublicUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('id','username','first_name','last_name')




class PublicUserProfileSerializer(serializers.ModelSerializer):

    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    user = PublicUserSerializer()
    class Meta:
        model = UserProfile
        fields = ('id','avatar','bio','user','followers_count','following_count','is_following')


    def get_followers_count(self, obj):
        return obj.user.followers.count()
    
    def get_following_count(self,obj):
        return obj.user.following.count()


    def get_is_following(self,obj):
        user = self.context.get('user')
        print(user)
        if user and user.is_authenticated:
            return Follow.objects.filter(follower=user,following=obj.user).exists()
        return False



class FollowersSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='follower.username',read_only=True)
    follower_id = serializers.CharField(source='follower.id',read_only=True)
    avatar = serializers.CharField(source='follower.userprofile.avatar',read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id','follower_id','username','avatar','is_following','created_at')

    
    def get_is_following(self,obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user,following=obj.follower).exists()
        return False




class FollowingListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='following.username',read_only=True)
    following_id = serializers.CharField(source='following.id',read_only=True)
    avatar = serializers.CharField(source='following.userprofile.avatar',read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id','username','following_id','avatar','is_following')

    def get_is_following(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return Follow.objects.filter(follower=user,following=obj.follower).exists()
        return False





class NotificationsSerializer(serializers.ModelSerializer):
    
    user = UserSerializer(read_only=True)
    post = PostSerializer()
    avatar = serializers.CharField(source='user.userprofile.avatar')

    class Meta:
        model = Notification
        fields = ('id','user','avatar','post','message','is_read','timestamp')









class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(source="sender.userprofile",read_only=True)

    class Meta:
        model = ChatMessage
        fields = ('id','content','sender','is_read','created_at')




class UserDiscussionSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(source='userprofile.avatar')
    unread_count = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id','username','avatar','unread_count')


    def get_unread_count(self,obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            return ChatMessage.objects.filter(sender=obj,receiver=user,is_read=False).count()
        return 0