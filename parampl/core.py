from matplotlib import pyplot as plt

from parampl.statics import split_into_paragraphs, parse_avoid

vertical_lims = tuple[float, float]
avoid_specification = tuple[float, vertical_lims]


class ParaMPL:
    def write(self,
              text,
              xy,
              collapse_whites=True,
              width=None, spacing=None,
              fontsize=None,
              justify='left',
              color: str | None = None,
              ha='left',
              va='top',
              avoid_left_of: avoid_specification | list[avoid_specification] = None,
              avoid_right_of: avoid_specification | list[avoid_specification] = None,
              ):
        """
Write text into a paragraph

        :param collapse_whites:
          whether multiple side-by-side withes should be considered as one
        :param color:
          color of text
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
        old_artists = list(ax.texts)

        if ax.get_ylim()[1] < ax.get_ylim()[0]:
            raise NotImplementedError("paraMPL.write() is only available for plots with increasing y-axis")

        if va != 'top' and (avoid_left_of is not None or avoid_right_of is not None):
            raise ValueError("if using avoid areas, then va='top' must be used")

        widths, height, combined_hash = self._get_widths_height(fontsize,
                                                                words=text.split())
        space_width = widths[' ']

        xx, yy = xy
        yy -= height  # top alignment
        delta_yy = (1 + spacing) * height

        if ha == 'right':
            xx -= width
        elif ha == 'center':
            xx -= width / 2.0
        elif ha != 'left':
            raise ValueError(f"invalid ha '{ha}'. Must be 'right', 'left', or 'center'")

        borders = [(None, xx, width)]

        if avoid_left_of is not None or avoid_right_of is not None:
            borders = parse_avoid(borders, avoid_left_of, avoid_right_of, height)

        words = []
        length = 0
        paragraphs = split_into_paragraphs(text, collapse_whites=collapse_whites)

        limit, xx, width_line = borders.pop(0)

        for paragraph in paragraphs:

            if justify == 'left' or justify == 'right' or justify == 'center':
                for word in paragraph.split(' '):
                    if length + widths[word] > width_line:
                        justify_offset = ((justify == 'right') + 0.5 * (justify == 'center')
                                          ) * (width_line - length + space_width)
                        ax.text(xx + justify_offset, yy, ' '.join(words),
                                fontsize=fontsize, color=color)
                        length = 0
                        words = []
                        yy -= delta_yy
                        if limit is not None and yy < limit:
                            limit, xx, width_line = borders.pop(0)

                    length += widths[word] + space_width
                    words.append(word)

            elif justify == 'full':
                x = xx
                for word in paragraph.split(' '):
                    if length + widths[word] > width_line:
                        if len(word) == 1:
                            ax.text(x, yy, words[0],
                                    fontsize=fontsize, color=color)
                        else:
                            extra_spacing = (width_line - length + space_width) / (len(words) - 1)
                            for old_width in words:
                                ax.text(x, yy, old_width,
                                        fontsize=fontsize, color=color)
                                x += extra_spacing + space_width + widths[old_width]
                        length = 0
                        words = []

                        yy -= delta_yy
                        if limit is not None and yy < limit:
                            limit, xx, width_line = borders.pop(0)
                        x = xx

                    length += widths[word] + space_width
                    words.append(word)

                ax.text(xx, yy, ' '.join(words),
                        fontsize=fontsize, color=color)

            else:
                raise ValueError(f'Unrecognized justify {justify}')

        if va == 'bottom':
            total_height = xy[1] - yy
            for artist in ax.texts:
                if artist not in old_artists:
                    artist.set_y(artist.get_position()[1] + total_height)

        elif va == 'center':
            total_height = xy[1] - yy
            for artist in ax.texts:
                if artist not in old_artists:
                    artist.set_y(artist.get_position()[1] + total_height / 2)

        elif va != 'top':
            raise ValueError(f"invalid va '{va}'. Must be 'top', 'bottom', or 'center'")

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

    def _get_widths_height(self, fontsize,
                           words: list[str] = None,
                           ):
        text_artist = self.axes.text(0, 0, ' ', fontsize=fontsize)
        combined_hash = (fontsize,)  # todo: probably font name should be in here

        if combined_hash not in self.widths:
            text_artist.set_text(' ')
            widths: dict[str, float] = {' ': self._transformed_artist_extent(text_artist).width,
                                        '': 0,
                                        }

            text_artist.set_text('L')
            height = self._transformed_artist_extent(text_artist).height

            self.widths[combined_hash] = widths
            self.heights[combined_hash] = height
        else:
            widths = self.widths[combined_hash]

        if words is not None:
            for word in words:
                if word not in widths:
                    text_artist.set_text(word)
                    widths[word] = self._transformed_artist_extent(text_artist).width

        text_artist.remove()

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

    test_xy = (0.1, 0.8)
    test_width = 0.8
    para = ParaMPL(ax, spacing=0.3, fontsize=7)
    ax.axhline(test_xy[1])
    ax.axvline(test_xy[0])
    ax.axvline(test_xy[0] + test_width)

    para.write(test_text, test_xy,
               avoid_left_of=[(0.4, (0.2, 0.4)),
                              (0.2, (0, 0.7)),
                              ],
               avoid_right_of=[(0.8, (0.6, 0.5)),
                               (0.7, (0, 0.2)),
                               ],
               width=test_width, justify='center')
    # , justify='full')#, avoid_left_of=(0.2, (0.2, 0.4)))

    f.show()
