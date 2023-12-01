from aqara_msg_push import MessageConsumer, TopLevelMessage
from rocketmq.client import ReceivedMessage, ConsumeStatus

# Your params from https://developer.aqara.com/console/overview
ADDRESS = 'some-broker1.aqara.com:9876'
TOPIC = 'sensor monitoring' 
GROUP_ID = '99..ce'
ACCESS_KEY = 'K....'
SECRET_KEY = 'nt..jg'

KEY_ID = ACCESS_KEY


class MyMessageConsumer(MessageConsumer):

    def callback(self, obj: TopLevelMessage, raw_msg: ReceivedMessage) -> ConsumeStatus:
        print(type(obj), obj.data)
        return ConsumeStatus.CONSUME_SUCCESS


MyMessageConsumer(
    group_id=GROUP_ID,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    topic=TOPIC,
    address=ADDRESS,
).consume()
