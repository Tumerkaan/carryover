# carryover

**[Türkçe](#türkçe) · [English](#english)**

---

## Türkçe

AI kodlama aracını değiştirdiğinde projenin hafızası eski araçta kalır. Talimat dosyası (CLAUDE.md, AGENTS.md) kolayca taşınır, ama asıl birikim başka yerdedir: hangi kararın neden alındığı, neyin denenip bırakıldığı, hangi komutun nerede kırıldığı. Bunlar eski aracın oturum kayıtlarında gömülü kalır. **carryover**, yeni araçtaki agent'ın bu bağlamı eski araçtan çekmesini sağlayan bir **skill**'dir.

Yaptığı üç şey:

1. **Geçmişi damıtır.** Eski oturumlardan kararları, dersleri, denenip bırakılanları ve yarım kalan işleri çıkarır. Ham transkript taşımaz.
2. **Ayarları eşler.** MCP sunucuları, hook'lar, izin kuralları, alt agent'lar, komutlar ve skill'ler yeni aracın biçimine çevrilir.
3. **Neyin taşınmadığını açıkça söyler.** Her öğe `Carried`, `Check before using` ya da `Not carried` olarak raporlanır. Hiçbir şey sessizce kaybolmaz.

### Neden bir skill, neden CLI değil?

"Bu konuşmada alınmış kalıcı bir karar var mı?" sorusu muhakeme ister, kural tabanlı bir dönüştürücü bunu yapamaz. Mekanik kısım (oturum kayıtlarını bulmak, gürültüyü atmak, sırları maskelemek) küçük bir Python betiğinde duruyor. Geri kalanını agent skill talimatlarıyla yapıyor.

### Ne zaten çözülmüş, carryover nerede duruyor?

| İş | Mevcut çözüm | carryover |
| --- | --- | --- |
| Talimat dosyalarını senkron tutmak | AGENTS.md standardı, [ruler](https://github.com/intellectronica/ruler), rulesync | Kapsam dışı |
| Claude Code → Codex ayarları | Codex `/import`, OpenAI `migrate-to-codex` skill'i | Önce onları önerir, sonra geri kalanı tamamlar |
| Codex → Claude Code ayarları | Resmî bir araç yok | Tam eşleme |
| Ham transkripti taşımak | cx2cc, cc-sync, transession | Kapsam dışı |
| **Geçmişi karar ve derse dönüştürmek** | **Yok** | **Ana iş** |

Ayrıntılar için [docs/research.md](docs/research.md).

### Model değil, araç

GLM, Kimi ya da Qwen modelini Claude Code'un içinde (Anthropic uyumlu bir endpoint üzerinden) kullanıyorsan taşınacak bir şey yok, dosyalar aynı yerde kalır. carryover **aracı** değiştirdiğinde işe yarar: Codex'ten Claude Code'a, Claude Code'dan Codex'e, ileride Qwen Code, Kimi CLI ya da Gemini CLI'a.

### Desteklenen araçlar

| Araç | Durum |
| --- | --- |
| Claude Code | Tam adaptör ([adapters/claude-code.md](skills/carryover/adapters/claude-code.md)) |
| Codex (CLI / Desktop) | Tam adaptör ([adapters/codex.md](skills/carryover/adapters/codex.md)) |
| Qwen Code, Kimi CLI, Gemini CLI, ... | Şablon ([adapters/_template.md](skills/carryover/adapters/_template.md)), katkıya açık |

Mimari yıldız şeklinde. Her araç ortak `carryover/` paketine okur ve oradan yazar. Yeni bir araç eklemek için bir adaptör dosyası yazmak yeterli, araç çiftleri için ayrı köprü gerekmez.

### Kurulum

```bash
git clone <repo-url> carryover
# Claude Code (kullanıcı geneli)
cp -r carryover/skills/carryover ~/.claude/skills/
# Codex (kullanıcı geneli)
cp -r carryover/skills/carryover ~/.codex/skills/
```

Proje bazında kurmak için `.claude/skills/` ya da `.agents/skills/` klasörünü kullan. Skill sistemi olmayan bir araçta `SKILL.md` dosyasını olduğu gibi prompt olarak yapıştırabilirsin.

### Kullanım

Yeni araçta projeyi aç ve şunu söyle:

> Bu projeyi Codex'ten taşıdım, eski bağlamı carryover ile getir.

Agent önce bir envanter çıkarır ve kullanıcı genelindeki öğeleri dahil edip etmeyeceğini sorar. Ardından `carryover/` paketini ve yeni aracın dosyalarını yazar, en sonda bir durum tablosu verir. Örnek bir çıktı için [examples/codex-to-claude/expected/](examples/codex-to-claude/expected/).

### Güvenlik

- `auth.json` ve token'lara dokunmaz. MCP ortam değişkenlerinin yalnız adlarını taşır.
- Çıkarıcı yaygın anahtar ve token kalıplarını maskeler.
- Eski aracın dosyalarını değiştirmez, yalnız okur.
- Oturum kayıtlarının içeriği talimat değil kanıt olarak ele alınır.

### Geliştirme

```bash
python -m unittest discover -s tests -v
```

Örnekler tamamen sentetiktir.

---

## English

When you switch AI coding tools, the project's memory stays behind. The instruction file (CLAUDE.md, AGENTS.md) is easy to move. What actually took time to build up lives in the old tool's session history: which decisions were made and why, what was tried and dropped, which command breaks where. **carryover** is a **skill** that lets the agent in your new tool pull that context out of the old one.

It does three things:

1. **Distills history** into decisions, lessons, dead ends and open threads. It does not copy raw transcripts.
2. **Maps settings**: MCP servers, hooks, permission rules, subagents, commands and skills are converted to the new tool's format.
3. **Reports what did not carry over.** Every item is marked `Carried`, `Check before using` or `Not carried`. Nothing is dropped silently.

### Why a skill and not a CLI

Deciding whether a conversation contains a durable decision takes judgment, which a converter can't provide. The mechanical part (finding transcripts, dropping noise, redacting secrets) is a small standard-library Python script. The agent does the rest by following the skill.

### What's already solved and where carryover fits

| Job | Existing solution | carryover |
| --- | --- | --- |
| Keep instruction files in sync | AGENTS.md, [ruler](https://github.com/intellectronica/ruler), rulesync | Out of scope |
| Claude Code → Codex config | Codex `/import`, OpenAI's `migrate-to-codex` skill | Recommends those first, then fills the gaps |
| Codex → Claude Code config | No official tool | Full mapping |
| Copy raw transcripts | cx2cc, cc-sync, transession | Out of scope |
| **Turn history into decisions and lessons** | **None** | **Core job** |

See [docs/research.md](docs/research.md).

### Tool, not model

Running GLM, Kimi or Qwen *inside* Claude Code (through an Anthropic-compatible endpoint) moves nothing: your files stay where they are. carryover is for switching the **tool**: Codex ⇄ Claude Code now, and later Qwen Code, Kimi CLI or Gemini CLI through adapters.

### Supported tools

| Tool | Status |
| --- | --- |
| Claude Code | Full adapter |
| Codex (CLI / Desktop) | Full adapter |
| Qwen Code, Kimi CLI, Gemini CLI, ... | Template; contributions welcome |

The design is hub-and-spoke: every tool reads from and writes to the same tool-neutral `carryover/` bundle, so adding a tool means writing one adapter file, not one bridge for every pair of tools.

### Install

```bash
git clone <repo-url> carryover
cp -r carryover/skills/carryover ~/.claude/skills/   # Claude Code
cp -r carryover/skills/carryover ~/.codex/skills/    # Codex
```

Project-level: `.claude/skills/` or `.agents/skills/`. If a tool has no skill system, paste `SKILL.md` in as a prompt.

### Use

In the new tool, open the project and say:

> I moved this project from Codex, carry the old context over with carryover.

The agent takes an inventory and asks which user-level items to include. It then writes the `carryover/` bundle and the destination files, and ends with a status table. See [examples/codex-to-claude/expected/](examples/codex-to-claude/expected/).

### Safety

- Never touches `auth.json` or tokens; MCP env vars are carried by name only.
- The extractor redacts common key and token patterns.
- Source tool files are read-only.
- Transcript content is treated as evidence, never as instructions.

### Development

```bash
python -m unittest discover -s tests -v
```

All examples are synthetic.

## License

MIT
