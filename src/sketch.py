import cv2
import numpy as np

def import_image(filename):
    return cv2.imread(filename)

def get_borders(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invert = cv2.bitwise_not(gray)

    blur = cv2.GaussianBlur(invert, (5,5), 0)

    sobel = cv2.Sobel(invert, -1, 1, 1, ksize=5)

    ret, sobel_thresh = cv2.threshold(sobel, 50, 255, cv2.THRESH_BINARY)

    dx_kernel = 18 * np.array([[-1,0,1], [-1,0,1], [-1,0,1]])
    dx_edges = cv2.filter2D(invert, -1, dx_kernel)

    dy_kernel = 9 * np.array([[1,1,1], [0,0,0], [-1,-1,-1]])
    dy_edges = cv2.filter2D(invert, -1, dy_kernel)

    d_edges = cv2.addWeighted(dx_edges, 0.5, dy_edges, 0.5, 0)

    blur_d = cv2.GaussianBlur(d_edges, (7,7), 0)
    blur_d2 = cv2.GaussianBlur(blur_d, (15,15), 0)

    ret, thresh_d = cv2.threshold(blur_d, 100, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3,3), np.uint8)
    erode_d = cv2.erode(thresh_d, kernel, iterations=1)
    dilate_d = cv2.dilate(erode_d, kernel, iterations=1)
    erode_d2 = cv2.erode(dilate_d, kernel, iterations=1)
    dilate_d2 = cv2.dilate(erode_d2, kernel, iterations=2)

    canny_d = cv2.Canny(dilate_d2, 5, 8)

    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharp = cv2.filter2D(invert, -1, kernel)

    blur = cv2.GaussianBlur(sharp, (15,15), 0)

    ret, thresh = cv2.threshold(blur, 110, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3,3), np.uint8)
    dilate = cv2.dilate(thresh, kernel, iterations=3)

    blur_morph = dilate

    for iterations in range(10):
        blur_morph = cv2.GaussianBlur(blur_morph, (15,15), 0)

    dilate2 = cv2.dilate(blur_morph, kernel, iterations=1)

    output = dilate_d2

    # blur = cv2.GaussianBlur(gray, (15,15), 0)
    # blur2 = cv2.GaussianBlur(blur, (15,15), 0)
    # edges = cv2.Canny(blur2, 5, 8)
    # kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    # sharp = cv2.filter2D(blur2, -1, kernel)
    # sharp2 = cv2.filter2D(sharp, -1, kernel)
    # ret, thres = cv2.threshold(sharp, 150, 255, cv2.THRESH_BINARY)
    # invert = cv2.bitwise_not(thres)
    # contours, hierarchy = cv2.findContours(thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # thres = cv2.drawContours(thres, contours, -1, (0,0,255), 2)
    # kernel = np.ones((3,3), np.uint8)
    # erosion = cv2.erode(thres, kernel, iterations=3)
    while True:
        cv2.imshow('Output', output)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def main():
    ''' tests '''
    img = import_image("tests/test_data/sketch_scanned.png")
    get_borders(img)

if __name__ == "__main__":
    main()