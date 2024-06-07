import numpy as np
from matplotlib.axes import Axes

from parampl.statics import (split_into_paragraphs, parse_avoid,
                             avoid_specification, avoid_single_specification)


__all__ = ['ParaMPL', 'avoid_specification', 'avoid_single_specification']


class ParaMPL:
    def __init__(self,
                 axes: Axes,
                 width: float = 1.0,
                 spacing: float = 0.5,
                 fontsize: float = 10,
                 justify: str = "left",
                 fontname: str | None = None,
                 family: str | None = None,
                 color: None | str | tuple[float, float, float] = None,
                 transform: str = 'data',
                 ):
        """

        :param axes:
          matplotlib.axes.Axes in which to put the paragraphs
        :param spacing:
          default spacing
        :param width:
           default width
        :param fontsize:
           default fontsize
        :param color:
          default color
        :param transform:
          transform in which the coordinates are given. Currently supported: 'data'
        """
        self.width = width
        self.spacing = spacing
        self.axes = axes
        self.fontsize = fontsize
        self.color = color
        self.family = family
        self.fontname = fontname
        self.justify = justify

        self._renderer = axes.get_figure().canvas.get_renderer()
        if transform == 'data':
            self._transform = axes.transData.inverted()
        else:
            raise NotImplementedError("only 'data' transform is supported for now")

        self.widths: dict[tuple, dict[str, float]] = {}
        self.heights: dict[tuple, float] = {}

    def write(self,
              text: str,
              xy: tuple[float, float],
              width: float | None = None,
              spacing: float | None = None,
              fontsize: float | None = None,
              color: str | None = None,
              fontname: str | None = None,
              family: str | None = None,
              rotation: float = 0,
              justify: str | None = None,
              ha: str = 'left',
              va: str = 'top',
              avoid_left_of: avoid_specification = None,
              avoid_right_of: avoid_specification = None,
              collapse_whites: bool = True,
              paragraph_per_line: bool = False,
              ):
        """
Write text into a paragraph

        :param text:
          text to write
        :param xy:
           xy to place the paragraph
        :param width:
          use this width instead of the initialized one
        :param paragraph_per_line:
          if true, each new line is considered a new paragraph
        :param family:
          family of the font
        :param fontname:
          specific fontname, if not specified then use family
        :param rotation:
           anticlockwise rotation
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
        :param spacing:
          use this spacing instead of the initialized one
        :param fontsize:
          use this fontsize instead of the initialized one
        """

        if width is None:
            width = self.width
        if justify is None:
            justify = self.justify
        if spacing is None:
            spacing = self.spacing
        if fontsize is None:
            fontsize = self.fontsize
        if color is None:
            color = self.color
        if family is None:
            family = self.family
        if fontname is None:
            fontname_dict = {}
        else:
            fontname_dict = {'fontname': self.fontname}

        ax = self.axes

        def write_line(left, bottom, text_in_line):

            ax.text(left, bottom, text_in_line,
                    fontsize=fontsize, color=color, rotation=rotation,
                    family=family, **fontname_dict)

        old_artists = list(ax.texts)

        if ax.get_ylim()[1] < ax.get_ylim()[0] or ax.get_xlim()[1] < ax.get_xlim()[0]:
            raise NotImplementedError("paraMPL.write() is only available for plots with increasing x- and y-axis")

        if va != 'top' and (avoid_left_of is not None or avoid_right_of is not None):
            raise ValueError("if using avoid areas, then va='top' must be used")

        widths, height, combined_hash = self._get_widths_height(fontsize, family, fontname,
                                                                words=text.split())
        space_width = widths[' ']

        xx, yy = xy

        yy -= height * np.cos(rotation * np.pi / 180)  # top alignment
        xx += height * np.sin(rotation * np.pi / 180)  # top alignment

        delta_yy = - (1 + spacing) * height * np.cos(rotation * np.pi / 180)
        delta_xx = (1 + spacing) * height * np.sin(rotation * np.pi / 180)

        if ha == 'right':
            xx -= width
        elif ha == 'center':
            xx -= width / 2.0
        elif ha != 'left':
            raise ValueError(f"invalid ha '{ha}'. Must be 'right', 'left', or 'center'")

        borders = [(None, xx, width)]
        justify_mult = (justify == 'right') + 0.5 * (justify == 'center')

        if avoid_left_of is not None or avoid_right_of is not None:
            borders = parse_avoid(borders, avoid_left_of, avoid_right_of, height)

        words = []
        length = 0
        paragraphs = split_into_paragraphs(text,
                                           collapse_whites=collapse_whites,
                                           paragraph_per_line=paragraph_per_line,
                                           )

        limit, xx, width_line = borders.pop(0)
        if limit is not None and yy < limit:
            limit, xx, width_line = borders.pop(0)

        for paragraph in paragraphs:

            if justify == 'left' or justify == 'right' or justify == 'center':
                for word in paragraph.split(' '):
                    if length + widths[word] > width_line:
                        justify_offset = justify_mult * (width_line - length + space_width)
                        write_line(xx + justify_offset, yy, ' '.join(words))

                        xx, yy = xx + delta_xx, yy + delta_yy
                        length, words = 0, []

                        if limit is not None and yy < limit:
                            limit, xx, width_line = borders.pop(0)

                    length += widths[word] + space_width
                    words.append(word)

                justify_offset = justify_mult * (width_line - length + space_width)
                write_line(xx + justify_offset, yy, ' '.join(words))

                length, words = 0, []
                xx, yy = xx + delta_xx, yy + delta_yy

            elif justify == 'full':
                for word in paragraph.split(' '):
                    if length + widths[word] > width_line:
                        if len(words) > 1:
                            extra_spacing = (width_line - length + space_width) / (len(words) - 1)
                        else:
                            extra_spacing = 0

                        x = xx
                        for old_width in words:
                            write_line(x, yy, old_width)
                            x += extra_spacing + space_width + widths[old_width]
                        length = 0
                        words = []

                        yy += delta_yy
                        xx += delta_xx
                        if limit is not None and yy < limit:
                            limit, xx, width_line = borders.pop(0)

                    length += widths[word] + space_width
                    words.append(word)

                write_line(xx, yy, ' '.join(words))
                length = 0
                words = []
                yy += delta_yy
                xx += delta_xx

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

    def _get_widths_height(self, fontsize, family, fontname,
                           words: list[str] = None,
                           ):
        text_artist = self.axes.text(0, 0, ' ',
                                     fontsize=fontsize, fontname=fontname, family=family)
        combined_hash = (fontsize, family, fontname)

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
