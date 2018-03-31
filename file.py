'''

* Author List:       Siddharth Aggarwal,Vipin Bhardwaj

* Functions:         overlay, identifyCM, reset, stop_, update_direction, checkZI

* Global Variables:  cam, img_width, img_height, left, right, left_r, right_r, red_led, green_led, blue_led, LineArea, BLUE, GREEN, RED, TRAINGLE, SQUARE, CIRCLE
                     Zone, color_observed,plantation_img, bg_img, csv_file, frm, inv_plane, lower_val, upper_val

'''



import csv
import cv2
import numpy as np 
from picamera import PiCamera 
from picamera.array import PiRGBArray
from time import sleep
import RPi.GPIO as GPIO
import math
import time

####Initilizing the camera#####

cam = PiCamera()
img_height = 90
img_width = 80
raw_cap = PiRGBArray(cam, size = (img_width, img_height))
cam.resolution = (img_width, img_height)
sleep(3)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
cam.brightness = 50
cam.contrast = 50

### Setting up the GPIO pins ###
M1A = 36
M1B = 32
M1E = 33
M2A = 35
M2B = 37
M2E = 40
RED_LED = 8
GREEN_LED = 12
BLUE_LED = 11


GPIO.setup(M1A,GPIO.OUT)
GPIO.setup(M1B,GPIO.OUT)
GPIO.setup(M1E,GPIO.OUT)
GPIO.setup(M2A,GPIO.OUT)
GPIO.setup(M2B,GPIO.OUT)
GPIO.setup(M2E,GPIO.OUT)
GPIO.setup(RED_LED,GPIO.OUT)
GPIO.setup(GREEN_LED,GPIO.OUT)
GPIO.setup(BLUE_LED,GPIO.OUT)

GPIO.output(33, 0)
GPIO.output(35, 0)
GPIO.output(37, 0)
GPIO.output(36, 0)
GPIO.output(32, 0)
GPIO.output(40, 0)

left = GPIO.PWM(M1A, 100)           #left represents the PWM for left wheel in forward irection
right = GPIO.PWM(M2A, 100)          #right represents the PWM for right wheel in forward irection
left_r = GPIO.PWM(M1B, 100)         #left_r represents the PWM for left wheel in reverse direction
right_r = GPIO.PWM(M2B, 100)        #right_r represents the PWM for right wheel in reverse direction
red_led = GPIO.PWM(RED_LED, 100)    #red_led represents the PWM for controlling RED LED
blue_led = GPIO.PWM(BLUE_LED, 100)  #blue_led represents the PWM for controlling BLUE LED
green_led = GPIO.PWM(GREEN_LED,100) #green_led represents the PWM for controlling GREEN LED

red_led.start(0)
blue_led.start(0)
green_led.start(0)

cur_duty = 40                       #cur_duty represents the value of current duty Cycle of the motor
left.start(cur_duty)                #setting the start value of left wheel
right.start(cur_duty)               #setting the start value of right wheel

left_r.start(0)         
right_r.start(0)


LineArea = 10000                      # It represents the area of the line in the image, currently set to some default value
BLUE, GREEN, RED = 0, 1, 2            # Macro's representing colors of CM
TRIANGLE, SQUARE, CIRCLE = 0, 1, 2    # Macro's representing shape of CM
Zone = 0                              # it tells the current zone number

color_observed = []                    # this is a list which will store the colors observed during the traversal

################### OVERLAYING FUNCTIONS ######################

plantation_img = cv2.imread('./Plantation.png')  # plantation image represents the Background image
bg_img = plantation_img.copy()                   # bg_img is a copy of the original background image
csv_file={}
with open('./Input Table.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Color'] =='Blue':
            if row['Shape'] == 'Triangle':
                csv_file[BLUE,TRIANGLE]=row['Seedling Image']
            elif row['Shape'] == 'Square':
                csv_file[BLUE,SQUARE]=row['Seedling Image']
            elif row['Shape'] == 'Circle':
                csv_file[BLUE,CIRCLE]=row['Seedling Image']
        elif row['Color'] =='Red':
            if row['Shape'] == 'Triangle':
                csv_file[RED,TRIANGLE]=row['Seedling Image']
            elif row['Shape'] == 'Square':
                csv_file[RED,SQUARE]=row['Seedling Image']
            elif row['Shape'] == 'Circle':
                csv_file[RED,CIRCLE]=row['Seedling Image']
        elif row['Color'] =='Green':
            if row['Shape'] == 'Triangle':
                csv_file[GREEN,TRIANGLE]=row['Seedling Image']
            elif row['Shape'] == 'Square':
                csv_file[GREEN,SQUARE]=row['Seedling Image']
            elif row['Shape'] == 'Circle':

                csv_file[GREEN,CIRCLE]=row['Seedling Image']
