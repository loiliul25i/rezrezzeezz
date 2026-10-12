Config = {}
Config.EnableDiagnostics = true
Config.MaxTestAmmo = 250

-- Dedicated authored swing clips: the default knife-like melee task is blocked.
-- Requires OneSync for authoritative weapon ownership and target validation.
Config.Melee = {
    Enabled = true,
    Dictionary = 'hw_melee_v2',
    Weapons = {
        WEAPON_HW_REAPER_AXE = { clip = 'axe_chop', duration = 1100, contact = 560, cooldown = 1200, reach = 1.65, damage = 30, wear = 0.5 },
        WEAPON_HW_SOUL_SCYTHE = { clip = 'scythe_sweep', duration = 1400, contact = 680, cooldown = 1500, reach = 2.05, damage = 35, wear = 0.5 }
    }
}

Config.Weapons = {
    { name = 'WEAPON_HW_EMBER', label = 'Braise — Pistolet', text = 'WT_HW_EMBER', model = 'w_pi_hw_ember', ammo = 'ammo-9', clip = 12 },
    { name = 'WEAPON_HW_REVENANT', label = 'Revenant — AR', text = 'WT_HW_REVENANT', model = 'w_ar_hw_revenant', ammo = 'ammo-rifle', clip = 30 },
    { name = 'WEAPON_HW_PUMPKIN', label = 'Citrouille — AK', text = 'WT_HW_PUMPKIN', model = 'w_ar_hw_pumpkin', ammo = 'ammo-rifle2', clip = 30 },
    { name = 'WEAPON_HW_REAPER_AXE', label = 'Faucheuse — Hache', text = 'WT_HW_REAPER', model = 'w_me_hw_reaper', clip = 0 },
    { name = 'WEAPON_HW_SOUL_SCYTHE', label = 'Âme perdue — Faux', text = 'WT_HW_SOUL', model = 'w_me_hw_soul', clip = 0 }
}
