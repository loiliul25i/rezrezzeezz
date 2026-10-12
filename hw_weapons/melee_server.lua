local attacks = {}
local nextToken = 0
local lastHits = {}

local function itemFor(player, name)
    local item = exports.ox_inventory:GetCurrentWeapon(player)
    if not item or item.name ~= name or not item.slot then return nil end
    if not item.metadata or type(item.metadata.durability) ~= 'number' or item.metadata.durability <= 0 then return nil end
    return item
end

local function pedFor(player, name)
    local ped = GetPlayerPed(player)
    if ped == 0 or not DoesEntityExist(ped) or GetEntityHealth(ped) <= 0 then return nil end
    if GetSelectedPedWeapon(ped) ~= joaat(name) then return nil end
    return ped
end

local function reject(player)
    TriggerClientEvent('hw_weapons:meleeRejected', player)
end

RegisterNetEvent('hw_weapons:meleeRequest', function(name, netId)
    local player = source
    if not Config.Melee.Enabled then return reject(player) end
    if type(name) ~= 'string' or type(netId) ~= 'number' or netId % 1 ~= 0 or netId < 0 then return reject(player) end
    local settings = Config.Melee.Weapons[name]
    if not settings then return reject(player) end
    local now = GetGameTimer()
    if attacks[player] and now < attacks[player].readyAt then return reject(player) end
    local item = itemFor(player, name)
    local ped = item and pedFor(player, name)
    if not ped then return reject(player) end
    nextToken = nextToken + 1
    local token = nextToken
    attacks[player] = { token = token, readyAt = now + settings.cooldown, slot = item.slot }
    exports.ox_inventory:SetDurability(player, item.slot, math.max(0, item.metadata.durability - settings.wear))
    TriggerClientEvent('hw_weapons:meleeApproved', player, name, token)
    if netId == 0 then return end

    -- The server owns the hit timing, cooldown, damage amount and reach.
    -- Recheck the equipped inventory slot at impact, so swapping/dropping cancels damage.
    local latency = math.min(150, math.max(0, GetPlayerPing(player) // 2))
    SetTimeout(settings.contact + latency, function()
        local state = attacks[player]
        if not state or state.token ~= token then return end
        local current = exports.ox_inventory:GetCurrentWeapon(player)
        local attacker = pedFor(player, name)
        if not current or current.name ~= name or current.slot ~= state.slot or not attacker then return end
        local target = NetworkGetEntityFromNetworkId(netId)
        if target == 0 or not DoesEntityExist(target) or target == attacker or GetEntityType(target) ~= 2 or GetEntityHealth(target) <= 0 then return end
        if GetEntityRoutingBucket(attacker) ~= GetEntityRoutingBucket(target) then return end
        local a, b = GetEntityCoords(attacker), GetEntityCoords(target)
        local dx, dy, dz = b.x-a.x, b.y-a.y, b.z-a.z
        local distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        if distance > settings.reach or math.abs(dz) > 1.2 then return end
        local heading = math.rad(GetEntityHeading(attacker))
        local dot = distance > 0.01 and (dx * -math.sin(heading) + dy * math.cos(heading)) / distance or 1.0
        if dot < 0.25 then return end
        local owner = NetworkGetEntityOwner(target)
        if not owner or owner < 1 or not GetPlayerName(owner) then return end
        -- Damage is applied once, on the entity owner's client, after the server checks.
        TriggerClientEvent('hw_weapons:meleeDamage', owner, netId, settings.damage, NetworkGetNetworkIdFromEntity(attacker))
        lastHits[netId] = { attacker = player, weapon = name, time = GetGameTimer(), token = token }
        SetTimeout(10000, function()
            if lastHits[netId] and lastHits[netId].token == token then lastHits[netId] = nil end
        end)
        TriggerEvent('hw_weapons:meleeHit', player, netId, name, settings.damage)
    end)
end)

AddEventHandler('playerDropped', function() attacks[source] = nil end)
exports('GetLastMeleeAttacker', function(netId)
    local hit = lastHits[netId]
    if hit and GetGameTimer() - hit.time < 10000 then return hit.attacker, hit.weapon end
end)
