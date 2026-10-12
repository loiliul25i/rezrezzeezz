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
            print('[hw_weapons] Testez ensuite equipement, tir/frappe, rechargement, vue FPS et synchronisation a deux joueurs.')
        end)
    end, false)
end
