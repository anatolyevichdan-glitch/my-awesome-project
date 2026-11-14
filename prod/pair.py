import cv2, sys, numpy as np
ims=[cv2.resize(cv2.imread(f'test/f_{float(t):06.2f}.jpg'),(540,960),interpolation=cv2.INTER_AREA) for t in sys.argv[2].split(',')]
cv2.imwrite(sys.argv[1], np.hstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 85])
