import cv2 as cv
import pandas as pd
import numpy as np
import time
import math



#通过与鼠标交互选取操作区域，去除镜子的干扰
global min_r,max_r,min_c,max_c,imgg
#整个图的行列
global rr,cc
#记录帧数
global frame_count
#前帧的坐标值
global x0_f,y0_f,x1_f,y1_f
#按帧截取视频，并进行闭运算和滤波

def capture(video_path):
    #初始化前帧的值
    global x0_f,y0_f,x1_f,y1_f
    global frame_count
    #保存视频的大小
    global rr,cc
    #白板图
    bg=np.zeros((rr,cc,3),dtype=np.uint8)
    #读取视频的预处理    
    cap = cv.VideoCapture(video_path)
    cap.isOpened()
    frame_count = 1
    success = True
    kernel1 = np.ones((8,8),np.uint8)#腐蚀运算的掩膜
    kernel2 = np.ones((15,15),np.uint8)#膨胀运算的掩膜
    kernel3 = np.ones((20,20),np.uint8)#深度腐蚀运算的掩膜
    kernel4 = np.ones((5,5),np.uint8)#深度膨胀运算的掩膜
    while (success):
        success, frame = cap.read()
        if success==0:
            break
        # 转化为灰度图
        frame2=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
        params = []
        # params.append(cv.CV_IMWRITE_PXM_BINARY) 设置压缩状况
        params.append(1)
        #开运算，去除噪声
        eroded = cv.erode(frame2, kernel1)
        eroded = cv.erode(eroded, kernel1)
        dilated = cv.dilate(eroded, kernel2)
        #中值滤波
        mean_result=cv.medianBlur(dilated, 3)
        #阈值化处理
        r,result1=cv.threshold(mean_result,85,255,cv.THRESH_BINARY)
        #提取非镜子区域
        temp=result1[min_r:max_r,min_c:max_c]
        #将镜子区域涂黑并把非镜子区域放回原图
        r,c=mean_result.shape
        result2=np.zeros((r,c),dtype=np.uint8)
        result2[min_r:max_r,min_c:max_c]=temp
        #canny边缘检测
        canny_Img = cv.Canny(result2,50,200)
        #获取轮廓
        result3,contours, hierarchy= cv.findContours(canny_Img,cv.RETR_TREE,cv.CHAIN_APPROX_NONE)
        for i in range(len(contours)):
            sum=0
            x, y, w, h = cv.boundingRect(contours[i])
            if w>20 and h>20:
                sum+=1
       #防止边缘不明显，导致只有一个轮廓         
        while sum<2:
            sum=0
            result2 = cv.erode(result2, kernel3)
            canny_Img = cv.Canny(result2,50,200)
            result3,contours, hierarchy= cv.findContours(canny_Img,cv.RETR_TREE,cv.CHAIN_APPROX_NONE)
            for i in range(len(contours)):
                x, y, w, h = cv.boundingRect(contours[i])
                if w>20 and h>20:
                    sum+=1  
                    
        #构建抑制多重临近值的数组            
        x_n=[]
        y_n=[]        
                
        #保存所有中心值  
        for i in range(len(contours)):
            x, y, w, h = cv.boundingRect(contours[i])
            if w>20 and h>20:  
                x_n.append(math.floor(x+w/2))
                y_n.append(math.floor(y+h/2))
        #去除临近值
        if sum>2:         
            for i in range(len(x_n)):
                for j in range(i+1,len(x_n)):
                    if abs(x_n[i]-x_n[j])+abs(y_n[i]-y_n[j])<80:
                        x_n[i]=0
                        y_n[i]=0
        #去除临近值
        while len(x_n)>2:
            x_n.remove(0)
            y_n.remove(0)

        #防止两个老鼠的坐标互换,第一帧的处理
        if(frame_count==1):
            x0_f=x_n[0]
            y0_f=y_n[0]
            x1_f=x_n[1]
            y1_f=y_n[1]
            
        if(frame_count>=2):
            if abs(x_n[0]-x0_f)+abs(y_n[0]-y0_f)>200:
                temp_x=x_n[0]
                temp_y=y_n[0]
                x_n[0]=x_n[1]
                y_n[0]=y_n[1]
                x_n[1]=temp_x
                y_n[1]=temp_y

        #防止两个老鼠的标值互换，第二帧及以后的处理
        if(frame_count>1):
            cv.line(bg,(x0_f,y0_f),(x_n[0],y_n[0]),(0,255,0),1)
            cv.line(bg,(x1_f,y1_f),(x_n[1],y_n[1]),(255,0,0),1)
            cv.imshow("tracking_mouse", bg)
            x0_f=x_n[0]
            y0_f=y_n[0]
            x1_f=x_n[1]
            y1_f=y_n[1]
                
        #绘图展示
        cv.circle(frame, (x_n[0],y_n[0]), 3, (0,255,0), 2)
        cv.circle(frame, (x_n[1],y_n[1]), 3, (255,0,0), 2)              
        cv.imshow("temp",frame)
        cv.waitKey(1)
        # 保存图片
        cv.imwrite("tracking_mouse.jpg",bg)
        frame_count = frame_count + 1
        print(frame_count,'finished')
    cap.release()

#画框的鼠标响应，画框，选择区域
def on_mouse(event, x, y, flags, param):
    global imgg, point1, point2,min_r,min_c,max_r,max_c
    img2 = imgg.copy()
    if event == cv.EVENT_LBUTTONDOWN:         #左键点击
        point1 = (x,y)
        cv.circle(img2, point1, 3, (0,255,0), 2)
        cv.imshow('image', img2)
    elif event == cv.EVENT_MOUSEMOVE and (flags & cv.EVENT_FLAG_LBUTTON):               #按住左键拖曳
        cv.rectangle(img2, point1, (x,y), (255,0,0), 2)
        cv.imshow('image', img2)
    elif event == cv.EVENT_LBUTTONUP:         #左键释放
        point2 = (x,y)
        cv.rectangle(img2, point1, point2, (0,0,255), 3)
        cv.imshow('image', img2)
        min_c = min(point1[0],point2[0])
        min_r = min(point1[1],point2[1])
        max_c=max(point1[0],point2[0])
        max_r=max(point1[1],point2[1])
#选择，与第画框与选择区域相匹配
def sele(path):
    global imgg,rr,cc
    cap_temp = cv.VideoCapture(path)
    su,fr=cap_temp.read()
    rr=fr.shape[0]
    cc=fr.shape[1]
    imgg=fr
    cv.namedWindow('image')
    cv.setMouseCallback('image', on_mouse)
    cv.imshow('image', imgg)
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__=="__main__":
    cv.namedWindow('image')
    path='video_ini.mp4'
    sele(path)
    start_time=time.time()
    capture(path)
    end_time=time.time()
    print("灰度化图片速度：",frame_count/(end_time-start_time),"帧/s")
    cv.destroyAllWindows()


