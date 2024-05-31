from matplotlib import pyplot as plt

vertical_lims = tuple[float, float]
avoid_specification = tuple[float, vertical_lims]

class ParaMPL:
    def write(self,
              text,
              xy,
              keep_lines=False,
              width=None, spacing=None,
              fontsize=None,
              justify='left',
              ha='left',
              va='top',
              avoid_left_of: avoid_specification = None,
              avoid_right_of: avoid_specification = None,
              ):
        """
Write text into a paragraph

        :param avoid_left_of:
          tuple (x_lim, (y1, y2)). Avoid space left of x_lim between y1 and y2
        :param avoid_right_of:
          tuple (x_lim, (y1, y2)). Avoid space right of x_lim between y1 and y2
        :param va:
          Paragraph vertical alignment
        :param ha:
          Paragraph horizontal alignment
        :param justify:
          Line's justification
        :param xy:
           xy to place the paragraph
        :param text:
          text to write
        :param keep_lines:
          if True, keep newline of text, there is a speed advantage to this case.
        :param width:
          use this width instead of the initialized one
        :param spacing:
          use this spacing instead of the initialized one
        :param fontsize:
          use this fontsize instead of the initialized one
        """

        if width is None:
            width = self.width
        if spacing is None:
            spacing = self.spacing
        if fontsize is None:
            fontsize = self.fontsize

        if keep_lines:
            lines = text.split('\n')
        else:
            lines = self._split_into_lines(text, width, fontsize)

        widths, height, combined_hash = self._get_widths_height(fontsize)
        n_lines = len(lines)

        xx = xy[0]
        yy = xy[1]
        delta_yy = height * (1 + spacing)

        if va == 'top':
            yy -= height
        elif va == 'bottom':
            yy += (n_lines - 1) * (1 + spacing) * height
        elif va == 'center':
            yy += ((n_lines - 1) * (1 + spacing) * height - height) / 2.0
        else:
            raise ValueError(f"invalid va '{va}'. Must be 'top', 'bottom', or 'center'")

        if ha == 'right':
            xx -= width
        elif ha == 'center':
            xx -= width / 2.0
        elif ha != 'left':
            raise ValueError(f"invalid ha '{ha}'. Must be 'right', 'left', or 'center'")

        width_per_line = [width] * n_lines
        xx_per_line = [xx] * n_lines

        def get_lines(y_1, y_2):
            if y_2 < y_1:
                y_1, y_2 = y_2, y_1

            return (int((yy - y_1) / ((1 + spacing) * height)),
                    int((yy - y_2) / ((1 + spacing) * height)))

        if avoid_left_of is not None:
            x_value, (y1, y2) = avoid_left_of
            line1, line2 = get_lines(y1, y2)

            initial_skip = x_value - xx
            initial_skip *= (0 < initial_skip < width)
            for i in range(line2, line1):
                xx_per_line[i] += initial_skip
                width_per_line[i] = xx + width - xx_per_line[i]
            lines = self._split_into_lines(text, width_per_line, fontsize)

        if avoid_right_of is not None:
            x_value, (y1, y2) = avoid_right_of
            line1, line2 = get_lines(y1, y2)

            width_per_line[line2:line1] = [x_value - xx_per_line[i] for i in range(line2, line1)]
            lines = self._split_into_lines(text, width_per_line, fontsize)

        if (justify == 'left') | (justify == 'right') | (justify == 'center'):
            for line in lines:
                x_line = xx_per_line.pop(0)
                text_artist = self.axes.text(x_line, yy, line, fontsize=fontsize)
                if justify == 'right':
                    text_artist.set_x(x_line + width - self._transformed_artist_extent(text_artist).width)
                elif justify == 'center':
                    text_artist.set_x(x_line + (width - self._transformed_artist_extent(text_artist).width) / 2.0)

                yy -= delta_yy

        elif justify == 'full':
            for line, width_of_line in zip(lines[:-1], width_per_line):
                x_line = xx_per_line.pop(0)
                text_artist = self.axes.text(x_line, yy, line, fontsize=fontsize)
                if ' ' not in line:
                    yy -= delta_yy
                    continue
                extra_spacing = (width_of_line
                                 - self._transformed_artist_extent(text_artist).width
                                 ) / line.count(' ') + widths[' ']
                text_artist.remove()
                wx = x_line

                for word in line.split():
                    if word not in widths:
                        widths, combined_hash = self._compute_word_widths(line.split(), fontsize)

                    text_artist = ax.text(wx, yy, word, fontsize=fontsize)
                    wx += extra_spacing + self._transformed_artist_extent(text_artist).width

                yy -= delta_yy

            x_line = xx_per_line.pop(0)
            self.axes.text(x_line, yy, lines[-1], fontsize=fontsize)

        else:
            raise ValueError("justify can be left, right, center, or full")

    def __init__(self, axes,
                 spacing=1.0,
                 width=1.0,
                 fontsize=10,
                 transform='data'
                 ):

        self.width = width
        self.spacing = spacing
        self.axes = axes
        self.fontsize = fontsize

        self._renderer = axes.figure.canvas.get_renderer()
        if transform == 'data':
            self._transform = axes.transData.inverted()
        else:
            raise NotImplementedError("only 'data' transform is supported for now")

        self.widths: dict[tuple, dict[str, float]] = {}
        self.heights: dict[tuple, float] = {}

    def _compute_word_widths(self, words, fontsize):

        widths, height, combined_hash = self._get_widths_height(fontsize)
        text_artist = self.axes.text(0, 0, ' ',
                                     fontsize=fontsize)

        for word in words:
            if word not in widths:
                text_artist.set_text(word)
                widths[word] = self._transformed_artist_extent(text_artist).width

        text_artist.remove()

        return widths, combined_hash

    def _split_into_lines(self,
                          text: str,
                          max_line_widths: float | list[float],
                          fontsize: float,
                          ):

        def get_line_width(max_widths):
            if len(max_widths) > 1:
                return max_widths.pop(0)
            else:
                return max_widths[0]

        if len(text) == 0:
            return ['']
        if isinstance(max_line_widths, float):
            max_line_widths = [max_line_widths]

        text = text.strip().replace('\n', ' ')
        words = text.split()

        widths, combined_hash = self._compute_word_widths(words, fontsize)
        width_space = widths[' ']

        lines = []
        length = 0.0
        line = ''
        max_line_width = get_line_width(max_line_widths)

        for word in words:
            width_word = widths[word]
            length += width_word + width_space

            if length >= max_line_width:
                if not line:
                    lines.append(word)  # put down the single long word
                    length = 0.0
                else:
                    lines.append(line[1:])  # omit the starting space
                    line = ' ' + word
                    length = width_word + width_space
                max_line_width = get_line_width(max_line_widths)

            else:
                line += ' ' + word  # keep growing the line

        lines.append(line[1:])  # omit the starting space

        self.widths[combined_hash] = widths

        return lines

    def _get_widths_height(self, fontsize):
        text_artist = self.axes.text(0, 0, ' ', fontsize=fontsize)
        combined_hash = (fontsize,)  # todo: probably font name should be in here

        if combined_hash not in self.widths:
            text_artist.set_text(' ')
            widths: dict[str, float] = {' ': self._transformed_artist_extent(text_artist).width}

            text_artist.set_text('L')
            height = self._transformed_artist_extent(text_artist).height

            self.widths[combined_hash] = widths
            self.heights[combined_hash] = height

        return self.widths[combined_hash], self.heights[combined_hash], combined_hash

    def _transformed_artist_extent(self, artist):
        extent = artist.get_window_extent(renderer=self._renderer)
        return extent.transformed(self._transform)


