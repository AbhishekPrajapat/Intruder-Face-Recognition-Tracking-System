import socket
from threading import Thread
from tkinter import *
from tkinter import ttk
import cv2
import pickle
import ars_face_recognition
import pymysql
import time
from tkinter import messagebox
from PIL import Image, ImageTk
import datetime


# SERVER CLASS
class Server(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.sock=socket.socket()
        self.host=socket.gethostbyname("127.0.0.1")
        self.port=9999
        self.sock.bind((self.host,self.port))
        self.sock.listen(5)

    def run(self):
        while(True):
            print("waiting for client")
            _client,addr=self.sock.accept()
            newclient = Client(_client)
            newclient.start()


# CLIENT CLASS
class Client(Thread):

    def __init__(self, request):
        Thread.__init__(self)
        self._client = request
        self.member = None

    def run(self):

        temp = self._client.recv(38)
        self.member = temp.decode("utf-8")
        self._client.sendall(b"done")
        print(self.member, " connected ")
        db = pymysql.connect("127.0.0.1", "root", "", "tracking_system")
        cur = db.cursor()
        cur2 = db.cursor()
        cur3 = db.cursor()


        while (True):

            while(True):
                try:
                    encsize=self._client.recv(39)
                    osize=encsize.decode("utf-8")
                        #print("before size=",osize)
                    self._client.sendall(b"done")
                    temp = self._client.recv(int(osize))
                except:
                    self._client.sendall(b"notd")
                    break

                    #print("size of recv data",sys.getsizeof(temp))
                try:
                    data = pickle.loads(temp)

                    data_encoded=ars_face_recognition.face_encodings(data)[0]

                    cur.execute("select * from master")
                    res = cur.fetchone()
                    while (res):

                        dbimg = pickle.loads(res[5])

                        res1 = ars_face_recognition.compare_faces([data_encoded], dbimg)

                        if res1[0] == True:

                            print(res[1], " is front on camera  ", self.member)
                            cv2.imwrite("known/"+str(res[1])+".jpeg",data)


                            cur2.execute("INSERT INTO track_info(id, camera, time, date) VALUES(%s,%s,%s,%s)",
                                        (int(res[0]), self.member, str(datetime.datetime.now().strftime('%H:%M:%S')),
                                         str(datetime.date.today())))
                            db.commit()
                            Comm_Res.admin.update_frame()
                            self._client.sendall(b"done")
                            time.sleep(4)
                            break
                        else:
                            res = cur.fetchone()

                    else:

                        unpickle=pickle.dumps(data_encoded)
                        #print(data)
                        print("unknown caught on camera ", self.member)


                        cur.execute("INSERT INTO master(name, dept, gender, type,img,other) VALUES('unknown','unknown','unknown','unknown',%s,'unknown')",(unpickle))

                        db.commit()
                        cur.execute("select last_insert_id() from master")
                        last_id = cur.fetchone()
                        cv2.imwrite("unknown/unknown id"+ str(last_id[0]) +" .jpeg", data)
                        cv2.imwrite("registered/unknown" + str(last_id[0]) + ".jpeg", data)
                        cur3.execute("INSERT INTO track_info(id,camera, time, date) VALUES(%s,%s,%s,%s)",
                                     (int(last_id),self.member, str(datetime.datetime.now().strftime('%H:%M:%S')),
                                      str(datetime.date.today())))
                        db.commit()
                        Comm_Res.admin.update_frame()
                        time.sleep(4)
                        self._client.sendall(b"done")
                except:
                    time.sleep(4)
                    self._client.sendall(b"done")



# GUI CLASS
class Gui:

    def __init__(self, master):
        self.window = master

        self.lbl = Label(self.window, text="Server is on")
        self.lbl.place(x=400, y=250)
        self.lbl.config(font=("Courier", 44))

        self.btn = Button(self.window, text="Login", command=self.btn_login)
        self.btn.place(x=600, y=400)

    def btn_login(self):
        root = Toplevel()
        root.state("zoomed")
        root.title("Tracking System")
        #root.geometry("1000x800")
        root.configure(background="black")
        obj = Login(root)
        root.mainloop()


# LOGIN CLASS
class Login:

    def __init__(self, master):
        self.window = master

        self.image = Image.open("image/final.jpg")
        self.img_copy = self.image.copy()

        self.background_image = ImageTk.PhotoImage(self.image)

        self.background = Label(self.window, image=self.background_image)
        self.background.pack(fill=BOTH, expand=YES)

        self.label_username = Label(self.window, text="Username :", bg="black", fg="white")
        self.label_username.config(font=("Courier", 15))
        self.label_username.place(x=0, y=200, h=40)
        self.label_password = Label(self.window, text="Password :", bg="black", fg="white")
        self.label_password.config(font=("Courier", 15))
        self.label_password.place(x=0, y=250, h=40)

        self.username = StringVar()
        self.password = StringVar()
        self.entry_username = Entry(self.window, textvariable=self.username)
        self.entry_username.place(x=126, y=200, h=40)
        self.entry_username.config(font=("ARIAL", 15))
        self.entry_password = Entry(self.window, show="*", textvariable=self.password)
        self.entry_password.place(x=126, y=250, h=40)
        self.entry_password.config(font=("ARIAL", 15))
        self.btn = Button(self.window, text="Log In", command=self.btn_submit)
        self.btn.place(x=268, y=291, h=30, w=80)

    def btn_submit(self):
        username=self.username.get()
        password=self.password.get()

        if username == "" or password == "":
            messagebox.showerror("login error", message="Username and Password cannot be blanked")
        elif username=="admin" and password=="admin":
            self.window.destroy()
            root1 = Toplevel()

            root1.title("Tracking System")
            root1.geometry("1000x800")
            root1.state("zoomed")
            Comm_Res.admin = Admin(root1)
            Comm_Res.admin.update_frame()
            root1.mainloop()

        else:
            messagebox.showinfo("Invalid",message="Invalid Username or Password try again")


#Common Resource

class Comm_Res:
    admin=None

# ADMIN PANEL CLASS
class Admin:

    def __init__(self,master):

        self.window=master
        self.btn=Button(self.window,text="Register",command=self.btn_register)
        self.btn.place(x=0,y=0,h=30,w=50)

        self.btn = Button(self.window, text="Log Out", command=self.btn_logout)
        self.btn.place(x=50, y=0, h=30, w=50)

        self.btn = Button(self.window, text="User Record", command=self.btn_userrec)
        self.btn.place(x=100, y=0,h=30,w=70)

        self.btn = Button(self.window, text="Log Report", command=self.btn_logrec)
        self.btn.place(x=170, y=0,h=30,w=70)

        self.db = pymysql.connect("127.0.0.1", "root", "", "tracking_system")
        self.userframe=None
        self.logframe=None
        self.inner_frame = None
        self.inner_frame2 = None

    def btn_logrec(self):
        if self.userframe is not None:
            self.userframe.destroy()
        self.logframe=Frame(self.window,width=1370, height=250)

        self.logframe.place(x=0,y=100)
        self.lbl = Label(self.logframe, text="Track Report")
        self.lbl.place(x=180, y=0)
        self.lbl.config(font=("ARIAl", 15))

        self.lblsearchby = Label(self.logframe, text="Track By:")
        self.lblsearchby.place(x=0, y=50)

        self.value = StringVar()
        self.byid = Radiobutton(self.logframe, text="By Id", variable=self.value, value="id")
        self.byid.place(x=70, y=50)
        self.byid.select()

        self.byname = Radiobutton(self.logframe, text="By Name", variable=self.value, value="name")
        self.byname.place(x=130, y=50)


        self.bytype = Radiobutton(self.logframe, text="By Date", variable=self.value, value="date")
        self.bytype.place(x=210, y=50)

        self.bytype = Radiobutton(self.logframe, text="By Camera", variable=self.value, value="camera")
        self.bytype.place(x=280, y=50)

        self.lblsearch = Label(self.logframe, text="Search:")
        self.lblsearch.place(x=0, y=125)

        self.txt = Entry(self.logframe)
        self.txt.place(x=100, y=125)

        self.btn_get = Button(self.logframe, text="Find", command=self.btn_track)
        self.btn_get.place(x=100, y=150)


    def btn_track(self):
        if self.txt.get()=="":
            messagebox.showerror("Alert",message="Search Value textbox cant be blanked")
        else:
            name=0
            inner_frame=Frame(self.logframe,height=250,width=770)
            inner_frame.place(x=500,y=0)
            cur=self.db.cursor()
            if self.value.get()=="name":
                name=1
                cur.execute("select * from master where " + self.value.get() + "=%s", (self.txt.get()))
                val = cur.fetchall()
            else:
                cur.execute("select * from track_info where "+self.value.get()+"=%s", (self.txt.get()))
                val=cur.fetchall()

            tree=ttk.Treeview(inner_frame,columns=(1,2,3,4,5),height=10,show="headings")
            tree.pack(side='left')
            tree.heading(1, text="Id")
            tree.heading(2, text="Name")
            tree.heading(3, text="Camera")
            tree.heading(4, text="Time")
            tree.heading(5, text="Date")
            tree.column(1,width=120)
            tree.column(2,width=170)
            tree.column(3,width=170)
            tree.column(4,width=170)
            tree.column(5,width=170)

            scroll = ttk.Scrollbar(inner_frame, orient="vertical", command=tree.yview)
            scroll.pack(side='right', fill='y')
            tree.configure(yscrollcommand=scroll.set)
            cur2 = self.db.cursor()
            if name==0:
                length = (len(val)) - 1

                while (length >= 0):
                    cur2.execute("select name from master where id = %s", (val[length][1]))
                    val2 = cur2.fetchall()
                    tree.insert('', 'end', values=(val[length][1],val2[0][0],val[length][2],val[length][3],val[length][4]))
                    length = length - 1
            if name==1:
                if len(val)>0:
                    cur2.execute("select * from track_info where id = %s", (val[0][0]))
                    val2 = cur2.fetchall()
                    length = (len(val2)) - 1

                    while (length >= 0):
                        tree.insert('', 'end',values=(val[0][0], val[0][1], val2[length][2], val2[length][3], val2[length][4]))
                        length = length - 1


    def btn_userrec(self):
        if self.logframe is not None:
            self.logframe.destroy()
        self.userframe = Frame(self.window, width=1370, height=250)
        self.userframe.place(x=0, y=100)
        self.lbl = Label(self.userframe, text="Search Record")
        self.lbl.place(x=180, y=0)
        self.lbl.config(font=("ARIAl", 15))

        self.lblsearchby = Label(self.userframe, text="Search By:")
        self.lblsearchby.place(x=0, y=50)
        self.value = StringVar()
        self.byid = Radiobutton(self.userframe, text="By Id", variable=self.value, value="id")
        self.byid.place(x=70, y=50)
        self.byid.select()
        self.byname = Radiobutton(self.userframe, text="By Name", variable=self.value, value="name")
        self.byname.place(x=130, y=50)

        self.bydept = Radiobutton(self.userframe, text="By Dept", variable=self.value, value="dept")
        self.bydept.place(x=210, y=50)

        self.bytype = Radiobutton(self.userframe, text="By Type", variable=self.value, value="type")
        self.bytype.place(x=280, y=50)

        self.bygen = Radiobutton(self.userframe, text="By Gender", variable=self.value, value="gender")
        self.bygen.place(x=350, y=50)

        self.txt = Entry(self.userframe)
        self.txt.place(x=100, y=125)

        self.lblsearch = Label(self.userframe, text="Search:")
        self.lblsearch.place(x=0, y=125)

        self.btn_get = Button(self.userframe, text="Get Data", command=self.btn_search)
        self.btn_get.place(x=100, y=150)

        self.btn_get = Button(self.userframe, text="View Image", command=self.btn_viewimg)
        self.btn_get.place(x=170, y=150)

    def btn_viewimg(self):
        if self.txt.get() == "":
            messagebox.showerror("Alert", message="Search Value textbox cant be blanked")
        elif self.value.get() == "name" or self.value.get() == "id":
            cur = self.db.cursor()

            cur.execute("select * from master where " + self.value.get() + "=%s", (self.txt.get()))
            var = cur.fetchall()
            if len(var) > 0:
                if self.inner_frame is not None:
                    self.inner_frame.destroy()
                img = var[0][1] + str(var[0][0])
                self.inner_frame2 = Frame(self.userframe, height=250, width=770)
                self.inner_frame2.place(x=500, y=0)
                si = Image.open("registered/" + img + ".jpeg", 'r')
                resize = si.resize((350, 220), Image.ANTIALIAS)
                ss = ImageTk.PhotoImage(resize)
                lbl = Label(self.inner_frame2, image=ss)
                lbl.image = ss
                lbl.place(x=0, y=0)


        else:
            messagebox.showerror("Alert", message="Image can search only by ID and NAME")

    def btn_search(self):
        if self.txt.get()=="":
            messagebox.showerror("Alert",message="Search Value textbox cant be blanked")
        else:
            if self.inner_frame2 is not None:
                self.inner_frame2.destroy()
            self.inner_frame=Frame(self.userframe,height=250,width=770)
            self.inner_frame.place(x=500,y=0)
            cur=self.db.cursor()

            cur.execute("select * from master where "+self.value.get()+"=%s", (self.txt.get()))
            var=cur.fetchall()

            tree=ttk.Treeview(self.inner_frame,columns=(1,2,3,4,5,6),height=10,show="headings")
            tree.pack(side='left')
            tree.heading(1, text="Id")
            tree.heading(2, text="Name")
            tree.heading(3, text="Department")
            tree.heading(4, text="Gender")
            tree.heading(5, text="Type")
            tree.heading(6, text="Other")
            tree.column(1,width=70)
            tree.column(2,width=170)
            tree.column(3,width=170)
            tree.column(4,width=90)
            tree.column(5,width=90)
            tree.column(6,width=260)
            scroll = ttk.Scrollbar(self.inner_frame, orient="vertical", command=tree.yview)
            scroll.pack(side='right', fill='y')
            tree.configure(yscrollcommand=scroll.set)
            for put in var:
                tree.insert("","end",values=(put[0],put[1],put[2],put[3],put[4],put[6]))



    def btn_logout(self):
        self.window.destroy()

    def btn_register(self):
        master=Toplevel()
        master.title("Register")
        master.geometry("1000x800")
        master.state("zoomed")
        obj=Register(master)
        master.mainloop()

    def update_frame(self):
        obj = Frame(self.window)
        obj.place(x=0, y=400)
        tree = ttk.Treeview(obj, columns=(1, 2, 3, 4, 5, 6, 7, 8), height=10, show="headings")
        tree.pack(side='left')
        tree.heading(1, text="Id")
        tree.heading(2, text="Name")
        tree.heading(3, text="Department")
        tree.heading(4, text="Gender")
        tree.heading(5, text="Type")
        tree.heading(6, text="Camera")
        tree.heading(7, text="Time")
        tree.heading(8, text="Date")
        tree.column(1,width=30)
        tree.column(2)
        tree.column(3)
        tree.column(4)
        tree.column(5)
        tree.column(6)
        tree.column(7)
        tree.column(8)
        scroll = ttk.Scrollbar(obj, orient="vertical", command=tree.yview)
        scroll.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scroll.set)
        cur = self.db.cursor()
        cur.execute("select * from track_info")
        cur2 = self.db.cursor()
        val = cur.fetchall()
        length = (len(val)) - 1

        while (length >= 0):
            cur2.execute("select * from master where id = %s", (val[length][1]))
            val2 = cur2.fetchall()
            tree.insert('', 'end', values=(
            val[length][1], val2[0][1], val2[0][2], val2[0][3], val2[0][4], val[length][2], val[length][3],
            val[length][4]))
            length = length - 1
        self.db.commit()