'''
Function Name:     overlay
Input :            plant (address of flower image which is to be overlayed), 
                   count (Number of Color markers detected, (1,4) )
Output :           NONE

Logic :            
'''
def overlay(plant, count):
    global Zone
    # The variable pos is assigned the position at which overlaying has to be done
    pos = [ [ (314,235), (380, 235), (450, 235), (520, 235) ], [(118,187), (161, 195), (67, 225), (114, 230)], [(227,165), (273, 175), (295, 140), (344, 154)], [(465,157), (513, 164), (612, 173), (563, 176)]] 
    res_img = cv2.imread(plant,cv2.IMREAD_UNCHANGED)
    
    res_img = cv2.resize(res_img,dsize=(42,42),interpolation = cv2.INTER_AREA)  
    # We store the height and width of the plant's image in 'h' and 'w'
    h,w,_ = res_img.shape  # Size of pngImg
    # We store the height and width of the background image in 'rows' and 'cols'
    rows,cols,_ = bg_img.shape  # Size of background Image
    #We store the x and y position which we passed to the function in variables 'y' and 'x'
    cur_cor = pos[Zone]
    for i in range(count):

	y,x = cur_cor[i]    # Position of PngImage
	    #loop over all pixels and apply the blending equation
	for i in range(h):
	    for j in range(w):
	        if x+i >= rows or y+j >= cols:
	            continue
	        alpha = float(res_img[i][j][3]/255.0) # read the alpha channel 
	        bg_img[x+i][y+j] = alpha*res_img[i][j][:3]+(1-alpha)*bg_img[x+i][y+j]


#######END#######

