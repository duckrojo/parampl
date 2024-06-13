from matplotlib import pyplot as plt
from parampl import ParaMPL

# noinspection SpellCheckingInspection
lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras elementum pellentesque interdum. 
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
hendrerit lectus, mattis laoreet quam euismod eget. Donec ullamcorper imperdiet imperdiet.
 """

f, ax = plt.subplots()
test_xy = (0.05, 0.95)
test_width = 0.7
para = ParaMPL(ax, spacing=0.3, fontsize=7)

command1 = f"""para.avoid_rectangle((0.6, 1, 0.6, 0.8))"""
command2 = f"""para.write(lorem_ipsum, {test_xy},
           avoid_left_of=[(0.15, (0.3, 0.7)),
                                 (0.3, (0.4, 0.5))],
           avoid_right_of=(0.7, (0.2, {test_xy[1]})),
           width={test_width}, justify='full', spacing=1.3,
           )"""

eval(command1)
eval(command2)

para.write(command1 + "\n" + command2, (0.8, 0.1), rotation=90,
           collapse_whites=False, paragraph_per_line=True,
           spacing=1.2, va='bottom',
           family='monospace', color='blue')

para.write("Very Much\nNot\nTop\nSecret", (0.5, 0.5),
           rotation=45, weight='bold',
           fontsize=35, width=0.6,
           ha='center', va='center',
           collapse_whites=False, paragraph_per_line=True,
           justify='center', spacing=0.9,
           family='cursive', color='red')


f.show()
