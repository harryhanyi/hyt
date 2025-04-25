"""
This module is a global configuration of the ui elements for protostar
"""
import inspect


class Config(object):
    class Color(object):
        selected_frame = (209, 247, 255)
        frame = (78, 100, 105)
        node_title_background = (71, 69, 65)
        graph_title_background = (64, 60, 79)

        title_color_running = (255, 218, 23)
        title_color_failed = (230, 32, 9)
        title_color_succeed = (45, 212, 17)

        node_color = [56, 55, 53]
        graph_color = [49, 45, 64]

        pending_line_color = (160, 160, 160, 80)
        in_use_socket_color = (232, 232, 232, 180)

        main_socket_color = (177, 222, 240, 180)

        node_alpha = 180

        parameter_node_color = (201, 111, 115)

        direct_connected_param = (235, 186, 7)
        expression_override_param = (179, 124, 235)
        dynamic_param = (90, 230, 206)

        refrence_indicator = (124, 178, 207)

    class Node(object):
        default_collapsed = False
        main_socket_radius = 20
        socket_radius = 18
        title_bar_height = 45
        icon_bar_height = 45
        outline_width = 4  # Make sure this is set to an even number
        margin = [4, 4, 2, 2]
        spacing = 8
        width = 250
        section_height = 30

        parameter_node_height = 48

    class View(object):
        scene_width = 8000000
        scene_height = 4000000

    class Font(object):
        parameter_font_size = 16
        title_font_size = 22
        parameter_font_family = 'Arial'
        title_font_family = 'Arial'

    @classmethod
    def export(cls):
        data = {}
        for name, member in inspect.getmembers(cls,
                                               lambda a: inspect.isclass(a)):
            if not name.startswith('__'):
                data[name] = Config.serialize_class_data(member)
        return data

    @staticmethod
    def serialize_class_data(cls):
        data = {}
        for name, member in inspect.getmembers(cls):
            if not name.startswith('__'):
                data[name] = member
        return data
