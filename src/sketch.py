from time import sleep
import math
from os import walk

import cv2
import numpy as np

#OCR
import pytesseract
from pytesseract import Output

import sketch_ocr

def import_image(filename):
    return cv2.imread(filename)

def display(img):
    cv2.imshow('Output', img)
    if cv2.waitKey(0) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    sleep(1)
    
def range_minus_255_to_255(image):
    img = image.copy()
    img = 2 * img
    for y in range(len(img)):
        for x in range(len(img[0])):
            img[y][x] -= 255
    return img

def convolve_symbols(img, symbols, width=128, height=128):
    image = img.copy()
    image = gray(image)
    image = invert(image)

    shape = (width, height)
    syms = []
    for symbol in symbols:
        sym = symbol.copy()
        sym = gray(sym)
        sym = cv2.resize(sym, shape)
        sym = invert(sym)
        sym = blur(sym, size=5)
        syms.append(sym.copy())

    merge_factor = 2
    merged_symbol = syms[0].copy()
    for sym in syms[1:]:
        merged_symbol = cv2.addWeighted(merged_symbol, (merge_factor - 1) / merge_factor, sym, 1 / merge_factor, 0)
        merge_factor += 1

    # display(merged_symbol)

    image = blur(image, size=5)
    image = threshold(image, 30)
    merged_symbol = blur(merged_symbol, size=5)
    merged_symbol = threshold(merged_symbol, 30)

    matched = cv2.matchTemplate(image, merged_symbol, cv2.TM_SQDIFF)
    largest = max([max(matched[y]) for y in range(len(matched))])
    matched = 1/largest * matched
    matched = (matched * 255.0).astype('uint8')
    matched = invert(matched)

    dw = len(image[0]) - len(matched[0])
    dh = len(image) - len(matched)

    matched = cv2.copyMakeBorder(matched, math.floor(dh/2), math.ceil(dh/2), math.floor(dw/2), math.ceil(dw/2), cv2.BORDER_CONSTANT, value=0)
    assert(len(image[0]) == len(matched[0]))
    assert(len(image) == len(matched))

    return matched

def merge_all(images):
    merge_factor = 2
    merged_image = images[0].copy()
    for img in images[1:]:
        merged_image = cv2.addWeighted(merged_image, (merge_factor - 1) / merge_factor, img, 1 / merge_factor, 0)
        merge_factor += 1
    return merged_image

def combine_all(images):
    if len(images) == 0:
        return None
    if len(images) == 1:
        return images[0]
    result = images[0]
    for img in images[1:]:
        result = cv2.bitwise_or(result, img)
    return result


def get_symbol(img, symbol_paths):
    symbols = [import_image(path) for path in symbol_paths]

    ts = []

    THRESHOLD_MIN = 170
    for width in range(28, 84, 8):  # 32, 133
        for height in range(44, 74, 8):  # 64, 145
            convolved = convolve_symbols(img, symbols, width=width, height=height)
            t = threshold(convolved, min=THRESHOLD_MIN)
            ts.append(t.copy())

    T = merge_all(ts)
    # T = combine_all(ts)
    # print("pre blur")
    # display(T)
    T = blur(T)
    # print("post blur")
    # display(T)
    # print("final thresh")
    thresh = threshold(T, 15)
    # display(thresh)

    thresh_rgb = cv2.merge([thresh, thresh, thresh])
    ctrs = find_contours(thresh)
    segs = draw_contours(thresh_rgb, ctrs, min_size=0)
    highlights = []
    for ctr in ctrs:
        x,y,w,h = cv2.boundingRect(ctr)
        cx = int(x + w / 2)
        cy = int(y + h / 2)
        highlights.append((cx, cy))
        cv2.circle(segs, (cx, cy), 20, (0, 255, 0))
    #display(segs)

    # output = img.copy()
    # output = gray(output)
    # BG = cv2.subtract(output, T)
    # R = cv2.add(output, T)
    # output = cv2.merge([BG, BG, R])

    #display(output)

    MIN_DIST = 32
    MAX_DIST = 256
    MAX_ANG = 10 # degrees

    matches = []
    # match highlights
    last_changed = 0 # how many times has the list been cycled without a match
    while len(highlights) > 0:
        p1 = highlights.pop(0)
        # look for a matching right
        change = False
        for i in range(len(highlights)):
            p2 = highlights[i]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            ang = math.degrees(math.atan(abs(dy) / abs(dx))) if dx != 0 else 90
            if dx > MIN_DIST and dx < MAX_DIST and ang < MAX_ANG:
                highlights.pop(i)
                matches.append((p1, p2))
                last_changed = 0
                change = True
                break
        if not change:
            highlights.append(p1) # cycle p1 to end of list
            last_changed += 1
            if last_changed > len(highlights): # all current options cycled through without a match
                break

    mids = [(int((match[0][0] + match[1][0]) / 2), int((match[0][1] + match[1][1]) / 2)) for match in matches]
    [cv2.circle(segs, mid, 20, (255, 0, 0)) for mid in mids]
    #display(segs)

    return mids

