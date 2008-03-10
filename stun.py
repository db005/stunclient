#coding=cp936
#ʵ��stunЭ���һЩ����
import util, constants
import binascii, random, socket, time, logging

BindRequestMsg               = '0001'
BindResponseMsg              = '0101'
BindErrorResponseMsg         = '0111'
SharedSecretRequestMsg       = '0002'
SharedSecretResponseMsg      = '0102'
SharedSecretErrorResponseMsg = '0112'

MappedAddress    = '0001'
ResponseAddress  = '0002'
ChangeRequest    = '0003'
SourceAddress    = '0004'
ChangedAddress   = '0005'
Username         = '0006'
Password         = '0007'
MessageIntegrity = '0008'
ErrorCode        = '0009'
UnknownAttribute = '000A'
ReflectedFrom    = '000B'
XorOnly          = '0021'
XorMappedAddress = '8020'
ServerName       = '8022'
SecondaryAddress = '8050'


SimpleBindRequestMsgLength   = 8

serverName   = "stunserver.org"
serverIP     = None
serverPort   = 3478

secondName   = None#stun�������ĵڶ�����ַ�������ٴη���test1����Ϣ
secondPort   = None

externalIP1   = None#������������IP��port
externalPort1 = None

externalIP2   = None#������������IP��port
externalPort2 = None

natType       = constants.Uncomplete

localIP = util.getLocalIP()

logFileName = "stun.txt"

logger = util.logger(logFileName)

stunAtrChangeRequest = None

messageID = [util.GenTranID(), util.GenTranID(), 
             util.GenTranID(), util.GenTranID()]

class responseMessage:
    #msgType, msgLength, attributeDict
    #attributeDict = {attributeType1:value1,......}
    def __init__(self):
        self.msgType       = None
        self.msgLength     = None
        self.msgTranID     = None
        self.attributeDict = {}
    
    def setType(self, msgType):
        self.msgType = msgType
        
    def setLength(self, msgLength):
        self.msgLength = msgLength
        
    def setTranID(self, msgTranID):
        self.msgTranID = msgTranID
        
    def setAttribute(self, attributeType, value):
        self.attributeDict[attributeType] = value

def builtRequestMsg(*params):
    #params = (changeIP, changePort, id)
    #����bindrequest��Ϣ, return msg
    global logger
    
    (changeIP, changePort, id) = params
    changeRequestFlag = (changeIP and 4 or 0)|(changePort and 2 or 0)
    changeRequestFlag = util.int2hex(changeRequestFlag, 8)
    
    msg  = binascii.a2b_hex(BindRequestMsg)#msg type
    msg += binascii.a2b_hex(util.int2hex(SimpleBindRequestMsgLength, 4))#msg length
    msg += binascii.a2b_hex(id)
    msg += binascii.a2b_hex(ChangeRequest)#attribute type
    msg += binascii.a2b_hex("0004")#attribute value length
    msg += binascii.a2b_hex(changeRequestFlag)
    
    fp = open("packet/"+id+".txt", "wb")
    fp.write(msg)
    fp.close()
    
    logger.log("generate a message, its id is %s."%id, logging.INFO)
    
    return msg

def stunSendTest(*params):
    #params = (socket, serverName, serverPort, msg)
    #return the length of the msg which has been sended
    (sock, serverName, serverPort, msg) = params
    length = sock.sendto(msg, (serverName, serverPort)) 
    logger.log("send %d bytes msg to server:%s, port:%d"%(length, serverName, serverPort),\
               logging.INFO)
    
    return length

def stunParserMsg(*params):
    #params = (responseMsg)
    #�������ص���Ϣ, return a message class
    global logger
    logger.log("====start parser response message====", logging.INFO)
    
    (msg,) = params
    resMsg = responseMessage()
    
    start = 0
    
    msgType   = binascii.b2a_hex(msg[start:start+2])
    resMsg.setType(msgType)
    start += 2
    logger.log("msgType is %s"%msgType, logging.INFO)
    
    msgLength = int(binascii.b2a_hex(msg[start:start+2]), 16)
    resMsg.setLength(msgLength)
    start += 2
    logger.log("msgLength is %d"%msgLength, logging.INFO)
    
    msgTranID = binascii.b2a_hex(msg[start:start+16])
    resMsg.setTranID(msgTranID)
    start += 16
    logger.log("msgTranID is %s"%(msgTranID), logging.INFO)
    
    fp = open("packet/"+msgTranID+"_res.txt", "wb")#
    fp.write(msg)#
    fp.close()#
    
    while msgLength > 0:
        attributeType = binascii.b2a_hex(msg[start:start+2])
        start += 2
        msgLength -= 2
        #logger.log("attributeType is %s"%attributeType, logging.INFO)
        
        attributeLength = int(binascii.b2a_hex(msg[start:start+2]), 16)
        start += 2
        msgLength -= 2
        #logger.log("attibuteLength is %d"%attributeLength, logging.INFO)
        
        value = msg[start:start+attributeLength]
        start += attributeLength
        msgLength -= attributeLength
        #print "value is %s"%binascii.b2a_hex(value)
        
        resMsg.setAttribute(attributeType, value)
    
    return resMsg    

