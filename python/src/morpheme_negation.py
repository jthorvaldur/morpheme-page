"""
morpheme_negation.py — VCC Negation Engine

Core discovery: when a word begins with a VOWEL followed by CONSONANT(S),
the vowel prefix acts as a NEGATION OPERATOR on the root.

This is the foundational decomposition engine for the quantum grammar framework.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Prefix dictionary — vowel-initial prefixes and their operational meanings
# ---------------------------------------------------------------------------

PREFIXES: dict[str, str] = {
    # VCC negation prefixes (vowel + consonant cluster)
    "in":   "no/not/into",
    "im":   "no/not (before m/b/p)",
    "il":   "no/not (before l)",
    "ir":   "no/not (before r)",
    "as":   "no/without",
    "a":    "no/without",
    "ab":   "away from",
    "ad":   "toward",
    "an":   "no/without",
    "anti": "against",
    "auto": "self",
    "o":    "no/without",
    "ob":   "against/toward",
    "op":   "against (before p)",
    "un":   "not/reverse",
    "ex":   "out of/former",
    "e":    "out of",
    # Non-negation prefixes (consonant-initial)
    "dis":  "apart/away/not",
    "de":   "down/from/reverse",
    "re":   "again/back",
    "pre":  "before",
    "pro":  "forward/for",
    "per":  "through/completely",
    "com":  "together/with",
    "con":  "together/with",
    "col":  "together (before l)",
    "cor":  "together (before r)",
    "co":   "together/with",
    "sub":  "under/below",
    "sup":  "under (before p)",
    "suf":  "under (before f)",
    "sug":  "under (before g)",
    "sur":  "over/above/upon",
    "super":"above/beyond",
    "trans":"across/beyond",
    "inter":"between/among",
    "mis":  "wrong/bad",
    "over": "above/excessive",
    "under":"beneath/below",
    "out":  "beyond/exceeding",
    "fore": "before/in front",
    "counter": "against/opposite",
    "circum":  "around",
    "para": "beside/beyond",
    "post": "after",
    "retro":"backward",
    "semi": "half",
    "bi":   "two",
    "tri":  "three",
    "multi":"many",
    "poly": "many",
    "mono": "one/single",
    "uni":  "one",
    "non":  "not",
    "mal":  "bad/evil",
    "bene": "good/well",
}

# ---------------------------------------------------------------------------
# Root dictionary — Latin/OE roots with core meanings (100+ entries)
# ---------------------------------------------------------------------------

ROOTS: dict[str, str] = {
    # ----- Action / Motion -----
    "act":     "do/drive",
    "ag":      "do/drive/lead",
    "ced":     "go/yield",
    "cede":    "go/yield",
    "cess":    "go/yield",
    "cur":     "run/flow",
    "curr":    "run/flow",
    "curs":    "run/flow",
    "duc":     "lead",
    "duct":    "lead",
    "fer":     "carry/bear",
    "flect":   "bend",
    "flex":    "bend",
    "flu":     "flow",
    "flux":    "flow",
    "grad":    "step/walk",
    "gree":    "step/grade",
    "gress":   "step/walk",
    "it":      "go",
    "ject":    "throw",
    "lev":     "lift/raise",
    "migr":    "move/wander",
    "mit":     "send",
    "miss":    "send",
    "mob":     "move",
    "mot":     "move",
    "mov":     "move",
    "pass":    "step/go through",
    "ped":     "foot",
    "pel":     "push/drive",
    "pend":    "hang/weigh/pay",
    "pens":    "hang/weigh/pay",
    "port":    "carry/gate/harbor",
    "pos":     "place/put",
    "pose":    "place/put",
    "press":   "push/squeeze",
    "puls":    "push/drive",
    "rupt":    "break",
    "sal":     "jump/salt",
    "scend":   "climb",
    "sequ":    "follow",
    "sist":    "stand/place",
    "sta":     "stand",
    "stand":   "stand/endure",
    "stit":    "stand/place",
    "sume":    "take/sum up",
    "tain":    "hold/keep",
    "ten":     "hold/stretch",
    "tend":    "stretch/reach",
    "tens":    "stretch",
    "tent":    "stretch/hold",
    "tort":    "twist",
    "tract":   "pull/draw",
    "vad":     "go",
    "ven":     "come",
    "vent":    "come",
    "ver":     "turn",
    "vers":    "turn",
    "vert":    "turn",
    "vi":      "way/road",
    "volve":   "roll/turn",
    # ----- Perception / Mind -----
    "aud":     "hear",
    "cern":    "separate/judge",
    "cogn":    "know",
    "gnos":    "know",
    "mem":     "remember/mindful",
    "ment":    "mind/think",
    "mon":     "warn/remind",
    "not":     "mark/know",
    "phen":    "show/appear",
    "put":     "think/reckon",
    "sci":     "know",
    "sent":    "feel/think",
    "sens":    "feel/perceive",
    "spec":    "look/see",
    "spect":   "look/see",
    "spic":    "look/see",
    "vid":     "see",
    "vis":     "see",
    "voc":     "call/voice",
    "voke":    "call",
    # ----- Communication / Writing -----
    "clam":    "cry out/shout",
    "claim":   "cry out/demand",
    "clar":    "clear",
    "dict":    "say/speak/declare",
    "doc":     "teach",
    "fa":      "speak",
    "fess":    "speak/declare",
    "graph":   "write/draw",
    "lect":    "read/choose",
    "leg":     "read/law/choose",
    "ling":    "tongue/language",
    "loc":     "speak/place",
    "log":     "word/reason/study",
    "loqu":    "speak",
    "nounce":  "report/declare",
    "nunci":   "report/declare",
    "or":      "speak/pray",
    "ora":     "speak/pray",
    "phor":    "carry (meaning)",
    "pin":     "write/fasten",
    "quir":    "seek/ask",
    "quer":    "seek/ask",
    "quest":   "seek/ask",
    "scribe":  "write",
    "script":  "write",
    "sign":    "mark/seal",
    "verb":    "word",
    # ----- Construction / Form -----
    "arch":    "chief/rule/first",
    "clos":    "close/shut",
    "clude":   "close/shut",
    "clus":    "close/shut",
    "cre":     "make/grow",
    "creat":   "make/grow",
    "fac":     "make/do",
    "fact":    "make/do",
    "fect":    "make/do",
    "fic":     "make/do/fiction",
    "fig":     "form/shape",
    "fin":     "end/limit/boundary",
    "form":    "shape/structure",
    "found":   "bottom/base/pour",
    "fund":    "bottom/base",
    "gen":     "birth/kind/origin",
    "ple":     "fill",
    "plet":    "fill",
    "pon":     "place/put",
    "sec":     "cut",
    "sect":    "cut",
    "serv":    "keep/save/serve",
    "solv":    "loosen/free",
    "solut":   "loosen/free",
    "string":  "bind/draw tight",
    "strict":  "bind/draw tight",
    "struct":  "build/arrange",
    "tect":    "cover/build",
    "test":    "witness/prove",
    # ----- Power / Law / Authority -----
    "archy":   "rule/government",
    "civ":     "citizen",
    "corp":    "body/dead body",
    "cracy":   "rule/power",
    "crat":    "ruler",
    "dom":     "rule/judgment",
    "domin":   "master/lord",
    "forc":    "strong",
    "fort":    "strong",
    "govern":  "steer a ship",
    "jud":     "judge/law",
    "jur":     "law/swear",
    "juris":   "law/right",
    "just":    "law/right",
    "liber":   "free",
    "lig":     "bind/choose",
    "magist":  "master/great",
    "mand":    "order/command",
    "mort":    "death",
    "nomin":   "name",
    "norm":    "rule/standard",
    "ord":     "order/rank",
    "poten":   "power/able",
    "reg":     "king/rule/straight",
    "reign":   "rule/kingdom",
    "rog":     "ask/propose",
    "sanct":   "holy/sacred",
    "sover":   "above/supreme",
    "stat":    "stand/state/fixed",
    "statu":   "stand/set up/fixed",
    "terr":    "land/earth",
    "torn":    "tear/twist",
    "tribut":  "give/assign",
    "vinc":    "conquer",
    "vict":    "conquer",
    # ----- Value / Commerce -----
    "capit":   "head/chief/stock",
    "count":   "reckon/calculate",
    "cred":    "believe/trust",
    "deb":     "owe",
    "equ":     "equal/fair",
    "gage":    "pledge/grip",
    "merc":    "trade/reward",
    "pric":    "value/worth",
    "prop":    "own/proper",
    "proper":  "own/one's own",
    "sec":     "cut/separate",
    "sure":    "certain/fixed/safe",
    "val":     "worth/strong",
    "valu":    "worth",
    # ----- Life / Body / Nature -----
    "anim":    "life/breath/spirit",
    "bio":     "life",
    "nat":     "born/birth",
    "son":     "sound",
    "spir":    "breathe/spirit",
    "vit":     "life",
    "viv":     "live/alive",
    # ----- Place / Boundary -----
    "bound":   "limit/border",
    "loc":     "place",
    "termin":  "end/boundary",
    "limin":   "threshold",
    "fin":     "end/limit",
}

# ---------------------------------------------------------------------------
# Suffix dictionary — endings and their operational meanings
# ---------------------------------------------------------------------------

SUFFIXES: dict[str, str] = {
    "tion":  "contract/action/process",
    "sion":  "contract/action/process",
    "ion":   "contract/action",
    "ment":  "mind/state/result of action",
    "ence":  "now-state/quality",
    "ance":  "now-state/quality",
    "ency":  "now-state/quality",
    "ancy":  "now-state/quality",
    "ity":   "quality/state",
    "ty":    "quality/state",
    "ness":  "state/condition",
    "ous":   "full of/having quality",
    "ious":  "full of/having quality",
    "eous":  "full of/having quality",
    "ive":   "tending to/having nature of",
    "ative": "tending to/relating to",
    "itive": "tending to/relating to",
    "able":  "capable of/worthy of",
    "ible":  "capable of/worthy of",
    "al":    "pertaining to/of the kind",
    "ial":   "pertaining to/of the kind",
    "ual":   "pertaining to/of the kind",
    "ing":   "now-time/living/present action",
    "ed":    "past/dead time/completed",
    "er":    "one who/that which",
    "or":    "one who/that which",
    "ar":    "one who/relating to",
    "ist":   "one who practices",
    "ant":   "one who/performing",
    "ent":   "one who/performing",
    "ate":   "to make/through/state",
    "ize":   "to make/to become",
    "ise":   "to make/to become",
    "fy":    "to make/to cause",
    "ify":   "to make/to cause",
    "en":    "to make/made of",
    "ure":   "act/process/result",
    "ture":  "act/process/result",
    "age":   "act/state/collection",
    "dom":   "domain/state/condition",
    "ship":  "state/office/skill",
    "hood":  "state/condition/group",
    "ward":  "direction/toward",
    "wise":  "manner/direction",
    "ly":    "in the manner of",
    "ful":   "full of",
    "less":  "without",
    "ment":  "mind/state/result of action",
    "ic":    "pertaining to/having nature of",
    "ical":  "pertaining to/having nature of",
    "ous":   "full of/characterized by",
    "ory":   "place of/serving for",
    "ary":   "relating to/place of",
    "ery":   "place of/art of/collection",
}

# ---------------------------------------------------------------------------
# Vowels and consonants for VCC detection
# ---------------------------------------------------------------------------

VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")

# ---------------------------------------------------------------------------
# VCC negation prefixes — the subset of prefixes that perform meaning-inversion
# These are vowel-initial prefixes that NEGATE the root.
# ---------------------------------------------------------------------------

VCC_NEGATION_PREFIXES: dict[str, str] = {
    "in":  "no/not",
    "im":  "no/not",
    "il":  "no/not",
    "ir":  "no/not",
    "a":   "no/without",
    "an":  "no/without",
    "as":  "no/without",
    "ab":  "away from",
    "o":   "no/without",
    "ob":  "against",
    "un":  "not/reverse",
    "ex":  "out of",
    "e":   "out of",
}


# ---------------------------------------------------------------------------
# Known decompositions — pre-analyzed words (50+ entries)
# ---------------------------------------------------------------------------

KNOWN_DECOMPOSITIONS: dict[str, dict] = {
    "insurance": {
        "word": "insurance",
        "prefix": "in",
        "prefix_meaning": "no/not",
        "root": "sure",
        "root_meaning": "certain/fixed/safe",
        "suffix": "ance",
        "suffix_meaning": "now-state/quality",
        "is_negated": True,
        "true_meaning": "NO certainty/NO safety — the state of having no surety",
        "apparent_meaning": "protection or coverage against loss",
    },
    "assume": {
        "word": "assume",
        "prefix": "as",
        "prefix_meaning": "no/without",
        "root": "sume",
        "root_meaning": "take/sum up",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "CANNOT sum up — without the ability to take/reckon",
        "apparent_meaning": "to take for granted or suppose",
    },
    "opinion": {
        "word": "opinion",
        "prefix": "o",
        "prefix_meaning": "no/without",
        "root": "pin",
        "root_meaning": "write/fasten",
        "suffix": "ion",
        "suffix_meaning": "contract/action",
        "is_negated": True,
        "true_meaning": "NO written contract — unfastened/unwritten claim",
        "apparent_meaning": "a personal view or belief",
    },
    "corporation": {
        "word": "corporation",
        "prefix": "",
        "prefix_meaning": "",
        "root": "corp",
        "root_meaning": "body/dead body",
        "suffix": "tion",
        "suffix_meaning": "contract/action/process",
        "is_negated": False,
        "true_meaning": "dead-body-contract — a dead entity speaking through contract",
        "apparent_meaning": "a business entity or organization",
    },
    "agreement": {
        "word": "agreement",
        "prefix": "a",
        "prefix_meaning": "no/without",
        "root": "gree",
        "root_meaning": "step/grade",
        "suffix": "ment",
        "suffix_meaning": "mind/state/result of action",
        "is_negated": True,
        "true_meaning": "NO step of mind — without graded mental assent",
        "apparent_meaning": "a mutual understanding or arrangement",
    },
    "government": {
        "word": "government",
        "prefix": "",
        "prefix_meaning": "",
        "root": "govern",
        "root_meaning": "steer a ship",
        "suffix": "ment",
        "suffix_meaning": "mind/state/result of action",
        "is_negated": False,
        "true_meaning": "steering of the mind — maritime piloting of thought",
        "apparent_meaning": "the system of administration and authority",
    },
    "mortgage": {
        "word": "mortgage",
        "prefix": "",
        "prefix_meaning": "",
        "root": "mort",
        "root_meaning": "death",
        "suffix": "age",
        "suffix_meaning": "act/state/collection",
        "is_negated": False,
        "true_meaning": "death-grip/death-pledge — a pledge unto death",
        "apparent_meaning": "a loan secured by real property",
    },
    "understand": {
        "word": "understand",
        "prefix": "under",
        "prefix_meaning": "beneath/below",
        "root": "stand",
        "root_meaning": "stand/endure",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "stand beneath / submit to authority — to stand under",
        "apparent_meaning": "to comprehend or grasp meaning",
    },
    "person": {
        "word": "person",
        "prefix": "per",
        "prefix_meaning": "through/completely",
        "root": "son",
        "root_meaning": "sound",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "through sound only — an entity of voice, not substance",
        "apparent_meaning": "a human being or individual",
    },
    "inform": {
        "word": "inform",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "form",
        "root_meaning": "shape/structure",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "NO form / put into form — to shape or to negate shape",
        "apparent_meaning": "to tell, communicate, or educate",
    },
    "represent": {
        "word": "represent",
        "prefix": "re",
        "prefix_meaning": "again/back",
        "root": "present",
        "root_meaning": "being here/now-time gift",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "present again — a COPY, not the original thing",
        "apparent_meaning": "to speak for or act on behalf of another",
    },
    "attorney": {
        "word": "attorney",
        "prefix": "at",
        "prefix_meaning": "to/toward",
        "root": "torn",
        "root_meaning": "tear/twist",
        "suffix": "ey",
        "suffix_meaning": "one who (agent)",
        "is_negated": False,
        "true_meaning": "one who tears apart — an agent of tearing/division",
        "apparent_meaning": "a lawyer or legal representative",
    },
    "register": {
        "word": "register",
        "prefix": "",
        "prefix_meaning": "",
        "root": "reg",
        "root_meaning": "king/rule/straight",
        "suffix": "er",
        "suffix_meaning": "one who/that which",
        "is_negated": False,
        "true_meaning": "of the king — to place under the king's rule/record",
        "apparent_meaning": "to officially record or enroll",
    },
    "certificate": {
        "word": "certificate",
        "prefix": "",
        "prefix_meaning": "",
        "root": "cert",
        "root_meaning": "certain/sure",
        "suffix": "ate",
        "suffix_meaning": "to make/through/state",
        "is_negated": False,
        "true_meaning": "made certain through process — certainty manufactured",
        "apparent_meaning": "an official document of verification",
    },
    "license": {
        "word": "license",
        "prefix": "",
        "prefix_meaning": "",
        "root": "lic",
        "root_meaning": "permission/be allowed",
        "suffix": "ense",
        "suffix_meaning": "now-state/quality",
        "is_negated": False,
        "true_meaning": "permission to do the otherwise illegal — state-granted allowance",
        "apparent_meaning": "an official permit or authorization",
    },
    "science": {
        "word": "science",
        "prefix": "",
        "prefix_meaning": "",
        "root": "sci",
        "root_meaning": "know",
        "suffix": "ence",
        "suffix_meaning": "now-state/quality",
        "is_negated": False,
        "true_meaning": "the now-state of knowing — knowledge in present time",
        "apparent_meaning": "systematic study of the natural world",
    },
    "scientific": {
        "word": "scientific",
        "prefix": "",
        "prefix_meaning": "",
        "root": "sci",
        "root_meaning": "know",
        "suffix": "ic",
        "suffix_meaning": "pertaining to/having nature of",
        "is_negated": False,
        "true_meaning": "know-it-is-fiction — SCI (know) + ENTI (entity/it) + FIC (fiction/make)",
        "apparent_meaning": "based on or characterized by science",
    },
    "appear": {
        "word": "appear",
        "prefix": "a",
        "prefix_meaning": "no/without",
        "root": "pear",
        "root_meaning": "be visible/come forth",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "without true presence — to seem without being",
        "apparent_meaning": "to become visible or come into view",
    },
    "court": {
        "word": "court",
        "prefix": "",
        "prefix_meaning": "",
        "root": "court",
        "root_meaning": "enclosed yard/dry dock (Latin cohors)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "enclosed yard / dry dock — where vessels are inspected",
        "apparent_meaning": "a place where justice is administered",
    },
    "current": {
        "word": "current",
        "prefix": "",
        "prefix_meaning": "",
        "root": "cur",
        "root_meaning": "run/flow",
        "suffix": "ent",
        "suffix_meaning": "one who/performing",
        "is_negated": False,
        "true_meaning": "that which flows/runs — water current = money current",
        "apparent_meaning": "present time / flow of water or electricity",
    },
    "currency": {
        "word": "currency",
        "prefix": "",
        "prefix_meaning": "",
        "root": "cur",
        "root_meaning": "run/flow",
        "suffix": "ency",
        "suffix_meaning": "now-state/quality",
        "is_negated": False,
        "true_meaning": "the state of flowing — liquid value in maritime commerce",
        "apparent_meaning": "money or medium of exchange",
    },
    "bank": {
        "word": "bank",
        "prefix": "",
        "prefix_meaning": "",
        "root": "bank",
        "root_meaning": "edge/ridge/river bank",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "river bank — that which directs the flow of current/currency",
        "apparent_meaning": "a financial institution",
    },
    "capital": {
        "word": "capital",
        "prefix": "",
        "prefix_meaning": "",
        "root": "capit",
        "root_meaning": "head/chief/stock",
        "suffix": "al",
        "suffix_meaning": "pertaining to/of the kind",
        "is_negated": False,
        "true_meaning": "pertaining to the head — head-count, human stock/chattel",
        "apparent_meaning": "wealth, chief city, or uppercase letter",
    },
    "execute": {
        "word": "execute",
        "prefix": "ex",
        "prefix_meaning": "out of/from",
        "root": "sequ",
        "root_meaning": "follow",
        "suffix": "ute",
        "suffix_meaning": "act/process",
        "is_negated": False,
        "true_meaning": "to follow out / carry out — or to put to death",
        "apparent_meaning": "to carry out or perform; to put to death",
    },
    "sentence": {
        "word": "sentence",
        "prefix": "",
        "prefix_meaning": "",
        "root": "sent",
        "root_meaning": "feel/think",
        "suffix": "ence",
        "suffix_meaning": "now-state/quality",
        "is_negated": False,
        "true_meaning": "a thought/judgment AND a punishment — dual meaning by design",
        "apparent_meaning": "a grammatical unit; a judicial punishment",
    },
    "charge": {
        "word": "charge",
        "prefix": "",
        "prefix_meaning": "",
        "root": "charge",
        "root_meaning": "load/burden/cargo (Latin carricare)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "to load cargo onto a vessel — maritime cargo loading",
        "apparent_meaning": "an accusation; a fee; to load with energy",
    },
    "suit": {
        "word": "suit",
        "prefix": "",
        "prefix_meaning": "",
        "root": "suit",
        "root_meaning": "follow/pursue (Latin sequi via Old French)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "pursuit — a chase at sea / following a vessel",
        "apparent_meaning": "a legal proceeding; a set of clothes",
    },
    "bar": {
        "word": "bar",
        "prefix": "",
        "prefix_meaning": "",
        "root": "bar",
        "root_meaning": "barrier/rod/obstruction",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "barrier between land and sea jurisdiction — the BAR in court",
        "apparent_meaning": "a barrier; the legal profession; a drinking establishment",
    },
    "dock": {
        "word": "dock",
        "prefix": "",
        "prefix_meaning": "",
        "root": "dock",
        "root_meaning": "enclosed water for ships / to cut short",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "where vessels are berthed, inspected, and judged",
        "apparent_meaning": "a structure for mooring ships; the accused's place in court",
    },
    "deliver": {
        "word": "deliver",
        "prefix": "de",
        "prefix_meaning": "down/from/reverse",
        "root": "liver",
        "root_meaning": "free/release (Latin liberare)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "to release from — a dock-tor delivers cargo from the vessel",
        "apparent_meaning": "to carry and hand over; to give birth",
    },
    "berth": {
        "word": "berth",
        "prefix": "",
        "prefix_meaning": "",
        "root": "berth",
        "root_meaning": "place assigned to a ship at dock",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "a ship's assigned place — birth/berth certificate = dock assignment",
        "apparent_meaning": "a sleeping place on a ship; a mooring spot",
    },
    "vessel": {
        "word": "vessel",
        "prefix": "",
        "prefix_meaning": "",
        "root": "vessel",
        "root_meaning": "container/ship (Latin vascellum)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "a container for cargo — the body as a vessel in maritime law",
        "apparent_meaning": "a ship or boat; a container; a blood vessel",
    },
    "citizen": {
        "word": "citizen",
        "prefix": "",
        "prefix_meaning": "",
        "root": "civ",
        "root_meaning": "citizen/city",
        "suffix": "en",
        "suffix_meaning": "to make/made of",
        "is_negated": False,
        "true_meaning": "citizen-SHIP — membership in a vessel/corporate entity",
        "apparent_meaning": "a member of a state or nation",
    },
    "commerce": {
        "word": "commerce",
        "prefix": "com",
        "prefix_meaning": "together/with",
        "root": "merc",
        "root_meaning": "trade/reward",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "trading together — exchange in maritime jurisdiction",
        "apparent_meaning": "the activity of buying and selling",
    },
    "statute": {
        "word": "statute",
        "prefix": "",
        "prefix_meaning": "",
        "root": "statu",
        "root_meaning": "stand/set up/fixed",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "something set up / standing order — maritime ship's statute",
        "apparent_meaning": "a written law passed by a legislature",
    },
    "jurisdiction": {
        "word": "jurisdiction",
        "prefix": "",
        "prefix_meaning": "",
        "root": "juris",
        "root_meaning": "law/right",
        "suffix": "tion",
        "suffix_meaning": "contract/action/process",
        "is_negated": False,
        "true_meaning": "law-speak-contract — the authority to say the law",
        "apparent_meaning": "the official power to make legal decisions",
    },
    "contract": {
        "word": "contract",
        "prefix": "con",
        "prefix_meaning": "together/with",
        "root": "tract",
        "root_meaning": "pull/draw",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "pulled together — two parties drawn into binding agreement",
        "apparent_meaning": "a legally binding agreement",
    },
    "constitution": {
        "word": "constitution",
        "prefix": "con",
        "prefix_meaning": "together/with",
        "root": "stit",
        "root_meaning": "stand/place",
        "suffix": "tion",
        "suffix_meaning": "contract/action/process",
        "is_negated": False,
        "true_meaning": "standing together contract — the vessel's charter/articles",
        "apparent_meaning": "the fundamental law of a state",
    },
    "parliament": {
        "word": "parliament",
        "prefix": "",
        "prefix_meaning": "",
        "root": "parli",
        "root_meaning": "speak (French parler)",
        "suffix": "ment",
        "suffix_meaning": "mind/state/result of action",
        "is_negated": False,
        "true_meaning": "the speaking-mind — a place of talk, not action",
        "apparent_meaning": "a legislative body",
    },
    "authority": {
        "word": "authority",
        "prefix": "",
        "prefix_meaning": "",
        "root": "author",
        "root_meaning": "originator/creator/one who augments",
        "suffix": "ity",
        "suffix_meaning": "quality/state",
        "is_negated": False,
        "true_meaning": "the quality of authorship — one who creates the narrative",
        "apparent_meaning": "the power to give orders or make decisions",
    },
    "magistrate": {
        "word": "magistrate",
        "prefix": "",
        "prefix_meaning": "",
        "root": "magist",
        "root_meaning": "master/great",
        "suffix": "ate",
        "suffix_meaning": "to make/through/state",
        "is_negated": False,
        "true_meaning": "one made master — a master of the maritime court",
        "apparent_meaning": "a judicial officer",
    },
    "sovereign": {
        "word": "sovereign",
        "prefix": "",
        "prefix_meaning": "",
        "root": "sover",
        "root_meaning": "above/supreme",
        "suffix": "eign",
        "suffix_meaning": "rule/reign",
        "is_negated": False,
        "true_meaning": "one who rules from above — supreme authority on the land",
        "apparent_meaning": "a supreme ruler; possessing supreme power",
    },
    "subject": {
        "word": "subject",
        "prefix": "sub",
        "prefix_meaning": "under/below",
        "root": "ject",
        "root_meaning": "throw",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "thrown under — cast beneath authority",
        "apparent_meaning": "a topic; one under the dominion of a monarch",
    },
    "interest": {
        "word": "interest",
        "prefix": "inter",
        "prefix_meaning": "between/among",
        "root": "est",
        "root_meaning": "to be (Latin esse)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "being between — caught between two parties (inter-esse)",
        "apparent_meaning": "a charge for borrowing money; a feeling of curiosity",
    },
    "account": {
        "word": "account",
        "prefix": "ac",
        "prefix_meaning": "toward (variant of ad-)",
        "root": "count",
        "root_meaning": "reckon/calculate",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "a reckoning toward — the tally of your vessel's cargo",
        "apparent_meaning": "a record of financial transactions",
    },
    "credit": {
        "word": "credit",
        "prefix": "",
        "prefix_meaning": "",
        "root": "cred",
        "root_meaning": "believe/trust",
        "suffix": "it",
        "suffix_meaning": "that which",
        "is_negated": False,
        "true_meaning": "that which is believed — trust-based, not substance-based",
        "apparent_meaning": "trust in a buyer's ability to pay; recognition",
    },
    "debit": {
        "word": "debit",
        "prefix": "",
        "prefix_meaning": "",
        "root": "deb",
        "root_meaning": "owe",
        "suffix": "it",
        "suffix_meaning": "that which",
        "is_negated": False,
        "true_meaning": "that which is owed — a debt instrument",
        "apparent_meaning": "an entry recording an amount owed",
    },
    "bond": {
        "word": "bond",
        "prefix": "",
        "prefix_meaning": "",
        "root": "bond",
        "root_meaning": "bind/fetter/obligation",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "a binding — fettered obligation, a chain of debt",
        "apparent_meaning": "a certificate of debt; a connection",
    },
    "security": {
        "word": "security",
        "prefix": "",
        "prefix_meaning": "",
        "root": "sec",
        "root_meaning": "cut/separate",
        "suffix": "ity",
        "suffix_meaning": "quality/state",
        "is_negated": False,
        "true_meaning": "the state of being cut off — separated from danger (or from freedom)",
        "apparent_meaning": "the state of being free from danger; a financial instrument",
    },
    "title": {
        "word": "title",
        "prefix": "",
        "prefix_meaning": "",
        "root": "title",
        "root_meaning": "inscription/claim/designation (Latin titulus)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "an inscription of claim — the label on the cargo",
        "apparent_meaning": "a name; a legal right to property",
    },
    "estate": {
        "word": "estate",
        "prefix": "e",
        "prefix_meaning": "out of",
        "root": "stat",
        "root_meaning": "stand/state/fixed",
        "suffix": "ate",
        "suffix_meaning": "to make/through/state",
        "is_negated": False,
        "true_meaning": "a standing out of — one's fixed position/property in law",
        "apparent_meaning": "property, especially land; a person's total possessions",
    },
    "property": {
        "word": "property",
        "prefix": "",
        "prefix_meaning": "",
        "root": "proper",
        "root_meaning": "own/one's own",
        "suffix": "ty",
        "suffix_meaning": "quality/state",
        "is_negated": False,
        "true_meaning": "the quality of being one's own — that which belongs to you",
        "apparent_meaning": "a thing or things belonging to someone",
    },
    "invest": {
        "word": "invest",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "vest",
        "root_meaning": "clothe/garment (Latin vestis)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "to clothe IN / to put garments on — or NO clothing (stripped)",
        "apparent_meaning": "to put money into something for profit",
    },
    "invalid": {
        "word": "invalid",
        "prefix": "in",
        "prefix_meaning": "no/not",
        "root": "val",
        "root_meaning": "worth/strong",
        "suffix": "id",
        "suffix_meaning": "having the quality of",
        "is_negated": True,
        "true_meaning": "NO worth — without strength or value",
        "apparent_meaning": "not valid; a person with illness",
    },
    "abstract": {
        "word": "abstract",
        "prefix": "ab",
        "prefix_meaning": "away from",
        "root": "tract",
        "root_meaning": "pull/draw",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "pulled away from — drawn away from reality/substance",
        "apparent_meaning": "existing in thought only; a summary",
    },
    "obstruct": {
        "word": "obstruct",
        "prefix": "ob",
        "prefix_meaning": "against/toward",
        "root": "struct",
        "root_meaning": "build/arrange",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "built against — to build a barrier against",
        "apparent_meaning": "to block or hinder",
    },
    "inspect": {
        "word": "inspect",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "spect",
        "root_meaning": "look/see",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "to look INTO — or: NO true looking (superficial)",
        "apparent_meaning": "to examine closely",
    },
    "include": {
        "word": "include",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "clude",
        "root_meaning": "close/shut",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "to close IN / shut into — enclosed, limited, confined",
        "apparent_meaning": "to contain as part of something",
    },
    "exclude": {
        "word": "exclude",
        "prefix": "ex",
        "prefix_meaning": "out of/from",
        "root": "clude",
        "root_meaning": "close/shut",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "to close/shut OUT — locked outside",
        "apparent_meaning": "to deny access to; to leave out",
    },
    "income": {
        "word": "income",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "come",
        "root_meaning": "come/arrive",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "that which comes IN — or: NO coming (income tax = tax on nothing?)",
        "apparent_meaning": "money received from work or investments",
    },
    "adverse": {
        "word": "adverse",
        "prefix": "ad",
        "prefix_meaning": "toward",
        "root": "vers",
        "root_meaning": "turn",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "turned toward — facing against, opposition",
        "apparent_meaning": "unfavorable or harmful",
    },
    "invert": {
        "word": "invert",
        "prefix": "in",
        "prefix_meaning": "no/not/into",
        "root": "vert",
        "root_meaning": "turn",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "to turn IN / turn NOT — reversal of direction",
        "apparent_meaning": "to turn upside down or reverse",
    },
    "convert": {
        "word": "convert",
        "prefix": "con",
        "prefix_meaning": "together/with",
        "root": "vert",
        "root_meaning": "turn",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": False,
        "true_meaning": "to turn together — to change from one form to another",
        "apparent_meaning": "to change the form or character of something",
    },
    "assert": {
        "word": "assert",
        "prefix": "as",
        "prefix_meaning": "no/without",
        "root": "sert",
        "root_meaning": "join/bind (Latin serere)",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "WITHOUT binding — an unjoined/unbound claim",
        "apparent_meaning": "to state a fact or belief confidently",
    },
    "assign": {
        "word": "assign",
        "prefix": "as",
        "prefix_meaning": "no/without",
        "root": "sign",
        "root_meaning": "mark/seal",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "WITHOUT a true sign/mark — an unsigned allocation",
        "apparent_meaning": "to allocate or designate",
    },
    "insure": {
        "word": "insure",
        "prefix": "in",
        "prefix_meaning": "no/not",
        "root": "sure",
        "root_meaning": "certain/fixed/safe",
        "suffix": "",
        "suffix_meaning": "",
        "is_negated": True,
        "true_meaning": "NOT sure / NOT certain — the opposite of surety",
        "apparent_meaning": "to arrange for compensation in case of loss",
    },
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def is_vcc_negated(word: str) -> bool:
    """
    Returns True if the word starts with a VCC (Vowel-Consonant-Consonant)
    negation pattern.

    The rule: when a word begins with a VOWEL followed by one or more
    CONSONANTS, that vowel prefix acts as a NEGATION OPERATOR on the root.
    """
    word_lower = word.lower().strip()

    # Check known decompositions first
    if word_lower in KNOWN_DECOMPOSITIONS:
        return KNOWN_DECOMPOSITIONS[word_lower]["is_negated"]

    # Check for known VCC negation prefixes
    result = detect_negation_prefix(word_lower)
    if result is not None:
        prefix, _ = result
        return prefix in VCC_NEGATION_PREFIXES

    return False


def detect_negation_prefix(word: str) -> tuple[str, str] | None:
    """
    Detects if a word begins with a negation prefix.

    Returns (prefix, remainder) if a negation prefix is found, else None.

    Checks longer prefixes first to avoid false matches
    (e.g., "inter-" before "in-").
    """
    word_lower = word.lower().strip()

    if not word_lower:
        return None

    # Check known decompositions first
    if word_lower in KNOWN_DECOMPOSITIONS:
        entry = KNOWN_DECOMPOSITIONS[word_lower]
        pfx = entry["prefix"]
        if pfx and pfx in VCC_NEGATION_PREFIXES:
            remainder = word_lower[len(pfx):]
            return (pfx, remainder)
        return None

    # Sort VCC prefixes by length (longest first) to avoid partial matches
    sorted_prefixes = sorted(VCC_NEGATION_PREFIXES.keys(), key=len, reverse=True)

    for prefix in sorted_prefixes:
        if word_lower.startswith(prefix) and len(word_lower) > len(prefix):
            remainder = word_lower[len(prefix):]
            # Verify the remainder looks like a plausible root
            # (at least 2 characters remaining)
            if len(remainder) >= 2:
                return (prefix, remainder)

    return None


def _find_suffix(word: str) -> tuple[str, str, str]:
    """
    Attempt to identify a suffix in the word.
    Returns (stem, suffix, suffix_meaning).
    Checks longer suffixes first.
    """
    word_lower = word.lower()

    # Sort suffixes by length (longest first) to find best match
    sorted_suffixes = sorted(SUFFIXES.keys(), key=len, reverse=True)

    for suffix in sorted_suffixes:
        if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 1:
            stem = word_lower[:-len(suffix)]
            return (stem, suffix, SUFFIXES[suffix])

    return (word_lower, "", "")


def _find_root(stem: str) -> tuple[str, str]:
    """
    Attempt to match a stem against known roots.
    Returns (root, root_meaning) or (stem, "") if no match.
    """
    stem_lower = stem.lower()

    # Direct match
    if stem_lower in ROOTS:
        return (stem_lower, ROOTS[stem_lower])

    # Check if stem starts with a known root (longest match first)
    sorted_roots = sorted(ROOTS.keys(), key=len, reverse=True)
    for root in sorted_roots:
        if stem_lower.startswith(root) and len(root) >= 2:
            return (root, ROOTS[root])

    # Check if stem contains a known root
    for root in sorted_roots:
        if root in stem_lower and len(root) >= 3:
            return (root, ROOTS[root])

    return (stem_lower, "")


def decompose(word: str) -> dict:
    """
    Full morphological decomposition of a word.

    Returns a dict with keys:
        word, prefix, prefix_meaning, root, root_meaning,
        suffix, suffix_meaning, is_negated, true_meaning, apparent_meaning
    """
    word_lower = word.lower().strip()

    # Check known decompositions first
    if word_lower in KNOWN_DECOMPOSITIONS:
        return dict(KNOWN_DECOMPOSITIONS[word_lower])

    # --- Algorithmic decomposition ---

    # 1. Detect prefix
    prefix = ""
    prefix_meaning = ""
    remainder = word_lower

    # Check all prefixes (longest first)
    sorted_all_prefixes = sorted(PREFIXES.keys(), key=len, reverse=True)
    for pfx in sorted_all_prefixes:
        if word_lower.startswith(pfx) and len(word_lower) > len(pfx) + 1:
            # Make sure the remainder is plausible (not just 1-2 random chars)
            rest = word_lower[len(pfx):]
            if len(rest) >= 2:
                prefix = pfx
                prefix_meaning = PREFIXES[pfx]
                remainder = rest
                break

    # 2. Detect suffix from remainder
    stem, suffix, suffix_meaning = _find_suffix(remainder)

    # 3. Find root in stem
    root, root_meaning = _find_root(stem)

    # 4. Determine negation
    is_negated = prefix in VCC_NEGATION_PREFIXES

    # 5. Build true meaning
    parts = []
    if prefix_meaning:
        parts.append(prefix_meaning.upper())
    if root_meaning:
        parts.append(root_meaning)
    else:
        parts.append(root)
    if suffix_meaning:
        parts.append(f"({suffix_meaning})")

    true_meaning = " + ".join(parts) if parts else word_lower

    # 6. Apparent meaning (we don't have a general dictionary,
    #    so just note it's the common usage)
    apparent_meaning = f"common usage of '{word_lower}'"

    return {
        "word": word_lower,
        "prefix": prefix,
        "prefix_meaning": prefix_meaning,
        "root": root,
        "root_meaning": root_meaning,
        "suffix": suffix,
        "suffix_meaning": suffix_meaning,
        "is_negated": is_negated,
        "true_meaning": true_meaning,
        "apparent_meaning": apparent_meaning,
    }


def decompose_batch(words: list[str]) -> list[dict]:
    """Decompose multiple words at once."""
    return [decompose(w) for w in words]


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def list_negated_words() -> list[str]:
    """Return all known words that are VCC-negated."""
    return [
        word for word, entry in KNOWN_DECOMPOSITIONS.items()
        if entry["is_negated"]
    ]


def list_known_words() -> list[str]:
    """Return all words in the known decompositions dictionary."""
    return sorted(KNOWN_DECOMPOSITIONS.keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_decomposition(result: dict) -> None:
    """Pretty-print a decomposition result to stdout."""
    w = result["word"].upper()
    neg_tag = " [VCC NEGATED]" if result["is_negated"] else ""
    print(f"\n{'='*60}")
    print(f"  {w}{neg_tag}")
    print(f"{'='*60}")
    if result["prefix"]:
        print(f"  prefix : {result['prefix']}- ({result['prefix_meaning']})")
    print(f"  root   : {result['root']} ({result['root_meaning'] or '?'})")
    if result["suffix"]:
        print(f"  suffix : -{result['suffix']} ({result['suffix_meaning']})")
    print(f"  ---")
    print(f"  TRUE meaning     : {result['true_meaning']}")
    print(f"  APPARENT meaning : {result['apparent_meaning']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        words = sys.argv[1:]
    else:
        print("morpheme_negation.py — VCC Negation Engine")
        print("Usage: python morpheme_negation.py word1 word2 ...")
        print(f"\nKnown decompositions: {len(KNOWN_DECOMPOSITIONS)}")
        print(f"Known roots: {len(ROOTS)}")
        print(f"Known prefixes: {len(PREFIXES)}")
        print(f"Known suffixes: {len(SUFFIXES)}")
        print(f"\nVCC-negated words in database:")
        for w in list_negated_words():
            print(f"  - {w}")
        sys.exit(0)

    for word in words:
        result = decompose(word)
        _print_decomposition(result)
