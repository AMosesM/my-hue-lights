#!/usr/bin/env python
# encoding: utf-8
from flask import Flask, request, jsonify, send_file
from huesdk import Light
from imageio import imread
from matplotlib import colors as mcolors
import gizeh as gz
import json
import moviepy.editor as mpy
import os
import webcolors
import yaml
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from setup_bridges import setup_bridge


CONFIG_FILE = os.path.realpath("/opt/app/conf.yaml")
CONFIG = yaml.safe_load(open(CONFIG_FILE))
VIDEO_SIZE = (500, 100)
FPS = 10
DURATION = 14.7

colors_flipbook_path = "colors_flipbook.gif"
curr_frame = 0

color_tuples = dict(**mcolors.CSS4_COLORS)
for color, hex in color_tuples.items():
    int_rgb = webcolors.hex_to_rgb(hex)
    color_tuples[color] = tuple([float(c/255.0) for c in [int_rgb.red, int_rgb.green, int_rgb.blue]])
color_tuples = [c for n,c in color_tuples.items()]

def make_frame(time):
    global curr_frame
    global color_tuples
    surface = gz.Surface(500, 100, bg_color=color_tuples[curr_frame])
    curr_frame += 1
    if curr_frame >= len(color_tuples):
        curr_frame = len(color_tuples) - 1
    return surface.get_npimage()

if not os.path.exists(colors_flipbook_path):
    colors_flipbook = mpy.VideoClip(make_frame, duration=DURATION)
    video = mpy.CompositeVideoClip([
        colors_flipbook,
    ], size=VIDEO_SIZE).set_duration(DURATION)
    video.write_gif(colors_flipbook_path, fps=FPS, opt="OptimizePlus", fuzz=10)

def create_app():
    app = Flask(__name__)
    connected_bridges = {}
    for bridge in CONFIG.get("bridges").keys():
        try:
            tmp_bridge = setup_bridge(CONFIG.get("bridges").get(bridge).get('url'))
            connected_bridges[bridge] = tmp_bridge
        except Exception as e:
            print(e)
 
    def light_switch(light, turn_off):
        if isinstance(light, Light):
            if turn_off:
                light.off()
            else:
                light.on()
                light.set_brightness(254)

    @app.route('/my_hue_lights', methods=['GET'])
    def my_hue_lights():
        lights = []
        for name, bridge in connected_bridges.items():
            lights += bridge.get_lights()
        
        return jsonify([{
            'name': str(l.name),
            'bridge': str(l.sdk.get('/config').get('name'))
            } for l in lights if isinstance(l, Light)])
    
    @app.route('/my_hue_lights/colors', methods=['GET'])
    def colors():
        return jsonify({'colors': color_tuples})
    
    @app.route('/my_hue_lights/colors_flipbook', methods=['GET'])
    def colors_flipbook():
        return send_file(colors_flipbook_path, mimetype='image/gif')

    @app.route('/my_hue_lights/set_image_color', methods=['POST'])
    def set_image_color():
        result = {}
        color_tuple = (255,255,255)
        try:
            bridge = request.form.get('bridge')
            name = request.form.get('name')
            image = request.files['image'] if 'image' in request.files else None

            if image:                
                frames = imread(image)
                if frames.any():
                    color_tuple = tuple(frames[0,0])

                _bridge = connected_bridges.get(bridge)

                lights_to_set = []

                if not _bridge:
                    result = jsonify({"ERROR": "No bridge specified"})
                else:
                    if name:
                        light = _bridge.get_light(name=name)
                        lights_to_set.append(light)
                    else:
                        lights_to_set = _bridge.get_lights()

                    for l in lights_to_set:
                        assert isinstance(l, Light)
                        light_switch(l, turn_off=False)
                        l.set_color(hexa=webcolors.rgb_to_hex(color_tuple))

            result = jsonify("The light(s) are on and colored {}".format(color_tuple))
        except Exception as e:
            result = jsonify({"ERROR": str(e)})
        return result

    @app.route('/my_hue_lights/set_color', methods=['POST'])
    def set_color():
        try:
            record = json.loads(request.data)
            bridge = record["bridge"]
            name = record.get("name")
            color = record.get("color")

            _bridge = connected_bridges.get(bridge)

            lights_to_set = []

            if name:
                light = _bridge.get_light(name=name)
                lights_to_set.append(light)
            else:
                lights_to_set = _bridge.get_lights()

            for l in lights_to_set:
                assert isinstance(l, Light)
                light_switch(l, turn_off=False)
                l.set_color(hexa=webcolors.name_to_hex(color))
            result = jsonify("The light(s) are on and colored {}".format(color))
        except Exception as e:
            result = jsonify({"ERROR": str(e)})

        return result

    @app.route('/my_hue_lights/switch', methods=['POST'])
    def lights_switch():
        try:
            record = json.loads(request.data)
            bridge = record["bridge"]
            name = record.get("name")

            _bridge = connected_bridges.get(bridge)

            if name:
                light = _bridge.get_light(name=name)
                light_switch(light, light.is_on)
                result = jsonify("light {} is {}".format(light.name, "on" if light.is_on else "off"))
            else:
                turn_off = -1
                for l in _bridge.get_lights():
                    if turn_off == -1:
                        turn_off = l.is_on
                    light_switch(l, turn_off)
                result = jsonify("{} lights are {}".format(bridge, "off" if turn_off else "on"))
        except Exception as e:
            result = jsonify({"ERROR": str(e)})

        return result
    
    return app


if __name__ == "__main__":
    create_app()
