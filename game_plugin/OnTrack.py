import socket
import json
import math
import os

try:
    import ac
    import acsys
except ImportError:
    pass

import config as config_module

_socket = None
_target_ip = "127.0.0.1"
_target_port = 20777
_app_id = -1
_frame_counter = 0
_update_every = 2
_config = {}

def acMain(ac_version):
    global _socket, _target_ip, _target_port, _app_id, _config, _update_every

    try:
        _app_id = ac.newApp("OnTrack")
        ac.setSize(_app_id, 200, 100)

        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(plugin_dir, "config.ini")
        _config = config_module.load_config(config_path)

        _target_ip = _config.get('ip', '127.0.0.1')
        _target_port = _config.get('port', 20777)

        update_rate = _config.get('update_rate_hz', 30)
        _update_every = max(1, 60 / update_rate)

        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _socket.setblocking(0)

        ac.log("OnTrack: Initialized. Broadcasting to {0}:{1}".format(_target_ip, _target_port))

    except Exception as e:
        ac.log("OnTrack init error: {0}".format(str(e)))

    return "OnTrack"

def acUpdate(deltaT):
    global _socket, _target_ip, _target_port, _frame_counter

    if _socket is None:
        return

    _frame_counter = _frame_counter + 1

    if _frame_counter % _update_every != 0:
        return

    try:
        speed = ac.getCarState(0, acsys.CS.SpeedKMH)
        if math.isnan(speed):
            speed = 0.0

        rpm = ac.getCarState(0, acsys.CS.RPM)
        if math.isnan(rpm):
            rpm = 0

        gear = ac.getCarState(0, acsys.CS.Gear)
        if math.isnan(gear):
            gear = 0

        throttle = ac.getCarState(0, acsys.CS.Gas)
        if math.isnan(throttle):
            throttle = 0.0

        brake = ac.getCarState(0, acsys.CS.Brake)
        if math.isnan(brake):
            brake = 0.0

        fuel = ac.getCarState(0, acsys.CS.Fuel)
        if math.isnan(fuel):
            fuel = 0.0

        lap_count = ac.getCarState(0, acsys.CS.LapCount)
        if math.isnan(lap_count):
            lap_count = 0

        lap_time = ac.getCarState(0, acsys.CS.LapTime)
        if math.isnan(lap_time):
            lap_time = 0

        best_lap = ac.getCarState(0, acsys.CS.BestLap)
        if math.isnan(best_lap):
            best_lap = 0

        last_lap = ac.getCarState(0, acsys.CS.LastLap)
        if math.isnan(last_lap):
            last_lap = 0

        tyre_temps = ac.getCarState(0, acsys.CS.TyreCoreTemp)
        if tyre_temps is None or len(tyre_temps) < 4:
            tyre_temps = [0.0, 0.0, 0.0, 0.0]
        else:
            tyre_temps = [float(t) if not math.isnan(t) else 0.0 for t in tyre_temps[:4]]

        g_forces = ac.getCarState(0, acsys.CS.AccG)
        if g_forces is None or len(g_forces) < 3:
            gx, gy, gz = 0.0, 0.0, 0.0
        else:
            gx = float(g_forces[0]) if not math.isnan(g_forces[0]) else 0.0
            gy = float(g_forces[1]) if not math.isnan(g_forces[1]) else 0.0
            gz = float(g_forces[2]) if not math.isnan(g_forces[2]) else 0.0

        telemetry = {
            'v': 1,
            'spd': round(speed, 1),
            'rpm': int(rpm),
            'gear': int(gear),
            'thr': round(throttle, 2),
            'brk': round(brake, 2),
            'fuel': round(fuel, 1),
            'lap': int(lap_count),
            'lap_t': int(lap_time),
            'best_t': int(best_lap),
            'last_t': int(last_lap),
            'tyre': [round(t, 1) for t in tyre_temps],
            'gx': round(gx, 2),
            'gy': round(gy, 2),
            'gz': round(gz, 2)
        }

        data = json.dumps(telemetry).encode('utf-8')
        _socket.sendto(data, (_target_ip, _target_port))

    except socket.error:
        pass
    except Exception as e:
        ac.log("OnTrack update error: {0}".format(str(e)))

def acShutdown():
    global _socket
    try:
        if _socket is not None:
            _socket.close()
    except:
        pass
