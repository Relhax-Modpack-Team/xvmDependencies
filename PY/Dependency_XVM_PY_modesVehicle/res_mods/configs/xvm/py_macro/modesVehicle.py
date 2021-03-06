from Vehicle import Vehicle
from AvatarInputHandler.commands.siege_mode_control import SiegeModeControl
from AvatarInputHandler import AvatarInputHandler
from aih_constants import CTRL_MODE_NAME

from xfw.events import registerEvent
from xvm_main.python.logger import *
from xfw_actionscript.python import *
import xvm_main.python.config as config
import xvm_battle.python.battle as battle

NORMAL = 'normal'
SPEED = 'speed'
SIEGE = 'siege'
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]

isWheeledTech = False
speedMode = NORMAL
hasAutoSiegeMode = False
hasSiegeMode = False
siegeMode = NORMAL
autoSiegeMode = NORMAL
visible = True


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_VEHICLE_MODE')


@registerEvent(Vehicle, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global isWheeledTech, siegeMode, autoSiegeMode, hasAutoSiegeMode, hasSiegeMode, speedMode, visible
    if config.get('sight/enabled', True) and self.isPlayerVehicle and battle.isBattleTypeSupported:
        isWheeledTech = self.isWheeledTech
        hasAutoSiegeMode = self.typeDescriptor.hasAutoSiegeMode
        hasSiegeMode = not (hasAutoSiegeMode or isWheeledTech) and self.typeDescriptor.hasSiegeMode
        speedMode = NORMAL
        siegeMode = NORMAL
        autoSiegeMode = NORMAL
        visible = True
        as_event('ON_VEHICLE_MODE')


@registerEvent(SiegeModeControl, 'notifySiegeModeChanged')
def SiegeModeControl_notifySiegeModeChanged(self, vehicle, newState, timeToNextMode):
    global siegeMode, autoSiegeMode, speedMode, isWheeledTech, hasAutoSiegeMode, hasSiegeMode
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        if not vehicle.isPlayerVehicle:
            return
        prev_siegeMode = siegeMode
        prev_autoSiegeMode = autoSiegeMode
        prev_speedMode = speedMode
        speedMode = SPEED if (newState == 2) and isWheeledTech else NORMAL
        siegeMode = SIEGE if (newState == 2) and hasSiegeMode else NORMAL
        autoSiegeMode = SIEGE if (newState == 2) and hasAutoSiegeMode else NORMAL
        if prev_siegeMode != siegeMode or prev_autoSiegeMode != autoSiegeMode or prev_speedMode != speedMode:
            as_event('ON_VEHICLE_MODE')


@xvm.export('mode.siege', deterministic=False)
def sight_siegeMode():
    return siegeMode if hasSiegeMode and visible else None


@xvm.export('mode.autoSiege', deterministic=False)
def sight_autoSiegeMode():
    return autoSiegeMode if hasAutoSiegeMode and visible else None


@xvm.export('mode.speed', deterministic=False)
def sight_speedMode():
    return speedMode if isWheeledTech and visible else None