'''
Function Name:     identifyCM
Input :            frame (Current Image at Zone Indicator).
Output :           It returns -1 if no color marker is detected,
                   else returns 0, indicating that there were some color markers at this zone.

Logic :            In this function we filter the frame for red, blue, and green color using cv2.inRange() function by setting color for
                   respective color, then we find contours for the filtered image using cv2.findContours() function.
                   By counting no of contours in the image we can check if there are some contours of the respective colors(red, blue, and green) 
                   If we get some contours for a respective filter, than we can say Color Markers present are of the color used for filtereing.
                   For getting the shape of the Colormarkers we apprximate number of points of the countour we have got using cv2.approxPolyDP()
                   function. By counting these approximate points we can easily decide the shape of the color marker(described below).
                   We also count the number of Colormarkers by counting the no of contours detected.
                   After getting the color and shape of the colormarker, we can easily get the corresponding flower for it can overlay this 
                   flower by calling overlay() function(mentioned above).

'''
def identifyCM(frame):
    ##CHECKING for red color
    k = np.ones((3,3,), np.uint8)     # this is mask used ofr eroding and dilating the image
    red_filter = cv2.inRange(frame, (0,0,170), (200,160,255))  # Filtering using red color
    red_filter = cv2.erode(red_filter, k, iterations = 2)     
    red_filter = cv2.dilate(red_filter, k, iterations = 3)   # these above functions are used to remove any small dots in the image and smoothing the image.
    
    cnt = (cv2.findContours(red_filter, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE))[1]  #getting contours for the above filtered image
    temp = []
    for i in cnt:
        if cv2.contourArea(i) >= 1500:
            temp.append(i)
        
    cnt = temp

    count_object = len(cnt)      ## count_object represents the number of Color Markers we have got
    color_object = RED      #color_object stores the value of the color of the colormarkers
    if len(cnt) == 0:
        #if not get anything from above filter than we check for next color.
        color_object = BLUE
        blue_filter = cv2.inRange(frame, (190, 0, 0), (255, 190,100))
        blue_filter = cv2.erode(blue_filter, k, iterations = 2)
        blue_filter = cv2.dilate(blue_filter, k, iterations = 3)

        cnt = (cv2.findContours(blue_filter, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE))[1]
        temp = []
        for i in cnt:
            if cv2.contourArea(i) >= 1500:
                temp.append(i)
        cnt = temp
        
        count_object = len(cnt)      ## count_object represents the number of Color Markers we have got
    if len(cnt) == 0:
        #if again we do not get anything from above filter than we check for next color.
        color_object = GREEN
        frame_temp = frame[:320, :].copy()
        green_filter = cv2.inRange(frame_temp, (40,110, 0), (150,255,90))
        green_filter = cv2.erode(green_filter, k, iterations = 1)
        green_filter = cv2.dilate(green_filter, k, iterations = 3)
        cnt = (cv2.findContours(green_filter, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE))[1]
        temp = []
        for i in cnt:
            if cv2.contourArea(i) >= 1700:
                temp.append(i)
        cnt = temp

        count_object = len(cnt)      ## count_object represents the number of Color Markers we have got
    


    if len(cnt) == 0:   # if we don't get anything from the three filters than we return -1 indicating no colormarker.
        return -1

    shape = -1   # shape stores the value of the shape of the colormarker
     
    cnt[0] = cv2.approxPolyDP(cnt[0], 0.04*cv2.arcLength(cnt[0], True), True)
    l = len(cnt[0])  # l means the no of points of the contour after approximating
    if l == 3:       # for triangle shape we neeed three points to represent
        shape = TRIANGLE 
    elif l == 4:     # for square shape we neeed four points to represent
        shape =  SQUARE 
    else:            # for cirlce shape we neeed more than four points to represent
        shape = CIRCLE 

    cur_led = green_led    # cur_led stores the GPIO PIN NUMBER for the color detected

    if color_object == RED:    
        cur_led = red_led        ##these conditions are used to get the GPIO pin according the color detected
    elif color_object == BLUE:
        cur_led = blue_led       ## as default GPIO pin is for green than we did not check for the green color

    color_observed.append(color_object)

    for i in range(count_object):      ## the loop is used to glow the led with a gap of 1 second for the no of color markers detected
        cur_led.ChangeDutyCycle(100)
        sleep(1)
        cur_led.ChangeDutyCycle(0)
        sleep(1)
       
    
    Req_flower = "./Seedlings/" + csv_file[color_object, shape]
    
    overlay(Req_flower, count_object)   ## after getting the flower and no of colormarkers we call the function overlay()

    global Zone
    Zone += 1     ## here we increment the zone no after overlaying
    return 0      ## retunr 0 shows the successfull detection of the color markers




####################ROBOT DRIVING FUNCTIONS#################


'''
Function Name:     reset
Input :            NONE 
Output :           NONE
Logic :            This function is used to reset the value of left and right motor so that it moves straight.

'''
def reset():    
    left.ChangeDutyCycle(cur_duty)
    right.ChangeDutyCycle(cur_duty)
    left_r.ChangeDutyCycle(0)
    right_r.ChangeDutyCycle(0)

'''
Function Name:     stop_
Input :            NONE 
Output :           NONE
Logic :            This function is used to stop the robot.

'''
def stop_():
    left.ChangeDutyCycle(0)
    right.ChangeDutyCycle(0)
    left_r.ChangeDutyCycle(0)
    right_r.ChangeDutyCycle(0)


