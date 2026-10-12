"""Exercise custom melee validation, timing, ownership and the real Lua client loop."""
from pathlib import Path
import unittest
from lupa.lua54 import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]

class MeleeServerTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'hw_weapons/config.lua').read_text())
        self.lua.execute('''
            events={}; outgoing={}; timers={}; exportsMap={}; now=1000; source=12
            selected='WEAPON_HW_SOUL_SCYTHE'; owned=selected; slot=4; durability=100
            targetDistance=1.5; targetY=1.5; targetZ=0; targetBucket=0; attackerBucket=0
            targetType=2; targetHealth=100; targetOwner=13; health=100
            function joaat(s) return s end
            function RegisterNetEvent(name, cb) events[name]=cb end
            function AddEventHandler(name, cb) events[name]=cb end
            function TriggerClientEvent(name, player, ...) table.insert(outgoing,{name=name,player=player,args={...}}) end
            function TriggerEvent(...) end
            function GetGameTimer() return now end
            function SetTimeout(ms, cb) table.insert(timers,{delay=ms,cb=cb}) end
            function GetPlayerPing(id) return 60 end
            function GetPlayerPed(id) return id==12 and 120 or 0 end
            function DoesEntityExist(entity) return entity==120 or entity==130 end
            function GetEntityHealth(entity) return entity==120 and health or targetHealth end
            function GetSelectedPedWeapon(ped) return selected end
            function NetworkGetEntityFromNetworkId(id) return id==77 and 130 or id==120 and 120 or 0 end
            function NetworkGetNetworkIdFromEntity(entity) return entity==120 and 120 or 77 end
            function GetEntityType(entity) return targetType end
            function GetEntityRoutingBucket(entity) return entity==120 and attackerBucket or targetBucket end
            function GetEntityCoords(entity) return entity==120 and {x=0,y=0,z=0} or {x=0,y=targetY,z=targetZ} end
            function GetEntityHeading(entity) return 0 end
            function NetworkGetEntityOwner(entity) return targetOwner end
            function GetPlayerName(id) return id==12 or id==13 end
            exports=setmetatable({ox_inventory={
                GetCurrentWeapon=function(self,player) return owned and {name=owned,slot=slot,metadata={durability=durability}} or nil end,
                SetDurability=function(self,player,which,value) durability=value end
            }},{__call=function(self,name,cb) exportsMap[name]=cb end})
        ''')
        self.lua.execute((ROOT/'hw_weapons/melee_server.lua').read_text())

    def attack(self,name='WEAPON_HW_SOUL_SCYTHE',target=77):
        self.lua.globals().events['hw_weapons:meleeRequest'](name,target)
    def damage_events(self):
        return [e for e in self.lua.globals().outgoing.values() if e['name']=='hw_weapons:meleeDamage']
    def impact(self):
        self.lua.globals().timers[1]['cb']()

    def test_attack_is_approved_but_damage_waits_for_contact(self):
        self.attack()
        self.assertEqual(len(self.damage_events()),0)
        self.assertEqual(self.lua.globals().timers[1]['delay'],710)
        self.assertEqual(self.lua.globals().durability,99.5)
        self.impact()
        event=self.damage_events()[0]
        self.assertEqual(event['player'],13)
        self.assertEqual(event['args'][2],35)
        self.assertEqual(event['args'][3],120)

    def test_unknown_name_and_missing_inventory_are_rejected(self):
        self.attack('WEAPON_RPG')
        self.lua.globals().owned=None;self.attack()
        self.assertEqual(len(self.lua.globals().timers),0)

    def test_equipped_hash_must_match_inventory(self):
        self.lua.globals().selected='WEAPON_KNIFE';self.attack()
        self.assertEqual(len(self.lua.globals().timers),0)

    def test_cooldown_rejects_second_request(self):
        self.attack();self.attack()
        self.assertEqual(len(self.lua.globals().timers),1)
        self.assertEqual(self.lua.globals().durability,99.5)

    def test_out_of_range_and_behind_targets_get_no_damage(self):
        self.attack();self.lua.globals().targetY=3;self.impact()
        self.assertEqual(len(self.damage_events()),0)
        self.lua.globals().targetY=-1;self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_other_routing_bucket_is_rejected(self):
        self.attack();self.lua.globals().targetBucket=7;self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_nonped_and_dead_targets_are_rejected(self):
        self.attack();self.lua.globals().targetType=3;self.impact()
        self.assertEqual(len(self.damage_events()),0)
        self.lua.globals().targetType=2;self.lua.globals().targetHealth=0;self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_weapon_swap_or_drop_before_impact_cancels_damage(self):
        self.attack();self.lua.globals().owned='WEAPON_HW_EMBER';self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_slot_swap_before_impact_cancels_damage(self):
        self.attack();self.lua.globals().slot=5;self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_dead_attacker_and_broken_weapon_cannot_start(self):
        self.lua.globals().health=0;self.attack()
        self.lua.globals().health=100;self.lua.globals().durability=0;self.attack()
        self.assertEqual(len(self.lua.globals().timers),0)

    def test_air_swing_is_approved_without_damage(self):
        self.attack(target=0)
        self.assertEqual(len(self.lua.globals().timers),0)
        self.assertEqual(len(self.damage_events()),0)
        self.assertEqual(self.lua.globals().outgoing[1]['name'],'hw_weapons:meleeApproved')

    def test_disconnect_cancels_pending_damage(self):
        self.attack();self.lua.globals().events['playerDropped']();self.impact()
        self.assertEqual(len(self.damage_events()),0)

    def test_invalid_network_ids_are_rejected(self):
        for target in [-1,1.1,'77']:
            self.attack(target=target)
        self.assertEqual(len(self.lua.globals().timers),0)

class MeleeClientTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'hw_weapons/config.lua').read_text())
        self.lua.execute('''
            events={}; sent={}; blocked={}; played={}; damageCalls=0; stops=0; source=65535
            now=0; selected='WEAPON_HW_SOUL_SCYTHE'; controlsPressed=true; canControl=true; clearLos=true
            function joaat(s) return s end
            function RegisterNetEvent(name, cb) events[name]=cb end
            function AddEventHandler(name,cb) events[name]=cb end
            function CreateThread(cb) loop=coroutine.create(cb) end
            function Wait(ms) coroutine.yield() end
            function GetGameTimer() return now end
            function PlayerPedId() return 120 end; function PlayerId() return 12 end
            function GetSelectedPedWeapon(ped) return selected end
            function RequestAnimDict(dict) end; function HasAnimDictLoaded(dict) return true end
            function DisablePlayerFiring(...) end
            function DisableControlAction(group,control,value) blocked[control]=value end
            function IsEntityDead(ped) return false end; function IsPedInAnyVehicle(...) return false end
            function IsPedRagdoll(ped) return false end
            function IsDisabledControlJustPressed(group,control) return controlsPressed end
            function GetEntityCoords(ped) return {x=0,y=0,z=0} end
            function GetEntityForwardVector(ped) return {x=0,y=1,z=0} end
            function GetGamePool(pool) return {} end
            function TriggerServerEvent(name,...) table.insert(sent,{name=name,args={...}}) end
            function TaskPlayAnim(ped,dict,clip,...) table.insert(played,{dict=dict,clip=clip}) end
            function StopAnimTask(...) stops=stops+1 end
            function SetPedCanArmIk(...) end; function SetPedCanTorsoIk(...) end
            function RemoveAnimDict(...) end; function GetCurrentResourceName() return 'hw_weapons' end
            function NetworkDoesEntityExistWithNetworkId(id) return true end
            function NetworkGetEntityFromNetworkId(id) return id end
            function DoesEntityExist(id) return true end; function IsEntityAPed(id) return true end
            function NetworkHasControlOfEntity(id) return canControl end
            function HasEntityClearLosToEntity(...) return clearLos end
            function ApplyDamageToPed(...) damageCalls=damageCalls+1 end
        ''')
        self.lua.execute((ROOT/'hw_weapons/melee_client.lua').read_text())

    def test_native_melee_is_blocked_and_custom_clip_needs_server_approval(self):
        self.lua.execute('assert(coroutine.resume(loop))')
        self.assertEqual(len(self.lua.globals().played),0)
        for control in [24,140,141,142,143]:self.assertTrue(self.lua.globals().blocked[control])
        self.assertEqual(self.lua.globals().sent[1]['name'],'hw_weapons:meleeRequest')
        self.lua.globals().events['hw_weapons:meleeApproved']('WEAPON_HW_SOUL_SCYTHE',1)
        self.assertEqual(self.lua.globals().played[1]['dict'],'hw_melee_v2')
        self.assertEqual(self.lua.globals().played[1]['clip'],'scythe_sweep')

    def test_weapon_change_stops_custom_clip(self):
        self.lua.execute('assert(coroutine.resume(loop))')
        self.lua.globals().events['hw_weapons:meleeApproved']('WEAPON_HW_SOUL_SCYTHE',1)
        self.lua.globals().selected='WEAPON_HW_EMBER'
        self.lua.execute('assert(coroutine.resume(loop))')
        self.assertEqual(self.lua.globals().stops,1)

    def test_local_forged_damage_event_is_ignored(self):
        self.lua.globals().source=0
        self.lua.globals().events['hw_weapons:meleeDamage'](77,35,120)
        self.assertEqual(self.lua.globals().damageCalls,0)

    def test_damage_requires_owner_and_line_of_sight(self):
        damage=self.lua.globals().events['hw_weapons:meleeDamage']
        self.lua.globals().canControl=False;damage(77,35,120)
        self.lua.globals().canControl=True;self.lua.globals().clearLos=False;damage(77,35,120)
        self.assertEqual(self.lua.globals().damageCalls,0)
        self.lua.globals().clearLos=True;damage(77,35,120)
        self.assertEqual(self.lua.globals().damageCalls,1)

if __name__=='__main__':unittest.main()