def getNatType():
    #return (natType, external IP, external port)
    global logger, natType
    
    #do test1, changeIP = False, changePort = False
    test1   = False#��ʾ�ڼ������Եĳɹ����
    test1_1 = False
    test2   = False
    test3   = False
    
    localPort1 = random.randint(30000, 50000)
    localPort2 = localPort1 + 1
    
    logger.log("open socket at port:%d, %d"%(localPort1, localPort2), logging.INFO)
    
    sock1      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock1.settimeout(20)
    sock1.bind(("", localPort1)) 
    
    sock2      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.settimeout(20)
    sock2.bind(("", localPort2))
    
    """
    send test 1
    """
    logger.log("send bind request one, changeIP = False, changePort = False", logging.INFO)
    changeIP   = False
    changePort = False
    id         = messageID[1]
    msg1 = builtRequestMsg(changeIP, changePort, id)
    stunSendTest(sock1, serverName, serverPort, msg1)
    #��ʼ������Ϣ
    #"""
    try:
        logger.log("start receive message", logging.INFO)
        response1 = sock1.recv(512)
        logger.log("receive %dbytes message"%len(response1), logging.INFO)
        responseMessageOne = stunParserMsg(response1)
        global externalIP1, externalPort1
        (externalIP1, externalPort1) = doMessageOne(responseMessageOne)
    except socket.timeout:
        #û�еõ����ذ������ܱ������ˣ�����nat ����Ϊ����
        logger.log("cann't receive response form server!It maybe blocked!", logging.INFO)
        natType = constants.Blocked#bat type is udp blocked
    
    #�ж��Ƿ��뱾��IP��ͬ
    global localIP, externalIP1
    if localIP == externalIP1:
        test1 = True
    else:
        test1 = False
    #"""
    #=============================================================
    """
    send test 2
    """
    logger.log("send bind request two, changeIP = True, changePort = False", logging.INFO)
    changeIP   = True
    changePort = False
    id         = messageID[2]
    msg2       = builtRequestMsg(changeIP, changePort, id)
    stunSendTest(sock1, serverName, serverPort, msg2)
    #������Ϣ
    #"""
    try:
        logger.log("start receive response two", logging.INFO)
        response2 = sock1.recv(512)
        logger.log("receive %dbytes message"%len(response2), logging.INFO)
        responseMessageTwo = stunParserMsg(response2)
        
        test2 = True        
        if test1 == True:
            natType = constants.OpenInternet
        else:
            natType = constants.FullCone
            
        doMessageTwo(responseMessageTwo)#
    except BaseException, info:
        #������û����Ӧ���򷵻�Uncomplete
        if test1 == True:
            logger.log("Nat type is SymmetricUDPFirewall.\n"+info.message, logging.INFO)
            natType = constants.SymmetricUDPFirewall
            #should return constants.SymmetricUDPFirewall
        else:
            logger.log("cann't receive response to message two\n"+info.message, logging.INFO)
            test2 = False#����ִ��test1_1
    #"""
    """
    send request 1_1
    """
    logger.log("send bind request one_one, changeIP = False, changePort = False", logging.INFO)
    changeIP   = False
    changePort = False
    id         = messageID[0]
    msg1_1 = builtRequestMsg(changeIP, changePort, id)
    stunSendTest(sock1, secondName, secondPort, msg1_1)
    #��ʼ������Ϣ
    #"""
    try:
        logger.log("start receive response 1_1", logging.INFO)
        response1_1 = sock1.recv(512)
        logger.log("receive %dbytes message"%len(response1_1), logging.INFO)
        responseMessageOne = stunParserMsg(response1_1)
        global externalIP2, externalPort2
        (externalIP2, externalPort2) = doMessageOne(responseMessageOne)
        
        
        if (externalIP1, ) != (externalIP2, ):
            logger.log("Nat type is SymmetricNAT", logging.INFO)
            natType = constants.SymmetricNAT
        else:
            test1_1 = True        
    except socket.timeout:
        #û�еõ����ذ������ܱ������ˣ�����nat ����Ϊ����
        logger.log("cann't receive response 1_1 form server!It maybe blocked!", logging.INFO)
        return constants.Uncomplete
    
    """
    send request three
    """
    logger.log("send bind request one_one, changeIP = False, changePort = True", logging.INFO)
    changeIP   = False
    changePort = True
    id         = messageID[0]
    msg3 = builtRequestMsg(changeIP, changePort, id)
    stunSendTest(sock1, secondName, secondPort, msg3)
    #��ʼ������Ϣ
    #"""
    try:
        logger.log("start receive response 3", logging.INFO)
        response3 = sock1.recv(512)
        logger.log("receive %dbytes message"%len(response3), logging.INFO)
        responseMessageThree = stunParserMsg(response3)
        #if receive message, nat type is the RestricNAT 
        if (not test1) and (not test2) and (test1_1):
            logger.log("nat type is RestricNAT", logging.INFO)
            natType = constants.RestricNAT
        
    except socket.timeout:
        #û�еõ����ذ������ܱ������ˣ�����nat ����Ϊ����
        #logger.log("cann't receive response 3 form server!It maybe blocked!", logging.INFO)
        if (not test1) and (not test2) and (test1_1):
            logger.log("nat type is RestricPortNAT", logging.INFO)
            natType = constants.RestricPortNAT            

    return natType

