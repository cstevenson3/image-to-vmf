from time import sleep
import math
from os import walk

import cv2
import numpy as np

DEBUGGING = False

def import_image(filename):
    return cv2.imread(filename)

def display(img):
    cv2.imshow('Output', img)
    if cv2.waitKey(0) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    sleep(1)

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
    merged_symbol = threshold(merged_symbol, 20)

    SCALE = 2
    scaled_image = scale(image, 1/SCALE, interpolation=cv2.INTER_LINEAR)
    template = scale(merged_symbol, 1/SCALE, interpolation=cv2.INTER_LINEAR)

    matched = cv2.matchTemplate(scaled_image, template, cv2.TM_SQDIFF)

    matched = scale(matched, SCALE)

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
    for width in range(28, 96, 8):  # 32, 133
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
    display(thresh) if DEBUGGING else None

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
    # display(segs) if DEBUGGING else None

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
    for match in matches:
        segs = cv2.line(segs, tuple(match[0]), tuple(match[1]), (0, 255, 0), 4)
    # [cv2.circle(segs, mid, 20, (255, 0, 0)) for mid in mids]
    display(segs) if DEBUGGING else None

    return mids

def get_text(img, texts = ["A"]):
    result = dict()

    SYMBOL_PATH = "tests/test_data/symbols/"
    _, _, filenames = next(walk(SYMBOL_PATH))
    for t in texts:
        t_filepaths = [SYMBOL_PATH + fn for fn in filenames if fn.startswith(t)]
        print("---- Finding symbol " + t + t)
        points = get_symbol(img, t_filepaths)
        result[t] = points

    return result

def scale(img, scale, interpolation=cv2.INTER_NEAREST):
    result = cv2.resize(img, (int(scale * len(img[0])), int(scale * len(img))), interpolation=interpolation)
    return result

def gray_to_rgb(gray):
    return cv2.merge([gray, gray, gray])

def threshold(img, min=128):
    ret, t = cv2.threshold(img, min, 255, cv2.THRESH_BINARY)
    return t

def adaptive_threshold(img, size=11):
   adp = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, size, 2)

   img = adp
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
    template = import_image("tests/test_data/symbols/B1.png")
    template = cv2.resize(template, (52, 74))
    img = scale(img, 1/2, interpolation=cv2.INTER_LINEAR)
    template = scale(template, 1/2, interpolation=cv2.INTER_LINEAR)
    matched = cv2.matchTemplate(img, template, cv2.TM_SQDIFF)
    matched = scale(matched, 2)
    largest = max([max(matched[y]) for y in range(len(matched))])
    matched = 1/largest * matched
    matched = (matched * 255.0).astype('uint8')
    matched = invert(matched)
    matched = threshold(matched, 160)
    display(matched) if DEBUGGING else None

def hamming_distance(img1, img2):
    ''' differing pixels between img1 and img2 relative to their size '''
    total = 0
    h, w = img1.shape[:2]
    for y in range(h):
        for x in range(w):
            if tuple(img1[y][x]) != tuple(img2[y][x]):
                total +=1
    proportion = float(total) / float(w * h)
    return proportion

