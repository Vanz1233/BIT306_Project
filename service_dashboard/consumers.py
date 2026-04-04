import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join the "notifications" broadcast group
        await self.channel_layer.group_add("notifications", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the broadcast group
        await self.channel_layer.group_discard("notifications", self.channel_name)

    # This method is triggered when the group receives a message
    async def send_notification(self, event):
        # Send the message down the WebSocket to the browser
        await self.send(text_data=json.dumps(event["message"]))