'''
Function Name:     update_direction
Input :            angle (angle representes the angle with which the line is turning (-90, 90)),
                   line_shift (line_shift represents how much line is shifted from the image center (-image_width/2, image_width/2) )
Output :           NONE
Logic :            this function is used to update the direction of the robot according to the current value of the angel and line_shift.
                   We change the DutyCycle value of the left and right motors according the input values(better described below).

'''
def update_direction(angle, line_shift):
    if (abs(line_shift) < 3 and abs(angle) < 4) :  ## these values are maximum values which we consider for a straight move
        reset()   
        return

    if (abs(line_shift) > 2  and abs(angle) < 12  and abs(line_shift) < img_width/4):
                    ## these values indicates that smooth curve turn, for which we simply decrease the speed of one wheel in respect to another wheel
                    ## such that we can have a turn according to the angle

		
    	if line_shift < 0:  # sign of line_shfit tells its left or right turn
    	    #turning left
    	    left.ChangeDutyCycle(cur_duty*8.0/11)
    	    right.ChangeDutyCycle(cur_duty)
    	    left_r.ChangeDutyCycle(0)
            right_r.ChangeDutyCycle(0)
    	else:
            #turning right
    	    right.ChangeDutyCycle(cur_duty*8.0/11)
    	    left.ChangeDutyCycle(cur_duty)
    	    left_r.ChangeDutyCycle(0)
            right_r.ChangeDutyCycle(0)

    elif   abs(angle) > 35 :
                            #For larger angle we move wheels in opposite direction for better turning
    	if angle < 0:
    	    left.ChangeDutyCycle(0)   
    	    left_r.ChangeDutyCycle(cur_duty)   # left is reversed
    	    right.ChangeDutyCycle(cur_duty)    # right is forward  for turning left
    	    right_r.ChangeDutyCycle(0)

    	else:
    	    left.ChangeDutyCycle(cur_duty)
    	    right.ChangeDutyCycle(0)           # here right is reversed
    	    right_r.ChangeDutyCycle(cur_duty)
    	    left_r.ChangeDutyCycle(0)
    		
    
    else:
                
                
        if line_shift < 0 :        #for small angle we turn by stopping one wheel and the other wheel keeps moving
		
    	    left.ChangeDutyCycle(0)
    	    right.ChangeDutyCycle(cur_duty + 10)
    	    left_r.ChangeDutyCycle(0)
            right_r.ChangeDutyCycle(0)
    	else:
    	    right.ChangeDutyCycle(0)
    	    left.ChangeDutyCycle(cur_duty + 10)
    	    left_r.ChangeDutyCycle(0)
            right_r.ChangeDutyCycle(0)


x

############################################################################################################4

'''
Function Name:     checkZI
Input :            NONE 
Output :           True when there is a chance of presence of ZI.
                   False when there is not a chance of presence of ZI.
Logic :            This function is used to differentiate between Zone Indicator and a sharp turn, we have used the value of area
                    of black line to detect the Zone Indicator but in case of sharp turn area also increase so for avoiding this we
                    have used the following feature.
                    When Zone Indicator comes the upper line is present in the image, whereas when a sharp turn comes upper line is not present.                   

'''

def checkZI(img):
    count = 0
    for i in range(img_width):  # detecting presence of line 
        if count == 7:
            return True
        if img[5][i] != 0:
            count += 1
        else:
            count = 0

    count = 0
    for i in range(img_width):
        if count == 7:
            return True
        if img[2][i] != 0:
            count += 1
        else:
            count = 0

    return False



frm = 0    #frm is used to count number of frames

