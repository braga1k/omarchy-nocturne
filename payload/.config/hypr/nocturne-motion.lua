-- Nocturne: movimento curto, sem overshoot, com saídas mais rápidas.
-- Tempos em décimos de segundo. Fonte: wiki.hypr.land/configuring/core/animations/
hl.curve("nocturneOut", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.curve("nocturneIn", { type = "bezier", points = { { 0.4, 0 }, { 1, 1 } } })

hl.animation({ leaf = "windows", enabled = true, speed = 3.0, bezier = "nocturneOut" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 2.6, bezier = "nocturneOut", style = "popin 94%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.5, bezier = "nocturneIn", style = "popin 98%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.8, bezier = "nocturneOut" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.5, bezier = "nocturneIn" })
hl.animation({ leaf = "border", enabled = true, speed = 1.6, bezier = "nocturneOut" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3.0, bezier = "nocturneOut", style = "slidefade 16%" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3.0, bezier = "nocturneOut", style = "slidefadevert 8%" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 1.8, bezier = "nocturneOut", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.2, bezier = "nocturneIn", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.8, bezier = "nocturneOut" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.2, bezier = "nocturneIn" })

-- Os componentes locais animam o cartão em QML, sem escalar o ecrã inteiro.
hl.layer_rule({ match = { namespace = "^omarchy-(dock-apps|menu|osd|emojis|clipboard)$" }, no_anim = true, animation = "none" })
-- As notificações nativas conservam o serviço original e recebem uma entrada discreta.
hl.layer_rule({ match = { namespace = "^omarchy-notifications$" }, no_anim = false, animation = "popin 98%" })

-- Reduz a transparência das janelas inativas, sem substituir regras por app.
-- Carregado antes de OmaControl; as escolhas guardadas e os toggles têm prioridade.
hl.config({ decoration = { inactive_opacity = 1.0 } })

-- Nocturne Glass: contraste estável no conteúdo, vidro apenas no chrome.
hl.config({ decoration = {
  rounding = 18,
  rounding_power = 2.6,
  blur = { enabled = true, size = 6, passes = 2, noise = 0.012, popups = true, popups_ignorealpha = 0.3 },
  shadow = { enabled = true, range = 24, render_power = 3 },
} })
hl.layer_rule({ match = { namespace = "^omacontrol$" }, blur = true, ignore_alpha = 0.3, no_anim = true })
-- Mesmo material no lançador e nos painéis; ignora a área transparente fora do cartão.
hl.layer_rule({ match = { namespace = "^omarchy-(dock-apps|bar|menu|keyboard-panel|osd|emojis|clipboard|notifications)$" }, blur = true, blur_popups = true, ignore_alpha = 0.3 })