if __name__ == '__main__':
    f, ax = plt.subplots()
    # noinspection SpellCheckingInspection
    test_text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras elementum pellentesque interdum.
Sed erat augue, cursus at ante nec, pretium feugiat metus. Aliquam laoreet nunc leo, eget porta
quam molestie eu. Vivamus in nunc faucibus, placerat justo eu, volutpat tellus. Vivamus tempus
ultricies augue, non feugiat ante vestibulum sed. Nulla eget lorem porttitor, molestie odio id,
faucibus nunc. Nunc vulputate risus metus, sed tincidunt sapien vestibulum vel. Sed laoreet nibh
ac mauris ultricies, vitae tincidunt justo blandit. Ut vel dui fermentum, vulputate purus quis, 
consectetur justo.
Proin metus nisl, accumsan eu efficitur in, bibendum nec ex. Curabitur facilisis, enim ut venenatis
ultrices, mi lorem vestibulum sem, vel sagittis lacus mauris ut ligula. Proin efficitur iaculis 
dolor imperdiet vehicula. Quisque quis elementum erat. Maecenas bibendum libero et eros blandit 
interdum. Nunc interdum elit ex, nec consequat mi gravida dictum. Phasellus tempor, magna eu auctor
posuere, nisl magna cursus justo, vitae molestie urna velit vitae nulla.
Donec pellentesque, tortor non pretium pretium, diam tortor malesuada magna, et auctor nisi eros 
vitae lectus. Duis maximus dui vel mauris varius, lobortis ultricies velit dignissim. Fusce hendrerit
hendrerit lectus, mattis laoreet quam euismod eget. Donec ullamcorper imperdiet imperdiet. Phasellus
commodo, orci venenatis pellentesque pulvinar, nisi mauris imperdiet purus, ut posuere ipsum diam 
et quam. Nam ut gravida libero, quis dapibus ante. Nam orci nisi, vehicula at mi ut, varius 
     """

    test_xy = (0.1, 0.5)
    test_width = 0.5
    para = ParaMPL(ax, spacing=0.3, fontsize=7)
    ax.axhline(test_xy[1])
    ax.axvline(test_xy[0])
    ax.axvline(test_xy[0] + test_width)

    para.write(test_text, test_xy, width=test_width, va='top')#, justify='full')#, avoid_left_of=(0.2, (0.2, 0.4)))

    f.show()
