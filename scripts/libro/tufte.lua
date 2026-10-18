--[[
Filtro pandoc -> tufte-latex.

  ::: nota / ::: pendiente / ::: caption  -> \marginnote{...}
      (se cuelga del párrafo anterior; si no hay, del siguiente)
  Figure                                  -> figure de tufte (caption al margen)
  CodeBlock                               -> Verbatim a ancho completo (fullwidth)
]]

local function latex(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), "latex")
end

local function margin_note(div)
  local body = latex(div.content):gsub("%s+$", "")
  if div.classes:includes("pendiente") then
    body = "\\itshape " .. body
  end
  return pandoc.RawInline("latex", "\\marginnote{" .. body .. "}")
end

local NOTE = { nota = true, pendiente = true, caption = true }

local function is_note(b)
  if b.t ~= "Div" then return false end
  for _, c in ipairs(b.classes) do
    if NOTE[c] then return true end
  end
  return false
end

-- Nota al margen: anclarla a un párrafo vecino, así no deja un renglón vacío.
local function attach_notes(blocks)
  local out, pending = pandoc.List(), {}
  for _, b in ipairs(blocks) do
    if is_note(b) then
      local prev = out[#out]
      if prev and prev.t == "Para" then
        prev.content:insert(margin_note(b))
      else
        table.insert(pending, margin_note(b))
      end
    else
      if #pending > 0 and b.t == "Para" then
        for k = #pending, 1, -1 do b.content:insert(1, pending[k]) end
        pending = {}
      end
      out:insert(b)
    end
  end
  for _, n in ipairs(pending) do out:insert(pandoc.Para({ n })) end
  return out
end

local function figure(fig)
  local src
  fig:walk({ Image = function(img) src = img.src end })
  if not src then return nil end
  local cap = latex(fig.caption.long):gsub("%s+$", "")
  return pandoc.RawBlock("latex", table.concat({
    "\\begin{figure}[!htbp]",
    "\\centering",
    "\\includegraphics[width=\\linewidth,height=0.42\\textheight,keepaspectratio]{" .. src .. "}",
    "\\caption{" .. cap .. "}",
    "\\end{figure}",
  }, "\n"))
end

local function code(cb)
  return pandoc.RawBlock("latex",
    "\\begin{fullwidth}\n\\begin{Verbatim}[fontsize=\\footnotesize]\n"
    .. cb.text .. "\n\\end{Verbatim}\n\\end{fullwidth}")
end

return {
  { Figure = figure, CodeBlock = code },
  { Blocks = attach_notes },
}
