from math import sin
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
print "def GUI"
class GUI(App):
  def build(self):
    graph = Graph(
      xlabel="X",
      ylabel="Y",
      x_ticks_minor=5,
      x_ticks_major=25,
      y_ticks_major=1,
      x_grid_label=True,
      y_grid_label=True,
      padding=5,
      x_grid=True,
      y_grid=True,
      xmin=-0,
      xmax=100,
      ymin=-1,
      ymax=1
    )
    plot = MeshLinePlot(color=[1,0,0,1])
    plot.point = [(x, sin(x)) for x in range(0,101)]
    graph.add_plot(plot)
    root = FloatLayout()
    root.add_widget(graph)
    print "build()"
    return root
print "running gui"
GUI().run()
