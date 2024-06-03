import re

vertical_lims = tuple[float, float]
avoid_single_specification = tuple[float, vertical_lims]
avoid_specification = avoid_single_specification | list[avoid_single_specification]

border_single_specification = tuple[float, float, float]
border_specification = border_single_specification | list[border_single_specification]


def split_into_paragraphs(text, collapse_whites=True):
    if collapse_whites:
        text = re.sub(r' +', ' ', text)

        def pre_process(x):
            return x.strip()
    else:
        def pre_process(x):
            return x

    ret = [pre_process(para).replace("\n", " ") for para in re.split('\n\n+', text)]
    return ret


def mix_borders(limit, x0, w0, left1, right1):
    right = x0 + w0
    left = max(left1, x0)
    ww = min(right, right1) - left
    return limit, left, ww


def finish_with_top(x, w,
                    x_left, x_right,
                    y_top, y_bottom):

    return [(y_top, x, w),
            mix_borders(y_bottom, x, w, x_left, x_right),
            (None, x, w),
            ]


def finish_with_bottom(x, w,
                       x_left, x_right,
                       y_bottom):

    return [mix_borders(y_bottom, x, w, x_left, x_right),
            (None, x, w)]


def write_line(ax, xy, words,
               length, width,
               fontsize, color,
               justify, widths):

    x, y = xy

    if justify == 'left' or justify == 'right':
        ax.text(x, y + (justify == 'right') * (width - length), ' '. join(words),
                fontsize=fontsize, color=color)

    elif justify == 'full':
        extra_spacing = (width - length) / (len(words) - 1)
        for word in words:
            ax.text(x, y, word,
                    fontsize=fontsize, color=color)
            x += extra_spacing + widths[word]


def parse_avoid(original_borders,
                avoid_left_of: avoid_specification,
                avoid_right_of: avoid_specification,
                height) -> list[border_single_specification]:

    if avoid_left_of is None:
        avoid_left_of = (None, (None, None))
    if avoid_right_of is None:
        avoid_right_of = (None, (None, None))

    if not isinstance(avoid_right_of, list):
        avoid_right_of = [avoid_right_of]
    if not isinstance(avoid_left_of, list):
        avoid_left_of = [avoid_left_of]

    _, xx, width = original_borders[0]

    # allows is a list of allowable rectangles to write. However, only the intersection of them is permitted.
    allows = []
    for x, (y1, y2) in avoid_left_of:
        if y2 < y1:
            y1, y2 = y2, y1
        if x is not None:
            allows.append((x, xx + width, y1 - height, y2))
    for x, (y1, y2) in avoid_right_of:
        if y2 < y1:
            y1, y2 = y2, y1
        if x is not None:
            allows.append((xx, x, y1 - height, y2))

    borders = original_borders

    # here it creates the final border by processing one by one each of the allowed rectangles and
    # computing the intersection
    for x_left, x_right, y_top, y_bottom in allows:
        if y_top < y_bottom:
            y_top, y_bottom = y_bottom, y_top

        borders = allow_to_borders(borders, x_left, x_right, y_top, y_bottom)

    return borders


def allow_to_borders(incoming_borders, x_left, x_right, y_top, y_bottom
                     ) -> list[border_single_specification]:
    """translates user-friendly avoid to code-friendly borders.

Avoid specifies a list of rectangles that can be written into. However, it is only
the intersection of them the real allowed place.

border specification is a vertical-sorted list of (limit, x_left, width). parampl will continue
writing text from position `x_left` and width `width` until it reached `limit` then it will get
the new border.

"""

    old_borders = incoming_borders.copy()
    borders = []

    # process the blocks on top of the new avoid
    l, x, w = old_borders.pop(0)
    if l is None:
        return borders + finish_with_top(x, w, x_left, x_right, y_top, y_bottom)

    while l > y_top:
        borders.append((l, x, w))
        l, x, w = old_borders.pop(0)
        if l is None:
            return borders + finish_with_top(x, w, x_left, x_right, y_top, y_bottom)

    # if the new avoid starts at the same place as an old, then mix and get the next avoid, otherwise place the new
    if l == y_top:
        borders.append((l, x, w))
        l, x, w = old_borders.pop(0)
        if l is None:
            return borders + finish_with_bottom(x, w, x_left, x_right, y_bottom)
    else:
        borders.append((y_top, x, w))

    if l > y_bottom:  # if the new finishes after layer keep looping
        borders.append(mix_borders(l, x, w, x_left, x_right))

        l, x, w = old_borders.pop(0)
        if l is None:
            return borders + finish_with_bottom(x, w, x_left, x_right, y_bottom)

        while l > y_bottom:
            borders.append(mix_borders(l, x, w, x_left, x_right))
            l, x, w = old_borders.pop(0)
            if l is None:
                return borders + finish_with_bottom(x, w, x_left, x_right, y_bottom)
        if l == y_bottom:
            borders.append(mix_borders(l, x, w, x_left, x_right))
            l, x, w = old_borders.pop(0)
            if l is None:
                return borders + [(l, x, w)]
        else:
            borders.append(mix_borders(y_bottom, x, w, x_left, x_right))
        borders.append((l, x, w))
        l, x, w = old_borders.pop(0)

    elif l == y_bottom:  # if the new matches the layer then mix and get the next layer
        borders.append(mix_borders(l, x, w, x_left, x_right))
        l, x, w = old_borders.pop(0)

    else:  # if the new is above, then add it and continue
        borders.append((mix_borders(y_bottom, x, w, x_left, x_right)))

    # keep adding all layers below current
    while l is not None:
        borders.append((l, x, w))
        l, x, w = old_borders.pop(0)

    return borders + [(l, x, w)]
