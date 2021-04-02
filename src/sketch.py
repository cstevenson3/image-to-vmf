import cv2
import numpy as np

def import_image(filename):
    return cv2.imread(filename)

def get_text(img):
    pass

def display(img):
    while True:
        cv2.imshow('Output', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def get_pixel_regions(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invert = cv2.bitwise_not(gray)

    dx_kernel = 9 * np.array([[-1,0,1], [-1,0,1], [-1,0,1]])
    dx_edges = cv2.filter2D(invert, -1, dx_kernel)

    dy_kernel = 9 * np.array([[1,1,1], [0,0,0], [-1,-1,-1]])
    dy_edges = cv2.filter2D(invert, -1, dy_kernel)

    both_edges = cv2.addWeighted(dx_edges, 0.5, dy_edges, 0.5, 0)

    # length = 15
    # long_x_kernel = 2 * np.array([[-1] * length, [-1] * length, [1] * length, [1] * length, [1] * length, [-1] * length, [-1] * length])
    # long_x_edge = cv2.filter2D(invert, -1, long_x_kernel)

    # long_y_kernel = np.transpose(long_x_kernel)
    # long_y_edge = cv2.filter2D(invert, -1, long_y_kernel)

    # both_edges = cv2.addWeighted(long_x_edge, 0.5, long_y_edge, 0.5, 0)

    blur = cv2.GaussianBlur(both_edges, (11,11), 0)
    ret, thresh_d = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)

    kernel = np.ones((7,7), np.uint8)
    dil = cv2.dilate(thresh_d, kernel, iterations = 2)
    closed = cv2.erode(dil, kernel, iterations=1)

    display(closed)

def get_borders(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invert = cv2.bitwise_not(gray)

    length = 15
    long_x_kernel = np.array([[-1] * length, [0] * length, [0] * length, [2] * length, [0] * length, [0] * length, [-1] * length])
    long_x_edge = cv2.filter2D(invert, -1, long_x_kernel)

    long_y_kernel = np.transpose(long_x_kernel)
    long_y_edge = cv2.filter2D(invert, -1, long_y_kernel)

    sobel = cv2.Sobel(invert, -1, 1, 1, ksize=5)
    ret, sobel_thresh = cv2.threshold(sobel, 50, 255, cv2.THRESH_BINARY)

    overlap = cv2.addWeighted(long_x_edge, 0.5, long_y_edge, 0.5, 0)
    #overlap = cv2.addWeighted(overlap, 0.5, sobel, 0.5, 0)

    sharp_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharp_invert = cv2.filter2D(invert, -1, sharp_kernel)

    blur = cv2.GaussianBlur(sharp_invert, (5,5), 0)

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
    dilate_d = cv2.dilate(erode_d, kernel, iterations=4)
    erode_d2 = cv2.erode(dilate_d, kernel, iterations=1)
    dilate_d2 = cv2.dilate(erode_d2, kernel, iterations=2)
    blur_dilate = cv2.GaussianBlur(dilate_d2, (7,7), 0)
    dilate_d2 = cv2.dilate(blur_dilate, kernel, iterations=1)
    ret, thresh_dil = cv2.threshold(dilate_d2, 100, 255, cv2.THRESH_BINARY)

    canny_d = cv2.Canny(thresh_dil, 5, 8)

    dilate_canny = cv2.dilate(canny_d, kernel, iterations=1)

    reinvert = cv2.bitwise_not(dilate_canny)
    contours, hierarchy = cv2.findContours(dilate_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_drawn = img.copy()
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:
            continue
        contours_drawn = cv2.drawContours(contours_drawn, [contour], -1, (0,0,255), 2)

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

    output = reinvert

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
    display(output)

def main():
    ''' tests '''
    img = import_image("tests/test_data/sketch_scanned2.png")
    get_pixel_regions(img)
    #get_borders(img)

if __name__ == "__main__":
    main()