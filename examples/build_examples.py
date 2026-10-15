"""Generate public textbook-level terminology and fictional review documents."""

import json
from pathlib import Path

DATA = {
    "water-treatment": """硬度|hardness||Calcium and magnesium contribution.
碱度|alkalinity||Acid-neutralizing capacity of water.
浊度|turbidity||Optical cloudiness from suspended matter.
电导率|conductivity|EC|Ability to carry electric current.
溶解氧|dissolved oxygen|DO|Oxygen present in aqueous solution.
总溶解固体|total dissolved solids|TDS|Combined dissolved material concentration.
悬浮固体|suspended solids|SS|Particles retained by specified filtration.
混凝|coagulation||Destabilization of suspended colloids.
絮凝|flocculation||Aggregation into larger flocs.
沉淀|sedimentation||Particle separation through settling.
过滤|filtration||Separation through a porous medium.
吸附|adsorption||Accumulation at a surface.
离子交换|ion exchange|IX|Exchange of ions between phases.
反渗透|reverse osmosis|RO|Pressure-driven membrane salt separation.
超滤|ultrafiltration|UF|Membrane separation of larger solutes.
纳滤|nanofiltration|NF|Membrane separation between UF and RO.
微滤|microfiltration|MF|Membrane removal of fine particles.
脱盐|desalination||Removal of dissolved salts.
消毒|disinfection||Inactivation of target microorganisms.
氯化消毒|chlorination||Disinfection using chlorine species.
臭氧氧化|ozonation||Treatment using dissolved ozone.
活性炭|activated carbon|AC|Porous carbon used for adsorption.
膜|membrane||Selective barrier between fluid regions.
树脂|resin||Polymeric material with exchange sites.
盐水|brine||Water containing concentrated dissolved salts.
反洗|backwash||Reverse-flow cleaning of filter media.
再生|regeneration||Restoration of exchange capacity.
产水|permeate||Fluid passing through a membrane.
浓水|concentrate||Retained, concentrated membrane feed fraction.
回收率|recovery||Product flow divided by feed.""",
    "power-chemistry": """给水|feedwater||Water supplied to a steam generator.
凝结水|condensate||Water formed by steam condensation.
锅炉水|boiler water||Liquid water within the boiler.
蒸汽|steam||Water in its gaseous state.
除氧器|deaerator||Equipment removing dissolved gases.
全挥发处理|all-volatile treatment|AVT|Chemistry using volatile conditioning agents.
加氧处理|oxygenated treatment|OT|Conditioning using controlled oxygen addition.
磷酸盐处理|phosphate treatment|PT|Boiler conditioning using phosphate chemistry.
苛性处理|caustic treatment|CT|Boiler conditioning using sodium hydroxide.
阳离子电导率|conductivity after cation exchange|CACE|Conductivity measured after cation exchange.
脱气电导率|degassed conductivity after cation exchange|DCACE|CACE measured after gas removal.
氢电导率|cation conductivity||Another label for CACE measurement.
二氧化硅|silica||Silicon dioxide in relevant forms.
钠|sodium|Na|Alkali-metal element and cation.
氯离子|chloride|Cl|Negatively charged chlorine ion.
磷酸盐|phosphate||Salts or ions of phosphoric acid.
氨|ammonia|NH3|Volatile nitrogen-hydrogen compound.
联氨|hydrazine|N2H4|Nitrogen-hydrogen reducing compound.
酸碱度|pH||Negative logarithm of hydrogen activity.
腐蚀|corrosion||Material degradation by environmental reaction.
流动加速腐蚀|flow-accelerated corrosion|FAC|Flow-enhanced dissolution of protective oxide.
点蚀|pitting corrosion||Localized corrosion forming cavities.
结垢|scaling||Deposition of sparingly soluble solids.
沉积物|deposit||Material accumulated on a surface.
排污|blowdown||Removal of concentrated circulating water.
机械携带|mechanical carryover||Water droplets transported with steam.
蒸汽纯度|steam purity||Extent of contaminants in steam.
凝结水精处理|condensate polishing||Removal of condensate impurities.
磁铁矿|magnetite||Iron oxide with formula Fe3O4.
补给水|makeup water||Water replacing system losses.""",
    "it": """应用程序接口|application programming interface|API|Contract for interacting software components.
超文本传输协议|Hypertext Transfer Protocol|HTTP|Protocol for exchanging web resources.
域名系统|Domain Name System|DNS|System mapping names to records.
统一资源定位符|Uniform Resource Locator|URL|Address identifying a resource location.
超文本标记语言|HyperText Markup Language|HTML|Markup describing web document structure.
层叠样式表|Cascading Style Sheets|CSS|Rules controlling document presentation.
文档对象模型|Document Object Model|DOM|Object representation of a document.
缓存|cache||Storage reused for faster access.
数据库|database|DB|Organized persistent collection of data.
结构化查询语言|Structured Query Language|SQL|Language for relational data operations.
事务|transaction||Operations treated as one logical unit.
索引|index||Structure supporting faster data lookup.
主键|primary key||Identifier unique within a table.
外键|foreign key||Reference to another table key.
序列化|serialization||Encoding structured data for transfer.
字符编码|character encoding||Mapping between characters and bytes.
统一码|Unicode||Standard assigning characters code points.
加密|encryption||Transformation using a cryptographic key.
哈希|hash||Fixed-size digest of input data.
身份验证|authentication||Verification of a claimed identity.
授权|authorization||Decision about permitted actions.
跨源资源共享|Cross-Origin Resource Sharing|CORS|Browser mechanism permitting selected cross-origin requests.
跨站脚本|cross-site scripting|XSS|Injection of script into trusted content.
内容安全策略|Content Security Policy|CSP|Policy restricting browser content sources.
传输层安全|Transport Layer Security|TLS|Protocol protecting transport confidentiality and integrity.
异步|asynchronous||Execution without waiting for immediate completion.
回调|callback||Function invoked after another operation.
闭包|closure||Function retaining its lexical environment.
幂等|idempotence||Repeated operation with unchanged resulting effect.
异常|exception||Signal interrupting ordinary program control.""",
}
SOURCES = {
    "water-treatment": "https://www.usgs.gov/water-science-school/science/water-science-glossary",
    "power-chemistry": "https://iapws.org/techguide/Instrumentation-2015.pdf",
    "it": "https://developer.mozilla.org/en-US/docs/Glossary",
}
rows = []
for domain, lines in DATA.items():
    for index, line in enumerate(lines.splitlines(), 1):
        zh, en, abbr, definition = line.split("|")
        rows.append(
            {
                "id": f"{domain}-{index:02d}",
                "domain": domain,
                "zh": zh,
                "en": en,
                "abbr": abbr,
                "definition_zh": definition,
                "definition_en": definition,
                "synonyms_zh": [],
                "synonyms_en": [],
                "forbidden": [],
                "notes": "Teaching entry; translations and concise explanations are editorial, not an official terminology standard. Definition fields are English in this edition.",
                "source": SOURCES[domain],
                "status": "approved",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        )
aliases = {
    "hardness": "water hardness",
    "conductivity": "electrical conductivity",
    "reverse osmosis": "reverse-osmosis process",
    "dissolved oxygen": "oxygen in solution",
    "activated carbon": "activated charcoal",
}
for row in rows:
    if row["en"] in aliases:
        row["synonyms_en"] = [aliases[row["en"]]]
    if row["en"] == "deaerator":
        row["forbidden"] = [{"lang": "zh", "text": "除空气器"}]
    if row["en"] == "reverse osmosis":
        row["forbidden"] = [{"lang": "en", "text": "inverse osmosis"}]
    if row["en"] == "conductivity":
        row["forbidden"] = [{"lang": "en", "text": "electric conductibility"}]
root = Path(__file__).parent
(root / "terms.json").write_text(
    json.dumps({"schema_version": 1, "terms": rows}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
(root / "review.md").write_text(
    """# Fictional terminology review

The hardness and water hardness values refer to one concept.
The conductivity and electrical conductivity values refer to one concept.
The reverse osmosis and reverse-osmosis process labels refer to one concept.
The dissolved oxygen and oxygen in solution labels refer to one concept.
The activated carbon and activated charcoal labels refer to one concept.
The phrase inverse osmosis is deprecated in this library.
The phrase electric conductibility is deprecated in this library.
The fictional label 除空气器 is deprecated in this library.
""",
    encoding="utf-8",
)
(root / "clean.md").write_text(
    "Hardness, conductivity, reverse osmosis, dissolved oxygen and activated carbon.\n",
    encoding="utf-8",
)
(root / "pair.csv").write_text(
    "zh,en\n反渗透,reverse osmosis\n除氧器,unrelated equipment\n", encoding="utf-8"
)
(root / "config.toml").write_text(
    '[gloss]\ndata_dir = "./data/example"\ntimezone = "Asia/Shanghai"\n'
)
print(f"Generated {len(rows)} terms across {len(DATA)} domains")