def doMessageOne(msg):
    #�����ص���Ϣ1
    mappedAddressValue = msg.attributeDict[MappedAddress]
    
    family       = binascii.b2a_hex(mappedAddressValue[0:2])
    externalPort = int(binascii.b2a_hex(mappedAddressValue[2:4]), 16)
    externalIP   = socket.inet_ntoa(mappedAddressValue[4:8])  
    logger.log("bind request one's response:", logging.INFO)    
    logger.log("mappedAddress--external IP:%s, externalPort is %d"%(externalIP, externalPort), logging.INFO)
    
    sourceAddressValue = msg.attributeDict[SourceAddress]
    
    sourcefamily = binascii.b2a_hex(sourceAddressValue[0:2])
    sourcePort   = int(binascii.b2a_hex(sourceAddressValue[2:4]), 16)
    sourceIP     = socket.inet_ntoa(sourceAddressValue[4:8])
    logger.log("message send from :%s:%d"%(sourceIP, sourcePort), logging.INFO)
    
    global serverIP
    serverIP = sourceIP
        
    changedAddressValue = msg.attributeDict[ChangedAddress]
    
    changedFamily = binascii.b2a_hex(changedAddressValue[0:2])
    changedPort   = int(binascii.b2a_hex(changedAddressValue[2:4]), 16)
    changedIP     = socket.inet_ntoa(changedAddressValue[4:8])  
    
    logger.log("the second server address is:%s:%d"%(changedIP, changedPort), logging.INFO)
    global secondName
    global secondPort
    #��õڶ���ip��ַ��port
    (secondName, secondPort) = (changedIP, changedPort)
    
    return (externalIP, externalPort)
    
def doMessageTwo(msg):
    #�����ص���Ϣ2
    mappedAddressValue = msg.attributeDict[MappedAddress]
    
    family       = binascii.b2a_hex(mappedAddressValue[0:2])
    externalPort = int(binascii.b2a_hex(mappedAddressValue[2:4]), 16)
    externalIP   = socket.inet_ntoa(mappedAddressValue[4:8])  
    logger.log("bind request two's response:", logging.INFO)    
    logger.log("mappedAddress--external IP:%s, externalPort is %d"%(externalIP, externalPort), logging.INFO)
    
    sourceAddressValue = msg.attributeDict[SourceAddress]
    
    sourcefamily = binascii.b2a_hex(sourceAddressValue[0:2])
    sourcePort   = int(binascii.b2a_hex(sourceAddressValue[2:4]), 16)
    sourceIP     = socket.inet_ntoa(sourceAddressValue[4:8])
    logger.log("message send from :%s:%d"%(sourceIP, sourcePort), logging.INFO)
    
    changedAddressValue = msg.attributeDict[ChangedAddress]
    
    changedFamily = binascii.b2a_hex(changedAddressValue[0:2])
    changedPort   = int(binascii.b2a_hex(changedAddressValue[2:4]), 16)
    changedIP     = socket.inet_ntoa(changedAddressValue[4:8])  
    
    logger.log("the changeedIP is %s, changedPort is %d"%(changedIP, changedPort), logging.INFO)
    
"""
fp = open("response_one.txt", "rb")
content = fp.read()
stunParserMsg(content)
fp.close()
"""