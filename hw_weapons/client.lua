for _, weapon in ipairs(Config.Weapons) do
    AddTextEntry(weapon.text, weapon.label)
end

if Config.EnableDiagnostics then
    -- Read-only check; this never gives weapons or bypasses ox_inventory.
    RegisterCommand('hw_check', function()
        CreateThread(function()
            for _, weapon in ipairs(Config.Weapons) do
                local hash = joaat(weapon.name)
                local model = GetWeapontypeModel(hash)
                local definitionOk = IsWeaponValid(hash)
                local modelOk = model == joaat(weapon.model) and IsModelValid(model) and IsModelInCdimage(model)
                local loaded = false

                if modelOk then
                    RequestModel(model)
                    local deadline = GetGameTimer() + 8000
                    repeat
                        Wait(50)
                        loaded = HasModelLoaded(model)
                    until loaded or GetGameTimer() >= deadline
                end

                local clip = definitionOk and GetWeaponClipSize(hash) or -1
                local ok = definitionOk and modelOk and loaded and clip == weapon.clip
                print(('[hw_weapons] %s %s | definition=%s model=%s loaded=%s clip=%d/%d'):format(
                    ok and 'PASS' or 'FAIL', weapon.name, tostring(definitionOk), tostring(modelOk),
                    tostring(loaded), clip, weapon.clip))
                if loaded then SetModelAsNoLongerNeeded(model) end
            end
            if Config.Melee.Enabled then
                RequestAnimDict(Config.Melee.Dictionary)
                local deadline = GetGameTimer() + 8000
                while not HasAnimDictLoaded(Config.Melee.Dictionary) and GetGameTimer() < deadline do Wait(50) end
                for name, settings in pairs(Config.Melee.Weapons) do
                    local seconds = GetAnimDuration(Config.Melee.Dictionary, settings.clip)
                    local ok = HasAnimDictLoaded(Config.Melee.Dictionary) and math.abs(seconds * 1000 - settings.duration) < 50
                    print(('[hw_weapons] %s animation %s/%s | duree %.2fs'):format(
                        ok and 'PASS' or 'FAIL', Config.Melee.Dictionary, settings.clip, seconds))
                end
            end
            print('[hw_weapons] Testez ensuite equipement, tir/frappe, rechargement, vue FPS et synchronisation a deux joueurs.')
        end)
    end, false)
end