inv_plane = False   #this flag is used for presence of inverted plane or not.
lower_val = (0,0,0)   # upper and lower value is used to extract the balck line from the image.
upper_val = (100, 100, 100)
for frame in cam.capture_continuous(raw_cap, format = "bgr", use_video_port = True):
	
    image = frame.array     #image is our current frame
    image = image[:62, :]   #here we reudced the size of our image
    frm += 1           #incrementing the fram
    if frm <= 3:       #we start moving after 3 frames for accurate performance
        raw_cap.truncate(0)
        continue



    black_img = cv2.inRange(image, lower_val, upper_val)  #here we filter our image for black color 
    kernel = np.ones((3,3), np.uint8)          #Kernel is used in below functions
    black_img = cv2.erode(black_img, kernel, iterations = 3)   #we used erode function for removing any noise
    img, cnt, hier = cv2.findContours(black_img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)   #here we get the contours from the current frame
    index = 0           #index represents the contour with maximum area
    area = 0            # area is used to store area of largest contour
    total_area = 0      #total_area represents the total area of the black part

    for i in range(len(cnt)):    # this loop is used to get the maximum area contour
        cur_area = cv2.contourArea(cnt[i])
        total_area += cur_area
        if(cur_area > area):
            area = cur_area
            index = i
	
    if frm == 4:  ## from fourth frame we capture the area of the line, which we use for comparing with zone indicator and IP terrain
        LineArea = area
        LineArea = 700   ### we were geting different value for different runs so we kept it 700

    
    if(len(cnt) == 0) or (area > 1.2*LineArea and area < 2.7*LineArea and not inv_plane and checkZI(black_img)):   ## this is used for better stopping at Zone Indicator
        raw_cap.truncate(0)
        continue


    if(total_area > 2.5*LineArea and not inv_plane and checkZI(black_img)):    ## if area become larger than we consider it as a Zone Indicator

        print "Zone Indicator"
        reset()
        sleep(0.37)   # this lag is just to make robot stop accurately
        stop_()    ## robot stops
        # flag = True
        ### here we change resolution, brightness and contrast of image for getting better color quality
        cam.resolution = (700,550)
        cam.brightness = 60
        cam.contrast = 60  
        sleep(1)
        cam.capture('image1.jpg')               #we take a picture of higher resolution
        image = cv2.imread('image1.jpg')
        image = image[:500, : ]                 #we reduced the size of image to remove Zone Indicator from image
        value = identifyCM(image)  ## here we send the image for detecting CM
        if value == -1:   ## Indicating Inverted plane
            inv_plane = True
        reset()       ##we reset the speed f robot
        cam.resolution = (img_width, img_height) # reseting the resolution
        cam.brightness = 50
        cam.contrast = 50
        raw_cap.truncate(0)
        continue

    if(lower_val == (150,150,150) and inv_plane and total_area > 450):  ###this code is used for travelling the small region after Inverted Plane, after completing inverted plane area increase (>450)
                ##we lower value of inv_plane and lower_val to check reach of end
        sleep(1) 
        stop_()
        break

    if(total_area > 750 and inv_plane):     ## this for changing the filtering range according to the inverted plane
        if lower_val == (0,0,0):
            reset()   ## this is for going ahead of ZI
            sleep(1)
            lower_val = (150, 150, 150)
            upper_val = (255, 255, 255)
        else :        
            lower_val = (0,0,0)
            upper_val = (100, 100, 100)
            
            
        raw_cap.truncate(0)
        continue



    x, y, w, h = cv2.boundingRect(cnt[index])  # x,y are upper coordinates, w and h are width and hight 
	# This rectangle is used to know the position of line(left or right side from the mid of the frame)

    blackbox = cv2.minAreaRect(cnt[index]) # this rectangle is used for getting direction
    (x_min, y_min), (w_min, h_min), angle = blackbox   #these are values returned by the cv2.minAreaRect()
    # (x_min, y_min) is the upper coordinates of this rectangle, (w_min, h_min) these are width and height of the rectangle

	# adjusting angle
    if w_min > h_min:   # for negative angle it value start from -90 to -1 for make it -1 to -90 we added 90 to it.
		# going right
        angle += 90
	 
    angle = int(angle)   # for removing decimal value of angle

	# positive angle means line is in right direction
	# negative angle means line is in left direction
    if angle > 50:  # for larger angle we will decide sign of turning from line_shift
        angle = abs(angle)  

    box = cv2.boxPoints(blackbox)
    box = np.int0(box)  #rounding to nearrest integer
    cv2.drawContours(image, [box], 0, (255,255,0),3) # angled rectangle
    cv2.drawContours(image, [cnt[index]], 0, (255,0,0),3) # angled rectangle
	
    center_x_rect = x + w/2   # center of the bounding rectangle 

    line_shift = center_x_rect - (img_width/2)  # line_shift gives the shift in the line from the mid of image
	# negative means line is in left and poisitive means line is in right       
    if line_shift < 0 and angle > 50:   # changing sign according to the sign of line_shift
        angle *= -1

    update_direction(angle, line_shift)  ##  update_direction is called for updating the direction of the robot
    
    cv2.imshow('image', bg_img)  ##showing plantation image
    raw_cap.truncate(0)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
	   break



## this code is for glowing led in the last of the traversal
for clr in color_observed:
    cur_led = green_led
    if clr == RED:    
        cur_led = red_led        
    elif clr == BLUE:
        cur_led = blue_led 
    cur_led.ChangeDutyCycle(100)
    sleep(1)
    cur_led.ChangeDutyCycle(0)
    sleep(1)



