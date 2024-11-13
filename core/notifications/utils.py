
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from api.serializers import UserSerializer,PostSerializer

channel_layer = get_channel_layer()



def send_notification(action_user,message,request,target_user=None,post=None):
    if target_user:
        notification = Notification.objects.create(user=action_user,post=post,target_user=target_user,message=message)
        notifications_count = Notification.objects.filter(target_user=target_user,is_read=False).count()
        user = UserSerializer(action_user)
        post = PostSerializer(post,context={'user':request.user}) if post else None
        avatar = action_user.userprofile.avatar
        payload = {
            'notifications_count':notifications_count,
            'results':{
                'id':notification.id,
                'user':user.data,
                'post':post.data,
                'avatar':str(avatar),
                'message':message,
                'is_read':notification.is_read,
            }
        }

        async_to_sync(channel_layer.group_send)(
        f"notifications_user_{target_user.id}",
        {
            "type":"send_notification",
            "payload":payload,
            }
        )




    else:
        followers = action_user.followers.all()
        for follower in followers:
            notification = Notification.objects.create(user=action_user,post=post,target_user=follower.follower,message=message)
            notifications_count = Notification.objects.filter(target_user=follower,is_read=False).count()
            user = UserSerializer(follower)
            post = PostSerializer(post,context={'user':request.user}) if post else None
            avatar = follower.userprofile.avatar
            payload = {
            'notifications_count':notifications_count,
            'results':{
                'id':notification.id,
                'user':user.data,
                'post':post.data,
                'avatar':str(avatar),
                'message':message,
                'is_read':notification.is_read,
                }
            }
            async_to_sync(channel_layer.group_send)(
            f"notifications_user_{follower.id}",
            {
                "type":"send_notification",
                "payload":payload,
            }
            )

