import cv2
import numpy as np

#OCR
import pytesseract
from pytesseract import Output

def import_image(filename):
    return cv2.imread(filename)

def display(img):
    while True:
        cv2.imshow('Output', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def get_text(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invert = cv2.bitwise_not(gray)
    invert_blur = cv2.GaussianBlur(invert, (11,11), 0)

    adp_threshold = cv2.adaptiveThreshold(invert_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    adp_invert = cv2.bitwise_not(adp_threshold)

    display(adp_invert)

    d = pytesseract.image_to_data(adp_invert, output_type=Output.DICT)
    print(d.keys())

def find_edge_ends(bin_img, dilation_iterations = 1):
    ret, thresh = cv2.threshold(bin_img, 128, 255, cv2.THRESH_BINARY)
    # set white pixels to 10, black pixels to 0
    reshade_kernel = np.array([[10.0/255.0]])
    reshade = cv2.filter2D(thresh, -1, reshade_kernel)

    # slow method for reshade
    # for i in range(len(thresh)):
    #     for j in range(len(thresh[0])):
    #         if thresh[i][j] == 255:
    #             thresh[i][j] = 10
    #         else:
    #             thresh[i][j] = 0

    # convolve with kernel which gives 110 as output
    # for white pixels with exactly one white neighbour
    edge_end_kernel = np.array([[1, 1, 1], [1, 10, 1], [1, 1, 1]])
    edge_end_110 = cv2.filter2D(reshade, -1, edge_end_kernel)
    edge_end_thresh = cv2.inRange(edge_end_110, 109, 111)

    kernel = np.ones((11,11), np.uint8)
    dil = cv2.dilate(edge_end_thresh, kernel, iterations = dilation_iterations)

    #display(dil)

    return dil

def adaptive_threshold(img, size=11):
   adp = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, size, 2)

   img = adp
   return img

def xy_edges(img):
    dx_kernel = 9 * np.array([[-1,0,1], [-1,0,1], [-1,0,1]])
    dx_edges = cv2.filter2D(img, -1, dx_kernel)

    dy_kernel = np.transpose(dx_kernel)
    dy_edges = cv2.filter2D(img, -1, dy_kernel)

    both_edges = cv2.addWeighted(dx_edges, 0.5, dy_edges, 0.5, 0)
    
    img = both_edges
    return img

def close(img, size=5, dilations=1, erosions=1):
    kernel = np.ones((size, size), np.uint8)
    dil = cv2.dilate(img, kernel, iterations = dilations)
    ero = cv2.erode(dil, kernel, iterations = erosions)
    
    img = ero
    return img

def invert(img):
    inverted = cv2.bitwise_not(img)
    
    img = inverted
    return img

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inverted = invert(gray)
    
    img = inverted
    return img

def blur(img, size=11, iterations=1):
    blurred = img
    for i in range(iterations):
        blurred = cv2.GaussianBlur(blurred, (size, size), 0)
    
    img = blurred
    return img

def merge(img1, img2):
    merged = cv2.bitwise_or(img1, img2)
    
    img = merged
    return img

def find_contours(img):
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def draw_contours(img, contours, min_size=2000):
    contours_drawn = img.copy()
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_size:
            continue
        contours_drawn = cv2.drawContours(contours_drawn, [contour], -1, (0,0,255), 2)
    return contours_drawn

def flood_fill(img, seed_point, value):
    mask = cv2.copyMakeBorder(img, 1, 1, 1, 1, cv2.BORDER_CONSTANT, 0)
    _,result,_,_ = cv2.floodFill(img, mask, seed_point, value)
    return result

def fill_exterior(img):
    seed = [10, 10]
    while img[seed[1]][seed[0]] != 0:
        seed[0] += 1
        seed[1] += 1
    return flood_fill(img, tuple(seed), 255)

def get_pixel_regions(img):
    pp = preprocess(img)
    ppb = blur(pp)
    adp = adaptive_threshold(ppb)
    adp_inv = invert(adp)
    adp_closed = close(adp_inv, dilations=2, erosions=1)
    # filled_ex = fill_exterior(adp_closed)
    # fex_inv = invert(filled_ex)
    # c = find_contours(fex_inv)
    # output = draw_contours(fex_inv, c)
    display(adp_closed)

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
    #get_text(img)
    get_pixel_regions(img)
    #get_borders(img)

if __name__ == "__main__":
    main()