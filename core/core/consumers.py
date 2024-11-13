from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.exceptions import DenyConnection
from chat.models import ChatMessage
from api.models import CustomUser
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from api.serializers import ChatMessageSerializer





def serialize_message(message,user):
    serializer = ChatMessageSerializer(message,context={'user':user})
    return serializer.data



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.room_group_name = f'notifications_user_{self.scope["user"].id}'
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

        else:
            DenyConnection('User is not authenticated')


    async def disconnect(self, code):
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print('disconnected with code: ',code)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
    
    async def send_notification(self,event):
        payload= event['payload']

        await self.send(text_data=json.dumps({'payload':payload}))




class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = f"chat_user_{self.scope['user'].id}"
        await self.channel_layer.group_add(self.room_name,self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name,self.channel_name)



    async def receive(self,text_data):
        data = json.loads(text_data)
        recipient_id = data['recipient_id']
        message_content = data['content']

        recipient = await database_sync_to_async(CustomUser.objects.get)(id=recipient_id)
        message = await database_sync_to_async( ChatMessage.objects.create)(sender=self.scope['user'],
        receiver=recipient,content=message_content)
        serializer = await database_sync_to_async(serialize_message)(message=message,user=self.scope['user'])

        await self.channel_layer.group_send(
            f"chat_user_{recipient_id}",
            {
                'type':'chat_message',
                'alert':f"{self.scope['user'].username} sent you a message!",
                'message':serializer
            },
        )

    

    async def chat_message(self,event):
        message = event['message']
        alert = event['alert']


        await self.send(text_data=json.dumps({
            'alert':alert,
            'message':message,
        }))