def main():
    ''' tests '''
    # template_match_test()

    # hamming distance test
    # img1 = import_image("tests/test_data/output/manual.png")
    # img2 = import_image("tests/test_data/output/manual2.png")
    # print(hamming_distance(img1, img2))
    # quit()

    img = import_image("tests/test_data/sketch_scanned9.png")
    text_img = import_image("tests/test_data/sketch_scanned9.png")

    display(img) if DEBUGGING else None

    print("Finding text...")
    text_locations = get_text(text_img, texts = ["X", "Z", "H", "W"])
    all_locs = []
    for key in text_locations.keys():
        locs = text_locations[key]
        for l in locs:
            all_locs.append(l)
            # cv2.circle(text_img, l, 10, (255, 0, 0), thickness=5)
            text_img = cv2.putText(text_img, key, l, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4, cv2.LINE_AA)
    # covering rectangle
    WIDTH = 90
    HEIGHT = 80
    for tl in all_locs:
        left = int(tl[0] - WIDTH / 2)
        right = int(tl[0] + WIDTH / 2)
        top = int(tl[1] - HEIGHT / 2)
        bottom = int(tl[1] + HEIGHT / 2)
        cv2.rectangle(img, (left, top), (right, bottom), (255, 255, 255), thickness=-WIDTH)
    display(img) if DEBUGGING else None
    display(text_img) if DEBUGGING else None
    # print(text_locations)

    print("Segmenting...")
    pr = get_pixel_regions(img)
    bs = get_black_segments(pr)

    bs_rgb = gray_to_rgb(bs)

    COLORS = {"Z": (0, 255, 255), "X": (0, 255, 0), "H": (255, 0, 0), "W": (0, 128, 255)}
    for key in text_locations.keys():
        locs = text_locations[key]
        color = COLORS[key]
        for l in locs:
            bs_rgb,_ = flood_fill(bs_rgb, l, color)

    display(bs_rgb) if DEBUGGING else None

    UNKNOWN_COLORS = [(192, 192, 192), (255, 255, 255)]

    for y in range(len(bs_rgb)):
        for x in range(len(bs_rgb[0])):
            if tuple(bs_rgb[y][x]) in UNKNOWN_COLORS:
                bs_rgb[y][x] = (0, 0, 0)
    
    display(bs_rgb) if DEBUGGING else None

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
    
    # filling in gaps
    SCALE_DOWN = 4
    PENCIL_THICKNESS = int(16 / SCALE_DOWN)
    PADDING = 4

    # crop
    boundary = SCALE_DOWN * (PENCIL_THICKNESS + PADDING)
    h, w = bs_rgb.shape[:2]
    bs_rgb = bs_rgb[max(top-boundary, 0):min(bottom+boundary, h-1), max(left-boundary, 0):min(right+boundary, w-1)]
    original = img[max(top-boundary, 0):min(bottom+boundary, h-1), max(left-boundary, 0):min(right+boundary, w-1)]  # for testing
    display(bs_rgb) if DEBUGGING else None

    #resize
    h, w = bs_rgb.shape[:2]
    bs_rgb = cv2.resize(bs_rgb, (int(w/SCALE_DOWN), int(h/SCALE_DOWN)), interpolation=cv2.INTER_NEAREST)
    original = cv2.resize(original, (int(w/SCALE_DOWN), int(h/SCALE_DOWN)), interpolation=cv2.INTER_NEAREST)
    display(bs_rgb) if DEBUGGING else None

    print("Filling pencil gaps...")
    cur_img = bs_rgb.copy()
    next_img = cur_img.copy()
    for passes in range(PENCIL_THICKNESS):
        print("--Pass {}".format(passes + 1))
        for y in range(len(cur_img)):
            for x in range(len(cur_img[0])):
                if tuple(cur_img[y][x]) == (0, 0, 0):
                    ncs = neighbour_colors(cur_img, x, y)
                    for nc in ncs:
                        if nc != (0, 0, 0):
                            next_img[y][x] = nc
                            break
        cur_img = next_img.copy()

    display(cur_img) if DEBUGGING else None

    WALL_COLOR = (0, 0, 255)
    for y in range(len(cur_img)):
        for x in range(len(cur_img[0])):
            if tuple(cur_img[y][x]) == (0, 0, 0):
                cur_img[y][x] = WALL_COLOR

    # cur_img = scale(cur_img, 4, interpolation=cv2.INTER_NEAREST)
    # original = scale(original, 4, interpolation=cv2.INTER_NEAREST)

    # break up the outer wall to avoid donut topology and excessively large brushes
    h, w = cur_img.shape[:2]
    x = int(w/2)
    y = 0
    while tuple(cur_img[y][x]) == (0, 0, 255): #TODO don't hardcode color
        cur_img[y][x] = [0, 0, 0]
        y += 1

    display(cur_img) if DEBUGGING else None

    cv2.imwrite("tests/test_data/output/output.png", cur_img)
    cv2.imwrite("tests/test_data/output/original.png", original)

if __name__ == "__main__":
    main()