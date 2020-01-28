from xfw.events import registerEvent
from Vehicle import Vehicle
import BigWorld

timeBeginBattle = 0.0


@registerEvent(Vehicle, 'onEnterWorld')
def onEnterWorld(self, prereqs):
    global timeBeginBattle
    if self.isPlayerVehicle:
        timeBeginBattle = BigWorld.serverTime()


@xvm.export('xvm.leftTime', deterministic=False)
def xvm_leftTime(lt=0):
    global timeBeginBattle
    if timeBeginBattle == 0.0:
        timeBeginBattle = BigWorld.serverTime()
    return 'lt' if (BigWorld.serverTime() - timeBeginBattle) < lt else None