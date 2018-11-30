import socket
import cv2
import pickle
import sys


mySocket = None
ip = '127.0.0.1'
port = 9999

print('starting Client')

mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#print('trying to connet')

mySocket.connect((ip, port))
print("connected")
#print('conneted successfuly  camera open..!')

faceDetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cam_name="cam 1"
data=cam_name.encode("utf-8")

mySocket.sendall(data)
data=mySocket.recv(37)
cam = cv2.VideoCapture(0)


while True:
    data = None
    ret, img = cam.read()

    faces = faceDetect.detectMultiScale(img, 1.3, 5)

    for(x,y,w,h) in faces:
        ch = cv2.Laplacian(img, cv2.CV_64F).var()

        if ch > 40:

            if y>99 and x>99:
                y=y-100
                x=x-100

                main_img=img[y:y+h+200,x:x+w+200]
                #print("size of img",sys.getsizeof(main_img))
                data = pickle.dumps(main_img)

                size=str(sys.getsizeof(data))
                enc=size.encode("utf-8")
                #print("encodede size =",sys.getsizeof(enc))
                #print("size sending")
                mySocket.sendall(enc)
                #print("size sent")
                ack=mySocket.recv(37)
                if ack==b"notd":
                    break
                #print("ack of size and send img")
                #print("size after pickle=",sys.getsizeof(data))
                #print("sendind data=",data)
                mySocket.sendall(data)
                #sprint("ack of image")

                ack = mySocket.recv(37)





cam.release()
cv2.destroyAllWindows()
