from nicegui import ui

page_name = "🦗 Crickets 🦗"

with ui.header():
    ui.label(page_name).style("margin: auto; font-size: 30px; font-weight: bold")

with ui.left_drawer(fixed=False):
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
#   DISK
#   status of sensors/actuators

# TODO more

ui.run(title=page_name, dark=True)


# TODO cards
