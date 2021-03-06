import BigWorld
from Avatar import PlayerAvatar
from gui.Scaleform.daapi.view.battle.classic.stats_exchange import FragsCollectableStats
from gui.Scaleform.daapi.view.battle.shared.crosshair.container import CrosshairPanelContainer
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import TargetDistancePlugin
from AvatarInputHandler import AvatarInputHandler
from aih_constants import CTRL_MODE_NAME

from xfw.events import registerEvent
from xvm_main.python.logger import *
import xvm_main.python.config as config
from xfw_actionscript.python import *
import xvm_battle.python.battle as battle


VEHICLE_CLASSES = {'mediumTank': 'MT', 'lightTank': 'LT', 'heavyTank': 'HT', 'AT-SPG': 'TD', 'SPG': 'SPG'}
DISPLAY_IN_MODES = [CTRL_MODE_NAME.ARCADE,
                    CTRL_MODE_NAME.ARTY,
                    CTRL_MODE_NAME.DUAL_GUN,
                    CTRL_MODE_NAME.SNIPER,
                    CTRL_MODE_NAME.STRATEGIC]

targetDistance = None
targetName = None
targetVehicle = None
targetVehicleName = None
targetVType = None
targetColorsVType = None
targetReload = None
targetVisionRadius = None
playerVehicleID = None
f_delayHideTarget = None
isAlly = None
targetAlive = False
visible = True


@registerEvent(AvatarInputHandler, 'onControlModeChanged')
def AvatarInputHandler_onControlModeChanged(self, eMode, **args):
    global visible
    newVisible = eMode in DISPLAY_IN_MODES
    if newVisible != visible:
        visible = newVisible
        as_event('ON_TARGET')


@registerEvent(TargetDistancePlugin, '_TargetDistancePlugin__updateDistance', True)
def TargetDistancePlugin__updateDistance(self, target):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global targetAlive
        targetAlive = target.isAlive()


@registerEvent(CrosshairPanelContainer, 'setDistance')
def CrosshairPanelContainer_setDistance(self, distance):
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global targetDistance
        if targetDistance is None and targetVehicle is None:
            return
        if targetDistance != distance and targetAlive:
            targetDistance = distance if targetVehicle is not None else None
            as_event('ON_TARGET')


def targetClear():
    global targetName, targetVehicle, targetVType, targetColorsVType, targetReload, targetVisionRadius, targetDistance, targetVehicleName
    targetDistance = None
    targetName = None
    targetVehicle = None
    targetVehicleName = None
    targetVType = None
    targetColorsVType = None
    targetReload = None
    targetVisionRadius = None


def delayHideTarget():
    global f_delayHideTarget
    f_delayHideTarget = None
    targetClear()
    as_event('ON_TARGET')


@registerEvent(PlayerAvatar, 'targetBlur')
def PlayerAvatar_targetBlur(self, prevEntity):
    global f_delayHideTarget, isAlly
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        isAlly = None
        if prevEntity in self._PlayerAvatar__vehicles:
            delay = config.get('sight/delayHideTarget', 0)
            if delay > 0:
                f_delayHideTarget = BigWorld.callback(delay, delayHideTarget)
            else:
                targetClear()
                as_event('ON_TARGET')


@registerEvent(PlayerAvatar, 'targetFocus')
def PlayerAvatar_targetFocus(self, entity):
    global targetName, targetVehicle, targetVType, targetColorsVType, targetReload, targetVisionRadius, targetDistance
    global targetVehicleName, isAlly, targetAlive
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        targetAlive = entity.isAlive()
        if entity in self._PlayerAvatar__vehicles and targetAlive:
            if f_delayHideTarget is not None:
                BigWorld.cancelCallback(f_delayHideTarget)
            td = entity.typeDescriptor
            _type = td.type
            _gun = td.gun
            _miscAttrs = td.miscAttrs
            _turret = td.turret
            crewLevelIncrease = 0.0043 * _miscAttrs.get('crewLevelIncrease', 0)
            targetVehicle = _type.shortUserString
            targetVehicleName = td.name.replace(':', '-', 1)
            targetName = entity.publicInfo.name
            isAlly = 'al' if entity.publicInfo.team == self.team else 'en'
            targetReload = _gun.reloadTime * _miscAttrs.get('gunReloadTimeFactor', 1) / (1.0695 + crewLevelIncrease)
            targetVisionRadius = _turret.circularVisionRadius * _miscAttrs.get('circularVisionRadiusFactor', 1) * (1.0434 + crewLevelIncrease)
            vehClass = VEHICLE_CLASSES[list(_type.tags.intersection(VEHICLE_CLASSES.keys()))[0]]
            targetVType = config.get('texts/vtype/' + vehClass)
            targetColorsVType = config.get('colors/vtype/' + vehClass)
            targetAlive = entity.isAlive()
            # targetDistance = int(math.sqrt(self.getVehicleAttached().position.distSqrTo(entity.position)))
            as_event('ON_TARGET')


@registerEvent(PlayerAvatar, 'onEnterWorld')
def Vehicle_onEnterWorld(self, prereqs):
    global playerVehicleID, isAlly, visible
    if config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        playerVehicleID = self.playerVehicleID
        isAlly = None
        visible = True
        targetClear()


@registerEvent(PlayerAvatar, 'updateVehicleHealth')
def PlayerAvatar_updateVehicleHealth(self, vehicleID, health, deathReasonID, isCrewActive, isRespawn):
    if not (health > 0 and isCrewActive) and config.get('sight/enabled', True) and battle.isBattleTypeSupported:
        global isAlly
        targetClear()
        isAlly = None
        as_event('ON_TARGET')

#
# @registerEvent(FragsCollectableStats, 'addVehicleStatusUpdate')
# def FragsCollectableStats_addVehicleStatusUpdate(self, vInfoVO):
#     global isAlly
#     if config.get('sight/enabled', True) and (not vInfoVO.isAlive()) and (playerVehicleID == vInfoVO.vehicleID) and battle.isBattleTypeSupported:
#         targetClear()
#         isAlly = None
#         as_event('ON_TARGET')


@xvm.export('sight.nameTarget', deterministic=False)
def sight_targetName():
    return targetName if visible else None


@xvm.export('sight.vehicleTarget', deterministic=False)
def sight_targetVehicle():
    return targetVehicle if visible else None


@xvm.export('sight.vehNameTarget', deterministic=False)
def sight_vehNameTarget():
    return targetVehicleName if visible else None


@xvm.export('sight.vtypeTarget', deterministic=False)
def sight_targetVType():
    return targetVType if visible else None


@xvm.export('sight.c_vtypeTarget', deterministic=False)
def sight_targetColorsVType():
    return targetColorsVType if visible else None


@xvm.export('sight.reloadTarget', deterministic=False)
def sight_targetReload():
    return targetReload if visible else None


@xvm.export('sight.visionRadiusTarget', deterministic=False)
def sight_targetVisionRadius():
    return targetVisionRadius if visible else None


@xvm.export('sight.distanceTarget', deterministic=False)
def sight_targetDistance():
    return targetDistance if visible else None


@xvm.export('sight.allyTarget', deterministic=False)
def sight_targetAlly():
    return isAlly if visible else None