# REGISTER CLASS
class Register:
    def __init__(self,master):
        self.check=0
        self.imgvar=None
        self.window=master
        self.lblname=Label(self.window,text="Enter Name:")
        self.lblname.place(x=10,y=10)

        self.lbldept=Label(self.window,text="Department:")
        self.lbldept.place(x=10,y=50)

        self.lblgender=Label(self.window,text="Select Gender:")
        self.lblgender.place(x=10,y=90)

        self.lbltype=Label(self.window,text="Select Type:")
        self.lbltype.place(x=10,y=130)

        self.lblimg=Label(self.window,text="Take Image:")
        self.lblimg.place(x=10,y=170)


        self.txtname=Entry(self.window)
        self.txtname.place(x=120,y=10)


        self.txtdept=Entry(self.window)
        self.txtdept.place(x=120,y=50)

        self.mygender=StringVar()
        self.mgender=Radiobutton(self.window,text="Male", variable=self.mygender,value="Male")
        self.mgender.place(x=120,y=90)

        self.fgender = Radiobutton(self.window, text="Female", variable=self.mygender, value="Female")
        self.fgender.place(x=200, y=90)
        self.fgender.deselect()

        self.type=StringVar()

        self.typestudent=Radiobutton(self.window,text="Student",variable=self.type,value="Student")
        self.typestudent.place(x=120,y=130)

        self.typefaculty = Radiobutton(self.window, text="Faculty", variable=self.type, value="Faculty")
        self.typefaculty.place(x=200, y=130)
        self.typefaculty.deselect()

        self.typestaff = Radiobutton(self.window, text="Staff", variable=self.type, value="Staff")
        self.typestaff.place(x=280, y=130)
        self.typestaff.deselect()

        self.takeimg=Button(self.window,text="Upload",command=self.upimage)
        self.takeimg.place(x=120,y=170)

        self.lblcaptute = Label(self.window, text="Press c to capture image")
        self.lblcaptute.place(x=180, y=170)

        self.submit=Button(self.window,text="Submit",command=self.enter)
        self.submit.place(x=120,y=400)


        self.lblother=Label(self.window,text="Other Details:")
        self.lblother.place(x=0,y=220)

        self.other=Text(self.window,height="10",width="30")
        self.other.place(x=100,y=220)

    def upimage(self):

        faceDetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        cam = cv2.VideoCapture(0)
        while (True):
            ret, img = cam.read()
            cv2.imshow("Face", img)
            if (cv2.waitKey(1) == ord('c')):
                #img_encoded = ars_face_recognition.face_encodings(img)[0]
                ch = cv2.Laplacian(img, cv2.CV_64F).var()
                if ch>40:

                    faces = faceDetect.detectMultiScale(img, 1.3, 5)

                    for (x, y, w, h) in faces:
                        y=y-100
                        x=x-100

                        self.temp = img[y:y + h +200, x:x + w+200 ]
                        cv2.imwrite("temp/temp.jpg",self.temp)
                        try:

                            dbimg = ars_face_recognition.face_encodings(self.temp)[0]
                        except:
                            break
                        self.imgvar=pickle.dumps(dbimg)

                        self.check=1

                        si=Image.open("temp/temp.jpg",'r')
                        ss=ImageTk.PhotoImage(si)
                        lbl=Label(self.window,image=ss)
                        lbl.image=ss
                        lbl.place(x=500,y=170)
                    break

        cam.release()
        cv2.destroyAllWindows()

    def enter(self):
        name=self.txtname.get()
        dept=self.txtdept.get()
        gender=self.mygender.get()
        type=self.type.get()
        img=self.imgvar
        other=self.other.get("1.0",END)

        if name=="" or dept=="":
            messagebox.showinfo("Alert",message="Enter proper detail")
        elif self.check==0:
            messagebox.showinfo("Alert",message="Please Take Picture")
        else:

            db=pymysql.connect("127.0.0.1","root","","tracking_system")
            cur=db.cursor()
            cur.execute("INSERT INTO master(name, dept, gender, type, img, other) VALUES(%s,%s,%s,%s,%s,%s)",(name,dept,gender,type,img,other))
            db.commit()
            cur2=db.cursor()
            cur2.execute("select last_insert_id() from master")
            last_id = cur2.fetchone()
            cv2.imwrite("registered/"+name+str(last_id[0])+".jpeg", self.temp)
            messagebox.showinfo("Info", message="Successfully added record")
            self.window.destroy()

def main():

    Gui.n=40
    ser=Server()
    ser.start()
    root=Tk()
    root.state("zoomed")
    root.title("Server")
    root.geometry("1200x800")
    obj=Gui(root)
    root.mainloop()


main()