def get_text(img, texts = ["A"]):
    result = dict()

    SYMBOL_PATH = "tests/test_data/symbols/"
    _, _, filenames = next(walk(SYMBOL_PATH))
    for t in texts:
        t_filepaths = [SYMBOL_PATH + fn for fn in filenames if fn.startswith(t)]
        points = get_symbol(img, t_filepaths)
        result[t] = points

    return result

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

def gray_to_rgb(gray):
    return cv2.merge([gray, gray, gray])

def threshold(img, min=128):
    ret, t = cv2.threshold(img, min, 255, cv2.THRESH_BINARY)
    return t

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

def gray(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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
    ic = img.copy()
    height = len(img)
    width = len(img[0])
    mask = np.zeros((height + 2, width + 2), dtype=np.uint8)
    # mask = cv2.copyMakeBorder(img, 1, 1, 1, 1, cv2.BORDER_CONSTANT, 0)
    _,result,_,rect = cv2.floodFill(ic, mask, seed_point, value, loDiff=0, upDiff=0)
    return (result, rect)

def fill_exterior(img):
    seed = [10, 10]
    while img[seed[1]][seed[0]] != 0:
        seed[0] += 1
        seed[1] += 1
    result,_ = flood_fill(img, tuple(seed), 255)
    return result

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
    return(adp_closed)

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

def get_black_segments(img):
    MIN_AREA = 1000

    result = img.copy()
    height = len(img)
    width = len(img[0])
    for i in range(height):
        for j in range(width):
            #print(str(i) + " " + str(j))
            # if unsegmented
            if result[i][j] == 0:
                seed_point = (j, i)
                # flood fill with 128 to find segment points
                result, rect = flood_fill(result, seed_point, 128)
                #print(rect)
                delete_segment = False
                area = 0
                for y in range(rect[1], rect[1] + rect[3]):
                    double_break = False
                    for x in range(rect[0], rect[0] + rect[2]):
                        if result[y][x] == 128:
                            # if segment touches border, remove it
                            if (y == 0 or y == height - 1) or (x == 0 or x == width - 1):
                                delete_segment = True
                                double_break = True
                                break
                            area += 1
                    if double_break:
                        break
                # if segment is too small (noise), remove it
                if area < MIN_AREA:
                    delete_segment = True
                else:
                    pass
                    #print()

                if delete_segment:
                    result,_ = flood_fill(result, seed_point, 255)
                    #print("Deleted segment with area " + str(area))
                else:
                    # confirm segment
                    result,_ = flood_fill(result, seed_point, 192)
                    #display(result)
    return result


def neighbour_colors(img, x, y):
    result = []
    xys = []
    ys = [max(y - 1, 0), y, min(len(img) - 1, y + 1)]
    xs = [max(x - 1, 0), x, min(len(img[0]) - 1, x + 1)]
    for y in ys:
        for x in xs:
            xys.append((x, y))
    for xy in xys:
        result.append(tuple(img[xy[1]][xy[0]]))
    return result


def template_match_test():
    img = import_image("tests/test_data/sketch_scanned5.png")
    template = import_image("tests/test_data/symbols/A1.png")
    template = cv2.resize(template, (52, 74))
    matched = cv2.matchTemplate(img, template, cv2.TM_SQDIFF)
    largest = max([max(matched[y]) for y in range(len(matched))])
    matched = 1/largest * matched
    matched = (matched * 255.0).astype('uint8')
    matched = invert(matched)
    matched = threshold(matched, 160)
    display(matched)

def main():
    ''' tests '''
    # template_match_test()

    img = import_image("tests/test_data/sketch_scanned6.png")
    text_img = import_image("tests/test_data/sketch_scanned6.png")

    display(img)

    text_locations = get_text(text_img, texts = ["B", "C", "F", "T"])
    all_locs = []
    for key in text_locations.keys():
        locs = text_locations[key]
        for l in locs:
            all_locs.append(l)
            # cv2.circle(text_img, l, 10, (255, 0, 0), thickness=5)
            text_img = cv2.putText(text_img, key, l, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2, cv2.LINE_AA)
    WIDTH = 80
    HEIGHT = 90
    for tl in all_locs:
        left = int(tl[0] - WIDTH / 2)
        right = int(tl[0] + WIDTH / 2)
        top = int(tl[1] - HEIGHT / 2)
        bottom = int(tl[1] + HEIGHT / 2)
        cv2.rectangle(img, (left, top), (right, bottom), (255, 255, 255), thickness=-WIDTH)
    display(img)
    display(text_img)
    # print(text_locations)

    pr = get_pixel_regions(img)
    bs = get_black_segments(pr)

    bs_rgb = gray_to_rgb(bs)

    COLORS = {"B": (0, 255, 255), "F": (0, 255, 0), "C": (255, 0, 0), "T": (0, 128, 255)}
    for key in text_locations.keys():
        locs = text_locations[key]
        color = COLORS[key]
        for l in locs:
            bs_rgb,_ = flood_fill(bs_rgb, l, color)

    display(bs_rgb)
    #get_borders(img)

    UNKNOWN_COLORS = [(192, 192, 192), (255, 255, 255)]

    for y in range(len(bs_rgb)):
        for x in range(len(bs_rgb[0])):
            if tuple(bs_rgb[y][x]) in UNKNOWN_COLORS:
                bs_rgb[y][x] = (0, 0, 0)
    
    display(bs_rgb)

    left = math.inf
    right = 0
    top = math.inf
    right = 0
    for y in range(len(bs_rgb)):
        for x in range(len(bs_rgb[0])):
            if tuple(bs_rgb[y][x]) != (0, 0, 0):
                if x < left:
                    left = x
                if x > right:
                    right = x
                if y < top:
                    top = y
                if y > bottom:
                    bottom = y
    
    # crop
    bs_rgb = bs_rgb[top-2:bottom+2, left-2:right+2]

    display(bs_rgb)

    SCALE_DOWN = 4

    h, w = bs_rgb.shape[:2]

    bs_rgb = cv2.resize(bs_rgb, (int(w/SCALE_DOWN), int(h/SCALE_DOWN)), interpolation=cv2.INTER_NEAREST)
    print("resizing")
    display(bs_rgb)

    PENCIL_THICKNESS = int(16 / SCALE_DOWN)
    cur_img = bs_rgb.copy()
    next_img = cur_img.copy()
    for passes in range(PENCIL_THICKNESS):
        print("Pass {}".format(passes + 1))
        for y in range(len(cur_img)):
            for x in range(len(cur_img[0])):
                if tuple(cur_img[y][x]) == (0, 0, 0):
                    ncs = neighbour_colors(cur_img, x, y)
                    for nc in ncs:
                        if nc != (0, 0, 0):
                            next_img[y][x] = nc
                            break
        cur_img = next_img.copy()

    display(cur_img)

    WALL_COLOR = (0, 0, 255)
    for y in range(len(cur_img)):
        for x in range(len(cur_img[0])):
            if tuple(cur_img[y][x]) == (0, 0, 0):
                cur_img[y][x] = WALL_COLOR
    
    display(cur_img)

if __name__ == "__main__":
    main()