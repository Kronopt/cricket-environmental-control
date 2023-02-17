from nicegui import ui

# DOCS: https://nicegui.io/reference

with ui.header():
    ui.label("🦗 Crickets 🦗").style("margin: auto; font-size: 30px; font-weight: bold")

with ui.left_drawer(fixed=False).style("background-color: #ebf1fa"):
    ui.label("drawer")
    # TODO
    #   Home
    #   Nodes
    #       node-1
    #       node-2
    #       ...

# TODO
#   CPU
#   RAM
#   status of sensors/actuators

# TODO more

ui.run()
