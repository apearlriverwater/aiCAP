#coding=utf8
import itchat
import time

def locate_sender(send_id):
    sender_name=''
    for i in range(1,len(friends)):
        if send_id ==friends[i]['UserName']:
            sender_name=friends[i]['NickName']
            break

    return  sender_name

def send_market_msg(msg):
    itchat.send(msg, market_status_ID)

# 自动回复
# 封装好的装饰器，当接收到的消息是Text，即文字消息
@itchat.msg_register(itchat.content.TEXT)
def text_reply(msg):
    # 当消息不是由自己发出的时候
    if not msg['FromUserName'] == myUserName:
        sender_name=locate_sender(msg['FromUserName'])
        # 发送一条提示给文件助手
        itchat.send_msg(u"[%s]收到好友@%s 的信息：%s\n" %
                        (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg['CreateTime'])),
                         sender_name,
                         msg['Text']), 'filehelper')
        #send_market_msg('市场动态测试')
        # 回复给好友
        return u'[自动回复]您好，我现在有事不在，一会再和您联系。\n已经收到您的的信息：%s\n' % (msg['Text'])


#导入后自动运行、自动登录
itchat.auto_login(hotReload=True)
# 获取自己的UserName
friends=itchat.get_friends(update=True)[:1]
market_status_ID=itchat.search_chatrooms('市场动态')[0]["UserName"]
myUserName = friends[0]["UserName"]
itchat.run()


if __name__ == '__main__':
    pass

