local active = nil
local pending = nil
local loaded = false
local weaponByHash = {}
for name, settings in pairs(Config.Melee.Weapons) do
    weaponByHash[joaat(name)] = { name = name, settings = settings }
end

local function nearestTarget(ped, range)
    local position = GetEntityCoords(ped)
    local forward = GetEntityForwardVector(ped)
    local best, bestDistance = nil, range
    for _, target in ipairs(GetGamePool('CPed')) do
        if target ~= ped and DoesEntityExist(target) and not IsEntityDead(target) and NetworkGetEntityIsNetworked(target) and HasEntityClearLosToEntity(ped, target, 17) then
            local delta = GetEntityCoords(target) - position
            local distance = #delta
            local dot = distance > 0.01 and (delta.x * forward.x + delta.y * forward.y) / distance or 1.0
            if distance <= bestDistance and math.abs(delta.z) < 1.2 and dot > 0.25 then
                best, bestDistance = target, distance
            end
        end
    end
    return best and NetworkGetNetworkIdFromEntity(best) or 0
end

local function cancel(ped)
    if active then
        StopAnimTask(ped, Config.Melee.Dictionary, active.clip, 0.15)
        SetPedCanArmIk(ped, true)
        SetPedCanTorsoIk(ped, true)
    end
    active = nil
    pending = nil
end

RegisterNetEvent('hw_weapons:meleeApproved', function(name, token)
    if source ~= 65535 then return end
    local settings = Config.Melee.Weapons[name]
    local ped = PlayerPedId()
    if not settings or not pending or pending.name ~= name or GetSelectedPedWeapon(ped) ~= joaat(name) then return end
    pending = nil
    -- Upper body only, synchronized as an ordinary network ped animation.
    SetPedCanArmIk(ped, false)
    SetPedCanTorsoIk(ped, false)
    TaskPlayAnim(ped, Config.Melee.Dictionary, settings.clip, 5.0, -5.0, settings.duration, 48, 0.0, false, false, false)
    active = { clip = settings.clip, name = name, token = token, untilTime = GetGameTimer() + settings.duration }
end)

RegisterNetEvent('hw_weapons:meleeRejected', function()
    if source == 65535 then pending = nil end
end)

RegisterNetEvent('hw_weapons:meleeDamage', function(netId, damage, attackerNetId)
    if source ~= 65535 then return end
    if type(netId) ~= 'number' or type(damage) ~= 'number' or damage < 1 or damage > 100 then return end
    if not NetworkDoesEntityExistWithNetworkId(netId) then return end
    local ped = NetworkGetEntityFromNetworkId(netId)
    if type(attackerNetId) ~= 'number' or not NetworkDoesEntityExistWithNetworkId(attackerNetId) then return end
    local attacker = NetworkGetEntityFromNetworkId(attackerNetId)
    if DoesEntityExist(ped) and IsEntityAPed(ped) and NetworkHasControlOfEntity(ped) and not IsEntityDead(ped) then
        if DoesEntityExist(attacker) and HasEntityClearLosToEntity(attacker, ped, 17) then
            ApplyDamageToPed(ped, damage, false)
        end
    end
end)

CreateThread(function()
    while Config.Melee.Enabled do
        local ped = PlayerPedId()
        local entry = weaponByHash[GetSelectedPedWeapon(ped)]
        if not entry then
            if active or pending then cancel(ped) end
            Wait(150)
        else
            if not loaded then
                RequestAnimDict(Config.Melee.Dictionary)
                loaded = HasAnimDictLoaded(Config.Melee.Dictionary)
            end
            -- Suppress the native strike/takedown so it cannot play a knife fallback
            -- or apply damage a second time during the custom strike.
            DisablePlayerFiring(PlayerId(), true)
            for _, control in ipairs({ 24, 140, 141, 142, 143, 257, 263, 264 }) do
                DisableControlAction(0, control, true)
            end
            if IsEntityDead(ped) or IsPedInAnyVehicle(ped, false) or IsPedRagdoll(ped) then
                cancel(ped)
            elseif active and GetGameTimer() >= active.untilTime then
                cancel(ped)
            elseif pending and GetGameTimer() > pending.deadline then
                pending = nil
            elseif loaded and not active and not pending and
                   (IsDisabledControlJustPressed(0, 24) or IsDisabledControlJustPressed(0, 140)) then
                pending = { name = entry.name, deadline = GetGameTimer() + 2500 }
                TriggerServerEvent('hw_weapons:meleeRequest', entry.name, nearestTarget(ped, entry.settings.reach))
            end
            Wait(0)
        end
    end
end)

AddEventHandler('onResourceStop', function(resource)
    if resource == GetCurrentResourceName() then
        cancel(PlayerPedId())
        if loaded then RemoveAnimDict(Config.Melee.Dictionary) end
    end
end)
