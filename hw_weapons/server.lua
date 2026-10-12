local byName = {}
for _, weapon in ipairs(Config.Weapons) do byName[weapon.name] = weapon end

local function reply(source, message)
    print(('[hw_weapons] %s'):format(message))
    if source ~= 0 then
        TriggerClientEvent('chat:addMessage', source, { args = { 'Halloween', message } })
    end
end

local function knownItem(name)
    return exports.ox_inventory:Items(name) ~= nil
end

local function give(source, target, weapon, ammoCount)
    if not knownItem(weapon.name) then
        reply(source, weapon.name .. ' manque dans ox_inventory/data/weapons.lua. Installez les entrees puis redemarrez le serveur.')
        return false
    end
    if weapon.ammo and ammoCount > 0 and not knownItem(weapon.ammo) then
        reply(source, 'Munition absente de ox_inventory: ' .. weapon.ammo)
        return false
    end
    if not exports.ox_inventory:CanCarryItem(target, weapon.name, 1) then
        reply(source, 'Inventaire plein pour ' .. weapon.name)
        return false
    end
    -- ox_inventory supplies serial, registration and persistent metadata.
    local success, reason = exports.ox_inventory:AddItem(target, weapon.name, 1, { durability = 100, ammo = 0 })
    if not success then
        reply(source, 'Ajout refuse: ' .. tostring(reason))
        return false
    end
    reply(source, weapon.name .. ' ajoute au joueur ' .. target)
    if weapon.ammo and ammoCount > 0 then
        local ammoSuccess, ammoReason = exports.ox_inventory:AddItem(target, weapon.ammo, ammoCount)
        if not ammoSuccess then
            reply(source, 'Arme ajoutee, mais munitions non ajoutees: ' .. tostring(ammoReason))
        end
    end
    return true
end

-- restricted=true enforces FiveM ACE command.hw_give, including for ESX servers.
RegisterCommand('hw_give', function(source, args)
    local target = tonumber(args[1])
    local name = (args[2] or ''):upper()
    local ammoCount = args[3] == nil and 60 or tonumber(args[3])

    if not target or target % 1 ~= 0 or target < 1 or not GetPlayerName(target) then
        reply(source, 'ID joueur invalide ou joueur hors ligne.')
        return
    end
    if not ammoCount or ammoCount % 1 ~= 0 or ammoCount < 0 or ammoCount > Config.MaxTestAmmo then
        reply(source, 'Quantite de munitions attendue: entier de 0 a ' .. Config.MaxTestAmmo)
        return
    end
    if name == 'ALL' then
        local given = 0
        for _, weapon in ipairs(Config.Weapons) do
            if give(source, target, weapon, ammoCount) then given = given + 1 end
        end
        reply(source, ('Distribution terminee: %d/%d armes.'):format(given, #Config.Weapons))
    elseif byName[name] then
        give(source, target, byName[name], ammoCount)
    else
        reply(source, 'Usage: hw_give <ID> <WEAPON_HW_...|all> [munitions 0-' .. Config.MaxTestAmmo .. ']')
    end
end, true)

AddEventHandler('onResourceStart', function(resource)
    if resource ~= GetCurrentResourceName() then return end
    for _, weapon in ipairs(Config.Weapons) do
        if not knownItem(weapon.name) then
            print('[hw_weapons] INSTALLATION INCOMPLETE: entree ox_inventory manquante: ' .. weapon.name)
        end
    end
end)
